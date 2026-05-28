from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api")
async def api_info():
    return {"app": "sistema-medico", "version": "0.1.0"}
