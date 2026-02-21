"""Mind Map Agent — parse mind map files with VLM fallback."""
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional

from backend.agents.base_agent import BaseAgent
from backend.models.schemas import FileMetadata, ParsedOutput
from backend.models.enums import FileType
from backend.processing.bedrock_client import invoke_claude_haiku
from backend.processing.vlm_client import classify_image, extract_from_image
from backend.utils.logger import append_job_log, get_logger

logger = get_logger("mindmap_agent")


class MindMapAgent(BaseAgent):
    agent_name = "mindmap_agent"

    def process(self, file_meta: FileMetadata, file_bytes: bytes) -> ParsedOutput:
        markdown = ""
        warnings = []

        if file_meta.file_type == FileType.MINDMAP_XMIND:
            markdown = self._parse_xmind(file_bytes, warnings)
        elif file_meta.file_type == FileType.MINDMAP_FREEMIND:
            markdown = self._parse_freemind(file_bytes, warnings)
        elif file_meta.file_type == FileType.IMAGE:
            # VLM fallback for image exports of mind maps
            markdown = self._vlm_fallback(file_meta, file_bytes, warnings)
        else:
            # Try all parsers
            markdown = self._parse_xmind(file_bytes, warnings)
            if not markdown or markdown == "# Empty Mind Map":
                markdown = self._parse_freemind(file_bytes, warnings)
            if not markdown or markdown == "# Empty Mind Map":
                markdown = self._parse_mmap(file_bytes, warnings)

        if not markdown.strip():
            markdown = "# Unable to parse mind map"
            warnings.append("No content could be extracted from the mind map file")

        # Generate LCA context summary
        summary = ""
        if markdown and markdown != "# Unable to parse mind map":
            summary = self._generate_lca_summary(markdown, file_meta)
            if summary:
                markdown += f"\n\n## Mind Map Summary\n\n{summary}"

        lca_keywords = ["lca", "impact", "co2", "emission", "life cycle", "functional unit"]
        lca_relevant = any(kw in markdown.lower() for kw in lca_keywords)

        return ParsedOutput(
            file_id=file_meta.file_id,
            job_id=file_meta.job_id,
            agent=self.agent_name,
            markdown=markdown,
            structured_json={"mind_map_type": file_meta.file_type.value, "summary": summary},
            lca_relevant=lca_relevant,
            confidence=0.85 if markdown != "# Unable to parse mind map" else 0.2,
            word_count=len(markdown.split()),
            warnings=warnings,
        )

    def _parse_xmind(self, file_bytes: bytes, warnings: list) -> str:
        """Parse XMind (.xmind) file — ZIP archive with content.json or content.xml."""
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                names = zf.namelist()

                # Try content.json first (XMind 8+)
                if "content.json" in names:
                    content = json.loads(zf.read("content.json"))
                    if isinstance(content, list) and len(content) > 0:
                        root_topic = content[0].get("rootTopic", {})
                        return self._topic_to_markdown(root_topic, level=1)

                # Try content.xml (older XMind)
                if "content.xml" in names:
                    xml_bytes = zf.read("content.xml")
                    root = ET.fromstring(xml_bytes)
                    # Navigate XMind XML namespace
                    ns = {"xm": "urn:xmind:xmap:xmlns:content:2.0"}
                    topics = root.findall(".//xm:topic", ns) or root.findall(".//topic")
                    if topics:
                        return self._xml_topic_to_markdown(topics[0], level=1)

        except Exception as e:
            warnings.append(f"XMind parsing error: {str(e)}")
        return "# Empty Mind Map"

    def _parse_freemind(self, file_bytes: bytes, warnings: list) -> str:
        """Parse FreeMind (.mm) XML file."""
        try:
            root = ET.fromstring(file_bytes)
            map_elem = root if root.tag == "map" else root.find("map")
            if map_elem is None:
                map_elem = root

            nodes = map_elem.findall("node")
            if nodes:
                return self._freemind_node_to_markdown(nodes[0], level=1)
        except Exception as e:
            warnings.append(f"FreeMind parsing error: {str(e)}")
        return "# Empty Mind Map"

    def _parse_mmap(self, file_bytes: bytes, warnings: list) -> str:
        """Parse MindManager (.mmap) XML file."""
        try:
            root = ET.fromstring(file_bytes)
            topics = root.findall(".//Topic") or root.findall(".//topic")
            if topics:
                return self._mmap_topic_to_markdown(topics[0], level=1)
        except Exception as e:
            warnings.append(f"MindManager parsing error: {str(e)}")
        return "# Empty Mind Map"

    def _topic_to_markdown(self, topic: dict, level: int = 1) -> str:
        """Recursively convert XMind JSON topic to Markdown."""
        title = topic.get("title", "Untitled")
        if level == 1:
            md = f"# {title}\n"
        else:
            indent = "  " * (level - 2)
            md = f"{indent}- {title}\n"

        children = topic.get("children", {}).get("attached", [])
        for child in children:
            md += self._topic_to_markdown(child, level + 1)

        return md

    def _xml_topic_to_markdown(self, elem, level: int = 1) -> str:
        """Recursively convert XMind XML topic to Markdown."""
        title = elem.get("text", "") or elem.findtext("title", "")
        if not title:
            title_elem = elem.find("{urn:xmind:xmap:xmlns:content:2.0}title")
            title = title_elem.text if title_elem is not None else "Untitled"

        if level == 1:
            md = f"# {title}\n"
        else:
            indent = "  " * (level - 2)
            md = f"{indent}- {title}\n"

        for child in elem:
            if "topic" in child.tag.lower():
                md += self._xml_topic_to_markdown(child, level + 1)

        return md

    def _freemind_node_to_markdown(self, node, level: int = 1) -> str:
        """Recursively convert FreeMind node to Markdown."""
        text = node.get("TEXT", "") or node.get("text", "")
        if level == 1:
            md = f"# {text}\n"
        else:
            indent = "  " * (level - 2)
            md = f"{indent}- {text}\n"

        for child in node.findall("node"):
            md += self._freemind_node_to_markdown(child, level + 1)
        return md

    def _mmap_topic_to_markdown(self, topic, level: int = 1) -> str:
        """Recursively convert MindManager topic to Markdown."""
        text = topic.get("Text", "") or topic.get("text", "") or topic.text or ""
        if level == 1:
            md = f"# {text}\n"
        else:
            indent = "  " * (level - 2)
            md = f"{indent}- {text}\n"

        for child in topic.findall("Topic") + topic.findall("topic"):
            md += self._mmap_topic_to_markdown(child, level + 1)
        return md

    def _vlm_fallback(self, file_meta: FileMetadata, file_bytes: bytes, warnings: list) -> str:
        """Process mind map image via VLM."""
        try:
            extraction = extract_from_image(file_bytes, "mind_map")
            return f"# Mind Map (from image)\n\n{extraction}"
        except Exception as e:
            warnings.append(f"VLM fallback failed: {str(e)}")
            return "# Unable to parse mind map image"

    def _generate_lca_summary(self, markdown: str, file_meta: FileMetadata) -> str:
        """Generate an LCA context summary using Claude Haiku."""
        try:
            prompt = (
                "This is a mind map from an LCA study. Summarise the key topics, "
                "identify any LCA-specific nodes (impact categories, processes, life cycle stages, "
                "methodologies), and flag missing standard LCA components.\n\n"
                f"Mind map content:\n{markdown[:6000]}"
            )
            system = "You are an LCA expert. Provide a concise analysis summary."
            response = invoke_claude_haiku(prompt, system, max_tokens=1024)
            return response
        except Exception as e:
            logger.warning("lca_summary_failed", error=str(e))
            return ""
