from app import create_app
import os
from app.config import SQLALCHEMY_DATABASE_URI

app = create_app({
    "SECRET_KEY": os.environ.get("SECRET_KEY", os.urandom(50)),
    "SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URI,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False
})

if __name__ == '__main__':
    with app.app_context():
        from app import db
        db.create_all()
    app.run(debug=True)