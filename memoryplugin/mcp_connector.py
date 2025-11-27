# mcp_connector.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .dual_account_manager import DualAccountManager


class MemoryPluginMCPTooling:
    """
    Expose MemoryPlugin as MCP tools.

    This is a skeleton; adapt it to your specific MCP framework.
    """

    def __init__(
        self,
        api_key_legal: str,
        api_key_business: str,
        base_url: str = "https://api.memoryplugin.com",
    ) -> None:
        self.manager = DualAccountManager(
            api_key_legal=api_key_legal,
            api_key_business=api_key_business,
            base_url=base_url,
        )

    # Example MCP "tools" (you'll map these to JSON-RPC / tool definitions)

    def tool_add_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args expected (JSON):
          - namespace: str
          - content: str
          - tags: [str] (optional)
          - metadata: dict (optional)
          - source: str (optional)
        """
        namespace = args["namespace"]
        content = args["content"]
        tags = args.get("tags")
        metadata = args.get("metadata")
        source = args.get("source")

        result = self.manager.add_memory(
            namespace=namespace,
            content=content,
            tags=tags,
            metadata=metadata,
            source=source,
        )
        return {"status": "ok", "memory": result}

    def tool_get_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args expected:
          - namespace: str
          - query: str
          - limit: int (optional)
        """
        namespace = args["namespace"]
        query = args["query"]
        limit = int(args.get("limit", 10))

        memories, stats = self.manager.get_relevant_context(
            namespace=namespace,
            query=query,
            limit=limit,
        )
        return {"status": "ok", "memories": memories, "stats": stats}
