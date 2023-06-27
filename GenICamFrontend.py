import base64
import io
import json
import logging
from datetime import datetime as dt
from time import sleep

import eventlet
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO
from PIL import Image, ImageDraw, ImageFont
from stringcolor import *

import GenICamHub

runStream = True

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

logger = logging.getLogger(__name__)

with open("config.json") as config_file:
    config = json.load(config_file)

fallBackColorstring = False
if config["colorstring"].upper() == "TRUE":
    try: 
        from stringcolor import *
    except Exception as e:
        fallBackColorstring = True
        logger.exception(cs(str(e),"Red"),stack_info=True)
else: fallBackColorstring = True

if fallBackColorstring:
    def cs(text,color):
        return str(text)




@socketio.on("cam_config")
def Test(data):
    runStream = False
    # sleep(config["refresh_delay"])
    try:
        logger.info(cs(str(data), "Yellow"))
        GCH.change_Device(data[0])
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
        logger.info(cs(f"Changes to {GCH.activeDeviceId} applied","Teal"))
    except Exception as e:
        logger.exception(cs(str(e),"Red"),stack_info=True)


@app.before_first_request
def before_first_request():
    """code run before loading Main page"""
    global GCH
    GCH = GenICamHub.GenICamHub()
    logger.info("")
    logger.info(cs("-" * 100, "Green"))
    logger.info(cs(f"Start of Log - {dt.now()} - Frontend", "Green"))
    if fallBackColorstring:
        logger.info(f"Using fallback for colorstring in {__file__}")

    logger.info(cs("Start: before_first_request", "Olive"))

    global scales
    scales = {}

    for id in list(GCH.deviceDict.keys()):
        scales[id] = [1280, 1024]

    eventlet.spawn(genCamOutputs)

    logger.info(cs("Eventlets spawned", "Olive"))

    logger.info(cs("END: before_first_request", "Olive"))


@app.route("/")
def index():
    """main page displayed"""
    socketio.emit("Displays", list(GCH.deviceDict.keys()))
    # account for WhiteBalance only working in BRG8 mode
    wb = "NONE"
    a_wb = []
    if GCH.activeDevice.PixelFormat == "BGR8":
        wb = GCH.activeDevice.Whitebalance
        a_wb = GCH.activeDevice.nodeMap.BalanceWhiteAuto.symbolics

    return render_template(
        "index.html",
        gain=GCH.activeDevice.gain,
        res=list(scales.values())[0],
        # cur_res=GCH.activeDevice.scale,
        expo=int(GCH.activeDevice.exposure),
        info=f"<p>{GCH.activeDevice.nodeMap.DeviceVendorName.value} - {GCH.activeDeviceId}</p>",
        pixelformat=GCH.activeDevice.PixelFormat,
        available_pixelformats=np.intersect1d(
            GCH.activeDevice.supported_PixelFormats,
            GCH.activeDevice.nodeMap.PixelFormat.symbolics,
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
            
            logger.info(cs(f"GenICamFrontend is running for {runningTime}","Thistle"))
            time = dt.now()
        if runStream is True:
            if logEventlet:
                logger.info("")
                logger.info(cs("Generating active device Output", "Aqua"))

            for id in list(GCH.deviceDict.keys()):
                if id != GCH.activeDeviceId:
                    GCH.change_Device(id,log = logEventlet)
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
                            "temp": f"{round(GCH.activeDevice.nodeMap.DeviceTemperature.value,1)} °C",
                            "id": GCH.activeDeviceId,
                        },
                    )

                    socketio.emit(
                        "fps_feed",
                        {
                            "fps": round(
                                GCH.activeDevice.nodeMap.AcquisitionFrameRate.value,
                                1,
                            ),
                            "id": GCH.activeDeviceId,
                        },
                    )

                    if logEventlet:
                        logger.info(cs(f"Data for Device {id} send","Teal"))
                except Exception as e:
                    logger.exception(str(e),stack_info=True)
                    #logger.error(cs(str(e), "Maroon"))

                    eventlet.sleep(0.1)

            eventlet.sleep(config["refresh_delay"])


if __name__ == "__main__":
    """Run Flask application"""

    # run app
    socketio.run(app, host="0.0.0.0", port=int(config["port"]), debug=True)
