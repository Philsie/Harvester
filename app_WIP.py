import argparse
import json
import os
import random as rd
import numpy as np

from datetime import datetime as dt

from flask import Flask, Response, flash, render_template, request, send_file, redirect, url_for

from GenICam import GenICam

#########
#https://github.com/langenhagen/experiments-and-tutorials/blob/master/Python/genicam-harvesters-hello/main.py
#########

#Todo
#SynchronizedCamera

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
    return render_template(
        "index.html",
        gain=cam.gain,
        res=cam.scale,
        cur_res=cam.scale,
        expo=cam.exposure,
        info=cam_info,
        pixelformat=cam.PixelFormat,
        available_pixelformats=np.intersect1d(cam.supported_PixelFormats,cam.ia.remote_device.node_map.PixelFormat.symbolics)
    )

@app.route("/info")
def info():
    return f"{cam.info()}"


@app.route("/cam_config", methods=["POST"])
def cam_res():
    if request.method == "POST":
        data = request.form
        print(data)
        cam.ia.stop_acquisition()
        keys = data.keys()
        print(keys)
        if "exposure" in keys and data["exposure"] != "":
            cam.exposure = int(float(data["exposure"]))
        if "gain" in keys and data["gain"] != "":
            cam.gain = float(data["gain"])
        if "width" in keys and data["width"] != "":
            cam.scale[0] = int(data["width"])
        if "height" in keys and data["height"] != "":
            cam.scale[1] = int(data["height"])
        if "PixelFormat" in keys and str(data["PixelFormat"]) != "":
            cam.PixelFormat = data["PixelFormat"]
        cam.ia.start_acquisition()
    return redirect(url_for("index"))

@app.route('/video_feed')
def video_feed():
    return Response(gen_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/fps')
def fps():
    return Response("666", mimetype="text")

def gen_frame():
    while True:
        cam.exposure = rd.randint(800,1200)
        cam.trigger()
        print(dt.now())
        yield cam.grab()


if __name__ == '__main__':
    print("Main")
    app.run(host="0.0.0.0", port=5050, debug=True)
