## Packages needed:

PIL
harvesters==1.3.2
numpy
logging
datetime
time
json
io
copy
flask
flask_socketio
eventlet
base64

## .Cti

Place all .cti file into the cti folder or create a symlink with the ending .sym  
    > ln -s /path/to/target /path/to/symlink.sym

## Camera Setup:

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

## known issues:

# Allied Vision:

* Stoppen working even though plugged in and found by Harvester  
    > GenTL exception: Operation timed out before completion. (Message from the source: Timeout while sending packet.) (ID: -1011)
    fixed by replugging during testing
