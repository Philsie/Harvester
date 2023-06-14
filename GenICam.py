import copy
import io
import json
import logging
import logging.handlers as handlers
import time
from datetime import datetime as dt
from logging.handlers import RotatingFileHandler

import numpy as np
from harvesters.core import Harvester
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(filename)s:%(lineno)d: %(message)s",
    datefmt="%T",
    filename="logs/app.log",
    level=logging.INFO
)

# Create a rotating file handler
log_file = "app.log"
max_file_size = 1024  # 100*1024*1024  # Size in bytes
handler = RotatingFileHandler(log_file, maxBytes=max_file_size)
handler.setLevel(logging.DEBUG)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger
log.addHandler(handler)


class GenICam:
    """universal camera class used to manage multiple types of camera
    """
    def __init__(self) -> None:
        log.info("Init: GeniCam")

        self.supported_PixelFormats = ["BGR8", "Mono8"]

        with open("config.json") as config_file:
            self.config = json.load(config_file)

        if self.config["loglevel"].upper() == "DEBUG":
            log.setLevel = logging.DEBUG
        log.info("Config loaded")

        self.cam = None
        self.ia = None
        self.Harvester = Harvester()
        log.info("Harvester created")

        for path in self.config["ctis"]:
            log.info(path)
            self.Harvester.add_file(path)
        log.info(self.Harvester.files)
        self.Harvester.update()
        log.info(self.Harvester.device_info_list)
        log.info("ctis loaded")

        self.ia_id = None
        self.device_list = (
            self.Harvester.device_info_list
        )  # might be unnecessary needs testing on performance

        # dict of all image acquirer with
        # key: id of camera --> eg: MQ013CG-E2 (38205351)
        # value: ImageAcquirer Object
        self.ia_dict = {}
        for device in self.device_list:
            log.info(str(device))
            try:
                self.ia_dict[str(device).split("'")[1]] = self.Harvester.create_image_acquirer(
                self.device_list.index(device))
            except:
                log.warning(f"could not creare Image-Acquirer for {device}")
                

        # initial setup of all ImageAcquirers
        for id in list(self.ia_dict.keys()):
            self.change_ia(id, setup=True)

        log.info("Init Done: GenICam")

    def change_ia(self, id, setup=False, logChange = True):
        """change the used Image Acquirer to a new one based on provided Id"""
        if str(id) in list(self.ia_dict.keys()) and id != self.ia_id:
            if not str(id) in list(self.ia_dict.keys()) : log.error("++++++++++++++++"*10) 
            self.ia = self.ia_dict[str(id)]
            if setup:
                self.setup_ia()
            if logChange: log.info(f"changed ImageAcquirer from {self.ia_id} to {id}")
            self.ia_id = str(id)

    def setup_ia(self):
        # configure current ImageAcquirer based on config and default values
        self.ia.remote_device.node_map.BalanceWhiteAuto.value = "Off"

        self.PixelFormat = "BGR8"
        #self.width = self.config["width"]
        #self.height = self.config["height"]
        self.exposure = self.config["exposure"]
        self.gain = self.config["gain"]

        self.ia.stop_image_acquisition()
        self.ia.remote_device.node_map.TriggerMode.value = "On"
        self.ia.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
        self.ia.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
        self.ia.start_image_acquisition()

        self.trigger()
        self.grab()

    #%% GenICam properties
    @property
    def width(self):
        """set/get width of image taken"""
        return self.ia.remote_device.node_map.Width.value

    @width.setter
    def width(self, w):
        if w > 0 and isinstance(w, int):
            self.ia.remote_device.node_map.Width.value = w
        else:
            log.warning(f"Invalid input for width.setter: {w}, {type(w)}")

    @property
    def height(self):
        """set/get height of image taken"""
        return self.ia.remote_device.node_map.Height.value

    @height.setter
    def height(self, h):
        if h > 0 and isinstance(h, int):
            self.ia.remote_device.node_map.Height.value = h
        else:
            log.warning(f"Invalid input for height.setter: {h}, {type(h)}")

    @property
    def exposure(self):
        """set/get exposure of image taken"""
        return self.ia.remote_device.node_map.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            try:
                self.ia.remote_device.node_map.ExposureTime.value = e
            except Exception as e:
                log.warning(str(e))
        else:
            log.warning(f"Invalid input for exposure.setter: {e}, {type(e)}")

    @property
    def gain(self):
        """set/get gain of image taken"""
        return self.ia.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        log.warning("Gain: " + str(g) + " " + str(type(g)))
        if g >= 0 and type(g) == float:
            self.ia.remote_device.node_map.Gain.value = g
        else:
            log.warning(f"Invalid input for gain.setter: {g}, {type(g)}")

    @property
    def PixelFormat(self):
        """set/get PixelFormat of image taken"""
        return self.ia.remote_device.node_map.PixelFormat.value

    @PixelFormat.setter
    def PixelFormat(self, pf):
        try:
            if isinstance(pf, str) and pf in np.intersect1d(
                self.supported_PixelFormats,
                self.ia.remote_device.node_map.PixelFormat.symbolics,
            ):
                self.ia.remote_device.node_map.PixelFormat.value = pf
            else:
                log.warning(f"Invalid input for PixelFormat.setter: {pf}, {type(pf)}")
        except Exception as e:
            log.error(str(e))

    #%% GenICam functions

    def trigger(self):
        """Make the camera take a picture"""
        log.debug("GenICam.trigger")
        self.ia.remote_device.node_map.TriggerSoftware.execute()

    def grab(self, save=False):
        """Return the image taken as a list of pixel Values"""
        log.debug("GenICam.grab")
        time = dt.now()
        with self.ia.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            component_data = component.data
            if self.PixelFormat == "BGR8":
                image_data = copy.copy(component_data.reshape(self.height, self.width, 3)[
                    :, :, ::-1
                ])
            else:
                image_data = copy.copy(component_data.reshape(self.height, self.width))
            
        if save:
            # if specified save image to file
            img = Image.fromarray(image_data)
            img.save("cam_download.png")

        return image_data
