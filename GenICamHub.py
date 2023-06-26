import copy
import logging
import os
from datetime import datetime as dt

from harvesters.core import Harvester
from stringcolor import *

from GenICam import GenICam


class GenICamHub:
    """

    """

    def __init__(self) -> None:

        self.deviceDict = {}
        self.activeDevice = None
        self.activeDeviceId = None

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s]: %(filename)s: "
            + "ln "
            + "%(lineno)d: "
            + "\t" * 2
            + "%(message)s",
            datefmt="%T",
            filename="logs/GenICam.log",
            level=logging.INFO,
        )

        self.logger.info(".\n" * 25)
        self.logger.info(cs(f"Start of Log - {dt.now()} - Hub", "Green"))

        self.ctiFiles = []

        self.Harvester = Harvester()

        for root, dir, files in os.walk("./cti"):
            for file in files:
                if file.split(".")[-1] in ["cti", "sym"] and root != "./cti/inactive":
                    path = root + "/" + file
                    self.ctiFiles.append(path)
                else:
                    pass

        self.ctiFiles.sort()

        for file in self.ctiFiles:
            self.logger.info(cs(f"File added; {file}", "Teal"))
            self.Harvester.add_file(file)

        self.Harvester.update()

        self.deviceList = self.Harvester.device_info_list

        self.logger.info(cs(f"Devices found:", "Teal"))
        for device in self.deviceList:
            self.logger.info(cs(f"\t {str(device)}", "Teal"))

        for device in self.deviceList:
            devString = str(device)

            id = devString.split("'")[1]
            self.logger.info(cs(id, "Teal"))

            try:
                self.deviceDict[id] = GenICam(
                    self.logger,
                    ImageAcquirer=self.Harvester.create_image_acquirer(
                        self.deviceList.index(device)
                    ),
                    id=id,
                )
                self.logger.info(cs(f"Device stated: {id}", "Teal"))
            except Exception as e:
                    self.logger.exception(cs(str(e),"Orange"),stack_info=True)
            

        self.list_Running_Devices()

        if len(self.deviceDict) > 0:
            self.activeDevice = list(self.deviceDict.values())[0]
            self.activeDeviceId = list(self.deviceDict.keys())[0]
        else:
            self.logger.error(cs(f"No Valid devices running - shutting down"))
            exit()

    def list_Running_Devices(self):
        if len(self.deviceDict) > 0:
            self.logger.info(cs(f"{len(self.deviceDict)} devices running", "Teal"))

            for id, Device in self.deviceDict.items():
                self.logger.info(cs(" " * 8 + f" {id} - {Device}", "Teal"))
            return list(self.deviceDict.values())
        else:
            self.logger.info(cs("No devices found", "Teal"))

    def change_Device(self, id: str, log = True):
        if log:
            self.logger.info(
                cs(f"changing active device from {self.activeDeviceId} to {id}", "Teal")
            )

        if id in list(self.deviceDict.keys()):
            if id != self.activeDeviceId:
                self.activeDevice = self.deviceDict[id]
                old_id = copy.copy(self.activeDeviceId)
                self.activeDeviceId = id
        else:
            self.logger.warning(cs(f"No device with ID: {id} found", "Orange"))

    def export_Device(self,id:str):
        self.logger.info(cs(f"exporting {id}", "Teal"))
        try:
            self.change_Device(id)  
            return self.activeDevice
        except Exception as e:
            self.logger.exception(cs(str(e),"Orange"),stack_info=True)


if __name__ == "__main__":
    GCH = GenICamHub()
    GCH.activeDevice.trigger()
    GCH.activeDevice.grab(save=True)
