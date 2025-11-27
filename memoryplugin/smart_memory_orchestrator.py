# smart_memory_orchestrator.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .memoryplugin_client import MemoryPluginClient


class SmartMemoryOrchestrator:
    """
    High-level orchestration on top of MemoryPluginClient.

    Responsibilities:
      - Bucket strategy (per-client, per-matter, per-project, etc.)
      - Write flows that accumulate enough memories for Smart Memory
      - Read flows that compress/retrieve only what's relevant
    """

    def __init__(
        self,
        client: MemoryPluginClient,
        *,
        min_memories_for_smart: int = 30,
    ) -> None:
        self.client = client
        self.min_memories_for_smart = min_memories_for_smart

    # ------------------------------------------------------------------
    # Bucket strategy
    # ------------------------------------------------------------------
    def ensure_bucket_for_namespace(
        self,
        namespace: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Idempotently ensure a bucket exists for a given namespace.

        Example namespace: 'client:ACME:case:1234'
        """
        buckets = self.client.list_buckets()
        for b in buckets:
            # Choose a convention: store namespace in name or metadata
            if b.get("name") == namespace or b.get("metadata", {}).get("namespace") == namespace:
                return b["id"]

        # Not found, create
        md = metadata or {}
        md.setdefault("namespace", namespace)

        created = self.client.create_bucket(
            name=namespace,
            description=description or f"Bucket for {namespace}",
            metadata=md,
        )
        return created["id"]

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def add_memory(
        self,
        namespace: str,
        content: str,
        *,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a memory in the namespace bucket, ensuring the bucket exists.
        """
        bucket_id = self.ensure_bucket_for_namespace(namespace)
        return self.client.create_memory(
            content,
            bucket_id=bucket_id,
            tags=tags,
            metadata=metadata,
            source=source,
        )

    # ------------------------------------------------------------------
    # Read / retrieval
    # ------------------------------------------------------------------
    def get_relevant_context(
        self,
        namespace: str,
        query: str,
        *,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve relevant memories for a query within a namespace.

        Returns:
          - list of memory objects
          - a small metadata dict with stats (e.g., how many available)
        """
        bucket_id = self.ensure_bucket_for_namespace(namespace)

        result = self.client.search_memories(
            query=query,
            bucket_id=bucket_id,
            limit=limit,
        )

        # This shape depends on API. We'll handle common patterns safely.
        memories: List[Dict[str, Any]]
        total_available: Optional[int] = None

        if isinstance(result, dict):
            # Common patterns: {"items": [...], "total": N} or {"results": [...]}
            if "items" in result:
                memories = result["items"]
            elif "results" in result:
                memories = result["results"]
            else:
                # Fallback if the API just returns a list
                memories = result.get("memories", []) or result.get("data", []) or []
            total_available = result.get("total") or result.get("total_count")
        elif isinstance(result, list):
            memories = result
            total_available = len(result)
        else:
            memories = []
            total_available = 0

        stats = {
            "total_available": total_available,
            "returned": len(memories),
            "limit": limit,
        }
        return memories, stats
