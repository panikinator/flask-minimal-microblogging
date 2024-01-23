from flask import g, current_app, flash, session, redirect
import sqlite3
from functools import wraps


def login_required(f):

    @wraps(f)
    def wrap(*args, **kwargs):
        if 'id' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect("/login")

    return wrap


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE_PATH"])
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=()):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv

def execute_db(cmd, args=()):
    db = get_db()
    cur = db.cursor()
    cur.execute(cmd, args)
    db.commit()
    cur.close()

def init_db():
    with current_app.app_context():
        db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
