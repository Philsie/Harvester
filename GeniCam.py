import io
import json
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import Harvester
from PIL import Image


class GenICam:
    def __init__(self) -> None:
        print("Init: GeniCam")

        with open("config.json") as config_file:
            self.config = json.load(config_file)

        print(self.config)

        self.cam = None
        self.ia = None
        self.Harvester = Harvester()
        for path in self.config["ctis"]:
            self.Harvester.add_file(path)
            self.Harvester.update()
        if len(self.Harvester.device_info_list)>0:
            self.cam = self.Harvester.device_info_list[0]
            self.ia = self.Harvester.create_image_acquirer(self.Harvester.device_info_list.index(self.cam))
        print("Tree")
        if True:
            print(self.ia.remote_device.node_map.PixelFormat.symbolics)
            self.ia.remote_device.node_map.PixelFormat.value = (
                "BGR8"  # Resets width and size
            )
            print("!!!!!")
            self.width = self.config["width"]
            self.height = self.config["height"]
            self.exposure = self.config["exposure"]
            self.gain = self.config["gain"]
            # self.ia.remote_device.node_map.TriggerMode.value = "On"
            # self.ia.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
            # self.ia.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
        print("////", self.width)
        print("Init Done: GenICam")
        
    @property
    def width(self):
        return self.ia.remote_device.node_map.Width.value
    
    @width.setter
    def width(self,w):
        if w > 0 and isinstance(w, int):
            self.ia.remote_device.node_map.Width.value = w
        else: print(f"Invalid input for width.setter: {w}, {type(w)}")

    @property
    def height(self):
        return self.ia.remote_device.node_map.Height.value
    
    @height.setter
    def height(self,h):
        if h > 0 and isinstance(h, int):
            self.ia.remote_device.node_map.Height.value = h
        else: print(f"Invalid input for width.setter: {h}, {type(h)}")

    @property
    def exposure(self):
        return self.ia.remote_device.node_map.ExposureTime.value
    
    @exposure.setter
    def exposure(self,e):
        if e > 0 and isinstance(e, int):
            self.ia.remote_device.node_map.ExposureTime.value = e
        else: print(f"Invalid input for width.setter: {e}, {type(e)}")

    @property
    def gain(self):
        return self.ia.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        if g >= 0 and isinstance(g, float):
            self.ia.remote_device.node_map.Gain.value = g
        else:
            print(f"Invalid input for width.setter: {g}, {type(g)}")

    def Trigger(self):
        print("Trigger")
        self.ia.remote_device.node_map.TriggerSoftware.execute()

    def getSize(self):
        print(self.width, self.height)
        return (self.width, self.height)

    def Grab(self):
        print("Grab")
        time = dt.now()
        with self.ia.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            print(self.getSize())
            image_data = component.data.reshape(self.height, self.width, 3)[:, :, ::-1]
            img = Image.fromarray(image_data)
            img = img.crop()
            img_byte_arr = io.BytesIO()

            img.save(img_byte_arr, format="JPEG")
            img_byte_arr = img_byte_arr.getvalue()
            fps = dt.now().timestamp() - time.timestamp()
            self.Frame = (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + img_byte_arr + b"\r\n"
            )
            return self.Frame
