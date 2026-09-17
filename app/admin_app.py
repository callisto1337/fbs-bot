from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.config import settings
from app.db import engine
from app.models import MaxUser


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"authenticated": True})
            return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("authenticated"))


class MaxUserAdmin(ModelView, model=MaxUser):
    name = "Пользователь MAX"
    name_plural = "Пользователи MAX"
    icon = "fa-solid fa-user"

    column_list = [
        MaxUser.id,
        MaxUser.phone,
        MaxUser.max_user_id,
        MaxUser.display_name,
        MaxUser.is_active,
        MaxUser.access_expires_at,
        MaxUser.created_at,
    ]
    column_searchable_list = [MaxUser.phone, MaxUser.display_name]
    column_sortable_list = [MaxUser.access_expires_at, MaxUser.created_at]
    form_columns = [
        MaxUser.phone,
        MaxUser.max_user_id,
        MaxUser.display_name,
        MaxUser.is_active,
        MaxUser.access_expires_at,
        MaxUser.comment,
    ]


app = FastAPI(title="xlsx-converter admin")

admin = Admin(
    app,
    engine,
    authentication_backend=AdminAuth(secret_key=settings.admin_secret_key),
)
admin.add_view(MaxUserAdmin)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
