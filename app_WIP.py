import argparse
import json
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

@app.before_first_request
def before_first_request():
    print("Start: before_first_request")
    global cam
    global cam_info
    cam = GenICam()
    cam_info = f"<p>{cam.info()}</p>"
    print("Cam: ", cam)
    print("END: before_first_request")

@app.route('/')
def index():
    with open("./templates/config.json") as config_file:
        config = json.load(config_file)
    return render_template(
        "index.html",
        gain=cam.gain,
        res=config["aspects"],
        cur_res=cam.scale,
        expo=cam.exposure,
        info=cam_info,
    )


@app.route("/info")
def info():
    return f"{cam.info()}"


@app.route("/cam_config", methods=["POST"])
def cam_res():
    if request.method == "POST":
        with open("./templates/config.json") as config_file:
            config = json.load(config_file)
        data = request.form
        print(data)
        cam.ia.stop_acquisition()
        keys = data.keys()
        print(keys)
        if "exposure" in keys and data["exposure"] != "":
            cam.exposure = int(data["exposure"])
        if "gain" in keys and data["gain"] != "":
            cam.gain = float(data["gain"])
        cam.scale = data["resolution"]
        cam.ia.start_acquisition()
    return render_template(
        "index.html",
        gain=cam.gain,
        res=config["aspects"],
        cur_res=cam.scale,
        expo=cam.exposure,
        info=cam_info,
    )

@app.route('/video_feed')
def video_feed():
    cam.trigger()
    return Response(cam.grab(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/fps')
def fps():
    return Response("666", mimetype="text")

print(__name__)
#%%
if __name__ == '__main__':
    print("Main")
    app.run(host="0.0.0.0", port=5050, debug=True)
