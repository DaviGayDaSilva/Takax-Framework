#!/usr/bin/env python3
"""
Build Cache - Cache management for faster builds
"""

import os
import json
import hashlib
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry for build artifacts"""
    key: str
    recipe_hash: str
    output_path: str
    created_at: float
    size: int
    hits: int = 0


class BuildCache:
    """
    Build cache for storing and reusing build artifacts.
    
    Reduces build time by caching base systems and packages.
    """
    
    def __init__(self, cache_dir: str = ".takax/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.entries: Dict[str, CacheEntry] = {}
        self.max_size = 5 * 1024 * 1024 * 1024  # 5GB default
        self._load_index()
        
    def _load_index(self):
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file) as f:
                    data = json.load(f)
                    for key, entry in data.get("entries", {}).items():
                        self.entries[key] = CacheEntry(**entry)
            except:
                pass
                
    def _save_index(self):
        """Save cache index to disk."""
        data = {
            "entries": {
                key: {
                    "key": entry.key,
                    "recipe_hash": entry.recipe_hash,
                    "output_path": entry.output_path,
                    "created_at": entry.created_at,
                    "size": entry.size,
                    "hits": entry.hits
                }
                for key, entry in self.entries.items()
            }
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _get_recipe_hash(self, recipe: Dict[str, Any]) -> str:
        """Generate hash from recipe."""
        recipe_str = json.dumps(recipe, sort_keys=True)
        return hashlib.sha256(recipe_str.encode()).hexdigest()[:16]
        
    def get(self, recipe: Dict[str, Any]) -> Optional[str]:
        """
        Get cached output path for recipe.
        
        Args:
            recipe: Recipe dictionary
            
        Returns:
            Cached output path or None
        """
        recipe_hash = self._get_recipe_hash(recipe)
        
        # Find matching entry
        for key, entry in self.entries.items():
            if entry.recipe_hash == recipe_hash:
                # Check if files still exist
                if Path(entry.output_path).exists():
                    entry.hits += 1
                    self._save_index()
                    return entry.output_path
                    
        return None
        
    def put(self, recipe: Dict[str, Any], output_path: str) -> bool:
        """
        Cache build output.
        
        Args:
            recipe: Recipe dictionary
            output_path: Path to output
            
        Returns:
            True if cached successfully
        """
        # Check cache size
        if self._get_cache_size() > self.max_size:
            self._evict_oldest()
            
        recipe_hash = self._get_recipe_hash(recipe)
        key = f"cache-{recipe_hash}"
        
        # Copy to cache
        cache_path = self.cache_dir / key
        try:
            shutil.copytree(output_path, cache_path, dirs_exist_ok=True)
            
            # Get size
            size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
            
            # Add to index
            self.entries[key] = CacheEntry(
                key=key,
                recipe_hash=recipe_hash,
                output_path=str(cache_path),
                created_at=time.time(),
                size=size
            )
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"Cache put error: {e}")
            return False
            
    def _get_cache_size(self) -> int:
        """Get total cache size."""
        total = 0
        for entry in self.entries.values():
            total += entry.size
        return total
        
    def _evict_oldest(self):
        """Evict oldest cache entries."""
        if not self.entries:
            return
            
        # Sort by created_at
        sorted_entries = sorted(self.entries.values(), key=lambda e: e.created_at)
        
        # Remove oldest entries until under limit
        for entry in sorted_entries:
            if self._get_cache_size() <= self.max_size * 0.8:
                break
                
            # Remove files
            try:
                shutil.rmtree(entry.output_path)
            except:
                pass
                
            # Remove from index
            del self.entries[entry.key]
            
        self._save_index()
        
    def clear(self):
        """Clear all cache."""
        for entry in self.entries.values():
            try:
                shutil.rmtree(entry.output_path)
            except:
                pass
                
        self.entries.clear()
        self._save_index()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = self._get_cache_size()
        
        return {
            "entries": len(self.entries),
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size": self.max_size,
            "usage_percent": (total_size / self.max_size) * 100 if self.max_size > 0 else 0,
            "hits": sum(e.hits for e in self.entries.values())
        }
        
    def list_entries(self) -> List[Dict[str, Any]]:
        """List all cache entries."""
        return [
            {
                "key": key,
                "recipe_hash": entry.recipe_hash,
                "size_mb": entry.size / (1024 * 1024),
                "created": time.ctime(entry.created_at),
                "hits": entry.hits
            }
            for key, entry in self.entries.items()
        ]


class PackageCache:
    """Cache for downloaded packages."""
    
    def __init__(self, cache_dir: str = ".takax/packages"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_package_path(self, distro: str, package: str) -> Optional[Path]:
        """Get path to cached package."""
        package_dir = self.cache_dir / distro
        
        if not package_dir.exists():
            return None
            
        for file in package_dir.glob(f"{package}_*"):
            return file
            
        return None
        
    def add_package(self, distro: str, package: str, filepath: str) -> bool:
        """Add package to cache."""
        package_dir = self.cache_dir / distro
        package_dir.mkdir(exist_ok=True)
        
        filename = Path(filepath).name
        dest = package_dir / filename
        
        try:
            shutil.copy(filepath, dest)
            return True
        except:
            return False
            
    def clear(self):
        """Clear package cache."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)