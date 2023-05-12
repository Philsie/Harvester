import argparse
import os
import random as rd

from flask import Flask, Response, flash, render_template, request, send_file

from GenICam import GenICam

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
    print("Start: before_first_request")
    global cam
    cam = GenICam()
    print("Cam: ", cam)
    cam.ia.start_image_acquisition()
    print("END: before_first_request")

@app.route('/')
def index():
    print("hi therte")
    print(cam.get_size())
    return render_template(
        "index.html", gain=cam.gain, res=cam.get_size(), expo=cam.exposure
    )

@app.route("/cam_res",methods = ['POST'])
def cam_res(): 
    if request.method == "POST":
        data = request.form
        print(data)
        cam.ia.stop_acquisition()
        config_device(cam.ia, data)
        keys = data.keys()
        print(keys)
        if "exposure" in keys and data["exposure"] != "":
            cam.exposure = int(data["exposure"])
        if "gain" in keys and data["gain"] != "":
            cam.gain = float(data["gain"])
        cam.ia.start_acquisition()
    return render_template(
        "index.html", gain=cam.gain, res=cam.get_size(), expo=cam.exposure
    )

@app.route('/video_feed')
def video_feed():
    print("/video_feed")
    cam.trigger()
    print("Trigger Done")
    return Response(cam.grab(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/fps')
def fps():
    return Response("666", mimetype="text")


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


print(__name__)
#%%
if __name__ == '__main__':
    print("Main")
    app.run(host="0.0.0.0", port=5050, debug=True)
