"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""
from db import db
from db import Users


def get_user_by_email(email):
    """
    Returns a user object from the database given an email
    """
    return Users.query.filter(Users.email == email).first()


def get_user_by_session_token(session_token):
    """
    Returns a user object from the database given a session token
    """
    return Users.query.filter(Users.session_token == session_token).first()


def get_user_by_update_token(update_token):
    """
    Returns a user object from the database given an update token
    """
    return Users.query.filter(Users.update_token == update_token).first()


def verify_credentials(email, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    optional_user = get_user_by_email(email)

    if optional_user is None:
        return False, None

    return optional_user.verify_password(password), optional_user


def create_user(name, netid, email, password):
    """
    Creates a User object in the database

    Returns if creation was successful, and the User object
    """
    optional_user = get_user_by_email(email)

    if optional_user is not None:
        return False, optional_user

    user = Users(name=name, netid=netid, email=email, password=password)

    db.session.add(user)
    db.session.commit()

    return True, user


def renew_session(update_token):
    """
    Renews a user's session token

    Returns the User object
    """
    optional_user = get_user_by_update_token(update_token)
    if optional_user is None:
        return False, None

    optional_user.renew_session()
    db.session.commit()
    return True, optional_user
