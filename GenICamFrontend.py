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
from stringcolor import *

import GenICamHub

runStream = True

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

with open("config.json") as config_file:
    config = json.load(config_file)


@socketio.on("cam_config")
def Test(data):
    runStream = False
    # sleep(config["refresh_delay"])
    GCH.logger.info(cs(str(data), "Yellow"))
    GCH.changeDevice(data[0])
    if data[1] == "exposure":
        GCH.activeDevice.exposure = int(data[2])
    if data[1] == "gain":
        GCH.activeDevice.gain = float(data[2])
    if data[1] == "pixelformat":
        GCH.activeDevice.ImageAcquirer.stop_acquisition()  # might remove
        GCH.activeDevice.PixelFormat = str(data[2])
        GCH.activeDevice.ImageAcquirer.start_acquisition()  # might remove
    if data[1] == "whitebalance":
        GCH.activeDevice.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value = (
            str(data[2])
        )
    if data[1] == "width":
        scales[data[0]][0] = int(data[2])
    if data[1] == "height":
        scales[data[0]][1] = int(data[2])
    runStream = True
    GCH.logger.info(cs(f"Changes to {GCH.activeDeviceId} applied"))


@app.before_first_request
def before_first_request():
    """code run before loading Main page"""
    global GCH
    GCH = GenICamHub.GenICamHub()
    GCH.logger.info("")
    GCH.logger.info(cs("-" * 100, "Green"))
    GCH.logger.info(cs(f"Start of Log - {dt.now()} - Frontend", "Green"))

    GCH.logger.info(cs("Start: before_first_request", "Olive"))

    global scales
    scales = {}

    for id in list(GCH.deviceDict.keys()):
        scales[id] = [1280, 1024]

    eventlet.spawn(genCamOutputs)

    GCH.logger.info(cs("Eventlets spawned", "Olive"))

    GCH.logger.info(cs("END: before_first_request", "Olive"))


@app.route("/")
def index():
    """main page displayed"""
    socketio.emit("Displays", list(GCH.deviceDict.keys()))
    # account for WhiteBalance only working in BRG8 mode
    wb = "NONE"
    a_wb = []
    if GCH.activeDevice.PixelFormat == "BGR8":
        wb = GCH.activeDevice.Whitebalance
        a_wb = (
            GCH.activeDevice.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.symbolics
        )

    return render_template(
        "index.html",
        gain=GCH.activeDevice.gain,
        res=list(scales.values())[0],
        # cur_res=GCH.activeDevice.scale,
        expo=int(GCH.activeDevice.exposure),
        info=f"<p>{GCH.activeDevice.ImageAcquirer.remote_device.node_map.DeviceVendorName.value} - {GCH.activeDeviceId}</p>",
        pixelformat=GCH.activeDevice.PixelFormat,
        available_pixelformats=np.intersect1d(
            GCH.activeDevice.supported_PixelFormats,
            GCH.activeDevice.ImageAcquirer.remote_device.node_map.PixelFormat.symbolics,
        ),
        whitebalance=wb,
        available_whitebalances=a_wb,
        camera=GCH.activeDeviceId,
        available_Cameras=list(GCH.deviceDict.keys()),
    )


def genCamOutputs():
    """get frame displayable on website from camera"""
    firstRun = dt.now()
    time = dt.now()

    logEventlet = True if config["logEventlet"].upper() == "TRUE" else False

    while True:
        if config["logSignOfLife"] != 0 and (dt.now() - time).seconds > config["logSignOfLife"]:
            runningTime = dt.now() - firstRun
            
            GCH.logger.info(cs(f"GenICamFrontend is running for {runningTime}","Thistle"))
            time = dt.now()
        if runStream is True:
            if logEventlet:
                GCH.logger.info("")
                GCH.logger.info(cs("Generating active device Output", "Aqua"))

            for id in list(GCH.deviceDict.keys()):
                if id != GCH.activeDeviceId:
                    GCH.changeDevice(id,log = logEventlet)
                try:
                    GCH.activeDevice.trigger(log=logEventlet)
                    image_data = GCH.activeDevice.grab(log=logEventlet)
                    img_byte_arr = io.BytesIO()
                    img = Image.fromarray(image_data)
                    img = img.resize(scales[GCH.activeDeviceId])
                    img.save(img_byte_arr, format="JPEG")

                    encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode(
                        "utf-8"
                    )

                    # Emit the encoded image to the client
                    socketio.emit(
                        "video_feed", {"image": encoded_image, "id": GCH.activeDeviceId}
                    )

                    socketio.emit(
                        "temp_feed",
                        {
                            "temp": f"{round(GCH.activeDevice.ImageAcquirer.remote_device.node_map.DeviceTemperature.value,1)} °C",
                            "id": GCH.activeDeviceId,
                        },
                    )

                    socketio.emit(
                        "fps_feed",
                        {
                            "fps": round(
                                GCH.activeDevice.ImageAcquirer.remote_device.node_map.AcquisitionFrameRate.value,
                                1,
                            ),
                            "id": GCH.activeDeviceId,
                        },
                    )

                    if logEventlet:
                        GCH.logger.info(cs(f"Data for Device {id} send","Teal"))
                except Exception as e:
                    GCH.logger.error(cs(str(e), "Maroon"))

                    eventlet.sleep(0.1)

            eventlet.sleep(config["refresh_delay"])


if __name__ == "__main__":
    """Run Flask application"""

    # run app
    socketio.run(app, host="0.0.0.0", port=int(config["port"]), debug=True)
