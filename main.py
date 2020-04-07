
from . import app


def setup_application():
    #Let conf figure out how to configure itself
    from .conf import configure_application
    configure_application(app)

    # TODO set up logging here if I need it

    # Bring the application to life
    from . import views
    from . import models
    from . import lib


    return app