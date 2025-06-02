from fastapi import HTTPException
from typing import Any, Dict, Optional

class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, detail, headers)

class AIServiceException(APIException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"AI Service Error: {detail}")

class MemoryNotFoundException(APIException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=400, 
            detail=f"No conversation history found for user {user_id}"
        )

class ValidationException(APIException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)