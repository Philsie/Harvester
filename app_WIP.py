import argparse
import json
import os
import random as rd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from time import sleep
import asyncio

import base64

from datetime import datetime as dt

from flask import Flask, Response, flash, render_template, request, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
import eventlet

from GenICam import GenICam, log

#########
#https://github.com/langenhagen/experiments-and-tutorials/blob/master/Python/genicam-harvesters-hello/main.py
#########

#Todo
#SynchronizedCamera


color_red = "\033[91m"
color_green = "\033[92m"
color_yellow = "\033[93m"
color_blue = "\033[94m"
color_magenta = "\033[95m"
color_cyan = "\033[96m"
color_reset = "\033[0m"

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

with open("config.json") as config_file:
            config = json.load(config_file)

@socketio.on('connect')
def handle_connect():
    eventlet.spawn(gen_temp)
    eventlet.spawn(gen_frame)
    eventlet.spawn(gen_time)
    eventlet.spawn(gen_fps)

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
        available_pixelformats=np.intersect1d(cam.supported_PixelFormats,cam.ia.remote_device.node_map.PixelFormat.symbolics),
        whitebalance=cam.ia.remote_device.node_map.BalanceWhiteAuto.value,
        available_whitebalances=cam.ia.remote_device.node_map.BalanceWhiteAuto.symbolics,
        #Following 2 lines are way to slow for some reason
        #cam=str(cam.cam).split("'")[1],
        #available_Cameras=[str(device).split("'")[1] for device in cam.device_list]
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
        if "CameraSelect" in keys and str(data["CameraSelect"]) != "" and str(data["CameraSelect"]) != str(cam.cam).split("'")[1]:
            cam.setup_ia(data["CameraSelect"])
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
        if "WhiteBalance" in keys and str(data["WhiteBalance"]) != "":
            cam.ia.remote_device.node_map.BalanceWhiteAuto.value = data["WhiteBalance"]
        cam.ia.start_acquisition()
    return redirect(url_for("index"))

def gen_time():
    """get time current time to display on website"""
    while True:
        log.info(color_magenta+"gen_time"+color_reset)
        socketio.emit("time",dt.now().strftime('%Y-%m-%d %H:%M:%S'))
        eventlet.sleep(config["refresh_delay_data"])

def gen_fps():
    """get time current time to display on website"""
    while True:
        if "cam" in globals(): 
            log.info(color_cyan+"gen_fps"+color_reset)
            socketio.emit("fps", round(cam.ia.remote_device.node_map.AcquisitionFrameRate.value,1))
        eventlet.sleep(config["refresh_delay_data"])

def gen_temp():
    """get camera temperature displayable on website"""
    while True:
        if "cam" in globals(): 
            log.info(color_green+"gen_temp"+color_reset)
            socketio.emit("temp_feed",f"{round(cam.ia.remote_device.node_map.DeviceTemperature.value,1)} °C" + '\n\n')
        eventlet.sleep(config["refresh_delay_data"])

def gen_frame():
    """get frame displayable on website from camera"""
    while True:
        if "cam" in globals():
            log.info(color_blue+"gen_frame"+color_reset)
            #cam.exposure = rd.randint(cam.exposure-200,cam.exposure+200)
            cam.trigger()
            image_data = cam.grab()

            img_byte_arr = io.BytesIO()
            img = Image.fromarray(image_data)
            img = img.resize((int(cam.scale[0]), int(cam.scale[1])))
            img.save(img_byte_arr, format="JPEG")

            encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

            # Emit the encoded image to the client
            socketio.emit('video_feed', {'image': encoded_image})

        eventlet.sleep(config["refresh_delay_camera"])

if __name__ == '__main__':
    """Run Flask application"""
    #app.run(host="0.0.0.0", port=5050, debug=True, threaded=True)
    socketio.run(app,host="0.0.0.0", port=5050, debug=True)