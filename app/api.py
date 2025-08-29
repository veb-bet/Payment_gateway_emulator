from fastapi import APIRouter, HTTPException, Header, Request
import time
import uuid
import json
from . import utils, config
from .models import ChargeCreate

router = APIRouter()

@router.post("/charge")
async def create_charge(charge: ChargeCreate, idempotency_key: str | None = None):
    r = await utils.get_redis()
    
    idemp_key = f"idemp:{idempotency_key}" if idempotency_key else None
    if idemp_key:
        cached_response = await r.get(idemp_key)
        if cached_response:
            return json.loads(cached_response)
    
    tx_id = str(uuid.uuid4())
    payment = {
        "tx_id": tx_id,
        "amount": charge.amount,
        "currency": charge.currency,
        "merchant_id": charge.merchant_id,
        "description": charge.description or "",
        "metadata": json.dumps(charge.metadata or {}),
        "status": "pending",
        "created_at": str(time.time())
    }
    
    payment_key = config.PAYMENT_PREFIX + tx_id
    await r.hset(payment_key, mapping={k: json.dumps(v) for k, v in payment.items()})
    await r.expire(payment_key, config.PROCESSED_TTL)

    response_body = {"tx_id": tx_id, "status": "accepted"}
    
    if idemp_key:
        await r.set(idemp_key, json.dumps(response_body), ex=config.IDEMPOTENCY_TTL)

    await r.rpush(config.QUEUE_KEY, json.dumps({"tx_id": tx_id}))
    return response_body

@router.get("/status/{tx_id}")
async def status(tx_id: str):
    r = await utils.get_redis()
    key = config.PAYMENT_PREFIX + tx_id
    data = await r.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="tx not found")
    return {k: json.loads(v) for k, v in data.items()}

@router.post("/test/receive_webhook")
async def receive_webhook(request: Request, x_pg_signature: str | None = Header(None)):
    body = await request.body()
    secret = request.query_params.get("secret")
    verification = None
    ok = None
    if secret and x_pg_signature:
        verification = utils.hmac_signature(secret, body)
        ok = hmac.compare_digest(verification, x_pg_signature)
    print("Received webhook", body.decode())
    return {"ok": ok, "expected_sig": verification}