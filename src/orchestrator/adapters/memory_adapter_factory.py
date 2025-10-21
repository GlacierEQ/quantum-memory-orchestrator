"""Factory for creating and managing memory adapters"""

import os
from typing import Dict, List, Any, Optional
import logging

from .memory_adapter import MemoryAdapter
from .mem0_adapter import Mem0Adapter
from .pinecone_adapter import PineconeAdapter
from .supermemory_adapter import SuperMemoryAdapter

class MemoryAdapterFactory:
    """Factory for creating and managing memory adapters"""
    
    ADAPTER_CLASSES = {
        "mem0": Mem0Adapter,
        "pinecone": PineconeAdapter,
        "supermemory": SuperMemoryAdapter
    }
    
    def __init__(self):
        self.logger = logging.getLogger("AdapterFactory")
        self.adapters: Dict[str, MemoryAdapter] = {}
    
    async def initialize_all_adapters(self) -> Dict[str, Any]:
        """Initialize all available adapters based on environment configuration"""
        results = {}
        
        for adapter_name, adapter_class in self.ADAPTER_CLASSES.items():
            try:
                config = self._get_adapter_config(adapter_name)
                if config and self._check_required_config(adapter_name, config):
                    adapter = adapter_class(config)
                    success = await adapter.initialize()
                    
                    if success:
                        self.adapters[adapter_name] = adapter
                        results[adapter_name] = {"status": "initialized", "config_keys": list(config.keys())}
                        self.logger.info(f"✅ {adapter_name.upper()} adapter initialized")
                    else:
                        results[adapter_name] = {"status": "failed_initialization"}
                        self.logger.warning(f"❌ {adapter_name.upper()} adapter failed to initialize")
                else:
                    results[adapter_name] = {"status": "missing_config"}
                    self.logger.info(f"⚠️ {adapter_name.upper()} adapter skipped - missing config")
                    
            except Exception as e:
                results[adapter_name] = {"status": "error", "error": str(e)}
                self.logger.error(f"❌ {adapter_name.upper()} adapter error: {e}")
        
        return results
    
    def _get_adapter_config(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific adapter from environment"""
        configs = {
            "mem0": {
                "api_key": os.getenv("MEM0_API_KEY"),
                "api_key_secondary": os.getenv("MEM0_API_KEY_SECONDARY"),
                "base_url": os.getenv("MEM0_BASE_URL")
            },
            "pinecone": {
                "api_key": os.getenv("PINECONE_API_KEY"),
                "environment": os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free"),
                "index_name": os.getenv("PINECONE_INDEX_NAME", "quantum-memory")
            },
            "supermemory": {
                "api_key": os.getenv("SUPERMEMORY_API_KEY"),
                "base_url": os.getenv("SUPERMEMORY_BASE_URL")
            }
        }
        
        return configs.get(adapter_name)
    
    def _check_required_config(self, adapter_name: str, config: Dict[str, Any]) -> bool:
        """Check if required configuration is present"""
        required_keys = {
            "mem0": ["api_key"],
            "pinecone": ["api_key"],
            "supermemory": ["api_key"]
        }
        
        required = required_keys.get(adapter_name, [])
        return all(config.get(key) for key in required)
    
    def get_adapter(self, adapter_name: str) -> Optional[MemoryAdapter]:
        """Get initialized adapter by name"""
        return self.adapters.get(adapter_name)
    
    def get_all_adapters(self) -> Dict[str, MemoryAdapter]:
        """Get all initialized adapters"""
        return self.adapters.copy()
    
    async def get_adapter_health(self) -> Dict[str, Any]:
        """Get health status of all adapters"""
        health_status = {}
        
        for name, adapter in self.adapters.items():
            health_status[name] = await adapter.get_health_status()
        
        return health_status