from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_sock import Sock

hostname = 'http://192.168.1.102:5000'

device_models = {
    'fumfli_c3':{
        'outputs':1, 
        'inputs':1,
        },
    'fumfli_pi':{
        'outputs':1, 
        'inputs':1,
        },
    'fumfli_c3-16':{
        'outputs':16,
        'inputs':1,
        }
}

DB_NAME = "database.db"

db = SQLAlchemy()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'huP_*jsh!2jQ#hdj4$$#ahskAKDjfks798KljPo457/%2DGkj^&shk@#jdhjs'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

app.config['MQTT_BROKER_URL'] = 'ubda.ge'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

sock = Sock(app)

db.init_app(app)

from .views import views
from .auth import auth
from .access import access
from .user_views import user_views
from .log_views import log_views

app.register_blueprint(views, url_prefix='/')
app.register_blueprint(auth, url_prefix='/')
app.register_blueprint(access, url_prefix='/access/')
app.register_blueprint(user_views, url_prefix='/')
app.register_blueprint(log_views, url_prefix='/log')

#from .device_server import deviceServer
#app.register_blueprint(deviceServer)###

from .models import *

with app.app_context():
    db.create_all()
    print('Created Database!')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

