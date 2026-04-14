"""Knowledge Base retrieval module.

Queries a Bedrock Knowledge Base backed by S3 documents (SOPs, compliance
checklists, training materials) to enrich agent responses with relevant
policy and procedural context.

For the hackathon demo, this module can operate in two modes:
1. LIVE mode: Queries a real Bedrock Knowledge Base via the RetrieveAndGenerate API
2. LOCAL mode: Searches local markdown files in knowledge_base/ directory

Set KNOWLEDGE_BASE_ID env var to enable LIVE mode. Otherwise falls back to LOCAL.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
_KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"

# Cache loaded docs
_local_docs: list[dict] | None = None


def retrieve(query: str, max_results: int = 3) -> list[dict]:
    """Retrieve relevant documents for a query.

    Returns a list of dicts with 'title', 'excerpt', and 'source' fields.
    """
    if _KNOWLEDGE_BASE_ID:
        return _retrieve_from_bedrock(query, max_results)
    return _retrieve_from_local(query, max_results)


def _retrieve_from_bedrock(query: str, max_results: int) -> list[dict]:
    """Query Bedrock Knowledge Base via Retrieve API."""
    try:
        import boto3
        client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

        response = client.retrieve(
            knowledgeBaseId=_KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results,
                }
            },
        )

        results = []
        for result in response.get("retrievalResults", []):
            content = result.get("content", {}).get("text", "")
            source = result.get("location", {}).get("s3Location", {}).get("uri", "")
            title = source.split("/")[-1] if source else "Unknown"

            results.append({
                "title": title,
                "excerpt": content[:500],
                "source": source,
                "score": result.get("score", 0),
            })

        return results

    except Exception as e:
        logger.error("Bedrock KB retrieval failed: %s — falling back to local", e)
        return _retrieve_from_local(query, max_results)


def _retrieve_from_local(query: str, max_results: int) -> list[dict]:
    """Simple keyword search against local markdown files."""
    global _local_docs
    if _local_docs is None:
        _local_docs = _load_local_docs()

    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for doc in _local_docs:
        content_lower = doc["content"].lower()
        # Simple relevance: count matching query words in content
        score = sum(1 for w in query_words if w in content_lower)
        # Boost for title matches
        title_lower = doc["title"].lower()
        score += sum(3 for w in query_words if w in title_lower)

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, doc in scored[:max_results]:
        # Extract a relevant excerpt (first paragraph containing a query word)
        paragraphs = doc["content"].split("\n\n")
        excerpt = ""
        for para in paragraphs:
            if any(w in para.lower() for w in query_words):
                excerpt = para.strip()[:500]
                break
        if not excerpt:
            excerpt = paragraphs[0].strip()[:500] if paragraphs else ""

        results.append({
            "title": doc["title"],
            "excerpt": excerpt,
            "source": doc["path"],
            "score": score,
        })

    return results


def _load_local_docs() -> list[dict]:
    """Load all markdown files from the knowledge_base directory."""
    docs = []
    if not _KB_DIR.exists():
        return docs

    for md_file in _KB_DIR.rglob("*.md"):
        content = md_file.read_text()
        # Extract title from first heading
        title = md_file.stem.replace("-", " ").title()
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        docs.append({
            "title": title,
            "content": content,
            "path": str(md_file.relative_to(_KB_DIR)),
            "category": md_file.parent.name,
        })

    logger.info("Loaded %d local knowledge base documents", len(docs))
    return docs
