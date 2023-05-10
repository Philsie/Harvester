from flask import Flask, render_template, Response, send_file, request
#from pypylon import genicam, pylon
from harvesters.core import Harvester
import numpy as np
from PIL import Image
import os
import io
import random as rd
import argparse
from datetime import datetime as dt

parser = argparse.ArgumentParser()
parser.add_argument("res")
args = parser.parse_args()
res = args.res
res=res.split("x")

app = Flask(__name__)

global cam_stats
cam_stats = {}
default_config = {"resolution":"600x400","width":600,"height":400}

@app.before_first_request
def before_first_request():
    global h
    global cam
    global fps
    h = Harvester()
    h.add_file('/home/philipp/src/Harvester/ximea.gentl.cti')
    h.update()
    cam = h.create_image_acquirer(0)
    config_device(cam,default_config)
    cam.start_acquisition()
    

@app.route('/')
def index():
    print(fps)
    return render_template('index.html',cam_stats=cam_stats,fps=fps)

@app.route("/cam_res",methods = ['POST'])
def cam_res():
    print(fps)
    if request.method == "POST":
        data = request.form
        print(data)
        cam.stop_acquisition()
        config_device(cam,data)
        cam.remote_device.node_map.Exposure.value(10000)
        input()
        cam.start_acquisition()
    return render_template('index.html',cam_stats=cam_stats,fps=fps)


@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#%%

def config_device(dev,config):
    print(config)
    if "width" in config.keys():
        print("*")
        res = config["resolution"].split("x")
        config["width"] = res[0]
        config["height"] = res[1]
        dev.remote_device.node_map.Width.value = int(config["width"])
        dev.remote_device.node_map.Height.value = int(config["height"])
        cam_stats["width"], cam_stats["height"] = config["width"],config["height"]

def gen():
    global fps
    while True:
        time = dt.now()
        with cam.fetch_buffer() as buffer:
            component = buffer.payload.components[0]
            image_data = component.data.reshape(component.height,component.width) 
            img = Image.fromarray(image_data)
            img = img.crop()
            img_byte_arr = io.BytesIO()
            
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            fps = str(dt.now().timestamp()-time.timestamp())
            print(fps)
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr + b'\r\n')
        

#%%
if __name__ == '__main__':
    fps = 0
    app.run(debug=False)#,host='0.0.0.0')