from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import LoginManager
import logging
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.configuration_manager import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Use configuration manager for app settings
app.config['SECRET_KEY'] = config_manager.config.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = config_manager.get_max_file_size()

db = SQLAlchemy(app)

# TODO: Add bcrypt back when installation issues are resolved
# bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import routes at the end to avoid circular imports
from attendance import routes