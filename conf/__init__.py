
from .. import app
import sys
import logging
import flask






class BaseConfig(object):
    APP_LOGGING_HANDLER = logging.NullHandler()
    APP_LOGGING_FMT = "|%(levelname)s|[%(name)s:%(lineno)s] %(message)s"
    APP_LOGGING_LEVEL = logging.ERROR


class DevConfig(BaseConfig):
    APP_LOGGING_HANDLER = logging.StreamHandler(stream=sys.stderr)
    APP_LOGGING_LEVEL = logging.DEBUG
    RUN_PORT=7070
    DEBUG = True
    DATABASE_URI = "sqlite://./test.sqlite3"


class ProdConfig(BaseConfig):
    RUN_PORT=8000




def configure_application(app:flask.Flask):

    app.logger.debug(f"conf/__init__.py - Loading {app.env}")
    if app.env == "development":
        app.config.from_object(DevConfig)

    # Must be an environment var pointing to a relative or absolute file path.
    # eg set AP_REG_CONFIG=/path/to/config.ini
    app.config.from_envvar("AB_REG_CONFIG")
