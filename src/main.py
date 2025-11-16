# main.py
from fastapi import FastAPI
from src.api.admin.user.audit import router as admin_user_audit_router
from src.api.external.event_in.create import router as external_event_in_create_router

app = FastAPI()

app.include_router(admin_user_audit_router)
app.include_router(external_event_in_create_router)
