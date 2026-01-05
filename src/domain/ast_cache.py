"""
Abstracción de cache para AST.

Este módulo define el protocolo AstCache y sus implementaciones:
- InMemoryLRUCache: Cache en memoria con evicción LRU
- SQLiteCache: Cache persistente en SQLite segmentado por repo
- NullCache: Cache nulo (no-op) para tests y benchmarks

Principios de diseño:
- Clean Architecture: Dependencias explícitas (DI), no estado oculto
- Evicción LRU: Límites de tamaño para evitar bombas de RAM
- Persistencia robusta: SQLite segmentado por repo, no pickle
- Versionable: Claves de cache incluyen versión del formato
"""

from typing import Protocol, Optional, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import time


class CacheStatus(Enum):
    """Status de una operación de cache."""
    HIT = "hit"
    MISS = "miss"
    ERROR = "error"


@dataclass
class CacheEntry:
    """Entrada de cache."""
    key: str
    value: Any
    created_at: float
    last_access: float


@dataclass
class CacheStats:
    """Estadísticas del cache."""
    entries: int
    hits: int
    misses: int
    hit_rate: float
    max_entries: int
    max_bytes: int
    current_bytes: int


class AstCache(Protocol):
    """Protocolo para cache de AST."""
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Guardar valor en el cache."""
        ...
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del cache. Retorna True si existía."""
        ...
    
    def clear(self) -> None:
        """Limpiar todo el cache."""
        ...
    
    def stats(self) -> CacheStats:
        """Obtener estadísticas del cache."""
        ...


class InMemoryLRUCache:
    """Cache en memoria con evicción LRU."""
    
    def __init__(self, max_entries: int = 10000, max_bytes: int = 100 * 1024 * 1024):
        """
        Initialize LRU cache.
        
        Args:
            max_entries: Máximo número de entradas (default: 10k)
            max_bytes: Máximo tamaño en bytes (default: 100MB)
        """
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []  # Para LRU
        self._lock = None
        self._hits = 0
        self._misses = 0
        self._current_bytes = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache."""
        if key not in self._cache:
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        entry = self._cache[key]
        entry.last_access = time.time()
        self._access_order.remove(key)
        self._access_order.append(key)
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any) -> None:
        """Guardar valor en el cache."""
        import json
        from dataclasses import asdict
        
        # Serialize value (handle lists of dataclass objects)
        if isinstance(value, list) and value and hasattr(value[0], "to_dict"):
            value_serialized: Any = [v.to_dict() for v in value]
        elif isinstance(value, list) and value and hasattr(value[0], "__dataclass_fields__"):
            value_serialized: Any = [asdict(v) for v in value]
        elif hasattr(value, "to_dict"):
            value_serialized: Any = value.to_dict()
        elif hasattr(value, "__dataclass_fields__"):
            value_serialized: Any = asdict(value)
        else:
            value_serialized: Any = value
        
        # Calculate size
        value_bytes = len(json.dumps(value_serialized).encode())
        
        # Evict if necessary
        while (len(self._cache) >= self.max_entries or 
               self._current_bytes + value_bytes > self.max_bytes):
            self._evict_oldest()
        
        # Add or update entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_access=time.time(),
        )
        self._cache[key] = entry
        self._current_bytes += value_bytes
        
        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del cache."""
        if key not in self._cache:
            return False
        
        entry = self._cache.pop(key)
        self._access_order.remove(key)
        
        import json
        self._current_bytes -= len(json.dumps(entry.value).encode())
        return True
    
    def clear(self) -> None:
        """Limpiar todo el cache."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0
        self._current_bytes = 0
    
    def stats(self) -> CacheStats:
        """Obtener estadísticas del cache."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total) if total > 0 else 0.0
        return CacheStats(
            entries=len(self._cache),
            hits=self._hits,
            misses=self._misses,
            hit_rate=hit_rate,
            max_entries=self.max_entries,
            max_bytes=self.max_bytes,
            current_bytes=self._current_bytes,
        )
    
    def _evict_oldest(self) -> None:
        """Evictar la entrada más antigua (LRU)."""
        if not self._access_order:
            return
        
        key = self._access_order.pop(0)
        entry = self._cache.pop(key, None)
        
        if entry:
            import json
            self._current_bytes -= len(json.dumps(entry.value).encode())


class SQLiteCache:
    """Cache persistente en SQLite."""
    
    def __init__(self, db_path: Path, max_entries: int = 10000, max_bytes: int = 100 * 1024 * 1024):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Ruta al archivo de base de datos
            max_entries: Máximo número de entradas (default: 10k)
            max_bytes: Máximo tamaño en bytes (default: 100MB)
        """
        self.db_path = db_path
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializar base de datos."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_access REAL NOT NULL,
                    value_bytes INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_access ON cache(last_access)
            """)
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache."""
        import sqlite3
        import json
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT value, value_bytes FROM cache WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            value_json, value_bytes = row
            
            # Update last_access
            conn.execute("""
                UPDATE cache SET last_access = ? WHERE key = ?
            """, (time.time(), key))
            conn.commit()
            
            return json.loads(value_json)
    
    def set(self, key: str, value: Any) -> None:
        """Guardar valor en el cache."""
        import sqlite3
        import json
        
        value_json = json.dumps(value)
        value_bytes = len(value_json.encode())
        
        # Evict if necessary
        self._evict_if_needed(value_bytes)
        
        # Add or update entry
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, value, created_at, last_access, value_bytes)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value_json, time.time(), time.time(), value_bytes))
            conn.commit()
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del cache."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM cache WHERE key = ?
            """, (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self) -> None:
        """Limpiar todo el cache."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
    
    def stats(self) -> CacheStats:
        """Obtener estadísticas del cache."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as entries,
                    SUM(CASE WHEN last_access > created_at THEN 1 ELSE 0 END) as hits,
                    SUM(CASE WHEN last_access = created_at THEN 1 ELSE 0 END) as misses,
                    SUM(value_bytes) as current_bytes
                FROM cache
            """)
            row = cursor.fetchone()
            
            entries, hits, misses, current_bytes = row or (0, 0, 0, 0)
            total = hits + misses
            hit_rate = (hits / total) if total > 0 else 0.0
            
            return CacheStats(
                entries=entries,
                hits=hits,
                misses=misses,
                hit_rate=hit_rate,
                max_entries=self.max_entries,
                max_bytes=self.max_bytes,
                current_bytes=current_bytes,
            )
    
    def _evict_if_needed(self, new_bytes: int) -> None:
        """Evictar entradas si es necesario."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            # Check current size
            cursor = conn.execute("""
                SELECT COUNT(*), SUM(value_bytes) FROM cache
            """)
            entries, current_bytes = cursor.fetchone() or (0, 0)
            
            # Evict until we have space
            while (entries >= self.max_entries or 
                   current_bytes + new_bytes > self.max_bytes):
                # Delete oldest entries
                cursor = conn.execute("""
                    DELETE FROM cache 
                    WHERE key IN (
                        SELECT key FROM cache ORDER BY last_access ASC LIMIT 100
                    )
                    RETURNING value_bytes
                """)
                deleted_bytes = sum(row[0] for row in cursor.fetchall())
                entries -= cursor.rowcount
                current_bytes -= deleted_bytes
                conn.commit()


class NullCache:
    """Cache nulo (no-op) para tests y benchmarks."""
    
    def get(self, key: str) -> Optional[Any]:
        """Siempre retorna None."""
        return None
    
    def set(self, key: str, value: Any) -> None:
        """No hace nada."""
        pass
    
    def delete(self, key: str) -> bool:
        """Siempre retorna False."""
        return False
    
    def clear(self) -> None:
        """No hace nada."""
        pass
    
    def stats(self) -> CacheStats:
        """Retorna estadísticas vacías."""
        return CacheStats(
            entries=0,
            hits=0,
            misses=0,
            hit_rate=0.0,
            max_entries=0,
            max_bytes=0,
            current_bytes=0,
        )
