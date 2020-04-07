
from flask import render_template
from logging import getLogger
from .. import app
from ..lib.forms import Donor, CustomerRegister

log = getLogger(__name__)


@app.route("/", methods=["GET"])
def index():

    donor_form = Donor()
    customer_form = CustomerRegister()

    return render_template("home.html", donor = donor_form, customer=customer_form)