"""SuperMemory Adapter"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .memory_adapter import MemoryAdapter, MemoryRecord

class SuperMemoryAdapter(MemoryAdapter):
    """SuperMemory system adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
    
    async def initialize(self) -> bool:
        """Initialize SuperMemory client"""
        try:
            # For now, simulate SuperMemory client initialization
            # In production, this would be: from supermemory import SuperMemoryClient
            
            self.client = MockSuperMemoryClient(self.config.get("api_key"))
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"SuperMemory initialization failed: {e}")
            return False
    
    async def store(self, content: str, metadata: Dict[str, Any]) -> MemoryRecord:
        """Store content in SuperMemory"""
        if not self.is_initialized:
            raise RuntimeError("SuperMemory adapter not initialized")
        
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Store in SuperMemory
        result = await self.client.store(content, {**metadata, "id": record_id})
        
        return MemoryRecord(
            id=record_id,
            content=content,
            metadata=metadata,
            timestamp=timestamp,
            source_system="SuperMemory",
            legal_relevance_score=metadata.get("legal_relevance", 0.0)
        )
    
    async def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryRecord]:
        """Search SuperMemory"""
        if not self.is_initialized:
            return []
        
        try:
            results = await self.client.search(query, limit=limit, filters=filters)
            
            records = []
            for result in results:
                record = MemoryRecord(
                    id=result.get("id", str(uuid.uuid4())),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    source_system="SuperMemory",
                    legal_relevance_score=result.get("legal_relevance", 0.0)
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"SuperMemory search failed: {e}")
            return []
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """Get memory by ID"""
        if not self.is_initialized:
            return None
        
        try:
            result = await self.client.get(memory_id)
            if result:
                return MemoryRecord(
                    id=memory_id,
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    source_system="SuperMemory"
                )
            return None
            
        except Exception as e:
            print(f"SuperMemory get_by_id failed: {e}")
            return None
    
    async def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> MemoryRecord:
        """Update existing memory"""
        if not self.is_initialized:
            raise RuntimeError("SuperMemory adapter not initialized")
        
        existing = await self.get_by_id(memory_id)
        if existing:
            if content:
                existing.content = content
            if metadata:
                existing.metadata.update(metadata)
            
            # Re-store updated record
            await self.client.update(memory_id, existing.content, existing.metadata)
            return existing
        
        raise ValueError(f"Memory {memory_id} not found")
    
    async def delete(self, memory_id: str) -> bool:
        """Delete memory"""
        if not self.is_initialized:
            return False
        
        try:
            await self.client.delete(memory_id)
            return True
        except Exception as e:
            print(f"SuperMemory delete failed: {e}")
            return False
    
    async def sync_from_source(self, source_records: List[MemoryRecord]) -> Dict[str, Any]:
        """Sync records from another source"""
        if not self.is_initialized:
            return {"synced": 0, "errors": 1, "message": "Not initialized"}
        
        synced = 0
        errors = 0
        
        for record in source_records:
            try:
                await self.store(record.content, record.metadata)
                synced += 1
            except Exception as e:
                print(f"Sync error for record {record.id}: {e}")
                errors += 1
        
        return {"synced": synced, "errors": errors}

# Mock client for development/testing
class MockSuperMemoryClient:
    """Mock SuperMemory client for development"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.memories = {}
    
    async def store(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        record_id = metadata.get("id", str(uuid.uuid4()))
        self.memories[record_id] = {
            "id": record_id,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        return {"id": record_id, "status": "stored"}
    
    async def search(self, query: str, limit: int = 10, filters: Dict = None) -> List[Dict[str, Any]]:
        # Simple keyword search in mock
        results = []
        query_lower = query.lower()
        
        for memory in list(self.memories.values())[:limit]:
            if query_lower in memory["content"].lower():
                results.append(memory)
        
        return results
    
    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.memories.get(memory_id)
    
    async def update(self, memory_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        if memory_id in self.memories:
            self.memories[memory_id]["content"] = content
            self.memories[memory_id]["metadata"].update(metadata)
            return True
        return False
    
    async def delete(self, memory_id: str) -> bool:
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False