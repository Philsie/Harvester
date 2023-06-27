"""
The GenICam module is desigened as a wrapper for the Harvesters ImageAcquirer Object

Improving usability by adding error handling and implementing basic configurations as properties
Also adding simplified functions for taking an image and returning it.
"""
#%% Libraries
import copy
import json
import logging
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import ImageAcquirer
from PIL import Image

#%% Logger and Config
logger = logging.getLogger(__name__)

with open("config.json") as config_file:
    config = json.load(config_file)

    #%% Fallback for color-string
    fallBackColorstring = False
    if config["colorstring"].upper() == "TRUE":
        try:
            from stringcolor import *
        except Exception as e:
            fallBackColorstring = True
            logger.exception(cs(str(e), "Red"), stack_info=True)
    else:
        fallBackColorstring = True

    if fallBackColorstring:

        def cs(text, color):
            return str(text)


#%% GenICam
class GenICam:
    """
    The GenICam class is an extension to the Harvesters ImageAcquirer
    """

    def __init__(self, ImageAcquirer: ImageAcquirer, id: str) -> None:
        """
        Creates the GenICam object

        Args:
            ImageAcquirer (ImageAcquirer):
                provides an interface with the camera device used
            id (str):
                identifier used to adress the camera

        Fields:
            self.id(str):
                stores the id passed during creation
            self.logPrefix(str):
                prefix added during logging to identifiy the GenICam object logging
            self.ImageAcquirer(ImageAcquirer):
                stores the ImageAcquirer passed during creation
            self.nodeMap(node_map):
                shortcut to the ImageAcquirers node_map
            self.supported_PixelFormats(list<str>):
                List of Pixelformats supported, used to limit setting of values
        """
        self.id = id
        self.logPrefix = "\t" + self.id + " -"
        self.ImageAcquirer = ImageAcquirer
        self.nodeMap = self.ImageAcquirer.remote_device.node_map
        self.supported_PixelFormats = ["BGR8", "Mono8"]

        logger.info("")
        logger.info(cs("-" * 100, "Green"))
        logger.info(cs(f"{self.logPrefix}Start of Log - {dt.now()} - {id}", "Green"))
        if fallBackColorstring:
            logger.info(f"{self.logPrefix}Using fallback for colorstring in {__file__}")

        self.baseConfig()

    def baseConfig(self):
        """Handles basic configuration of the GenICam"""
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
        """GenICam property used to set/get ExposureTime"""
        return self.nodeMap.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            try:
                self.nodeMap.ExposureTime.value = e
                logger.info(cs(f"{self.logPrefix} Exposure set to {e}", "Teal"))
            except Exception as ex:
                logger.exception(
                    cs(self.logPrefix + str(ex), "Maroon"), stack_info=True
                )
        else:
            logger.warning(
                cs(
                    f"{self.logPrefix} Invalid input for exposure.setter: {e}, {type(e)}"
                ),
                "Orange",
            )

    @property
    def gain(self):
        """GenICam property used to set/get Gain"""
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
        """GenICam property used to set/get PixelFormat"""
        return self.nodeMap.PixelFormat.value

    @PixelFormat.setter
    def PixelFormat(self, pf):
        try:
            if isinstance(pf, str) and pf in np.intersect1d(
                self.supported_PixelFormats,
                self.nodeMap.PixelFormat.symbolics,
            ):
                self.nodeMap.PixelFormat.value = pf
                logger.info(cs(f"{self.logPrefix} Pixelformat set to {pf}", "Teal"))
            else:
                logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for PixelFormat.setter: {pf}, {type(pf)}",
                        "Orange",
                    )
                )
        except Exception as e:
            logger.exception(cs(self.logPrefix + str(e), "Maroon"), stack_info=True)

    @property
    def Whitebalance(self):
        """GenICam property used to set/get BalanceWhiteAuto"""
        return self.nodeMap.BalanceWhiteAuto.value

    @Whitebalance.setter
    def Whitebalance(self, wb):
        try:
            if isinstance(wb, str) and wb in self.nodeMap.BalanceWhiteAuto.symbolics:
                self.nodeMap.BalanceWhiteAuto.value = wb
                logger.info(cs(f"{self.logPrefix} Whitebalance set to {wb}", "Teal"))
            else:
                logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for Whitebalance.setter: {wb}, {type(wb)}",
                        "Orange",
                    )
                )
        except Exception as e:
            logger.exception(cs(self.logPrefix + str(e), "Maroon"), stack_info=True)

    def trigger(self, log:bool=True):
        """Executes a SoftwareTrigger on the GenICam

        Allowes for grabbing the imagedata at any later point

        Args:
            log (bool, optional):
                Log information during execution.
                    * Defaults to True.
        """
        if log:
            logger.info(cs(f"{self.logPrefix} Triggered", "Aqua"))
        self.nodeMap.TriggerSoftware.execute()

    def grab(self, save:bool=False, log:bool=True):
        """Read the GenICam buffer

        Reads the content of the Buffer and converts it into a usable form.

        Args:
            save (bool, optional):
                saves the image contained inside the buffer into a file.
                    * Defaults to False.
            log (bool, optional):
                Log information during execution.
                    * Defaults to True.

        Returns:
            list<list<int>>: list of Int based PixelValues as an 2D-Array
        """
        if log:
            logger.info(cs(f"{self.logPrefix} Grabed", "Aqua"))
        with self.ImageAcquirer.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            component_data = component.data
            if self.PixelFormat == "BGR8":
                image_data = copy.copy(
                    component_data.reshape(component.height, component.width, 3)[
                        :, :, ::-1
                    ]
                )
            else:
                image_data = copy.copy(
                    component_data.reshape(component.height, component.width)
                )

        if save:
            if log:
                logger.info(cs(f"{self.logPrefix} Saved during grabbing", "Aqua"))
            img = Image.fromarray(image_data)
            img.save(f"./images/{self.id}-Image.png")

        return image_data
