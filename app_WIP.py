from flask import Flask, render_template, Response, send_file, request
from GeniCam import GeniCam
import os
import random as rd
import argparse


#########
#https://github.com/langenhagen/experiments-and-tutorials/blob/master/Python/genicam-harvesters-hello/main.py
#########

#Todo
#SynchronizedCamera
#Treading --> function

app = Flask(__name__)

global cam_stats
cam_stats = {}

@app.before_first_request
def before_first_request():
    global cam
    global gen
    cam = GeniCam().ia
    cam.start_acquisition()
    gen = GeniCam.Frame_getter(cam)

@app.route('/')
def index():
    return render_template('index.html',cam_stats=cam_stats)

@app.route("/cam_res",methods = ['POST'])
def cam_res(): 
    if request.method == "POST":
        data = request.form
        print(data)
        cam.stop_acquisition()
        config_device(cam,data)
        cam.remote_device.node_map.Exposure.value(10000)
        input()
        cam.start_acquisition()
    return render_template('index.html',cam_stats=cam_stats)


@app.route('/video_feed')
def video_feed():
    return Response(gen.run(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

    """

    return Response(gen.get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    """

@app.route('/fps')
def fps():
    return Response(gen.get_fps(),
                    mimetype='text')
#%%

def config_device(dev,config):
    print(config)
    if "width" in config.keys():
        print("*")
        res = config["resolution"].split("x")
        config["width"] = res[0]
        config["height"] = res[1]
        dev.remote_device.node_map.Width.value = int(config["width"])
        dev.remote_device.node_map.Height.value = int(config["height"])
        cam_stats["width"], cam_stats["height"] = config["width"],config["height"]

#%%
if __name__ == '__main__':
    app.run(debug=False)#,host='0.0.0.0')