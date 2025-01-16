from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import path
from flask_login import LoginManager
from flask_sock import Sock

hostname = 'http://192.168.1.102:5000'

device_models = {
    'fumfli_c3':{
        'outputs':1, 
        'inputs':1,
        },
    'fumfli_c3_bt':{
        'outputs':1, 
        'inputs':1,
        },
    'fumfli_c3_ac':{
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
        },
    'fumfli_s3':{
        'outputs':1,
        'inputs':1,
        }
}
db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'huP_*jsh!2jQ#hdj4$$#ahskAKDjfks798KljPo457/%2DGkj^&shk@#jdhjs'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db'

app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}




sock = Sock(app)

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
db.init_app(app)
migrate = Migrate(app, db)

'''
with app.app_context():
    db.create_all()
    print('Created Database!')
'''
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

