import os
import json
import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)

DEFAULT_REDIS_HOST = os.getenv("REDIS_HOST")
DEFAULT_REDIS_PORT = int(os.getenv("REDIS_PORT"))


class Cache:
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None

    def init(self, host: str = None, port: int = None) -> Optional[redis.Redis]:
        if not os.getenv("REDIS_HOST"):
            logger.info("Running without Redis cache (local mode)")
            self._redis_client = None
            return None

        host = host or DEFAULT_REDIS_HOST
        port = port or DEFAULT_REDIS_PORT
        try:
            client = redis.Redis(host=host, port=port, decode_responses=False)
            client.ping()
            self._redis_client = client
            logger.info(f"Redis connected at {host}:{port}")
            return client
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Running without cache.")
            self._redis_client = None
            return None

    def get_redis(self) -> Optional[redis.Redis]:
        return self._redis_client

    def make_gene_key(self, genes) -> str:
        key_tuple = tuple(
            (g.course_id, g.timeslot_id, g.room_id, g.units)
            for g in genes
        )
        return json.dumps(key_tuple, sort_keys=True)

    def _get_json(self, key: str) -> Optional[dict]:
        if self._redis_client is None:
            return None
        try:
            data = self._redis_client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def _set_json(self, key: str, value: dict, ttl: int = 3600) -> None:
        if self._redis_client is None:
            return
        try:
            self._redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def get_cached_fitness(self, key: str) -> Optional[dict]:
        return self._get_json(key)

    def set_cached_fitness(self, key: str, value: dict, ttl: int = 3600) -> None:
        self._set_json(key, value, ttl)


cache = Cache()
