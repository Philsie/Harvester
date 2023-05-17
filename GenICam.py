import io
import json
import logging
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import Harvester
from PIL import Image

log = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s.%(msecs)d [%(levelname)s]: %(filename)s:%(lineno)d: %(message)s",
    datefmt="%T",
    filename="app_WIP.log",
    level=logging.INFO
    ,
)

log.info(".\n"*25)
log.info("Start of Log - "+str(dt.now()))


class GenICam:
    def __init__(self) -> None:
        log.info("Init: GeniCam")

        
        with open("config.json") as config_file:
            self.config = json.load(config_file)
        log.info("Config loaded")

        self.cam = None
        self.ia = None
        self.Harvester = Harvester()
        log.info("Harvester created")

        for path in self.config["ctis"]:
            self.Harvester.add_file(path)
            self.Harvester.update()
        log.info("ctis loaded")

        self.scale = None

        if len(self.Harvester.device_info_list) > 0:
            self.cam = self.Harvester.device_info_list[0]
            self.ia = self.Harvester.create_image_acquirer(
                self.Harvester.device_info_list.index(self.cam)
            )
            self.ia.remote_device.node_map.PixelFormat.value = (
                "BGR8"  # Resets width and size
            )
            print("Pre Checkpoint")
            log.info("DEBUG-CHECKPOINT: 0")
            self.width = self.config["width"]
            log.info("DEBUG-CHECKPOINT: 1")
            self.height = self.config["height"]
            log.info("DEBUG-CHECKPOINT: 2")
            self.exposure = self.config["exposure"]
            log.info("DEBUG-CHECKPOINT: 3")
            self.gain = self.config["gain"]
            log.info("DEBUG-CHECKPOINT: 4")
            self.ia.stop_image_acquisition()
            self.ia.remote_device.node_map.TriggerMode.value = "On"
            log.info("DEBUG-CHECKPOINT: 5")
            self.ia.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
            log.info("DEBUG-CHECKPOINT: 6")
            self.ia.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
            self.ia.start_image_acquisition()
            log.info("DEBUG-CHECKPOINT: 7")
            print("Post Checkpoint")
            log.info("Image-Acquirer created")
        
        #%%
        log.info("Start Logging attributes")
        for name in dir(self.ia.remote_device.node_map):
            if not name[0].isupper():
                info = ""
                value = ""
                try:
                    node = getattr(self.ia.remote_device.node_map, name)
                    if hasattr(node, "value"):
                        value = node.value
                    if hasattr(node, "symbolics"):
                        info += f"    {node.symbolics}"
                    if hasattr(node, "execute"):
                        info += f"     \033[92m*EXECUTABLE*\033[0m"
                except:
                    pass
                log.debug(f"{name}={value}{info}")
        
        log.info("Stop Logging attributes")
        #%%

        log.info("Init Done: GenICam")

    @property
    def width(self):
        return self.ia.remote_device.node_map.Width.value

    @width.setter
    def width(self, w):
        if w > 0 and isinstance(w, int):
            self.ia.remote_device.node_map.Width.value = w
        else:
            log.warning(f"Invalid input for width.setter: {w}, {type(w)}")

    @property
    def height(self):
        return self.ia.remote_device.node_map.Height.value

    @height.setter
    def height(self, h):
        if h > 0 and isinstance(h, int):
            self.ia.remote_device.node_map.Height.value = h
        else:
            log.warning(f"Invalid input for height.setter: {h}, {type(h)}")

    @property
    def exposure(self):
        print("exposure.getter")
        return self.ia.remote_device.node_map.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            self.ia.remote_device.node_map.ExposureTime.value = e
        else:
            log.warning(f"Invalid input for exposure.setter: {e}, {type(e)}")

    @property
    def gain(self):
        print("gain.getter")
        return self.ia.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        if g >= 0 and isinstance(g, float):
            self.ia.remote_device.node_map.Gain.value = g
        else:
            log.warning(f"Invalid input for gain.setter: {g}, {type(g)}")

    def trigger(self):
        log.info("GenICam.trigger")
        self.ia.remote_device.node_map.TriggerSoftware.execute()

    def get_size(self):
        log.info("GenICam.get_size")
        return (self.width, self.height)

    def grab(self):
        #while True:
        log.info("GenICam.grab")
        time = dt.now()
        print("GRAB")
        with self.ia.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            image_data = component.data.reshape(self.height, self.width, 3)[:, :, ::-1]
            img = Image.fromarray(image_data)
            img = img.crop()
            img_byte_arr = io.BytesIO()
            if self.scale != None:
                log.info(self.scale)
                log.info(type(self.scale))
                self.scale = self.scale.split(",")
                img = img.resize((int(self.scale[0][1:]), int(self.scale[1][:-1])))
            img.save(img_byte_arr, format="PNG")
            img.save("debuf.png")
            img_byte_arr = img_byte_arr.getvalue()
            fps = dt.now().timestamp() - time.timestamp()
            self.Frame = (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + img_byte_arr + b"\r\n"
            )
            return self.Frame

    def info(self):
        return str(self.cam)
