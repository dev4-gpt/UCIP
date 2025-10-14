"""Redis-based feature store for fast ML feature access."""
import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import redis
from loguru import logger


class RedisFeatureStore:
    """Redis feature store for caching ML features."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        """Initialize Redis feature store.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional password
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False  # Handle binary data
        )
        
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")

    def set_feature(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "features",
    ) -> bool:
        """Store a feature in Redis.
        
        Args:
            key: Feature key
            value: Feature value (can be dict, list, array, etc.)
            ttl: Time to live in seconds
            namespace: Feature namespace
            
        Returns:
            True if successful
        """
        full_key = f"{namespace}:{key}"
        
        try:
            # Serialize value
            if isinstance(value, np.ndarray):
                serialized = json.dumps({
                    "type": "numpy",
                    "data": value.tolist(),
                    "dtype": str(value.dtype),
                    "shape": value.shape
                })
            elif isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            if ttl:
                self.client.setex(full_key, ttl, serialized)
            else:
                self.client.set(full_key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Error setting feature {full_key}: {e}")
            return False

    def get_feature(
        self,
        key: str,
        namespace: str = "features",
    ) -> Optional[Any]:
        """Retrieve a feature from Redis.
        
        Args:
            key: Feature key
            namespace: Feature namespace
            
        Returns:
            Feature value or None if not found
        """
        full_key = f"{namespace}:{key}"
        
        try:
            value = self.client.get(full_key)
            if value is None:
                return None
            
            # Deserialize value
            value_str = value.decode('utf-8')
            
            try:
                data = json.loads(value_str)
                if isinstance(data, dict) and data.get("type") == "numpy":
                    return np.array(data["data"], dtype=data["dtype"]).reshape(data["shape"])
                return data
            except json.JSONDecodeError:
                return value_str
                
        except Exception as e:
            logger.error(f"Error getting feature {full_key}: {e}")
            return None

    def set_batch(
        self,
        features: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: str = "features",
    ) -> int:
        """Store multiple features in a batch.
        
        Args:
            features: Dictionary of key-value pairs
            ttl: Time to live in seconds
            namespace: Feature namespace
            
        Returns:
            Number of features successfully stored
        """
        count = 0
        for key, value in features.items():
            if self.set_feature(key, value, ttl, namespace):
                count += 1
        return count

    def get_batch(
        self,
        keys: List[str],
        namespace: str = "features",
    ) -> Dict[str, Any]:
        """Retrieve multiple features in a batch.
        
        Args:
            keys: List of feature keys
            namespace: Feature namespace
            
        Returns:
            Dictionary of key-value pairs
        """
        results = {}
        for key in keys:
            value = self.get_feature(key, namespace)
            if value is not None:
                results[key] = value
        return results

    def delete_feature(
        self,
        key: str,
        namespace: str = "features",
    ) -> bool:
        """Delete a feature from Redis.
        
        Args:
            key: Feature key
            namespace: Feature namespace
            
        Returns:
            True if successful
        """
        full_key = f"{namespace}:{key}"
        try:
            self.client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting feature {full_key}: {e}")
            return False

    def list_keys(
        self,
        pattern: str = "*",
        namespace: str = "features",
    ) -> List[str]:
        """List feature keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            namespace: Feature namespace
            
        Returns:
            List of matching keys
        """
        full_pattern = f"{namespace}:{pattern}"
        try:
            keys = self.client.keys(full_pattern)
            # Remove namespace prefix
            return [k.decode('utf-8').replace(f"{namespace}:", "") for k in keys]
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []

    def clear_namespace(self, namespace: str = "features") -> int:
        """Clear all features in a namespace.
        
        Args:
            namespace: Feature namespace
            
        Returns:
            Number of keys deleted
        """
        keys = self.client.keys(f"{namespace}:*")
        if keys:
            return self.client.delete(*keys)
        return 0


def main():
    """Example usage."""
    store = RedisFeatureStore()
    
    # Store a simple feature
    store.set_feature("building_001:temp", 72.5, ttl=3600)
    
    # Store a numpy array
    features = np.random.rand(10, 5)
    store.set_feature("building_001:embeddings", features)
    
    # Store a dictionary
    metadata = {
        "building_id": "001",
        "timestamp": "2024-10-13T12:00:00",
        "sensor_count": 5
    }
    store.set_feature("building_001:metadata", metadata)
    
    # Retrieve features
    temp = store.get_feature("building_001:temp")
    embeddings = store.get_feature("building_001:embeddings")
    meta = store.get_feature("building_001:metadata")
    
    logger.info(f"Temperature: {temp}")
    logger.info(f"Embeddings shape: {embeddings.shape if embeddings is not None else None}")
    logger.info(f"Metadata: {meta}")
    
    # List all keys
    keys = store.list_keys()
    logger.info(f"All keys: {keys}")


if __name__ == "__main__":
    main()

