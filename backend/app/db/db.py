import os
import json
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

COLLECTIONS = ["courses", "lecturers", "rooms", "timeslots"]

DEFAULT_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DEFAULT_DB = os.getenv("MONGO_DB", "lecscheduler")


class Database:
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._data: dict = {k: [] for k in COLLECTIONS}
        self._lock = threading.Lock()

    async def _async_init(self, uri: str, db_name: str):
        try:
            self._client = AsyncIOMotorClient(uri)
            await self._client.admin.command("ping")
            self._db = self._client[db_name]
            logger.info(f"MongoDB connected at {uri}")

            for coll_name in COLLECTIONS:
                cursor = self._db[coll_name].find()
                items = await cursor.to_list(length=None)
                self._data[coll_name] = [self._deserialize_doc(doc) for doc in items]
                logger.info(f"Loaded {len(self._data[coll_name])} items from {coll_name}")

            await self._seed_if_empty()

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def _deserialize_doc(self, doc: dict) -> dict:
        result = dict(doc)
        result.pop("_id", None)
        for key, value in result.items():
            if hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                result[key] = str(value)
        return result

    async def _seed_if_empty(self):
        force_seed = os.getenv("FORCE_SEED", "false").lower() == "true"
        needs_seed = any(len(self._data[coll]) == 0 for coll in COLLECTIONS)

        if not needs_seed and not force_seed:
            return

        seed_path = Path(__file__).parent.parent.parent / "data.json"
        if not seed_path.exists():
            logger.warning(f"Seed file not found: {seed_path}")
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        if force_seed:
            logger.info("FORCE_SEED=true - Re-seeding database from data.json...")
        else:
            logger.info("Seeding database from data.json...")

        for coll_name in COLLECTIONS:
            key = coll_name
            if self._db is None or key not in seed_data or not seed_data[key]:
                continue
            await self._db[coll_name].delete_many({})
            await self._db[coll_name].insert_many(seed_data[key])
            self._data[coll_name] = list(seed_data[key])
            logger.info(f"Seeded {len(seed_data[key])} items into {coll_name}")

    async def init(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        uri = uri or DEFAULT_URI
        db_name = db_name or DEFAULT_DB
        await self._async_init(uri, db_name)

    def get_collection(self, collection_name: str) -> list[dict]:
        with self._lock:
            return list(self._data.get(collection_name, []))

    def set_collection(self, collection_name: str, items: list[dict]):
        with self._lock:
            self._data[collection_name] = list(items)

        if self._db is not None:
            asyncio.create_task(self._db[collection_name].delete_many({}))
            if items:
                asyncio.create_task(self._db[collection_name].insert_many(items))

    def next_id(self, collection_name: str) -> int:
        with self._lock:
            items = self._data.get(collection_name, [])
            if not items:
                return 1
            return max(item.get("id", 0) for item in items) + 1

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")


db = Database()
