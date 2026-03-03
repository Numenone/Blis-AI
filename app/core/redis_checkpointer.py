import json
import logging
from typing import Any, AsyncIterator, Optional, Sequence, cast
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    PendingWrite,
    get_checkpoint_id,
)
import redis.asyncio as redis
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

logger = logging.getLogger(__name__)

class AsyncStandardRedisSaver(BaseCheckpointSaver):
    """
    A custom LangGraph checkpointer that uses standard Redis commands (HASHES).
    Does NOT require the RediSearch module (FT.* commands).
    Works on basic Redis, AWS ElastiCache, Azure Cache for Redis, etc.
    """
    
    def __init__(self, connection: redis.Redis):
        super().__init__()
        self.redis = connection
        self.serde = JsonPlusSerializer()

    def _make_checkpoint_key(self, thread_id: str, checkpoint_ns: str, checkpoint_id: str) -> str:
        return f"checkpoint:{thread_id}:{checkpoint_ns}:{checkpoint_id}"

    def _make_latest_key(self, thread_id: str, checkpoint_ns: str) -> str:
        return f"latest:{thread_id}:{checkpoint_ns}"

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)
        
        if not checkpoint_id:
            # Get latest ID
            latest_key = self._make_latest_key(thread_id, checkpoint_ns)
            checkpoint_id = await self.redis.get(latest_key)
            if checkpoint_id:
                checkpoint_id = checkpoint_id.decode() if isinstance(checkpoint_id, bytes) else checkpoint_id
                logger.info(f"checkpointer.aget_tuple found_latest={checkpoint_id} for thread_id={thread_id}")

        if not checkpoint_id:
            return None

        checkpoint_key = self._make_checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        data = await self.redis.hgetall(checkpoint_key)
        
        if not data:
            logger.warning(f"checkpointer.aget_tuple NO_DATA_FOUND key={checkpoint_key}")
            return None

        logger.info(f"checkpointer.aget_tuple data_type={type(data)} keys={list(data.keys())}")
        
        # Helper to get value from dict with potential bytes/str mismatch
        def get_val(d, key_str):
            b_key = key_str.encode()
            if b_key in d: return d[b_key]
            if key_str in d: return d[key_str]
            return None

        # Reconstruct the typed tuple for loads_typed
        cp_type = get_val(data, "checkpoint_type")
        cp_data = get_val(data, "checkpoint_data")
        md_type = get_val(data, "metadata_type")
        md_data = get_val(data, "metadata_data")
        parent_id_val = get_val(data, "parent_id")

        if cp_data is None:
            # Fallback to legacy fields if present
            raw_cp = get_val(data, "checkpoint")
            raw_md = get_val(data, "metadata")
            if raw_cp:
                try:
                    # Try to see if it was the JSON-wrapped tuple attempt
                    parsed = json.loads(raw_cp.decode() if hasattr(raw_cp, 'decode') else raw_cp)
                    if isinstance(parsed, (list, tuple)) and len(parsed) == 2:
                        checkpoint_data = tuple(parsed)
                    else:
                        # Very old format: raw JSON of the object. Wrap as "json" type.
                        checkpoint_data = ("json", raw_cp.decode() if hasattr(raw_cp, 'decode') else raw_cp)
                    
                    parsed_md = json.loads(raw_md.decode() if hasattr(raw_md, 'decode') else raw_md)
                    if isinstance(parsed_md, (list, tuple)) and len(parsed_md) == 2:
                        metadata_data = tuple(parsed_md)
                    else:
                        metadata_data = ("json", raw_md.decode() if hasattr(raw_md, 'decode') else raw_md)
                except Exception:
                    # If JSON parsing fails, treat as raw string/bytes if possible
                    checkpoint_data = ("json", raw_cp.decode() if hasattr(raw_cp, 'decode') else str(raw_cp))
                    metadata_data = ("json", raw_md.decode() if hasattr(raw_md, 'decode') else str(raw_md))
            else:
                logger.error(f"checkpointer.aget_tuple MISSING_FIELDS key={checkpoint_key}")
                return None
        else:
            # Modern fields: (type, bytes)
            checkpoint_data = (
                cp_type.decode() if hasattr(cp_type, "decode") else cp_type,
                cp_data
            )
            metadata_data = (
                md_type.decode() if hasattr(md_type, "decode") else md_type,
                md_data
            )
        
        try:
            checkpoint = self.serde.loads_typed(checkpoint_data)
            metadata = self.serde.loads_typed(metadata_data)
        except Exception as e:
            logger.error(f"checkpointer.aget_tuple DESERIALIZATION_ERROR key={checkpoint_key} error={str(e)}")
            return None

        parent_checkpoint_id = parent_id_val.decode() if hasattr(parent_id_val, 'decode') else (parent_id_val or "")

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": parent_checkpoint_id
                }
            } if parent_checkpoint_id else None
        )

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        # Basic implementation of list using SCAN
        # Note: This is less efficient than Search but works on standard Redis
        thread_id = config["configurable"]["thread_id"] if config else "*"
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "*") if config else "*"
        
        pattern = f"checkpoint:{thread_id}:{checkpoint_ns}:*"
        cursor = 0
        count = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                key_str = key.decode() if hasattr(key, 'decode') else str(key)
                if isinstance(key, tuple): key_str = str(key[0]) # Defensive
                
                # checkpoint:thread:ns:id
                parts = key_str.split(":")
                if len(parts) < 4: continue
                
                cid = parts[3]
                conf = {"configurable": {"thread_id": parts[1], "checkpoint_ns": parts[2], "checkpoint_id": cid}}
                
                item = await self.aget_tuple(conf)
                if item:
                    # Apply filters if needed (simplified)
                    yield item
                    count += 1
                    if limit and count >= limit:
                        return
            
            if cursor == 0:
                break

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        
        logger.info(f"checkpointer.aput thread_id={thread_id} checkpoint_id={checkpoint_id}")
        
        # Determine parent
        parent_id = config["configurable"].get("checkpoint_id")
        
        checkpoint_key = self._make_checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        latest_key = self._make_latest_key(thread_id, checkpoint_ns)
        
        # Store in Hash using JsonPlusSerializer
        # dumps_typed returns a tuple (type_name, bytes)
        cp_type, cp_data = self.serde.dumps_typed(checkpoint)
        md_type, md_data = self.serde.dumps_typed(metadata)
        
        await self.redis.hset(checkpoint_key, mapping={
            "checkpoint_type": cp_type,
            "checkpoint_data": cp_data,
            "metadata_type": md_type,
            "metadata_data": md_data,
            "parent_id": parent_id if parent_id else ""
        })
        
        # Update latest pointer
        await self.redis.set(latest_key, checkpoint_id)
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        # Standard Redis doesn't strictly need writes stored separately for basic chat ops,
        # but we can implement it if needed. For this test, put/get is enough for session persistence.
        pass
