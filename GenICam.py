import copy
import json
import logging
import os
from datetime import datetime as dt

import numpy as np
from harvesters.core import ImageAcquirer
from PIL import Image
from stringcolor import *


class GenICam:
    """ """

    def __init__(
        self, logger: logging.Logger, ImageAcquirer: ImageAcquirer, id: str
    ) -> None:
        """ """
        self.id = id
        self.logPrefix = "\t" + self.id + " -"

        self.ImageAcquirer = ImageAcquirer

        self.supported_PixelFormats = ["BGR8", "Mono8"]

        self.logger = logger

        self.logger.info("")
        self.logger.info(cs("-" * 100, "Green"))
        self.logger.info(
            cs(f"{self.logPrefix}Start of Log - {dt.now()} - {id}", "Green")
        )

        self.baseConfig()

    def baseConfig(self):
        # configure ImageAcquirer based to default values
        self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value = "Off"

        self.exposure = 1500
        self.gain = 0.0
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
        return self.ImageAcquirer.remote_device.node_map.ExposureTime.value

    @exposure.setter
    def exposure(self, e):
        if e > 0 and isinstance(e, int):
            try:
                self.ImageAcquirer.remote_device.node_map.ExposureTime.value = e
                self.logger.info(cs(f"{self.logPrefix} Exposure set to {e}", "Teal"))
            except Exception as ex:
                self.logger.error(cs(self.logPrefix + str(ex), "Maroon"))
        else:
            self.logger.warning(
                cs(
                    f"{self.logPrefix} Invalid input for exposure.setter: {e}, {type(e)}"
                ),
                "Orange",
            )

    @property
    def gain(self):
        """set/get gain of image taken"""
        return self.ImageAcquirer.remote_device.node_map.Gain.value

    @gain.setter
    def gain(self, g):
        if g >= 0.0 and type(g) == float:
            self.ImageAcquirer.remote_device.node_map.Gain.value = g
            self.logger.info(cs(f"{self.logPrefix} Gain set to {g}", "Teal"))
        else:
            self.logger.warning(
                cs(
                    f"{self.logPrefix} Invalid input for gain.setter: {g}, {type(g)}",
                    "Orange",
                )
            )

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
                self.logger.info(
                    cs(f"{self.logPrefix} Pixelformat set to {pf}", "Teal")
                )
            else:
                self.logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for PixelFormat.setter: {pf}, {type(pf)}",
                        "Orange",
                    )
                )
        except Exception as e:
            self.logger.error(cs(self.logPrefix + str(e), "Maroon"))

    @property
    def Whitebalance(self):
        """set/get Whitebalance of image taken"""
        return self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value

    @Whitebalance.setter
    def Whitebalance(self, wb):
        try:
            if isinstance(wb, str) and wb in self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.symbolics:
                self.ImageAcquirer.remote_device.node_map.BalanceWhiteAuto.value = wb
                self.logger.info(
                    cs(f"{self.logPrefix} Whitebalance set to {wb}", "Teal")
                )
            else:
                self.logger.warning(
                    cs(
                        f"{self.logPrefix} Invalid input for Whitebalance.setter: {wb}, {type(wb)}",
                        "Orange",
                    )
                )
        except Exception as e:
            self.logger.error(cs(self.logPrefix + str(e), "Maroon"))

    def trigger(self, log=True):
        """Make the camera take a picture"""
        if log:
            self.logger.info(cs(f"{self.logPrefix} Triggered", "Aqua"))
        self.ImageAcquirer.remote_device.node_map.TriggerSoftware.execute()

    def grab(self, save=False, log=True):
        """Return the image taken as a list of pixel Values"""
        if log:
            self.logger.info(cs(f"{self.logPrefix} Grabed", "Aqua"))
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
                self.logger.info(cs(f"{self.logPrefix} Saved during grabbing", "Aqua"))
            img = Image.fromarray(image_data)
            img.save(f"./images/{self.id}-Image.png")

        return image_data

