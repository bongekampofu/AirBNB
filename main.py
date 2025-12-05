from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, EmailField, TextAreaField, SubmitField, FloatField, FileField
from wtforms.validators import InputRequired, Length, DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.file import FileField, FileAllowed
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = "your_secret_key_here"
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bnb.db'  #SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\Bongeka.Mpofu\\DB.Browser.for.SQLite-v3.13.1-win64\\bnb.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

#database model
class User(db.Model): #creates a table in the database
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(150), nullable=False, unique=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    password = db.Column(db.String(25), nullable=False)
    house_number = db.Column(db.String(25))
    street_name = db.Column(db.String(35), nullable=False)
    country = db.Column(db.String(35), nullable=False)
    post_code = db.Column(db.String(7), nullable=False)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255))
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    host = db.relationship('User', backref=db.backref('properties', lazy=True))

#WTForms form
class Register(FlaskForm): #validation of input
    email_address = EmailField("Email Address:", validators=[InputRequired(), Length(min=4)])
    first_name = StringField("First Name:", validators=[InputRequired(), Length(max=25)])
    last_name = StringField("Last Name:", validators=[InputRequired(), Length(max=25)])
    password = PasswordField("Password:", validators=[InputRequired(), Length(min=8, max=25)])
    house_number = StringField("House Number:", validators=[InputRequired(), Length(max=25)])
    street_name = StringField("Street Name:", validators=[InputRequired(), Length(max=35)])
    country = StringField("Country:", validators=[InputRequired(), Length(max=35)])
    post_code = StringField("Post Code:", validators=[InputRequired(), Length(max=7)])

class PropertyForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    price_per_night = FloatField("Price per night", validators=[DataRequired()])
    image = FileField("Property Image", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], "Images only!")
    ])
    submit = SubmitField("Add Property")

#routes
@app.route("/register", methods=["GET", "POST"])
def register():
    form = Register()
    if form.validate_on_submit():
        # Save the user to the database
        new_user = User(
            email_address=form.email_address.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            password=bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
            house_number=form.house_number.data,
            street_name=form.street_name.data,
            country=form.country.data,
            post_code=form.post_code.data
        )
        db.session.add(new_user)
        db.session.commit()

        # Redirect to login page instead of success.html
        return redirect(url_for('login'))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email_address"]
        password = request.form["password"]
        user = User.query.filter_by(email_address=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            return render_template("welcome.html", first_name=user.first_name, last_name=user.last_name)
        else:
            error = "Invalid email or password"
    return render_template("login.html", error=error)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/add_property", methods=["GET", "POST"])
def add_property():
    if "user_id" not in session:
        return redirect(url_for("login"))
    form = PropertyForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(file_path)
        new_property = Property(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            price_per_night=form.price_per_night.data,
            image=filename,
            host_id=session["user_id"]
        )
        db.session.add(new_property)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_property.html", form=form)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    properties = Property.query.filter_by(host_id=session["user_id"]).all()
    return render_template("dashboard.html", properties=properties)

#run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  #create the SQLite database and tables
    app.run(debug=True)
