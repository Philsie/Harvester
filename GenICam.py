import io
import json
import logging
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import Harvester
from PIL import Image, ImageDraw, ImageFont

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
    """universal camera class used to manage multiple types of camera
    """
    def __init__(self) -> None:
        log.info("Init: GeniCam")

        self.supported_PixelFormats = ["BGR8", "Mono8"]

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
            log.info(self.Harvester.device_info_list)
            self.PixelFormat = "BGR8"
            log.info(self.ia.remote_device.node_map.PixelFormat.symbolics)
            print("Pre Checkpoint")
            self.width = self.config["width"]
            self.height = self.config["height"]
            self.exposure = self.config["exposure"]
            self.gain = self.config["gain"]

            if (
                self.ia.remote_device.node_map.DeviceModelName.value
                not in self.config["skip_autoWhiteBalance_models"]
            ):
                try:
                    self.ia.remote_device.node_map.BalanceWhiteAuto.value = "Off"
                except:
                    log.warning("setting AutoBalanceWhite failed")

            self.ia.stop_image_acquisition()
            self.ia.remote_device.node_map.TriggerMode.value = "On"
            self.ia.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
            self.ia.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
            self.ia.start_image_acquisition()
            self.trigger()
            self.grab()
            print("Post Checkpoint")
            log.info("Image-Acquirer created")
        

        #%%start of node listing
        log.debug("Start Logging attributes")
        for name in dir(self.ia.remote_device.node_map):
            if not name[0].isupper() or True:
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
        
        log.debug("Stop Logging attributes")
        #%%end of node listing
        log.info("Init Done: GenICam")

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
            self.ia.remote_device.node_map.ExposureTime.value = e
        else:
            log.warning(f"Invalid input for exposure.setter: {e}, {type(e)}")

    @property
    def gain(self):
        """set/get gain of image taken"""
        return self.ia.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        if g >= 0 and isinstance(g, float):
            self.ia.remote_device.node_map.Gain.value = g
        else:
            log.warning(f"Invalid input for gain.setter: {g}, {type(g)}")

    @property
    def PixelFormat(self):
        """set/get PixelFormat of image taken"""
        return self.ia.remote_device.node_map.PixelFormat.value

    @PixelFormat.setter
    def PixelFormat(self, pf):
        if isinstance(pf, str) and pf in np.intersect1d(
            self.supported_PixelFormats,
            self.ia.remote_device.node_map.PixelFormat.symbolics,
        ):
            self.ia.remote_device.node_map.PixelFormat.value = pf
        else:
            log.warning(f"Invalid input for PixelFormat.setter: {pf}, {type(pf)}")

    #%% GenICam functions

    def trigger(self):
        """Make the camera take a picture"""
        log.info("GenICam.trigger")
        self.ia.remote_device.node_map.TriggerSoftware.execute()

    def grab(self,Frame = False, save = False):
        """Return the image taken as a list
        Frame=True ==> returns a Frame for displaying on a website
        """
        log.info("GenICam.grab")
        time = dt.now()
        with self.ia.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            component_data = component.data
            if self.scale is None:
                self.scale = [component.width,component.height]
            if self.PixelFormat == "BGR8":
                image_data = component_data.reshape(self.height, self.width, 3)[
                    :, :, ::-1
                ]
            else:
                image_data = component_data.reshape(self.height, self.width)
            
            #log.info(image_data)
            if save:
                img = Image.fromarray(image_data)
                img.save("cam_download.png")

            if Frame:
                img = Image.fromarray(image_data)
    
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype('Arial.ttf', size=36)
                draw.text((10, 10), dt.now().strftime('%Y-%m-%d %H:%M:%S'), font=font, fill=255)
                draw.text((10, 50), f"{round(self.ia.remote_device.node_map.DeviceTemperature.value,1)} °C", font=font, fill=255)
                draw.text((10, 90), f"{round(self.ia.remote_device.node_map.AcquisitionFrameRate.value,1)} FPS", font=font, fill=255)
                
                if self.PixelFormat=="BGR8":
                    shape = [self.scale[0]-40,0,self.scale[0],40]
                    draw.rectangle(shape,fill="red")
                    shape = [self.scale[0]-80,0,self.scale[0]-40,40]
                    draw.rectangle(shape,fill="green")
                    shape = [self.scale[0]-120,0,self.scale[0]-80,40]
                    draw.rectangle(shape,fill="blue")

                img_byte_arr = io.BytesIO()
                img = img.resize((int(self.scale[0]), int(self.scale[1])))
                img.save(img_byte_arr, format="PNG")
                img_byte_arr = img_byte_arr.getvalue()
                return (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + img_byte_arr + b"\r\n"
                )
            return image_data

    def info(self):
        """Return camera information"""
        return str(self.cam)