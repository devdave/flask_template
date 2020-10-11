
from flask import render_template
from logging import getLogger
from .. import app

log = getLogger(__name__)


@app.route("/", methods=["GET"])
def index():

    return render_template("page_basic.html")