import random

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.secret_key = 'your_very_secret_key'
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

@app.route("/random")
def get_random_cafe():
    cafes = Cafe.query.all()
    random_cafe = random.choice(cafes) if cafes else None
    return render_template("random-cafe.html", cafe=random_cafe)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/all")
def get_all_cafes():
    cafes = Cafe.query.all()
    return render_template("all-cafes.html", cafes=cafes)

@app.route("/search")
def search_cafes():
    location = request.args.get('loc')
    if not location:
        return jsonify(error="Location parameter 'loc' is required."), 400
    cafes = Cafe.query.filter_by(location=location).all()
    return render_template("search-results.html", cafes=cafes) if cafes else render_template("search-results.html", cafes=None), 200 if cafes else 404


@app.route("/add", methods=["GET", "POST"])
def post_new_cafe():
    if request.method == "POST":
        new_cafe_data = request.form
        try:
            new_cafe = Cafe(
                name=new_cafe_data.get("name"),
                map_url=new_cafe_data.get("map_url"),
                img_url=new_cafe_data.get("img_url"),
                location=new_cafe_data.get("location"),
                seats=new_cafe_data.get("seats"),
                has_toilet=new_cafe_data.get("has_toilet") == 'on',
                has_wifi=new_cafe_data.get("has_wifi") == 'on',
                has_sockets=new_cafe_data.get("has_sockets") == 'on',
                can_take_calls=new_cafe_data.get("can_take_calls") == 'on',
                coffee_price=new_cafe_data.get("coffee_price"),
            )
            db.session.add(new_cafe)
            db.session.commit()
            # After adding the new cafe, you might want to redirect to the all cafes page or to a success page.
            return redirect(url_for('get_all_cafes'))
        except IntegrityError:
            db.session.rollback()
            return jsonify(error="This cafe already exists in the database."), 400
    else:
        # If it's a GET request, render the form to add a new cafe.
        return render_template("add-cafe.html")


@app.route("/update-price/<int:cafe_id>", methods=["POST"])
def update_cafe_price(cafe_id):
    new_price = request.form.get("new_price")
    if new_price:
        cafe = Cafe.query.get(cafe_id)
        if cafe:
            cafe.coffee_price = new_price
            db.session.commit()
            return redirect(url_for('get_all_cafes'))
        else:
            flash("Café not found.", "error")
            return redirect(url_for('get_all_cafes'))
    else:
        flash("New price parameter is required.", "error")
        return redirect(url_for('get_all_cafes'))


@app.route("/report-closed/<int:cafe_id>", methods=["POST"])
def delete_cafe(cafe_id):
    api_key = request.form.get("api_key")
    if api_key and api_key == app.secret_key:
        cafe = Cafe.query.get(cafe_id)
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            flash(f"Café with ID {cafe_id} has been deleted successfully.", "success")
        else:
            flash("Café not found.", "error")
    else:
        flash("Unauthorized. Please provide a valid API key.", "error")
    return redirect(url_for('get_all_cafes'))


@app.errorhandler(404)
def invalid_route(e):
    return jsonify(error=str(e)), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
