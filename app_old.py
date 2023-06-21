import base64
import io
import json
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

from GenICamOld import GenICamOld, log

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

runStream = True

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

with open("config.json") as config_file:
    config = json.load(config_file)


@socketio.on("cam_config")
def Test(data):
    runStream = False
    # sleep(config["refresh_delay"])
    log.info(" ")
    log.info("New Config")
    log.info(color_yellow + str(data) + color_reset)
    cam.change_ia(data[0], logChange=False)
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
    runStream = True
    log.info(color_green + "Done" + color_reset)


@app.before_first_request
def before_first_request():
    """code run before loading Main page"""
    print("Start: before_first_request")
    global cam
    cam = GenICamOld()

    global scales
    scales = {}

    for id in list(cam.ia_dict.keys()):
        scales[id] = [1280, 1024]

    eventlet.spawn(genCamOutputs)

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
        # cur_res=cam.scale,
        expo=int(cam.exposure),
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


def genCamOutputs():
    """get frame displayable on website from camera"""
    while True:
        if "cam" in globals() and runStream is True:
            if config["logEventlet"].upper() == "TRUE":
                log.info(color_blue + "gen_frame" + color_reset)
            # old_ia = cam.ia
            for id in list(cam.ia_dict.keys()):
                if id != cam.ia_id:
                    cam.change_ia(id, logChange=False)
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
                    socketio.emit(
                        "temp_feed",
                        {
                            "temp": f"{round(cam.ia.remote_device.node_map.DeviceTemperature.value,1)} °C",
                            "id": cam.ia_id,
                        },
                    )
                    socketio.emit(
                        "fps_feed",
                        {
                            "fps": round(
                                cam.ia.remote_device.node_map.AcquisitionFrameRate.value,
                                1,
                            ),
                            "id": cam.ia_id,
                        },
                    )
                except Exception as e:
                    log.warning("")
                    log.warning(color_red + "Start of Error" + color_reset)
                    log.warning(color_red + "Getting Frame Failed" + color_reset)
                    log.warning(color_yellow + str(e) + color_reset)
                    log.warning(color_yellow + cam.ia_id + color_reset)

                    eventlet.sleep(0.1)
            eventlet.sleep(config["refresh_delay"])


if __name__ == "__main__":
    """Run Flask application"""
    # mark start of new log
    log.info(".\n" * 25)
    log.info("Start of Log - " + str(dt.now()))

    # run app
    socketio.run(app, host="0.0.0.0", port=5050, debug=True)
