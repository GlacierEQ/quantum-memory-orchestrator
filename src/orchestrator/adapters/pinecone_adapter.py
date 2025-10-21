"""Pinecone Vector Database Adapter"""

import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .memory_adapter import MemoryAdapter, MemoryRecord

class PineconeAdapter(MemoryAdapter):
    """Pinecone vector database adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.index = None
        self.index_name = config.get("index_name", "quantum-memory")
    
    async def initialize(self) -> bool:
        """Initialize Pinecone client and index"""
        try:
            # For now, simulate Pinecone client initialization
            # In production, this would be: import pinecone
            
            self.client = MockPineconeClient(self.config.get("api_key"))
            self.index = await self.client.get_index(self.index_name)
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Pinecone initialization failed: {e}")
            return False
    
    async def store(self, content: str, metadata: Dict[str, Any]) -> MemoryRecord:
        """Store content in Pinecone as vector embedding"""
        if not self.is_initialized:
            raise RuntimeError("Pinecone adapter not initialized")
        
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Generate embedding (simulated)
        embedding = await self._generate_embedding(content)
        
        # Prepare metadata for Pinecone
        pinecone_metadata = {
            **metadata,
            "content": content[:1000],  # Pinecone has metadata size limits
            "timestamp": timestamp,
            "source_system": "Pinecone"
        }
        
        # Store vector in Pinecone
        await self.index.upsert([(record_id, embedding, pinecone_metadata)])
        
        return MemoryRecord(
            id=record_id,
            content=content,
            metadata=metadata,
            timestamp=timestamp,
            source_system="Pinecone",
            legal_relevance_score=metadata.get("legal_relevance", 0.0)
        )
    
    async def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryRecord]:
        """Search Pinecone using vector similarity"""
        if not self.is_initialized:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Search vectors
            search_results = await self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter=filters
            )
            
            records = []
            for match in search_results.get("matches", []):
                metadata = match.get("metadata", {})
                record = MemoryRecord(
                    id=match["id"],
                    content=metadata.get("content", ""),
                    metadata=metadata,
                    timestamp=metadata.get("timestamp", datetime.now().isoformat()),
                    source_system="Pinecone",
                    legal_relevance_score=metadata.get("legal_relevance", 0.0)
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"Pinecone search failed: {e}")
            return []
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """Get memory by ID from Pinecone"""
        if not self.is_initialized:
            return None
        
        try:
            result = await self.index.fetch([memory_id])
            vectors = result.get("vectors", {})
            
            if memory_id in vectors:
                vector_data = vectors[memory_id]
                metadata = vector_data.get("metadata", {})
                
                return MemoryRecord(
                    id=memory_id,
                    content=metadata.get("content", ""),
                    metadata=metadata,
                    timestamp=metadata.get("timestamp", datetime.now().isoformat()),
                    source_system="Pinecone"
                )
            
            return None
            
        except Exception as e:
            print(f"Pinecone get_by_id failed: {e}")
            return None
    
    async def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> MemoryRecord:
        """Update existing memory in Pinecone"""
        if not self.is_initialized:
            raise RuntimeError("Pinecone adapter not initialized")
        
        # Get existing record
        existing = await self.get_by_id(memory_id)
        if not existing:
            raise ValueError(f"Memory {memory_id} not found")
        
        # Update content and metadata
        if content:
            existing.content = content
        if metadata:
            existing.metadata.update(metadata)
        
        # Re-store with same ID
        embedding = await self._generate_embedding(existing.content)
        pinecone_metadata = {
            **existing.metadata,
            "content": existing.content[:1000],
            "timestamp": datetime.now().isoformat()
        }
        
        await self.index.upsert([(memory_id, embedding, pinecone_metadata)])
        
        return existing
    
    async def delete(self, memory_id: str) -> bool:
        """Delete memory from Pinecone"""
        if not self.is_initialized:
            return False
        
        try:
            await self.index.delete([memory_id])
            return True
        except Exception as e:
            print(f"Pinecone delete failed: {e}")
            return False
    
    async def sync_from_source(self, source_records: List[MemoryRecord]) -> Dict[str, Any]:
        """Sync records from another source to Pinecone"""
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
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (simulated)"""
        # In production, use actual embedding model like OpenAI or Sentence Transformers
        # For now, return dummy embedding
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to pseudo-embedding (1536 dimensions like OpenAI)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            byte_val = int(hash_hex[i:i+2], 16)
            embedding.extend([float(byte_val) / 255.0, -float(byte_val) / 255.0])
        
        # Pad to 1536 dimensions
        while len(embedding) < 1536:
            embedding.append(0.0)
        
        return embedding[:1536]

# Mock Pinecone client for development/testing
class MockPineconeClient:
    """Mock Pinecone client for development"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.indexes = {}
    
    async def get_index(self, index_name: str):
        if index_name not in self.indexes:
            self.indexes[index_name] = MockPineconeIndex(index_name)
        return self.indexes[index_name]

class MockPineconeIndex:
    """Mock Pinecone index for development"""
    
    def __init__(self, name: str):
        self.name = name
        self.vectors = {}
    
    async def upsert(self, vectors: List[tuple]):
        for vector_id, embedding, metadata in vectors:
            self.vectors[vector_id] = {
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            }
    
    async def query(self, vector: List[float], top_k: int = 10, include_metadata: bool = True, filter: Dict = None):
        # Simple mock similarity search
        matches = []
        for vec_data in list(self.vectors.values())[:top_k]:
            matches.append({
                "id": vec_data["id"],
                "score": 0.8,  # Mock similarity score
                "metadata": vec_data["metadata"] if include_metadata else None
            })
        
        return {"matches": matches}
    
    async def fetch(self, ids: List[str]):
        vectors = {}
        for vector_id in ids:
            if vector_id in self.vectors:
                vectors[vector_id] = self.vectors[vector_id]
        return {"vectors": vectors}
    
    async def delete(self, ids: List[str]):
        for vector_id in ids:
            if vector_id in self.vectors:
                del self.vectors[vector_id]