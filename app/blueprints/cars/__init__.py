from flask import Blueprint

cars_bp = Blueprint("cars_bp", __name__)

from . import routes