from harvesters.core import Harvester
import numpy as np
from PIL import Image
import os
import io
from datetime import datetime as dt
import json
from threading import Thread

with open('config.json') as config_file:
    config = json.load(config_file)

class GeniCam():
    def __init__(self) -> None:
        self.cam = None
        self.ia = None
        self.Harvester = Harvester()
        for path in config["ctis"]:
            self.Harvester.add_file(path)
            self.Harvester.update()
        if len(self.Harvester.device_info_list)>0:
            self.cam = self.Harvester.device_info_list[0]
            self.ia = self.Harvester.create_image_acquirer(self.Harvester.device_info_list.index(self.cam))

        if self.ia:
            self.width=config["width"]
            self.height=config["height"]
            self.ex=config["exposure"]
            #self.ia.remote_device.node_map.TriggerMode.value = "On"
            #self.ia.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
            #self.ia.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
            
        
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

    class Frame_getter():
        def __init__(self,ia):
            #Thread.__init__(self)
            self.ia = ia
            self.running = True
            self.frametime = 60
            self.Frame = ""
            #self.thread = Thread(target=self.run)
            #self.thread.run()
            #self.run()

        def get_fps(self):
            fps_bytes = str(int(1/self.frametime))+" FPS"
            return fps_bytes

        def get_frame(self):
            self.run()
            return self.Frame
                
        def run(self):
            time = dt.now()
            #self.ia.remote_device.node_map.TriggerSoftware.execute()
            with self.ia.fetch_buffer() as buffer:
                component = buffer.payload.components[0]
                image_data = component.data.reshape(component.height,component.width) 
                img = Image.fromarray(image_data)
                img = img.crop()
                img_byte_arr = io.BytesIO()
                
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                fps = (dt.now().timestamp()-time.timestamp())
                self.frametime = fps
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr + b'\r\n')