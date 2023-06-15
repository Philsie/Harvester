from harvesters.core import Harvester
import logging
import json
import os
from datetime import datetime as dt
import numpy as np
import copy
from PIL import Image
class GenICam:
    '''
    
    '''
    def __init__(self, id:str = None, logger:logging.Logger = None, PathToConfig:str = None, filter:str = None) -> None:
        '''
        
        '''
        #temp for testing
        #id = "MQ013CG-E2 (38205351)"
        #PathToConfig = "config.json"

        #end of enmp for testing

        self.supported_PixelFormats = ["BGR8", "Mono8"]

        if logger is None:
            self.logger = logging.getLogger(__name__)
            logging.basicConfig(
                format="%(asctime)s [%(levelname)s]: %(filename)s:"+ id +": "+"ln "+ "%(lineno)d: %(message)s",
                datefmt="%T",
                filename="".join(f"logs/GenICam-{id}.log".split(" ")),
                level=logging.INFO
            )

            if __name__ == "__main__":
                self.logger.info(".\n" * 25)
            

        else:   
            self.logger = logger
            

        self.logger.info(f"Start of Log - {dt.now()} - {id}")

        self.config = None
        if PathToConfig is not None:
            with open(PathToConfig) as config_file:
                self.config = json.load(config_file)

        self.Harvester = Harvester()
        for root, dir, files in os.walk("./cti"):
            for file in files:
                if file.split(".")[-1] in ["cti","sym"]:
                    self.logger.info(file)
                    if filter is not None:
                        if filter in file:
                            self.Harvester.add_file(root+"/"+file)
                    else:
                        self.Harvester.add_file(root+"/"+file)
                else:
                    pass
        self.logger.info(f"Files added: {self.Harvester.files}")

        self.Harvester.update()
        
        self.ImageAcquirer = None

        if self.Harvester.device_info_list != []:

            for device in self.Harvester.device_info_list:
                if id in str(device):
                    self.ImageAcquirer = self.Harvester.create_image_acquirer(self.Harvester.device_info_list.index(device))
                    self.logger.info(f"ImageAcquirer for {id} was created successfully")
            if self.ImageAcquirer is None:
                self.logger.error(f"ImageAcquirer for {id} could not be created created")
                self.logger.error(f"Devices found: \n {self.Harvester.device_info_list}")
        else:
            self.logger.error(f"No Cameras found")

        self.baseConfig()
    pass

    def baseConfig(self):
        # configure current ImageAcquirer based on config and default values
        self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value = "Off"

        if self.config is not None:
            self.exposure = self.config["exposure"]
            self.gain = self.config["gain"]
        self.Whitebalance = "Off"
        self.PixelFormat = "BGR8"

        self.ImageAcquirer.stop_image_acquisition()
        self.ImageAcquirer.remote_device.node_map.TriggerMode.value = "On"
        self.ImageAcquirer.remote_device.node_map.TriggerSource.value = "Software"  # with IDS, "Software" is the default
        self.ImageAcquirer.remote_device.node_map.TriggerActivation.value = "RisingEdge"  # with the IDS cam, "RisingEdge" is the default and only option
        self.ImageAcquirer.start_image_acquisition()

    @property
    def exposure(self):
        """set/get exposure of image taken"""
        return self.ia.remote_device.node_map.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            try:
                self.ImageAcquirer.remote_device.node_map.ExposureTime.value = e
            except Exception as e:
                self.logger.warning(str(e))
        else:
            self.logger.warning(f"Invalid input for exposure.setter: {e}, {type(e)}")

    @property
    def gain(self):
        """set/get gain of image taken"""
        return self.ImageAcquirer.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        try:
            if g >= 0.0 and type(g) == float:
                self.ImageAcquirer.remote_device.node_map.Gain.value = g
            else:
                self.logger.warning(f"Invalid input for gain.setter: {g}, {type(g)}")
        except Exception as e:
            self.logger.error(str(e))

    @property
    def PixelFormat(self):
        """set/get PixelFormat of image taken"""
        return self.ImageAcquirer.remote_device.node_map.PixelFormat.value

    @PixelFormat.setter
    def PixelFormat(self, pf):
        try:
            if isinstance(pf, str) and pf in np.intersect1d(
                self.supported_PixelFormats,
                self.ImageAcquirer.remote_device.node_map.PixelFormat.symbolics,
            ):
                self.ImageAcquirer.remote_device.node_map.PixelFormat.value = pf
            else:
                self.logger.warning(f"Invalid input for PixelFormat.setter: {pf}, {type(pf)}")
        except Exception as e:
            self.logger.error(str(e))

    @property
    def Whitebalance(self):
        """set/get Whitebalance of image taken"""
        return self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value

    @Whitebalance.setter
    def Whitebalance(self, wb):
        try:
            if isinstance(wb, str) and wb in self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.symbolics:
                self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value = wb
            else:
                self.logger.warning(f"Invalid input for Whitebalance.setter: {wb}, {type(wb)}")
        except Exception as e:
            self.logger.error(str(e))
            self.logger.error(self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.symbolics)

    def trigger(self):
        """Make the camera take a picture"""
        GC.logger.info("t")
        self.ImageAcquirer.remote_device.node_map.TriggerSoftware.execute()

    def grab(self, save=False):
        """Return the image taken as a list of pixel Values"""
        GC.logger.info("g")
        #self.ImageAcquirer.start_image_acquisition()
        with self.ImageAcquirer.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            component_data = component.data
            if self.PixelFormat == "BGR8":
                image_data = copy.copy(component_data.reshape(component.height, component.width, 3)[
                    :, :, ::-1
                ])
            else:
                image_data = copy.copy(component_data.reshape(component.height, component.width))
            
        if save:
            # if specified save image to file
            img = Image.fromarray(image_data)
            img.save("cam_download.png")

        return image_data


if __name__ == "__main__":
    GC = GenICam(id = "MQ013CG-E2 (38205351)")
    GC.trigger()
    GC.logger.info(GC.grab(save=True))

