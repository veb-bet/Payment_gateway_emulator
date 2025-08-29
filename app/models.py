from typing import Optional, Dict, Any
from pydantic import BaseModel

class ChargeCreate(BaseModel):
    amount: int
    currency: str = "USD"
    merchant_id: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MerchantRegister(BaseModel):
    merchant_id: str
    webhook_url: str
    secret: Optional[str] = None