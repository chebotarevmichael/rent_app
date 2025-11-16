from src.api.utils import build_router

router = build_router(__name__)


@router.get("/audit")
async def audit():
    return {"status": "ok"}
