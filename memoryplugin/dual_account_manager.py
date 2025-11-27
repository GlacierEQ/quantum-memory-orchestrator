# dual_account_manager.py

from __future__ import annotations

from typing import Dict, Optional

from .memoryplugin_client import MemoryPluginClient
from .smart_memory_orchestrator import SmartMemoryOrchestrator


class DualAccountManager:
    """
    Manages two MemoryPlugin accounts and routes traffic according to rules.

    Example:
      - account_legal: for legal/case-related namespaces
      - account_business: for ops/research/general namespaces
    """

    def __init__(
        self,
        api_key_legal: str,
        api_key_business: str,
        *,
        base_url: str = "https://api.memoryplugin.com",
    ) -> None:
        self.clients: Dict[str, SmartMemoryOrchestrator] = {
            "legal": SmartMemoryOrchestrator(
                MemoryPluginClient(api_key_legal, base_url=base_url)
            ),
            "business": SmartMemoryOrchestrator(
                MemoryPluginClient(api_key_business, base_url=base_url)
            ),
        }

    def _select_channel(self, namespace: str) -> str:
        """
        Basic routing logic.

        You can replace this with any rules you want, e.g.:
          - prefix patterns ('legal:', 'ops:', etc.)
          - explicit mapping table
        """
        ns_lower = namespace.lower()
        if "case:" in ns_lower or ns_lower.startswith("legal:"):
            return "legal"
        return "business"

    def get_orchestrator(self, namespace: str) -> SmartMemoryOrchestrator:
        channel = self._select_channel(namespace)
        return self.clients[channel]

    # Convenience API
    def add_memory(
        self,
        namespace: str,
        content: str,
        **kwargs,
    ):
        orch = self.get_orchestrator(namespace)
        return orch.add_memory(namespace, content, **kwargs)

    def get_relevant_context(
        self,
        namespace: str,
        query: str,
        **kwargs,
    ):
        orch = self.get_orchestrator(namespace)
        return orch.get_relevant_context(namespace, query, **kwargs)
