"""Flask application for DogeAnalyze dashboard."""

from flask import Flask
from flask_cors import CORS
from config.settings import FLASK_PORT, SECRET_KEY, FLASK_ENV
from dashboard.routes import register_routes
from utils.logger import setup_logger

logger = setup_logger('dashboard')

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['ENV'] = FLASK_ENV
    
    # Enable CORS
    CORS(app)
    
    # Register routes
    register_routes(app)
    
    logger.info("Dashboard application created successfully")
    return app


def main():
    """Run the Flask application."""
    app = create_app()
    logger.info(f"Starting dashboard server on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=(FLASK_ENV == 'development'))


if __name__ == '__main__':
    main()

