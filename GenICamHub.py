from GenICam import GenICam
from harvesters.core import Harvester
import os
import logging
from datetime import datetime as dt

class GenICamHub:
    """

    """

    def __init__(self, logger:logging.Logger = None) -> None:

        self.deviceList = {}
        self.activeDevice = None

        ids = []

        if logger is None:
            self.logger = logging.getLogger(__name__)
            logging.basicConfig(
                format="%(asctime)s [%(levelname)s]: %(filename)s: "+"ln "+ "%(lineno)d: %(message)s",
                datefmt="%T",
                filename="".join("logs/GenICam-Hub.log".split(" ")),
                level=logging.INFO
            )

            self.logger.info(".\n" * 25)
            self.logger.info(f"Start of Log - {dt.now()} - Hub")

        with Harvester() as H:
            for root, dir, files in os.walk("./cti"):
                for file in files:
                    if file.split(".")[-1] in ["cti","sym"]:
                        path = root+"/"+file
                        H.add_file(file_path = path)
                    else:
                        pass

            H.update()

            self.logger.info(H.device_info_list)
            for device in H.device_info_list:
                self.logger.info(str(device))
                self.logger.info(str(device).split("'")[1])
                ids.append(str(device).split("'")[1])

        #H.release()

        self.logger.info(ids)

        for id in ids:
            self.deviceList[id] = GenICam(id=id)

GCH = GenICamHub()
GCH.logger.info(GCH.deviceList)

