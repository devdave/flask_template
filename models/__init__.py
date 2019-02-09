from flask import g
from dcdb import dcdb

import logging

LOG = logging.getLogger(__name__)


# from . import task_detail
from . import inputs as mf




app = None
close_connection = None
setup_db = None



def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = dcdb.DBConnection(app.config['DATABASE_URI'])
        db.bind_scan(mf)

    return db

def _setup_db():

    db = getattr(g, "_database", None)
    if db is not None:
        return db

    db = g._database = dcdb.DBConnection(app.config['DATABASE_URI'])

    if app.config['TESTING'] is True:
        LOG.info("DB purged @", __file__)
        db.purge(this_deletes_everything=True)

    db.bind_scan(mf)

def _close_connection(exc: Exception = None):

    db = getattr(g, "_database", None)
    if db:
        db.close()
        setattr(g, "_database", None)
        del g._database


def init_models(my_app):
    global app, close_connection, setup_db

    LOG.debug(f"Intializing models {__name__}")
    if app is None:
        app = my_app
        close_connection = app.teardown_appcontext(_close_connection)
        setup_db = app.before_first_request(_setup_db)



    return app












