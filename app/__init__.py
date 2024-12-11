from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pymongo import PyMongo

db = SQLAlchemy()

def create_app(config:dict):
    app = Flask(__name__)
    app.config.update(config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'ResumeBuilder.login'
    login_manager.init_app(app)
    with app.app_context():
        from .models import User
        db.create_all()
        from .views.resume_builder import resume_builder
        app.register_blueprint(resume_builder)
   
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app