import wtforms

from wtforms import StringField, SelectField, IntegerField
from wtforms.validators import DataRequired
import flask_wtf
from flask_wtf import FlaskForm

class Donor(FlaskForm):
    name_first =    StringField("First name", validators=[DataRequired()])
    name_last =     StringField("Last name", validators=[DataRequired()])
    email =         StringField("Email address", validators=[DataRequired()])
    blood_type =    SelectField("Blood type",
                             validators=[DataRequired()],
                             choices=[("", "missing"), ("a-", "A-",),("a+", "A+",),("b-", "B-",),("b+", "B+",),("ab-", "AB-",),("ab+", "AB+",),("o-", "O-",),("o+", "O+",)])
    age =           IntegerField("Age", validators=[DataRequired()])
    body_weight =   IntegerField("(Optional) Body weight")
    sex =           SelectField("(Optional) Sex", choices=[("undisclosed","undisclosed"),("male","male"),("female","female")])

class CustomerRegister(FlaskForm):
    name = StringField("Title and full name", validators=[DataRequired()])
    agency = StringField("Agency", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    website = StringField("(Optional), website")
