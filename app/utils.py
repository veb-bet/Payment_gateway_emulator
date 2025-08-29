import hmac
import hashlib
import uuid
import json
import aioredis
from . import config

redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global redis
    if redis is None:
        redis = await aioredis.from_url(config.REDIS_URL, decode_responses=True)
    return redis

def hmac_signature(secret: str, payload: bytes) -> str:
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    return mac.hexdigest()

async def register_merchant_in_redis(r: aioredis.Redis, m):
    key = config.MERCHANT_PREFIX + m.merchant_id
    secret = m.secret or uuid.uuid4().hex
    await r.hset(key, mapping={"webhook_url": json.dumps(m.webhook_url), "secret": json.dumps(secret)})
    return secret

async def get_merchant(r: aioredis.Redis, merchant_id: str):
    key = config.MERCHANT_PREFIX + merchant_id
    data = await r.hgetall(key)
    if data:
        return {k: json.loads(v) for k, v in data.items()}
    return None