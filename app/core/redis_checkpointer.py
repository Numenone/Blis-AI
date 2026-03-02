import json
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

class AsyncStandardRedisSaver(BaseCheckpointSaver):
    """
    A custom LangGraph checkpointer that uses standard Redis commands (HASHES).
    Does NOT require the RediSearch module (FT.* commands).
    Works on basic Redis, AWS ElastiCache, Azure Cache for Redis, etc.
    """
    
    def __init__(self, connection: redis.Redis):
        super().__init__()
        self.redis = connection

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

        if not checkpoint_id:
            return None

        checkpoint_key = self._make_checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        data = await self.redis.hgetall(checkpoint_key)
        
        if not data:
            return None

        checkpoint = json.loads(data[b"checkpoint"].decode())
        metadata = json.loads(data[b"metadata"].decode())
        parent_checkpoint_id = data.get(b"parent_id", b"").decode()

        parent_config = None
        if parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": parent_checkpoint_id
                }
            }

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
            parent_config=parent_config
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
                key_str = key.decode()
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
        
        # Determine parent
        parent_id = config["configurable"].get("checkpoint_id")
        
        checkpoint_key = self._make_checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        latest_key = self._make_latest_key(thread_id, checkpoint_ns)
        
        # Store in Hash
        await self.redis.hset(checkpoint_key, mapping={
            "checkpoint": json.dumps(checkpoint),
            "metadata": json.dumps(metadata),
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
