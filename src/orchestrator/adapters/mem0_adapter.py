"""Mem0 Memory Adapter"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .memory_adapter import MemoryAdapter, MemoryRecord

class Mem0Adapter(MemoryAdapter):
    """Mem0 memory system adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.client_secondary = None
    
    async def initialize(self) -> bool:
        """Initialize Mem0 client(s)"""
        try:
            # For now, simulate Mem0 client initialization
            # In production, this would be: from mem0 import MemoryClient
            
            self.client = MockMem0Client(self.config.get("api_key"))
            
            # Initialize secondary client if available
            if self.config.get("api_key_secondary"):
                self.client_secondary = MockMem0Client(self.config.get("api_key_secondary"))
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Mem0 initialization failed: {e}")
            return False
    
    async def store(self, content: str, metadata: Dict[str, Any]) -> MemoryRecord:
        """Store content in Mem0"""
        if not self.is_initialized:
            raise RuntimeError("Mem0 adapter not initialized")
        
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Store in primary client
        primary_result = await self.client.add(content, {**metadata, "id": record_id})
        
        # Store in secondary client if available
        if self.client_secondary:
            await self.client_secondary.add(content, {**metadata, "id": record_id})
        
        return MemoryRecord(
            id=record_id,
            content=content,
            metadata=metadata,
            timestamp=timestamp,
            source_system="Mem0",
            legal_relevance_score=metadata.get("legal_relevance", 0.0)
        )
    
    async def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryRecord]:
        """Search Mem0 memories"""
        if not self.is_initialized:
            return []
        
        try:
            results = await self.client.search(query, limit=limit)
            
            records = []
            for result in results:
                record = MemoryRecord(
                    id=result.get("id", str(uuid.uuid4())),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    source_system="Mem0",
                    legal_relevance_score=result.get("legal_relevance", 0.0)
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"Mem0 search failed: {e}")
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
                    source_system="Mem0"
                )
            return None
            
        except Exception as e:
            print(f"Mem0 get_by_id failed: {e}")
            return None
    
    async def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> MemoryRecord:
        """Update existing memory"""
        if not self.is_initialized:
            raise RuntimeError("Mem0 adapter not initialized")
        
        # Implementation depends on Mem0 API
        # For now, simulate update
        existing = await self.get_by_id(memory_id)
        if existing:
            if content:
                existing.content = content
            if metadata:
                existing.metadata.update(metadata)
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
            print(f"Mem0 delete failed: {e}")
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
class MockMem0Client:
    """Mock Mem0 client for development"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.memories = {}
    
    async def add(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        record_id = metadata.get("id", str(uuid.uuid4()))
        self.memories[record_id] = {
            "id": record_id,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        return {"id": record_id, "status": "stored"}
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Simple keyword search in mock
        results = []
        query_lower = query.lower()
        
        for memory in list(self.memories.values())[:limit]:
            if query_lower in memory["content"].lower():
                results.append(memory)
        
        return results
    
    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.memories.get(memory_id)
    
    async def delete(self, memory_id: str) -> bool:
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False