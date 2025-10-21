"""Quantum Memory Orchestrator - Universal Intelligence System"""

__version__ = "1.0.0"
__author__ = "Casey - SOVEREIGNASCENSIONPROTOCOLV12.31COSMICAPEX"

from .core import QuantumMemoryOrchestrator
from .services.universal_memory import UniversalMemoryService
from .services.legal_workflow import LegalWorkflowService
from .services.github_ops import GitHubOpsService

__all__ = [
    "QuantumMemoryOrchestrator",
    "UniversalMemoryService", 
    "LegalWorkflowService",
    "GitHubOpsService"
]