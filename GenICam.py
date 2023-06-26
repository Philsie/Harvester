import copy
import json
import logging
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import ImageAcquirer
from PIL import Image

logger = logging.getLogger(__name__)

with open("config.json") as config_file:
    config = json.load(config_file)

fallBackColorstring = False
if config["colorstring"].upper() == True:
    try: 
        from stringcolor import *
    except Exception as e:
        fallBackColorstring = True
        logger.exception(cs(str(e),"Red"),stack_info=True)
else: fallBackColorstring = True

if fallBackColorstring:
    logger.info(f"Using fallback for colorstring in {__file__}")
    def cs(text,color):
        return str(text)

class GenICam:
    """ """

    def __init__(
        self, ImageAcquirer: ImageAcquirer, id: str
    ) -> None:
        """ """
        self.id = id
        self.logPrefix = "\t" + self.id + " -"

        self.ImageAcquirer = ImageAcquirer

        self.nodeMap = self.ImageAcquirer.remote_device.node_map

        self.supported_PixelFormats = ["BGR8", "Mono8"]

        
        logger.info("")
        logger.info(cs("-" * 100, "Green"))
        logger.info(
            cs(f"{self.logPrefix}Start of Log - {dt.now()} - {id}", "Green")
        )

        self.baseConfig()

    def baseConfig(self):
        # configure ImageAcquirer based to default values
        self.nodeMap.BalanceWhiteAuto.value = "Off"

        self.exposure = 1500
        self.gain = 0.0
        self.Whitebalance = "Off"
        self.PixelFormat = "BGR8"

        self.ImageAcquirer.stop_image_acquisition()
        self.nodeMap.TriggerMode.value = "On"
        self.nodeMap.TriggerSource.value = "Software"
        self.nodeMap.TriggerActivation.value = "RisingEdge"
        self.ImageAcquirer.start_image_acquisition()

    @property
    def exposure(self):
        """set/get exposure of image taken"""
        return self.nodeMap.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            try:
                self.nodeMap.ExposureTime.value = e
                logger.info(cs(f"{self.logPrefix} Exposure set to {e}", "Teal"))
            except Exception as ex:
                logger.exception(cs(self.logPrefix + str(ex), "Maroon"),stack_info=True)
        else:
            logger.warning(
                cs(
                    f"{self.logPrefix} Invalid input for exposure.setter: {e}, {type(e)}"
                ),
                "Orange",
            )

    @property
    def gain(self):
        """set/get gain of image taken"""
        return self.nodeMap.Gain.value

    @gain.setter
    def gain(self, g):
        if g >= 0.0 and type(g) == float:
            self.nodeMap.Gain.value = g
            logger.info(cs(f"{self.logPrefix} Gain set to {g}", "Teal"))
        else:
            logger.warning(
                cs(
                    f"{self.logPrefix} Invalid input for gain.setter: {g}, {type(g)}",
                    "Orange",
                )
            )

    @property
    def PixelFormat(self):
        """set/get PixelFormat of image taken"""
        return self.nodeMap.PixelFormat.value

    @PixelFormat.setter
    def PixelFormat(self, pf):
        try:
            if isinstance(pf, str) and pf in np.intersect1d(
                self.supported_PixelFormats,
                self.nodeMap.PixelFormat.symbolics,
            ):
                self.nodeMap.PixelFormat.value = pf
                logger.info(
                    cs(f"{self.logPrefix} Pixelformat set to {pf}", "Teal")
                )
            else:
                logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for PixelFormat.setter: {pf}, {type(pf)}",
                        "Orange",
                    )
                )
        except Exception as e:
            logger.exception(cs(self.logPrefix + str(e), "Maroon"),stack_info=True)

    @property
    def Whitebalance(self):
        """set/get Whitebalance of image taken"""
        return self.nodeMap.BalanceWhiteAuto.value

    @Whitebalance.setter
    def Whitebalance(self, wb):
        try:
            if isinstance(wb, str) and wb in self.nodeMap.BalanceWhiteAuto.symbolics:
                self.nodeMap.BalanceWhiteAuto.value = wb
                logger.info(
                    cs(f"{self.logPrefix} Whitebalance set to {wb}", "Teal")
                )
            else:
                logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for Whitebalance.setter: {wb}, {type(wb)}",
                        "Orange",
                    )
                )
        except Exception as e:
            logger.exception(cs(self.logPrefix + str(e), "Maroon"),stack_info=True)

    def trigger(self, log=True):
        """Make the camera take a picture"""
        if log:
            logger.info(cs(f"{self.logPrefix} Triggered", "Aqua"))
        self.nodeMap.TriggerSoftware.execute()

    def grab(self, save=False, log=True):
        """Return the image taken as a list of pixel Values"""
        if log:
            logger.info(cs(f"{self.logPrefix} Grabed", "Aqua"))
        # self.ImageAcquirer.start_image_acquisition()
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
            if log:
                logger.info(cs(f"{self.logPrefix} Saved during grabbing", "Aqua"))
            img = Image.fromarray(image_data)
            img.save(f"./images/{self.id}-Image.png")

        return image_data

