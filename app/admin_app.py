from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import update
from starlette.requests import Request

from app.config import settings
from app.db import async_session, engine, init_models
from app.models import MaxUser
from app.notifications import (
    close_notifier,
    notify_access_activated,
    notify_access_revoked,
)


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

    async def on_model_change(
        self, data: dict, model: MaxUser, is_created: bool, request: Request
    ) -> None:
        # Запоминаем состояние доступа до применения формы (model здесь ещё
        # не тронут), чтобы после сохранения понять, изменился ли доступ.
        request.state.had_access_before = False if is_created else model.has_access()

    async def after_model_change(
        self, data: dict, model: MaxUser, is_created: bool, request: Request
    ) -> None:
        had_access_before = getattr(request.state, "had_access_before", False)
        has_access_after = model.has_access()
        if not model.max_user_id:
            return
        if not had_access_before and has_access_after:
            await notify_access_activated(model.max_user_id)
            # Сбрасываем отметку об уведомлении об истечении, чтобы при
            # следующем истечении access_expires_at планировщик уведомил снова.
            async with async_session() as session:
                await session.execute(
                    update(MaxUser)
                    .where(MaxUser.id == model.id)
                    .values(expiry_notified_at=None)
                )
                await session.commit()
        elif had_access_before and not has_access_after:
            await notify_access_revoked(model.max_user_id)


app = FastAPI(title="xlsx-converter admin")

admin = Admin(
    app,
    engine,
    authentication_backend=AdminAuth(secret_key=settings.admin_secret_key),
)
admin.add_view(MaxUserAdmin)


@app.on_event("startup")
async def on_startup() -> None:
    await init_models()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_notifier()


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/admin")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
