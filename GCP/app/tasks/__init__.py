from flask import Blueprint

bp = Blueprint('tasks', __name__, url_prefix='/tasks')

from app.tasks import routes
