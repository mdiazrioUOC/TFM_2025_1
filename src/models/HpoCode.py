from typing import List, Optional
from pydantic import BaseModel, Field

class HpoCode(BaseModel):
    """Código HPO asignado"""
    hpo_code: Optional[str] = Field(
        default=None, description="Código HPO detectado con el formato HP:#######."
    )

