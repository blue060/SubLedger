from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["健康检查"])


@router.get("")
def health_check():
    return {"status": "ok"}