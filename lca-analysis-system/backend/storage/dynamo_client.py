"""DynamoDB client helpers for the LCA system."""
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)

# In-memory storage for MOCK_AWS mode (no localstack required)
_in_memory_files: Dict[str, Dict[str, Any]] = {}
_in_memory_analyses: Dict[str, Dict[str, Any]] = {}


class InMemoryTable:
    """In-memory DynamoDB table simulator for local development."""

    def __init__(self, storage: Dict[str, Dict[str, Any]], key_name: str):
        self._storage = storage
        self._key_name = key_name

    def put_item(self, Item: Dict[str, Any]) -> None:
        key = Item.get(self._key_name)
        if key:
            self._storage[key] = dict(Item)

    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        key_value = Key.get(self._key_name)
        item = self._storage.get(key_value)
        return {"Item": item} if item else {}

    def update_item(self, Key: Dict[str, Any], UpdateExpression: str,
                    ExpressionAttributeNames: Dict[str, str],
                    ExpressionAttributeValues: Dict[str, Any]) -> None:
        key_value = Key.get(self._key_name)
        if key_value not in self._storage:
            self._storage[key_value] = {self._key_name: key_value}

        item = self._storage[key_value]
        # Simple parser for SET expressions
        if UpdateExpression.startswith("SET "):
            parts = UpdateExpression[4:].split(", ")
            for part in parts:
                alias, val_alias = part.split(" = ")
                attr_name = ExpressionAttributeNames.get(alias, alias.lstrip("#"))
                attr_value = ExpressionAttributeValues.get(val_alias)
                item[attr_name] = attr_value

    def query(self, IndexName: str = None, KeyConditionExpression: Any = None, **kwargs) -> Dict[str, Any]:
        # For in-memory, just do a scan with filter
        return self.scan(FilterExpression=KeyConditionExpression, **kwargs)

    def scan(self, FilterExpression: Any = None, **kwargs) -> Dict[str, Any]:
        items = list(self._storage.values())
        # Simple filtering - for job_id queries
        if FilterExpression is not None and hasattr(FilterExpression, '_values'):
            # Extract the filter value (job_id)
            filter_value = None
            for v in FilterExpression._values:
                if isinstance(v, str):
                    filter_value = v
                    break
            if filter_value:
                items = [item for item in items if item.get("job_id") == filter_value]
        return {"Items": items}


class InMemoryResource:
    """In-memory DynamoDB resource simulator."""

    def Table(self, table_name: str):
        if "files" in table_name.lower():
            return InMemoryTable(_in_memory_files, "file_id")
        else:
            return InMemoryTable(_in_memory_analyses, "analysis_id")


def _get_dynamo_resource():
    """Get DynamoDB resource, using in-memory storage if MOCK_AWS."""
    cfg = get_settings()
    if cfg.MOCK_AWS:
        logger.debug("using_in_memory_dynamo")
        return InMemoryResource()
    return boto3.resource(
        "dynamodb",
        region_name=cfg.AWS_REGION,
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def _convert_floats(obj: Any) -> Any:
    """Convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats(i) for i in obj]
    return obj


def _convert_decimals(obj: Any) -> Any:
    """Convert Decimal values back to float from DynamoDB responses."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimals(i) for i in obj]
    return obj


# ──────────────────── File Records ────────────────────

def put_file_record(record: Dict[str, Any]) -> None:
    """Write a file metadata record to the files table."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_FILES)
    table.put_item(Item=_convert_floats(record))


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """Get a file record by file_id."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_FILES)
    response = table.get_item(Key={"file_id": file_id})
    item = response.get("Item")
    return _convert_decimals(item) if item else None


def update_file_status(file_id: str, status: str, extra_attrs: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of a file record, with optional extra attributes."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_FILES)

    update_expr = "SET #s = :status"
    expr_names = {"#s": "status"}
    expr_values: Dict[str, Any] = {":status": status}

    if extra_attrs:
        for i, (k, v) in enumerate(extra_attrs.items()):
            alias = f"#a{i}"
            val_alias = f":v{i}"
            update_expr += f", {alias} = {val_alias}"
            expr_names[alias] = k
            expr_values[val_alias] = _convert_floats(v)

    table.update_item(
        Key={"file_id": file_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )


def get_files_by_job(job_id: str) -> List[Dict[str, Any]]:
    """Query all file records for a given job_id using GSI."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_FILES)
    try:
        response = table.query(
            IndexName="job_id-index",
            KeyConditionExpression=Key("job_id").eq(job_id),
        )
        return [_convert_decimals(item) for item in response.get("Items", [])]
    except ClientError:
        # If GSI doesn't exist, fall back to scan
        response = table.scan(
            FilterExpression=Attr("job_id").eq(job_id)
        )
        return [_convert_decimals(item) for item in response.get("Items", [])]


# ──────────────────── Analysis Records ────────────────────

def put_analysis_record(record: Dict[str, Any]) -> None:
    """Write an analysis (job) record to the analyses table."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_ANALYSES)
    item = dict(record)
    analysis_id = item.get("analysis_id") or item.get("job_id")
    if analysis_id:
        item["analysis_id"] = analysis_id
    table.put_item(Item=_convert_floats(item))


def get_analysis_record_sync(job_id: str) -> Optional[Dict[str, Any]]:
    """Get an analysis record by job_id."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_ANALYSES)
    response = table.get_item(Key={"analysis_id": job_id})
    item = response.get("Item")
    if item and "job_id" not in item:
        item["job_id"] = item.get("analysis_id", job_id)
    return _convert_decimals(item) if item else None


async def get_analysis_record(job_id: str) -> Optional[Dict[str, Any]]:
    return get_analysis_record_sync(job_id)


def update_analysis_status(job_id: str, status: str, extra_attrs: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of an analysis record."""
    cfg = get_settings()
    resource = _get_dynamo_resource()
    table = resource.Table(cfg.DYNAMO_TABLE_ANALYSES)

    update_expr = "SET #s = :status"
    expr_names = {"#s": "status"}
    expr_values: Dict[str, Any] = {":status": status}

    if extra_attrs:
        for i, (k, v) in enumerate(extra_attrs.items()):
            alias = f"#a{i}"
            val_alias = f":v{i}"
            update_expr += f", {alias} = {val_alias}"
            expr_names[alias] = k
            expr_values[val_alias] = _convert_floats(v)

    table.update_item(
        Key={"analysis_id": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )


# ──────────────────── Async Compatibility Layer ────────────────────

async def get_file_records_for_job(job_id: str) -> List[Dict[str, Any]]:
    return get_files_by_job(job_id)


async def update_file_record(file_id: str, attrs: Dict[str, Any]) -> None:
    current = get_file_record(file_id) or {}
    status = attrs.get("status") or current.get("status") or "PENDING"
    extra_attrs = {k: v for k, v in attrs.items() if k != "status"}
    update_file_status(file_id, status, extra_attrs=extra_attrs)


async def update_analysis_record(job_id: str, attrs: Dict[str, Any]) -> None:
    current = get_analysis_record_sync(job_id) or {}
    status = attrs.get("status") or current.get("status") or "PENDING"
    extra_attrs = {k: v for k, v in attrs.items() if k != "status"}
    update_analysis_status(job_id, status, extra_attrs=extra_attrs)
