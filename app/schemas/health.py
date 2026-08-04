from typing import Dict
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]