import os
import json
import time
from datetime import datetime, timedelta

class CacheHandler:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, data):
        """Generate a cache key from data."""
        # Simple hash function for the data
        return str(hash(str(data)))
    
    def _get_cache_path(self, key):
        """Get the full path for a cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key):
        """Get data from cache if it exists and is not expired."""
        try:
            cache_path = self._get_cache_path(key)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r') as f:
                data = json.load(f)
                
            # Check if cache has expired
            if time.time() - data['timestamp'] > data['expiry']:
                os.remove(cache_path)  # Clean up expired cache
                return None
                
            return data['content']
            
        except Exception as e:
            print(f"Error reading from cache: {str(e)}")
            return None
    
    def set(self, key, content, expiry=24*60*60):
        """Save data to cache with expiration time."""
        try:
            cache_path = self._get_cache_path(key)
            data = {
                'content': content,
                'timestamp': time.time(),
                'expiry': expiry
            }
            
            with open(cache_path, 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            print(f"Error writing to cache: {str(e)}")
    
    def clear(self):
        """Clear all cached data."""
        try:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
    
    def clear_expired(self):
        """Remove expired cache entries."""
        try:
            for file in os.listdir(self.cache_dir):
                if not file.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.cache_dir, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if time.time() - data['timestamp'] > data['expiry']:
                        os.remove(file_path)
                except:
                    # If file is corrupted, remove it
                    os.remove(file_path)
                    
        except Exception as e:
            print(f"Error clearing expired cache: {str(e)}") 