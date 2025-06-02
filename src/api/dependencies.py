from fastapi import Depends, HTTPException
from src.services.memory_service import memory_service
from src.services.chain_factory import chain_factory
from src.models.requests import BaseRequest

def get_memory_service():
    return memory_service

def get_chain_factory():
    return chain_factory

def validate_user_id(request: BaseRequest):
    if not request.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return request.user_id