from flask import Blueprint
import socketserver
import threading 
from .models import Device
import json


def process(data): 
    return '*'


class fumfliServerRequestHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):        
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return
    def handle(self):
        cli = self.client_address
        print(f'connection from: {cli}')   
        self.request.settimeout(10)
        while True:
            try:
                data = self.request.recv(1024).decode('utf-8')
            except Exception as e:
                print(f'wtf:{e}')
                break
            if data:
                t = threading.currentThread()
                print(f'fumfli server on {t.name} received "{data}" from {cli}')
                js = json.loads(data)
                print(js)
                
                device = Device.query.filter_by(mac=data).first()
                if not device:
                    print(f"new device with mac:{js['MAC']}")
                else :
                    pass
                
                resp = process(js)
                self.request.sendall(resp.encode('utf-8'))
            else: 
                break
        print(f'connection with "{cli}" closed')


class fumfliServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def runFumfliServer(app):
    """ 
    with fumfliServer(('0.0.0.0', 999), fumfliServerRequestHandler) as server:
        server.serve_forever()
    """
    server = fumfliServer(('0.0.0.0', 999), fumfliServerRequestHandler)
    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True) # don't hang on exit
    t.start()
    print ('Fumfli server loop running in thread:', t.getName())
    

if __name__ == '__main__':
    runFumfliServer()




