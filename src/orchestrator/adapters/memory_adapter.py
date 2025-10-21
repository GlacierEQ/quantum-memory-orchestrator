"""Base Memory Adapter Interface"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class MemoryRecord:
    """Universal memory record structure"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    source_system: str
    legal_relevance_score: float = 0.0
    cross_references: List[str] = None
    
    def __post_init__(self):
        if self.cross_references is None:
            self.cross_references = []

class MemoryAdapter(ABC):
    """Base class for all memory adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.system_name = self.__class__.__name__.replace("Adapter", "")
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the memory system"""
        pass
    
    @abstractmethod
    async def store(self, content: str, metadata: Dict[str, Any]) -> MemoryRecord:
        """Store content with metadata"""
        pass
    
    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryRecord]:
        """Search for memories"""
        pass
    
    @abstractmethod
    async def get_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve memory by ID"""
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> MemoryRecord:
        """Update existing memory"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete memory"""
        pass
    
    @abstractmethod
    async def sync_from_source(self, source_records: List[MemoryRecord]) -> Dict[str, Any]:
        """Sync records from another source"""
        pass
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get adapter health status"""
        return {
            "system": self.system_name,
            "initialized": self.is_initialized,
            "status": "healthy" if self.is_initialized else "not_initialized"
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            "system": self.system_name,
            "total_records": 0,  # Override in subclasses
            "last_sync": None
        }