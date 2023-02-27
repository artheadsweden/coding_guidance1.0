import os
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from bson import ObjectId
from app.db.mongo_doc import create_collection_class, init_db, add_base_class, add_collection_method

init_db('mongodb://localhost:27017', 'coding_guidance')
login_manager = LoginManager()
User = create_collection_class('User', 'users')
add_base_class(User, UserMixin)
def get_id(self):
    return str(self._id)
add_collection_method(User, get_id)


def create_app():
    app = Flask(__name__)
    from app.config import Config, DevelopmentConfig, ProductionConfig
    # Select the configuration class based on the current environment
    if os.environ.get('MODE') == 'DEV':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)
    login_manager.init_app(app)

    # Define the user loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        # Load the user object from the database using the user_id
        user_id = ObjectId(user_id)
        user = User.find(_id=user_id).first_or_none()

        return user
    
    from app.blueprints.open import open_bp
    app.register_blueprint(open_bp)
    
    from app.blueprints.user import user_bp
    
    app.register_blueprint(user_bp)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    
    
    