## Packages needed:

Pillow
harvesters==1.3.2
numpy
python-json-logger
datetime
flask
flask_socketio
eventlet
string-color

* Including their dependencies
* install these into a .venv directory
    > bash setup.py


## .Cti

Place all .cti file into the cti folder or create a symlink with the ending .sym  
    > ln -s /path/to/target /path/to/symlink.sym

## Camera Setup:

# Ximea  

1. Ensure cti file or symlink is placed in ./cti directory

2. Ensure the necessay udev rule is placed in /etc/udev/ruled.d 

# Allied Vision:  

1. Download SDK from their website [Allied Vision](https://www.alliedvision.com/en/products/vimba-sdk/)  
***dont use Vimba_X !***

2. Install VimbaUSBTL  
    > sudo bash VimbaUSBTL/Install.sh

3. Copy .cti file into local cti folder
    > VimbaUSBTL/CTI/x86_64bit/VimbaUSBTL.cti

# IDS -- Not Working Currently

* Download https://en.ids-imaging.com/download-details/AB12776.html?os=linux&version=&bus=64&floatcalc=#anc-software-367
* cti files:
    > /lib/cti
* udev rules:
    > /local/scripts

# Configuration

* The load order of cti files and symlinks can be change with leading numbers.  
    * 00-VimbaUSBTL.cti is loaded before 02-ximea.gentl.cti. 

* to deactivate certain .cti files move them or their symlink into the ./cti/inactive directory.

* further configurations (Frontend only) can be done inside the config.json file.   
Note: Dont change fields with a key starting with 'comment-' these are used as descriptions only.

# Usage

## Frontend

1.  While in the main folder use this command to start the frontend
> .venv/bin/python GenICamFrontend.py  

2. To watch the programm outputs watch the log
> tail -f logs/GenICam.log

3. Start the execution by loading the website


# known issues:

## Allied Vision:

* Stoppen working even though plugged in and found by Harvester  
    > GenTL exception: Operation timed out before completion. (Message from the source: Timeout while sending packet.) (ID: -1011)  
    fixed by replugging during testing

* Not starting properly at times
    indication: log stops after grabbing a device  
    fixed by restarting the program

## Ximea

* XiApi keeps spamming the terminal when running  
    check log for readable outputs

## IDS

* Camera not detected by Harvester

## Basler 

* Camera not detected by Harvester
