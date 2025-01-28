from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, abort
from flask_login import login_required, current_user
from .models import *
from . import db
import time
from datetime import datetime
from werkzeug.security import generate_password_hash
from .device_server import send_reset_cmd, send_sync_cmd, send_ota_cmd, online_devices
import io
import json

views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    if current_user.role != 'admin':    
        return redirect(url_for('views.user_home'))
    return render_template("home.html", user=current_user)


@views.route('/user')
@login_required
def user_home():
    al = Access_level.query.filter_by(id=current_user.access_level).first()
    aps = al.access_points
    return render_template("user_home.html", user=current_user, aps=aps)


@views.route('/devices')
@login_required
def devices():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    devs = Device.query.all()
    now = int(time.time()) 
    return render_template("devices.html", 
                           user = current_user, 
                           devs = devs, 
                           now = now, 
                           online_devices = online_devices)


@views.route('/edit_device/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_device(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device :
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    if request.method == 'POST':
        name = request.form.get('Name')
        config = request.form.get('Config')
        try:
            j = json.loads(config)
        except:
            j = None
        if j is not None: #
            device.name = name
            device.config = config
            db.session.add(device)
            db.session.commit()
            flash('Device updated', category='success')
        else:
            flash('Wrong format, config must be json', category='error')
        return redirect(url_for('views.devices'))
    return render_template("edit_device.html", user = current_user, device = device)


@views.route('/delete_device/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_device(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device :
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    if request.method == 'POST':
        send_reset_cmd(device)##########################
        db.session.delete(device)
        db.session.commit()
        flash('Device deleted', category='success')
        return redirect(url_for('views.devices'))
    return render_template("delete_device.html", user = current_user, device=device)


@views.route('/get_cards/<string:id>')
def send_cards(id):
    device = Device.query.filter_by(mac=id).first()
    if not device :
        abort(404)
    buff = io.BytesIO()
    access_point = Access_point.query.filter_by(id=device.access_point).first()
    for access_level in access_point.access_levels:
        #access_level = Access_level.query.filter_by(id=access_level_id).first() 
        for user in access_level.users:
            c=user.card_number
            if c:
                buff.write(user.card_number.to_bytes(4,'big'))
    buff.seek(0)
    return send_file(buff, download_name='cards')
    

@views.route('/get_config/<string:id>')
def send_config(id):
    device = Device.query.filter_by(mac=id).first()
    if not device :
        abort(404)
    buf = io.BytesIO()
    if device.config is None:
        buf.write('''{"aps":[
            {"ssid":"shvancki","password":"11111111"},
            {"ssid":"10 e block guest","password":""},
            {"ssid":"GREAN_WIFI","password":"wifipass"},
            {"ssid":"OCH Lobby","password":"och2020!"},
            {"ssid":"MyLePort","password":"myleport"}
            ],
        "server_address":"wss://ubda.ge/ws",
        "ota_server_address":"https://static.ubda.ge",
        "config_host":"http://ubda.ge",
        "unlock_time" : 1000,
        "ota_filenames":[
        {"file":"boot.py"},
        {"file":"main.py"},
        {"file":"ws.py"},
        {"file":"wiegand.py"},
        {"file":"ota.py"},
        {"file":"config.json"}
        ],
        "model":"fumfli_c3"''').encode()
    else:
        buf.write(device.config.encode())
    buf.seek(0)
    return send_file(buf, download_name='conf.json')

@views.route('/update_fw/<string:id>', methods=['GET', 'POST'])
@login_required
def update_fw(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device :
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    if request.method == 'POST':
        ###send reset command
        send_ota_cmd(device)
        ###
        flash('OTA request sent', category='success')
        return redirect(url_for('views.devices'))
    return render_template("ota.html", user = current_user, device=device)

@views.route('/reset_device/<string:id>', methods=['GET', 'POST'])
@login_required
def reset_device(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device :
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    if request.method == 'POST':
        ###send reset command
        send_reset_cmd(device)
        ###
        flash('Reset request sent', category='success')
        return redirect(url_for('views.devices'))
    return render_template("reset_device.html", user = current_user, device=device)

@views.route('/sync_device/<string:id>', methods=['GET', 'POST'])
@login_required
def sync_device(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device :
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    if request.method == 'POST':
        
        send_sync_cmd(device)
        
        flash('Sync request sent', category='success')
        return redirect(url_for('views.devices'))
    return render_template("sync_device.html", user = current_user, device=device)


@views.route('/device_log/<string:id>')
@login_required
def device_log(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    device = Device.query.filter_by(id=id).first()
    if not device:
        flash(f'No device with id:{id}', category='error')
        return redirect(url_for('views.devices'))
    else:
        return render_template("device_log.html", 
                                device= device)


@views.route('/outputs')
@login_required
def outputs():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    devs = Device.query.all()
    return render_template("outputs.html", current_user = current_user, devs = devs)


@views.route('/edit_output/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_output(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    output = Output.query.filter_by(id=id).first()
    if not output :
        flash(f'No output with id:{id}', category='error')
        return redirect(url_for('views.outputs'))
    if request.method == 'POST':
        name = request.form.get('Name')
        output.name = name
        db.session.add(output)
        db.session.commit()
        flash('Output information updated', category='success')
        return redirect(url_for('views.outputs'))
    return render_template("edit_output.html", user = current_user, output = output)




#access levels
#******************************
@views.route('/access_levels')
@login_required
def access_levels():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    accessLevels = Access_level.query.all() 
    return render_template("access_levels.html", user = current_user, access_levels = accessLevels)

@views.route('/add_access_level', methods=['GET', 'POST'])
@login_required
def add_access_level():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_points = Access_point.query.all()
    outputs = Output.query.all()
    if request.method == 'POST':
        description = request.form.get('description')
        name = request.form.get('name')    
        access_level = Access_level.query.filter_by(name=name).first()
        if access_level:
            flash(f'Access level with name:"{name}" already exists', category='error')
        elif len(name) < 2:
            flash('Too short name', category='error')
        else:
            new_access_level = Access_level(description = description, name = name)
            for access_point in access_points:
                if request.form.get(access_point.name):
                    print(f'd-{access_point.id}')
                    new_access_level.access_points.append(access_point)
            for output in outputs:
                if request.form.get(str(output.id)):
                    print(f'o-{output.id}')
                    new_access_level.outputs.append(output)
            db.session.add(new_access_level)
            db.session.commit()
            flash('Access level added!', category='success') 
            #return redirect(url_for('views.access_levels'))     
    return render_template("add_access_level.html", user = current_user, 
                                                    access_points = access_points, 
                                                    outputs = outputs)


@views.route('/edit_access_level/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_access_level(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_level = Access_level.query.filter_by(id=id).first()
    access_points = Access_point.query.all()
    if not access_level :
        flash(f'No Access level with id:{id}', category='error')
        return redirect(url_for('views.access_levels'))  
    if request.method == 'POST':
        outputs = Output.query.all()
        access_level.description = request.form.get('description')
        access_level.name = request.form.get('name')
        access_level.access_points = []
        access_level.outputs = []
        for access_point in access_points:
            if request.form.get(access_point.name):
                access_level.access_points.append(access_point)
        for output in outputs:
            if request.form.get(str(output.id)):
                access_level.outputs.append(output)
        db.session.add(access_level)
        db.session.commit()
        flash('Access level updated', category='success')
        return redirect(url_for('views.access_levels'))
    return render_template("edit_access_level.html", user = current_user, 
                                                    access_level = access_level, 
                                                    access_points=access_points)


@views.route('/delete_access_level/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_access_level(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_level = Access_level.query.filter_by(id=id).first()
    if not access_level :
        flash(f'No access level with id:{id}', category='error')
        return redirect(url_for('views.access_levels'))
    if request.method == 'POST':
        db.session.delete(access_level)
        db.session.commit()
        flash('Access level deleted', category='success')
        return redirect(url_for('views.access_levels'))
    return render_template("delete_access_level.html", user = current_user, access_level=access_level)

#access points
#******************************
@views.route('/access_points')
@login_required
def access_points():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    accessPoints = Access_point.query.all() 
    return render_template("access_points.html", user = current_user, access_points = accessPoints)

@views.route('/add_access_point', methods=['GET', 'POST'])
@login_required
def add_access_point():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    devices = Device.query.all()
    if request.method == 'POST':
        description = request.form.get('description')
        name = request.form.get('name')    
        access_point = Access_point.query.filter_by(name=name).first()
        if access_point:
            flash(f'Access point with name:"{name}" already exists', category='error')
        elif len(name) < 2:
            flash('Too short name', category='error')
        else:
            new_access_point = Access_point(description = description, name = name)
            for device in devices:
                if request.form.get(device.mac):
                    print(f'd-{device.id}')
                    new_access_point.devices.append(device)
            db.session.add(new_access_point)
            db.session.commit()
            flash('Access point added!', category='success') 
            #return redirect(url_for('views.access_levels'))     
    return render_template("add_access_point.html", user = current_user, 
                                                    devices = devices, 
                                                    access_levels = access_levels)


@views.route('/delete_access_point/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_access_point(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_point = Access_point.query.filter_by(id=id).first()
    if not access_point :
        flash(f'No access point with id:{id}', category='error')
        return redirect(url_for('views.access_points'))
    if request.method == 'POST':
        db.session.delete(access_point)
        db.session.commit()
        flash('Access point deleted', category='success')
        return redirect(url_for('views.access_points'))
    return render_template("delete_access_point.html", user = current_user, access_point=access_point)

@views.route('/edit_access_point/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_access_point(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_point = Access_point.query.filter_by(id=id).first()
    devices = Device.query.all()
    if not access_point:
        flash(f'No Access point with id:{id}', category='error')
        return redirect(url_for('views.access_points'))  
    if request.method == 'POST':
        outputs = Output.query.all()
        access_point.description = request.form.get('description')
        access_point.name = request.form.get('name')
        access_point.devices = []
        for device in devices:
            if request.form.get(device.mac):
                access_point.devices.append(device)
        db.session.add(access_point)
        db.session.commit()
        flash('Access point updated', category='success')
        return redirect(url_for('views.access_points'))
    return render_template("edit_access_point.html", user = current_user, 
                                                    access_point = access_point, 
                                                    devices=devices)