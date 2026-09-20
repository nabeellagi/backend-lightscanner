from fastapi import APIRouter
from pydantic import BaseModel

from core.config import MODE_DESCRIPTIONS, ConversionMode

router = APIRouter(prefix="/mode", tags=["Modes"])

class ModeInfo(BaseModel):
    """Describes conversion mode"""
    
    name: str
    endpoint: str
    description: str
    

class ModeListResponse(BaseModel):
    """Response body for GET /mode."""
 
    modes: list[ModeInfo]
 
 
@router.get(
    "",
    response_model=ModeListResponse,
    summary="List all available conversion modes",
    description=(
        "Returns every supported conversion mode, the endpoint to POST "
    ),
)
def list_modes() -> ModeListResponse:
    modes = [
        ModeInfo(
            name=mode.value,
            endpoint=f"/mode/{mode.value}",
            description=MODE_DESCRIPTIONS[mode],
        )
        for mode in ConversionMode
    ]
    return ModeListResponse(modes=modes)
 