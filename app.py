import json

from flask import Flask, request
import users_dao
import datetime

from db import db
from db import Location
from db import Users
from db import Facility
from db import Reservation

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

    name = body.get("name")
    netid = body.get("netid")
    email = body.get("email")
    password = body.get("password")

    if name is None:
        return failure_response("Missing name", 400)

    if netid is None:
        return failure_response("Missing netid", 400)

    if email is None:
        return failure_response("Missing email", 400)

    if password is None:
        return failure_response("Missing password", 400)

    success, user = users_dao.create_user(name, netid, email, password)

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
    for l in Location.query.all():
        loc = l.serialize()
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
    weekday_operating_start = body.get("weekday_operating_start")
    if weekday_operating_start is None:
        return failure_response("No weekday operating time start", 400)

    weekday_operating_end = body.get("weekday_operating_start")
    if weekday_operating_end is None:
        return failure_response("No weekday operating time end", 400)
    weekend_operating_start = body.get("weekday_operating_start")
    if weekday_operating_start is None:
        return failure_response("No weekend operating time start", 400)

    weekend_operating_end = body.get("weekday_operating_start")
    if weekday_operating_end is None:
        return failure_response("No weekend operating time end", 400)

    location = Location(code=code, name=name, address=address, weekday_operating_start=weekday_operating_start, weekday_operating_end=weekday_operating_end,
                        weekend_operating_start=weekend_operating_start, weekend_operating_end=weekday_operating_end)
    db.session.add(location)
    db.session.commit()

    new_location = {
        "id": location.id,
        "code": location.code,
        "name": location.name,
        "weekday_operating_start": location.weekday_operating_start,
        "weekday_operating_end": location.weekday_operating_end,
        "weekend_operating_start": location.weekend_operating_start,
        "weekend_operating_end": location.weekend_operating_end,
    }
    return success_response(new_location, 201)


@app.route("/api/locations/<int:id>/")
def get_location(id):
    """
    Endpoint for getting a location by id
    """

    location = Location.query.filter_by(id=id).first()
    if location is None:
        return failure_response("Location not found")
    return success_response(location.serialize())


@app.route("/api/locations/<int:id>/", methods=["DELETE"])
def delete_location(id):
    """
    Endpoint for deleting a course by id
    """

    location = Location.query.filter_by(id=id).first()
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

    user = Users.query.filter_by(id=id).first()
    if user is None:
        return failure_response("User not found")
    return success_response(user.serialize())


@app.route("/api/users/<int:id>/", methods=["DELETE"])
def delete_user(id):
    """
    Endpoint for deleting a user by id
    """

    user = Users.query.filter_by(id=id).first()
    if user is None:
        return failure_response("User not found")

    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())


@app.route("/api/locations/<int:location_id>/facilities/", methods=["POST"])
def create_facility(location_id):
    """
    Endpoint for creating facilities
    """
    body = json.loads(request.data)

    name = body.get("name")
    if name is None:
        return failure_response("Missing name", 200)
    facility = Facility(name=name, location_id=location_id)

    db.session.add(facility)
    db.session.commit()

    return success_response(facility.serialize())


@app.route("/api/locations/<int:location_id>/facilities")
def get_all_facility(location_id):
    facilities = Facility.query.filter_by(location_id=location_id)
    if facilities is None:
        return failure_response("Facility not found")

    f = []
    for fac in facilities:
        facility = fac.simple_serialize()
        f.append(facility)
    return success_response({"facilities": f})


@app.route("/api/locations/<int:location_id>/facilities/<int:facility_id>/")
def get_facility(location_id, facility_id):
    facility = Facility.query.filter_by(
        location_id=location_id, id=facility_id)
    if facility is None:
        return failure_response("Facility not found")
    return success_response(facility.simple_serialize)


@app.route("/api/locations/<int:location_id>/facilities/<int:facility_id>/add/", methods=["POST"])
def add_reservation(location_id, facility_id):
    """
    Endpoint for adding a reservation for a specific user
    """

    facility = Facility.query.filter_by(
        id=facility_id, location_id=location_id)

    if facility is None:
        return failure_response("Facility not found.")
    body = json.loads(request.data)

    netid = body.get("netid")
    start_time = body.get("start_time")
    end_time = body.get("end_time")

    # convert start_time and end_time to datetime

    start_time = datetime.strptime(start_time, '%m/%d/%y %H:%M:%S')
    end_time = datetime.strptime(end_time, '%m/%d/%y %H:%M:%S')

    user = Users.query.filter_by(netid=netid).first()

    if user is None:
        return failure_response("Invalid netid.")

    # check if user inputted start time is between any other reservation's start and end time
    # check if user inputted end time is between any other reservation's start and end time
    # cuz this means that user is trying to start or end a reservation during another reservation
    # loop through all reservations at the facility the user is trying to reserve

    # authentication for user to add reservation
    if user.session_token == extract_token(request):
        for reservation in Reservation.query.filter_by(facility_id=facility_id):
            if reservation.start_time < start_time and reservation.end_time > start_time:
                return failure_response("Start time is during another reservation.")
            if reservation.start_time < end_time and reservation.end_time > end_time:
                return failure_response("End time is during another reservation.")

        reserve = Reservation(user_id=user.id, facility_id=facility.id,
                              start_time=start_time, end_time=end_time)
        db.session.add(reserve)
        db.session.commit()
        return success_response(reserve.serialize())
    else:
        return failure_response("Authentication error.")


@app.route("/api/reservations/<int:reservation_id>/cancel/", methods=["DELETE"])
def cancel_reservation(reservation_id):
    """
    Endpoint for cancelling a reservation for a specific user
    """
    reserve = Reservation.query.filter_by(id=reservation_id).first()
    user = Users.query.filter_by(id=reserve.user_id).first()
    if reserve is None:
        return failure_response("reservastion not found")
    if user.session_token == extract_token(request):
        db.session.delete(reserve)
        db.session.commit()
        return success_response(reserve.serialize())
    else:
        return failure_response("Authentication error.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
