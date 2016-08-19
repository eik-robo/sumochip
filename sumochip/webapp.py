from __future__ import print_function
from flask import Flask, render_template
from sumorobot import Sumorobot, SensorThread, isLine, isEnemy
from flask_sockets import Sockets
from threading import Thread
from time import sleep
import imp
import json
import textwrap

codeTemplate = """
from threading import Thread
class AutonomousThread(Thread):
    def __init__(self, sumorobot):
        Thread.__init__(self)
        self.sumorobot = sumorobot

    def run(self):
        self.running = True
        while self.running:
            self.step()
            sleep(0.5)
        self.sumorobot.stop()
    def step(self):
        sumorobot = self.sumorobot
        isEnemy = lambda x: False
        print(isEnemy("TEST"))
"""


sumorobot = Sumorobot()
codeThread = None
codeText = ""
codeBytecode = None

app = Flask(__name__)
try:
    with open("/etc/machine-id", "r") as fh:
        app.config['SECRET_KEY'] = fh.read()
except:
    app.config['SECRET_KEY'] = 'secret!'
sockets = Sockets(app)

@app.route('/')
def index():
    print("HTTP request")
    return render_template('index.html')

@sockets.route('/')
def command(ws):
    global codeThread
    global codeText
    global codeBytecode
    while not ws.closed:
        command = ws.receive()
        if command:
            print('Command: ' + command)
        if command == '0':
            print("Stop")
            sumorobot.stop()
        elif command == '1':
            print("Forward")
            sumorobot.forward()
        elif command == '2':
            print("Back")
            sumorobot.back()
        elif command == '3':
            print("Right")
            sumorobot.right()
        elif command == '4':
            print("Left")
            sumorobot.left()
        elif command == 'sensors':
            print("keegi kysib sensoreid")
            sensors = SensorThread(ws, sumorobot)
        elif command == 'getSavedCode':
            with open("code.txt", "r") as fh:
                code = fh.read()
                print(code)
                ws.send(json.dumps({'savedCode':code}))
        elif command == 'executeCode':
            if codeThread:
                codeThread.running = False
            slave = {}
            exec codeBytecode in slave
            codeThread = slave["AutonomousThread"]()
            codeThread.daemon = True
            codeThread.start()
            print("slave", slave)
        elif command == 'stopCode':
            if codeThread:
                codeThread.running = False
            print("code execution stopped")
        else:
            print("Code to be saved:")
            print(command)
            with open("code.txt", "w") as fh:
                fh.write(str(command))
            codeText = str(command)
            fullCodeText = codeTemplate + "".join((" "*8 + line + "\n" for line in codeText.split("\n")))
            print(fullCodeText)
            codeBytecode = compile(codeText, "<string>", "exec")
            print('Saved')

if __name__ == '__main__':
    print("Started server")
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('0.0.0.0', 5001), app, handler_class=WebSocketHandler)
    server.serve_forever()
