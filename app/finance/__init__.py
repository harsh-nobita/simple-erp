from flask import Blueprint

bp = Blueprint(
    "finance",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/finance",
)

from app.finance import routes  # noqa: E402, F401
