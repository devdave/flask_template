import logging
from flask import Flask

app:Flask = None
log:logging.Logger = None


def create_app(config=None)->Flask:

    global app, log

    log = logging.getLogger(__name__)

    log.debug(f"creating {__name__}")

    from . import settings, models, views, lib

    app = Flask(__name__)

    app = settings.create_app(app, config)
    app = views.init_views(app)
    app = models.init_models(app)
