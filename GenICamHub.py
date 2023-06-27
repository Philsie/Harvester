"""
The GenICamHub is used to handle creation and basic usage of all connected GenICam devices.
"""
#%% Libraries
import copy
import json
import logging
import os
from datetime import datetime as dt

from harvesters.core import Harvester

from GenICam import GenICam

#%% Logging and Config
logger = logging.getLogger(__name__)
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

with open("config.json") as config_file:
    config = json.load(config_file)

#%% Fallback for color-string

fallBackColorstring = False
if config["colorstring"].upper() == "TRUE":
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


#%% GenICamHub

class GenICamHub:
    """
    The GenICamHub creates and manages GenICam objects
    """

    def __init__(self) -> None:
        """
        Creates the GenICamHub object

        Fields:
            self.deviceDict(dict<str:GenICam>):
                matches every GenICam object to an id for ease of access
            self.activeDevice(GenICam):
                Currently selected GenICam when using GenICamHub to manage them
            self.activeDeviceId(str):
                id of currently active GenICam when using GenICamHub to manage them
            self.ctiFiles(list<str>):
                list of all cti files loaded accounting for loadorder
            self.Harvester(Harvester):
                Harvester object used for creation of GenICam objects
            self.deviceList:
                shortcut to the Harvester device_info_list
        """

        self.deviceDict = {}
        self.activeDevice = None
        self.activeDeviceId = None

        logger.info(".\n" * 25)
        logger.info(cs(f"Start of Log - {dt.now()} - Hub", "Green"))
        if fallBackColorstring:
            logger.info(f"Using fallback for colorstring in {__file__}")

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
            logger.info(cs(f"File added; {file}", "Teal"))
            self.Harvester.add_file(file)

        self.Harvester.update()

        self.deviceList = self.Harvester.device_info_list

        logger.info(cs(f"Devices found:", "Teal"))
        for device in self.deviceList:
            logger.info(cs(f"\t {str(device)}", "Teal"))

        for device in self.deviceList:
            devString = str(device)

            id = devString.split("'")[1]
            logger.info(cs(id, "Teal"))

            try:
                self.deviceDict[id] = GenICam(
                    ImageAcquirer=self.Harvester.create_image_acquirer(
                        self.deviceList.index(device)
                    ),
                    id=id,
                )
                logger.info(cs(f"Device stated: {id}", "Teal"))
            except Exception as e:
                    logger.exception(cs(str(e),"Orange"),stack_info=True)
            

        self.list_Running_Devices()


        if len(self.deviceDict) > 0:
            self.activeDevice = list(self.deviceDict.values())[0]
            self.activeDeviceId = list(self.deviceDict.keys())[0]
        else:
            logger.error(cs(f"No Valid devices running - shutting down"))
            exit()

    def list_Running_Devices(self):
        """creates a list of all running GenICam objects

        Returns:
            list<GenICam>: list of all GenICam objects
        """
        if len(self.deviceDict) > 0:
            logger.info(cs(f"{len(self.deviceDict)} devices running", "Teal"))

            for id, Device in self.deviceDict.items():
                logger.info(cs(" " * 8 + f" {id} - {Device}", "Teal"))
            return list(self.deviceDict.values())
        else:
            logger.info(cs("No devices found", "Teal"))

    def change_Device(self, id: str, log = True):
        """changes the currently active GenICam object

        Args:
            id (str): id of GenICam object set as active
            log (bool, optional): log the change in active GenICam.
                * Defaults to True
        """
        if log:
            logger.info(
                cs(f"changing active device from {self.activeDeviceId} to {id}", "Teal")
            )

        if id in list(self.deviceDict.keys()):
            if id != self.activeDeviceId:
                self.activeDevice = self.deviceDict[id]
                old_id = copy.copy(self.activeDeviceId)
                self.activeDeviceId = id
        else:
            logger.warning(cs(f"No device with ID: {id} found", "Orange"))

    def export_Device(self, id: str):
        """exports a GenICam for use outside of GenICamHub

        Args:
            id (str): id of GenICam object exported

        Returns:
            GenICam: GenICam object
        """
        logger.info(cs(f"exporting {id}", "Teal"))
        try:
            self.change_Device(id)  
            return self.activeDevice
        except Exception as e:
            logger.exception(cs(str(e),"Orange"),stack_info=True)

