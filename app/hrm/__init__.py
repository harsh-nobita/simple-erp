from flask import Blueprint

bp = Blueprint(
    "hrm",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/hrm",
)

from app.hrm import routes  # noqa: E402, F401
