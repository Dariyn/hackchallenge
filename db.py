import datetime
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey(
        "facilities.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    user = db.relationship("Users", back_populates="reservations")
    facility = db.relationship("Facility", back_populates="reservations")

    def __init__(self, **kwargs):
        """
        Creates a reservation object
        """
        self.user_id = kwargs.get("user_id", "")
        self.facility_id = kwargs.get("facility_id", "")
        self.start_time = kwargs.get("start_time", "")
        self.end_time = kwargs.get("end_time", "")

    def serialize(self):
        """
        Serializes a reservation object
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "facility_id": self.facility_id,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
        }


class Users(db.Model):
    """
    Table for Users
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # User information
    email = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)

    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    # Other information
    name = db.Column(db.String, nullable=False)
    netid = db.Column(db.String, nullable=False)
    reservations = db.relationship("Reservation", back_populates="user")

    def __init__(self, **kwargs):
        """
        Creates a User object
        """
        self.name = kwargs.get("name", "")
        self.netid = kwargs.get("netid", "")
        self.email = kwargs.get("email", "")
        self.password_digest = bcrypt.hashpw(kwargs.get(
            "password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    def serialize(self):
        """
        Serializes a User object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "email": self.email,
            "reservations": [f.simple_serialize() for f in self.reservations]
        }

    def simple_serialize(self):
        """
        Simple Serializes a User object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "email": self.email,
        }

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token


class Location(db.Model):
    """
    Has a many to many relationship with users
    Has a one to many relationship with facilties
    """

    __tablename__ = "location"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    weekday_operating_start = db.Column(db.String, nullable=False)
    weekday_operating_end = db.Column(db.String, nullable=False)
    weekend_operating_start = db.Column(db.String, nullable=False)
    weekend_operating_end = db.Column(db.String, nullable=False)

    def __init__(self, **kwargs):
        """
        Creates a Location object
        """
        self.code = kwargs.get("code", "")
        self.name = kwargs.get("name", "")
        self.address = kwargs.get("address", "")
        self.weekday_operating_start = kwargs.get(
            "weekday_operating_start")
        self.weekday_operating_end = kwargs.get(
            "weekday_operating_end")
        self.weekend_operating_start = kwargs.get(
            "weekend_operating_start")
        self.weekend_operating_end = kwargs.get(
            "weekend_operating_end")

    def serialize(self):
        """
        Serializes a Location object
        """
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "address": self.address,
            "weekday_operating_start": self.weekday_operating_start,
            "weekday_operating_end": self.weekday_operating_end,
            "weekend_operating_start": self.weekend_operating_start,
            "weekend_operating_end": self.weekend_operating_end,

        }


class Facility(db.Model):
    """
    Table for facilities
    """
    __tablename__ = "facilities"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey(
        "location.id"), nullable=False)
    reservations = db.relationship("Reservation", back_populates="facility")

    def __init__(self, **kwargs):
        """
        Creates a assignment object
        """
        self.name = kwargs.get("name", "")
        self.location_id = kwargs.get("location_id", "")

    def serialize(self):
        """
        Serializes a Facility object
        """
        return {
            "id": self.id,
            "name": self.name,
            "location_id": self.location_id,
            "reservations": [u.simple_serialize() for u in self.reservations]
        }

    def simple_serialize(self):
        """
        Simple serializes a Facility object
        """
        return {
            "id": self.id,
            "name": self.name,
        }
