"""DynamoDB client helpers for the LCA system."""
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from backend.config import settings


def _get_dynamo_resource():
    """Get DynamoDB resource, using localstack if MOCK_AWS."""
    if settings and settings.MOCK_AWS:
        return boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION,
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
    return boto3.resource(
        "dynamodb",
        region_name=settings.AWS_REGION if settings else "us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID if settings else None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if settings else None,
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
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_FILES if settings else "lca-files")
    table.put_item(Item=_convert_floats(record))


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """Get a file record by file_id."""
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_FILES if settings else "lca-files")
    response = table.get_item(Key={"file_id": file_id})
    item = response.get("Item")
    return _convert_decimals(item) if item else None


def update_file_status(file_id: str, status: str, extra_attrs: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of a file record, with optional extra attributes."""
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_FILES if settings else "lca-files")

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
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_FILES if settings else "lca-files")
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
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_ANALYSES if settings else "lca-analyses")
    item = dict(record)
    analysis_id = item.get("analysis_id") or item.get("job_id")
    if analysis_id:
        item["analysis_id"] = analysis_id
    table.put_item(Item=_convert_floats(item))


def get_analysis_record_sync(job_id: str) -> Optional[Dict[str, Any]]:
    """Get an analysis record by job_id."""
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_ANALYSES if settings else "lca-analyses")
    response = table.get_item(Key={"analysis_id": job_id})
    item = response.get("Item")
    if item and "job_id" not in item:
        item["job_id"] = item.get("analysis_id", job_id)
    return _convert_decimals(item) if item else None


async def get_analysis_record(job_id: str) -> Optional[Dict[str, Any]]:
    return get_analysis_record_sync(job_id)


def update_analysis_status(job_id: str, status: str, extra_attrs: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of an analysis record."""
    resource = _get_dynamo_resource()
    table = resource.Table(settings.DYNAMO_TABLE_ANALYSES if settings else "lca-analyses")

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
