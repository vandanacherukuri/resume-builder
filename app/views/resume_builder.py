from flask import Blueprint, render_template, request, session, redirect, url_for, g, abort, make_response, flash
from ..userform import UserForm
from ..functions import resume_data_required, get_all_fonts_name, font_exists, get_font
from ..config import TEMPLATES, TEMPLATES_PATH
from flask_login import login_user, login_required, logout_user, current_user
from ..models import User, db
from werkzeug.security import generate_password_hash, check_password_hash


resume_builder = Blueprint("ResumeBuilder", __name__)


@resume_builder.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('UserName already exists.', 'error')
            return redirect(url_for('.register')) 

        # Validate email format
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('.register'))

        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'error')
            return redirect(url_for('.register'))

        # Validate password strength (e.g., length)
        if len(password) < 6:  # Example: Minimum 6 characters
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('.register'))

        # All validations passed, create new user
        new_user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Registration successful!', 'success')
        return redirect(url_for('.create_resume'))

    return render_template('register.html')


@resume_builder.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('.login'))

        # Login successful, redirect to create_resume route
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('.create_resume'))

    return render_template('login.html')


@resume_builder.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('.create_resume'))

@resume_builder.route("/", methods=["GET", "POST"])
@login_required
def create_resume():
    current_user_form = UserForm()
    if request.method == "POST":
        current_user_form.from_request()
        current_user_form.validate()
        session.permanent = True
        session["resume-data"] = current_user_form.resume_data
        if len(current_user_form.errors) > 0:
            return redirect(url_for(".create_resume"))
        return redirect(url_for(".select_template"))

    current_user_form.from_session("resume-data")
    current_user_form.validate()

    return render_template(
        "resume_builder/create_resume.html",
        title="Build New Resume",
        resume_formdata=current_user_form.resume_data,
        resume_formdata_errors=current_user_form.errors,
    )


@resume_builder.route("/select-template")
@login_required
@resume_data_required
def select_template():
    return render_template(
        "resume_builder/select_template.html",
        title="Select template for Resume",
        all_fonts=get_all_fonts_name(),
        available_templates=TEMPLATES
    )


@resume_builder.route("/preview")
@login_required
@resume_data_required
def preview_and_save():
    TEMPLATE_NAME = request.args.get("template-name","").upper()
    HEADING_FONT = request.args.get("heading-font","")
    PARAGRAPH_FONT = request.args.get("paragraph-font","")
    if TEMPLATE_NAME not in TEMPLATES or\
        font_exists(HEADING_FONT) is False or\
        font_exists(PARAGRAPH_FONT) is False:
        flash("Please select template and fonts to view preview!")
        return redirect(url_for(".select_template"))

    current_user_form = g.user_form

    if request.args.get("form") == "iframe":
        return render_template(
            TEMPLATES_PATH[TEMPLATE_NAME],
            formdata=current_user_form.resume_data,
            HEADING_FONT=get_font(HEADING_FONT),
            PARAGRAPH_FONT=get_font(PARAGRAPH_FONT),
            type=type
        )

    elif request.args.get("form") == "download":
        HTML_DATA = render_template(
            TEMPLATES_PATH[TEMPLATE_NAME],
            formdata=current_user_form.resume_data,
            HEADING_FONT=get_font(HEADING_FONT),
            PARAGRAPH_FONT=get_font(PARAGRAPH_FONT),
            type=type
        )
        response = make_response(HTML_DATA)
        response.headers.add("Content-Disposition", 'attachment', filename='resume.html')
        return response
        

    elif request.args.get("form") is not None:
        abort(400)

    return render_template(
        "resume_builder/preview.html",
        title="Resume preview",
    )