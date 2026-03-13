from __future__ import annotations

from typing import Any

try:
    from starlette_admin import DateTimeField, FloatField, IntegerField, StringField, TextAreaField
    from starlette_admin.contrib.sqla import Admin, ModelView
except ImportError:
    raise ImportError("Install apimemo[fastapi-admin]: pip install apimemo[fastapi-admin]") from None


class ApiLogView(ModelView):
    fields = [
        "id",
        StringField("method", label="Method"),
        StringField("url", label="URL"),
        StringField("host", label="Host"),
        StringField("path", label="Path"),
        IntegerField("status_code", label="Status"),
        FloatField("duration_ms", label="Duration (ms)"),
        TextAreaField("request_body", label="Request Body"),
        TextAreaField("response_body", label="Response Body"),
        TextAreaField("error", label="Error"),
        DateTimeField("created_at", label="Created At"),
    ]
    fields_default_sort = [("created_at", True)]
    page_size = 50
    search_fields = ["url", "host", "method", "error"]
    list_display = ["method", "host", "path", "status_code", "duration_ms", "created_at"]


def mount_admin(app: Any, engine: Any, model: Any = None) -> None:
    if model is None:
        model = _discover_model()

    if model is None:
        import logging

        logging.getLogger("apimemo").warning(
            "apimemo: ApiLogMixin model not found. Pass model= explicitly or create a model inheriting ApiLogMixin."
        )
        return

    admin = Admin(engine, title="API Memo")
    view = ApiLogView(model, name="API Logs", icon="fa fa-exchange")
    admin.add_view(view)
    admin.mount_to(app)


def _discover_model() -> Any | None:
    from apimemo.integrations.sqlalchemy import ApiLogMixin

    try:
        from sqlalchemy.orm import DeclarativeBase
    except ImportError:
        return None

    for subclass in _all_subclasses(DeclarativeBase):
        if ApiLogMixin in subclass.__mro__ and not getattr(subclass, "__abstract__", False):
            return subclass

    return None


def _all_subclasses(cls: type) -> set[type]:
    result = set()
    work = list(cls.__subclasses__())
    while work:
        sub = work.pop()
        if sub not in result:
            result.add(sub)
            work.extend(sub.__subclasses__())
    return result
