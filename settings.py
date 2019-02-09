import os
from flask import Flask

class BaseConfig:
    DEBUG = True
    TESTING = False
    DATABASE_URI = "/base_db.sqlite3"


def create_app(app: Flask, config=None)->Flask:

    #load default
    app.config.from_object(BaseConfig)
    #load environment
    if "FLASK_CONF" in os.environ:
        app.config.from_envvar("FLASK_CONF")

    # load app specific config
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif isinstance(config, str) and config.endswith(".py"):
            app.config.from_pyfile(config)
        else:
            raise RuntimeError(f"Unsure how to handle {config}")

    return app
