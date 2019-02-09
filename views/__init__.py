from flask import Flask

app:Flask = None

def init_views(my_app:Flask)->Flask:
    global app
    app = my_app
    #from . import view_name

    return app