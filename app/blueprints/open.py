from flask import Blueprint, render_template, request, redirect, url_for, flash
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
from app import User
from app.utils.github_utils import get_github_user

open_bp = Blueprint('open', __name__, template_folder='templates')


@open_bp.get('/')
def index():
    return render_template('index.html')


@open_bp.get('/register')
def register():
    return render_template('signup.html')


@open_bp.post('/register')
def register_post():
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    email = request.form.get('email')
    github_username = request.form.get('github_username')
    password = request.form.get('password')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    full_name = first_name + ' ' + last_name
    github_user = get_github_user(github_username)
    user = User(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        email=email,
        github_username=github_username,
        password=hashed_password, 
        is_active=True,
        github_user=github_user,
        avatar=github_user['avatar_url'],
        generated_avatar=f"https://ui-avatars.com/api/?name={full_name}&background=0D8ABC&color=fff",
        repos=[],
        reports=[]
    )
    user.save()

    return redirect(url_for('open.login'))


@open_bp.get('/login')
def login():
    return render_template('signin.html')


@open_bp.post('/login')
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    if '@' in username:
        user = User.find(email=username).first_or_none()
    else:
        user = User.find(github_username=username).first_or_none()
    if user is not None:
        if bcrypt.checkpw(password.encode('utf-8'), user.password):
            login_user(user)
        return redirect(url_for("user.user_main"))
    flash('Login failed. Please try again.', 'error')
    return redirect(url_for('open.login'))
