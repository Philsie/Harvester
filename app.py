import base64
import copy
import io
import json
import os
from datetime import datetime as dt
from time import sleep

import eventlet
import numpy as np
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_socketio import SocketIO, emit
from PIL import Image, ImageDraw, ImageFont

from GenICam import GenICam, log

#########
# https://github.com/langenhagen/experiments-and-tutorials/blob/master/Python/genicam-harvesters-hello/main.py
#########

# Todo
# SynchronizedCamera


color_red = "\033[91m"
color_green = "\033[92m"
color_yellow = "\033[93m"
color_blue = "\033[94m"
color_magenta = "\033[95m"
color_cyan = "\033[96m"
color_reset = "\033[0m"

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

with open("config.json") as config_file:
    config = json.load(config_file)


@socketio.on("cam_config")
def Test(data):
    # log.info(color_red+str(event)+color_reset)
    log.info(color_red + str(data) + color_reset)
    cam.change_ia(data[0])
    if data[1] == "exposure":
        cam.exposure = int(data[2])
    if data[1] == "gain":
        cam.gain = float(data[2])
    if data[1] == "pixelformat":
        cam.ia.stop_acquisition()
        cam.PixelFormat = str(data[2])
        cam.ia.start_acquisition()
    if data[1] == "whitebalance":
        # cam.ia.stop_acquisition()
        cam.ia.remote_device.node_map.BalanceWhiteAuto.value = str(data[2])
        # cam.ia.start_acquisition()
    if data[1] == "width":
        scales[data[0]][0] = int(data[2])
    if data[1] == "height":
        scales[data[0]][1] = int(data[2])

    log.info(color_green + "Done" + color_reset)


@app.before_first_request
def before_first_request():
    """code run before loading Main page"""
    print("Start: before_first_request")
    global cam
    cam = GenICam()

    global scales
    scales = {}

    for id in list(cam.ia_dict.keys()):
        scales[id] = [1280, 1024]

    eventlet.spawn(gen_temp)
    eventlet.spawn(gen_frame)
    eventlet.spawn(gen_time)
    eventlet.spawn(gen_fps)
    log.info("Eventlets spawned")

    print("END: before_first_request")


@app.route("/")
def index():
    """main page displayed"""
    socketio.emit("Displays", list(cam.ia_dict.keys()))
    # account for WhiteBalance only working in BRG8 mode
    wb = "NONE"
    a_wb = []
    if cam.PixelFormat == "BGR8":
        wb = cam.ia.remote_device.node_map.BalanceWhiteAuto.value
        a_wb = cam.ia.remote_device.node_map.BalanceWhiteAuto.symbolics

    return render_template(
        "index.html",
        gain=cam.gain,
        res=list(scales.values())[0],
        #cur_res=cam.scale,
        expo=cam.exposure,
        info=f"<p>{cam.ia.remote_device.node_map.DeviceVendorName.value} - {cam.ia_id}</p>",
        pixelformat=cam.PixelFormat,
        available_pixelformats=np.intersect1d(
            cam.supported_PixelFormats,
            cam.ia.remote_device.node_map.PixelFormat.symbolics,
        ),
        whitebalance=wb,
        available_whitebalances=a_wb,
        camera=cam.ia_id,
        available_Cameras=list(cam.ia_dict.keys()),
    )


@app.route("/download")
def download():
    """Download the image currently displayed"""
    File = "cam_download.png"
    cam.trigger()
    cam.grab(save=True)
    return send_file(File, as_attachment=True)


def gen_time():
    """get time current time to display on website"""
    lastSignOfLife = int(dt.now().timestamp())
    startTime = dt.now()
    while True:
        if config["logEventlet"].upper() == "TRUE":
            log.info(color_magenta + "gen_time" + color_reset)
        socketio.emit("time", dt.now().strftime("%Y-%m-%d %H:%M:%S"))

        if (
            config["logSignOfLife"] != 0
            and int(dt.now().timestamp()) - lastSignOfLife >= config["logSignOfLife"]
        ):
            try:
                log.info(f"App ist still running: {str(dt.now()-startTime)[:-7]}")
            except Exception as e:
                log.warning(color_red + str(e) + color_reset)
            # lastSignOfLife = int(dt.now().timestamp())
            lastSignOfLife += config["logSignOfLife"]

        eventlet.sleep(config["refresh_delay_data"])


def gen_fps():
    """get time current time to display on website"""
    while True:
        if "cam" in globals():
            if config["logEventlet"].upper() == "TRUE":
                log.info(color_cyan + "gen_fps" + color_reset)
            socketio.emit(
                "fps",
                round(cam.ia.remote_device.node_map.AcquisitionFrameRate.value, 1),
            )
        eventlet.sleep(config["refresh_delay_data"])


def gen_temp():
    """get camera temperature displayable on website"""
    while True:
        if "cam" in globals():
            if config["logEventlet"].upper() == "TRUE":
                log.info(color_green + "gen_temp" + color_reset)
            socketio.emit(
                "temp_feed",
                f"{round(cam.ia.remote_device.node_map.DeviceTemperature.value,1)} °C"
                + "\n\n",
            )
        eventlet.sleep(config["refresh_delay_data"])


def gen_frame():
    """get frame displayable on website from camera"""
    while True:
        if "cam" in globals():
            if config["logEventlet"].upper() == "TRUE":
                log.info(color_blue + "gen_frame" + color_reset)
            old_ia = cam.ia
            for id in list(cam.ia_dict.keys()):
                if id != cam.ia_id:
                    cam.change_ia(id)
                try:
                    cam.trigger()
                    image_data = cam.grab()

                    img_byte_arr = io.BytesIO()
                    img = Image.fromarray(image_data)
                    img = img.resize(scales[cam.ia_id])
                    img.save(img_byte_arr, format="JPEG")

                    encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode(
                        "utf-8"
                    )

                    # Emit the encoded image to the client
                    socketio.emit(
                        "video_feed", {"image": encoded_image, "id": cam.ia_id}
                    )

                except Exception as e:
                    log.warning(color_red + "Getting Frame Failed" + color_reset)
                    log.warning(color_yellow + str(e) + color_reset)
                    eventlet.sleep(3)
            cam.ia = old_ia
            eventlet.sleep(config["refresh_delay_camera"])


if __name__ == "__main__":
    """Run Flask application"""
    # mark start of new log
    log.info(".\n" * 25)
    log.info("Start of Log - " + str(dt.now()))

    # run app
    socketio.run(app, host="0.0.0.0", port=5050, debug=True)
