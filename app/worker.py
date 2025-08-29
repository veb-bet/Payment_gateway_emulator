import asyncio
import json
import time
import httpx
from . import utils, config

async def queue_worker():
    r = await utils.get_redis()
    client = httpx.AsyncClient()
    
    try:
        while True:
            try:
                job_data = await r.blpop(config.QUEUE_KEY, timeout=1.0)
                if not job_data:
                    await asyncio.sleep(0.1)
                    continue
                
                job = json.loads(job_data[1])
                tx_id = job.get("tx_id")

                processed_key = f"processed:{tx_id}"
                if await r.get(processed_key):
                    continue

                payment_key = config.PAYMENT_PREFIX + tx_id
                p = await r.hgetall(payment_key)
                if not p:
                    continue

                payment = {k: json.loads(v) for k, v in p.items()}
                await r.hset(payment_key, mapping={"status": json.dumps("processing")})

                merchant = await utils.get_merchant(r, payment["merchant_id"])
                if not merchant:
                    await r.hset(payment_key, mapping={"status": json.dumps("failed")})
                    continue

                webhook_payload = {
                    "tx_id": tx_id,
                    "status": "succeeded",
                    "amount": payment["amount"],
                    "currency": payment["currency"]
                }
                body = json.dumps(webhook_payload).encode()
                signature = utils.hmac_signature(merchant["secret"], body)
                headers = {"Content-Type": "application/json", "X-PG-Signature": signature}

                delivered, attempt = False, 0
                while attempt < 5 and not delivered:
                    attempt += 1
                    try:
                        resp = await client.post(merchant["webhook_url"], content=body, headers=headers)
                        if 200 <= resp.status_code < 300:
                            delivered = True
                            break
                    except Exception as e:
                        print(f"Delivery attempt {attempt} failed: {e}")
                    await asyncio.sleep(1 * (2 ** (attempt - 1)) + (time.time() % 1))

                if delivered:
                    await r.hset(payment_key, mapping={"status": json.dumps("succeeded")})
                    await r.set(processed_key, "1", ex=config.PROCESSED_TTL)
                else:
                    await r.hset(payment_key, mapping={"status": json.dumps("failed")})

                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in queue worker: {e}")
                await asyncio.sleep(1)
    finally:
        await client.aclose()