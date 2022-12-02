import json

from flask import Flask, request
import users_dao
import datetime

from db import db

db_filename = "auth.db"
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()


# generalized response formats
def success_response(data, code=200):
    """
    Generalized success response function
    """
    return json.dumps(data), code


def failure_response(message, code=404):
    """
    Generalized failure response function
    """
    return json.dumps({"error": message}), code


def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")

    if auth_header is None:
        return False, failure_response("Missing authorization header.", 400)

    bearer_token = auth_header.replace("Bearer ", "").strip()

    if bearer_token is None or not bearer_token:
        return False, failure_response("Invalid authorization header.", 400)

    return True, bearer_token


@app.route("/")
def hello_world():
    """
    Endpoint for printing Hello World!
    """
    return "Hello World!"


@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Missing email or password", 400)

    success, user = users_dao.create_user(email, password)

    if not success:
        return failure_response("User already exists", 400)

    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })


@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Missing email or password", 400)

    success, user = users_dao.verify_credentials(email, password)

    if not success:
        return failure_response("Incorrect email or password", 401)

    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })


@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token. ", 400)
    success_user, user = users_dao.renew_session(update_token)

    if not success_user:
        return failure_response("Invalid update token", 400)

    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })


@app.route("/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Session token invalid.", 400)

    user = users_dao.get_user_by_session_token(session_token)

    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token.", 400)

    return success_response("You have successfully implemented sessions!")


@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token", 400)
    user = users_dao.get_user_by_session_token(session_token)

    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)

    user.session_token = ""
    user.session_expiration = datetime.datetime.now()
    user.update_token = ""

    db.session.commit()
    return success_response("You have successfully logged out")


@app.route("/api/locations/")
def get_all_locations():
    """
    Endpoint for getting all locations
    """

    locations = []
    for l in db.Locations.query.all():
        loc = l.simple_serialize()
        locations.append(loc)
    return success_response({"locations": locations})


@app.route("/api/locations/", methods=["POST"])
def create_location():
    """
    Endpoint for creating a location
    """
    body = json.loads(request.data)
    code = body.get("code")
    if code is None:
        return failure_response("No code", 400)
    name = body.get("name")
    if name is None:
        return failure_response("No name", 400)
    address = body.get("name")
    if address is None:
        return failure_response("No address", 400)
    weekday_operating_time = body.get("weekday_operating_time")
    if weekday_operating_time is None:
        return failure_response("No weekday operating time", 400)
    weekend_operating_time = body.get("weekend_operating_time")
    if weekend_operating_time is None:
        return failure_response("No weekend operating time", 400)
    holiday = body.get("holiday")
    if holiday is None:
        holiday = []

    location = db.Location(code=code, name=name, address=address, weekday_operating_time=weekday_operating_time,
                           weekend_operating_time=weekend_operating_time, holiday=holiday)
    db.session.add(location)
    db.session.commit()

    new_location = {
        "id": location.id,
        "code": location.code,
        "name": location.name,
        "weekday_operating_time": location.weekday_operating_time,
        "weekend_operating_time": location.weekend_operating_time,
        "holiday": location.holiday
    }
    return success_response(new_location, 201)


@app.route("/api/locations/<int:id>/")
def get_location(id):
    """
    Endpoint for getting a location by id
    """

    location = db.Location.query.filter_by(id=id).first()
    if location is None:
        return failure_response("Location not found")
    return success_response(location.serialize())


@app.route("/api/locations/<int:id>/", methods=["DELETE"])
def delete_location(id):
    """
    Endpoint for deleting a course by id
    """

    location = db.Locations.query.filter_by(id=id).first()
    if location is None:
        return failure_response("Location not found")

    db.session.delete(location)
    db.session.commit()
    return success_response(location.serialize())


@app.route("/api/users/<int:id>/")
def get_user(id):
    """
    Endpoint for getting a user by id
    """

    user = db.Users.query.filter_by(id=id).first()
    if user is None:
        return failure_response("User not found")
    return success_response(user.serialize())


def delete_user(id):
    """
    Endpoint for deleting a user by id
    """

    user = db.Locations.query.filter_by(id=id).first()
    if user is None:
        return failure_response("User not found")

    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())


@app.route("/api/locations/<int:location_id>/facilities")
def get_all_facility(location_id):
    facilities = db.Facility.query.filter_by(location_id=location_id)
    if facilities is None:
        return failure_response("Facility not found")

    f = []
    for fac in facilities:
        facility = fac.simple_serialize()
        f.append(facility)
    return success_response({"facilities": f})


@app.route("/api/locations/<int:location_id>/facilities/<int:facility_id>/")
def get_facility(location_id, facility_id):
    facility = db.Facility.query.filter_by(
        location_id=location_id, id=facility_id)
    if facility is None:
        return failure_response("Facility not found")
    return success_response(facility.simple_serialize)


@app.route("/api/locations/<int:location_id>/facilities/<int:facility_id>/add/", methods=["POST"])
def add_reservation(location_id, facility_id):
    """
    Endpoint for adding a reservation for a specific user
    """

    facility = db.Facility.query.filter_by(
        id=facility_id, location_id=location_id)

    if facility is None:
        return failure_response("Facility not found.")
    body = json.loads(request.data)

    netid = body.get("netid")
    start_time = body.get("start_time")
    end_time = body.get("end_time")

    user = db.User.query.filter_by(netid=netid).first()

    if user is None:
        return failure_response("Invalid netid.")

    if db.Facility.query.filterby(start_time=start_time) is None and db.Facility.query.filterby(end_time=end_time) is None:
        new_fac = db.Facility(name=facility.name, start_time=start_time,
                              end_time=end_time, location_id=location_id)
        db.session.add(new_fac)
        new_fac.booked.append(user)
    else:
        return failure_response("This time has been booked by some user.")
    db.session.commit()
    return success_response(new_fac.serialize())


@app.route("/api/locations/<int:location_id>/facilities/<int:facility_id>/cancel/", methods=["DELETE"])
def cancel_reservation(location_id, facility_id):
    """
    Endpoint for cancelling a reservation for a specific user
    """
    location = db.Location.query.filter_by(id=location_id).first()
    if location is None:
        return failure_response("Location not found")

    facility = db.Facility.query.filter_by(
        id=facility_id, location_id=location_id)

    if facility is None:
        return failure_response("Facility not found.")
    body = json.loads(request.data)

    netid = body.get("netid")
    start_time = body.get("start_time")
    end_time = body.get("end_time")

    user = db.User.query.filter_by(netid=netid).first()

    if user is None:
        return failure_response("Invalid netid.")

    times = [start_time, end_time]
    facility.datetime = times

    # [2022/11/08 1100 , 2022/11/08 1200]
    # datetime.now >

    db.session.commit()
    return success_response(course.serialize())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
