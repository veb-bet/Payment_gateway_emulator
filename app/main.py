import asyncio
from fastapi import FastAPI
from . import api, utils, worker

app = FastAPI(title="Payment Gateway Emulator")
app.include_router(api.router)

@app.on_event("startup")
async def startup_event():
    await utils.get_redis()
    app.state.worker_task = asyncio.create_task(worker.queue_worker())

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'worker_task') and app.state.worker_task:
        app.state.worker_task.cancel()
    if utils.redis:
        await utils.redis.close()