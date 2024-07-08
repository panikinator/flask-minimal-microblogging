import os

from flask import Flask, flash, g, redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import execute_db, init_db, login_required, query_db

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY",
                                "fallback_insecure_key_please_replace")

app.config["DATABASE_PATH"] = "database.sqlite3"


# automatically close the sqlite database connection upon closure of connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
@login_required
def index_route():
    recent_posts = query_db(
        "SELECT users.username, posts.content, posts.time_posted, posts.id FROM posts INNER JOIN users ON posts.user_id = users.id ORDER BY time_posted DESC LIMIT 10"
    )
    return render_template("index.html", posts=recent_posts)


# this route returns partial html fragments to work with htmx
@app.route("/get_posts")
@login_required
def get_posts_partial():
    page = request.args.get('page', type=int, default=1)
    offset = (page - 1) * 10
    recent_posts = query_db(
        "SELECT users.username, posts.content, posts.time_posted FROM posts INNER JOIN users ON posts.user_id = users.id ORDER BY time_posted DESC LIMIT ? OFFSET ?",
        (10, offset))
    reached_end = len(recent_posts) < 10
    return render_template("partial/load_more.html",
                           posts=recent_posts,
                           reached_end=reached_end,
                           next_n=page + 1)


@app.route("/register", methods=["GET", "POST"])
def register_route():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    # manual form validation
    if len(username) < 4 or len(password) < 8:
        flash("Too short")
        return redirect(request.url)
    if password != password_confirm:
        flash("Passwords don't match")
        return redirect(request.url)
    user = query_db('select * from users where username = ?', (username, ))
    if user:
        flash("sorry, Username already taken")
        return redirect(request.url)
    password_hash = generate_password_hash(password)
    user_in_db = execute_db(
        "INSERT INTO users (username, password) VALUES (?,?)",
        (username, password_hash))
    print(user_in_db)
    flash("Account created, please login")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = query_db("select * from users where username = ?", (username, ))
    if not user:
        flash("Invalid username or password")
        return redirect(request.url)
    user = user[0]
    if not check_password_hash(user["password"], password):
        flash("Invalid username or password")
        return redirect(request.url)
    session["id"] = user["id"]
    session["username"] = user["username"]
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


@app.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post_route():
    user_id = session.get("id")
    if request.method == "GET":
        return render_template("new_post.html")

    content = request.form.get("content", "")
    if not content:
        flash("Too short!")
        return redirect(request.url)
    if len(content) > 1000:
        flash("Max 1000 characters allowed")
        return redirect(request.url)
    execute_db("INSERT INTO posts(content, user_id) VALUES (?,?)",
               (content, user_id))
    flash("Posted!")
    return redirect("/")

@app.route("/posts/<post_id>/edit", methods=["GET", "PUT"])
@login_required
def edit_post_route(post_id: int):
    user_id = session.get("id")
    if request.method == "GET":
        post = query_db("select * from posts where id = ? AND user_id = ?", (post_id, user_id))
        if post:
            post = post[0]
        else:
            abort(404)
        return render_template("partial/edit_post.html", post=post)
    if request.method == "PUT":
        content = request.form.get("content", "")
        if not content:
            flash("Too short!")
            return redirect("/")
        if len(content) > 1000:
            flash("Max 1000 characters allowed")
            return redirect("/")
        execute_db("UPDATE posts SET content = ? WHERE id = ? AND user_id = ?",
                (content, post_id, user_id))

        post = query_db("SELECT users.username, posts.content, posts.time_posted FROM posts INNER JOIN users ON posts.user_id = users.id WHERE posts.id = ?", (post_id, ))[0]
        
        return render_template("partial/updated_post.html", post=post)

@app.route("/posts/<post_id>/delete", methods=["DELETE"])
@login_required
def delete_post_route(post_id: int):
    user_id = session.get("id")
    execute_db("DELETE from posts where id = ? AND user_id = ?", (post_id, user_id))
    return ""
    


if not os.path.exists(app.config["DATABASE_PATH"]):
    with app.app_context():
        init_db()

# run app through test debug server only if file is executed directly
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
