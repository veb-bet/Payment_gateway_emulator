import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
IDEMPOTENCY_TTL = int(os.getenv("IDEMPOTENCY_TTL", 60*60*24))
PROCESSED_TTL = int(os.getenv("PROCESSED_TTL", 60*60*24*7))
QUEUE_KEY = "pg:queue"
MERCHANT_PREFIX = "pg:merchant:"
PAYMENT_PREFIX = "pg:payment:"