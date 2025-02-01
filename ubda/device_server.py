from . import db, sock, device_models, app
from flask import request
from .models import Device, Output, User, Access_log, Access_level, Device_log
import json
import time

to_devices = {}

online_devices = {}   

def activate_allowed_outputs(user, ap, method):
    log_entry = Access_log(access_point = ap.id, user = user.id)
    access_level = Access_level.query.filter_by(id = user.access_level).first()
    if not access_level or not ap in access_level.access_points:
        result = -1
        log_entry.content = "access denied, method: " + method
    else:
        for device in ap.devices:
            outputs = []
            for output in device.outputs:
                if output in access_level.outputs:
                    outputs.append(output.n)
            if outputs:
                cmd = '{"open":%s}' %str(outputs)
                to_devices.update({device.id:cmd})
        result = 1
        log_entry.content = "access granted, method: " + method
    db.session.add(log_entry)
    db.session.commit()
    return result

def send_reset_cmd(device):
    to_devices.update({device.id:'{"cmd":"reset"}'}) 

def send_sync_cmd(device):
    to_devices.update({device.id:'{"cmd":"sync"}'}) 

def send_ota_cmd(device):
    to_devices.update({device.id:'{"cmd":"ota", "ota_url":"https://static.ubda.ge/'+device.model+'/fw.bin"}'}) 

@sock.route('/ws/<string:id>')
def dev_server(ws, id):
    client_ip = request.remote_addr
    print(f'incomming connection id:"{id}"')
    try:
        data = ws.receive(1)
    except:
        pass
    if not data:
        print('timeout')
        ws.close()
        return
    else:
        model = None  
        hv = None
        sv = None      
        try:
            js = json.loads(data)
            model = js['model']
            sv = js['sv']
            hv = js['hv']
        except Exception as e:              
            print(f'exception:{e}')
        if not model:
            print('unsupported format, closing connection...')
        elif not model in device_models:     
            print(f'unknown device model "{model}", closing connection...')
        else:
            print(f'connection from:"{client_ip}", device id: "{id}", device model: "{model}"')   
            device = Device.query.filter_by(mac=id).first()
            if not device:
                print(f'new device adding to DB...')
                device = Device(mac = id, 
                                model = model,
                                name = id, 
                                last_seen = int(time.time()),
                                sv = sv,
                                hv = hv)
                db.session.add(device)
                #db.session.commit()
                n_of_outputs = device_models[model]['outputs']
                for n in range(1, n_of_outputs+1):
                    output = Output(device = device.id, 
                                    name = f'{id} - {n}',
                                    n=n)
                    db.session.add(output)
                db.session.commit()
                log_entry = Device_log(device = device.id, content = f"added to db({device.mac})")
                db.session.add(log_entry)
                db.session.commit()
                print(f'device with id:{id} added to DB')
            else :
                print('known device')
                device.last_seen = int(time.time())
                device.sv = sv
                db.session.add(device)
                db.session.commit()
        log_entry = Device_log(device = device.id, content = "connected")
        db.session.add(log_entry)
        db.session.commit()
        if device.id not in online_devices:
            online_devices.update({device.id:1})
        else:
            online_devices.update({device.id:online_devices[device.id]+1}) 
        c=0
        while True:
            try:
                c=c+1
                if c>100:
                    c=0
                    ws.send('.')
                data = ws.receive(0.1) 
                if data:
                    print(f'from device "{device.mac}" - "{data}"')
                    device.last_seen = int(time.time())
                    db.session.add(device)
                    db.session.commit()
                    js = ''
                    try:
                        js = json.loads(data)
                    except: pass
                    if js:
                        if 'card' in js:
                            card = js['card']
                            person = User.query.filter_by(card_number = card).first()
                            if person:
                                if activate_allowed_outputs(person, device, 'card') > 0: 
                                    print(f'access granted - {person.first_name}')
                                else:
                                    print(f'no access - {person.first_name}')
                            else :
                                log_entry = Access_log(device = device.id, 
                                                       content = 'unknown card:' + card)
                                db.session.add(log_entry)
                                db.session.commit()
                                print(f'unknown card:{card}')
                        #if something in js: do something
                if device.id in to_devices:
                    cmd = to_devices[device.id]
                    print(f'to device "{device.mac}" - "{cmd}"')
                    ws.send(cmd)
                    to_devices.pop(device.id)
            except Exception as e:
                if device.id in online_devices:
                    online_devices.update({device.id:online_devices[device.id]-1})
                #print(f'connection with "{id}" closed. e:{e}')
                #print(online_devices)
                log_entry = Device_log(device = device.id, content = f"disconnected, e:{e}")
                db.session.add(log_entry)
                db.session.commit()
                break