import argparse
import json
import os
import random as rd
import numpy as np

import io

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
    """code run before loading first page"""
    print("Start: before_first_request")
    global cam
    global cam_info
    cam = GenICam()
    cam_info = f"<p>{cam.info()}</p>"
    print("Cam: ", cam)
    print("END: before_first_request")

@app.route('/')
def index():
    """main page displayed"""
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
    """url for retreaving information on camera"""
    return f"{cam.info()}"

@app.route("/download")
def download():
    File = "cam_download.png"
    cam.trigger()
    cam.grab(save=True)
    return send_file(File, as_attachment=True)


@app.route("/cam_config", methods=["POST"])
def cam_res():
    """api endpoint for changing camera settings"""
    if request.method == "POST":
        data = request.form
        cam.ia.stop_acquisition()
        keys = data.keys()
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
    """url used for image streaming"""
    return Response(gen_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")

def gen_frame():
    """get frame displayable on website from camera"""
    while True:
        cam.exposure = rd.randint(cam.exposure-200,cam.exposure+200)
        cam.trigger()
        """image_data = cam.grab()
        print(image_data)"""
        yield cam.grab(Frame=True)


if __name__ == '__main__':
    """Run Flask application"""
    app.run(host="0.0.0.0", port=5050, debug=True)
