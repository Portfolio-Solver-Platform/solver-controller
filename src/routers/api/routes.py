from fastapi import APIRouter, HTTPException
from src.config import Config
from pydantic import BaseModel, Field

router = APIRouter()

class StatusResponse(BaseModel):
    isFinished: bool = Field(..., description="Is it finished generating data")


@router.get("/status", response_model=StatusResponse)
def test_route():
    """
    
    """
    return StatusResponse(isFinished=True)
