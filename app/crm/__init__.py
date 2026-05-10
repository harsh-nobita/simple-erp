from flask import Blueprint

bp = Blueprint(
    "crm",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/crm",
)

from app.crm import crm_routes  # noqa: E402, F401
