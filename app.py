from flask import Flask, render_template, Response, send_file, request
from pypylon import genicam, pylon
import numpy as np
import climage as cli
from PIL import Image
import os
import io
import random as rd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("res")
args = parser.parse_args()
res = args.res
res=res.split("x")

app = Flask(__name__)

@app.before_first_request
def before_first_request():
    global cam
    global cam_stats
    cam_stats = {}
    cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    cam.Open()
    cam.ExposureTime.SetValue(rd.randint(4000,10000))
    cam.Width.SetValue(int(res[0]))
    cam.Height.SetValue(int(res[1]))
    cam_stats["width"] = str(cam.Width.GetValue())
    cam_stats["height"] = str(cam.Height.GetValue())
    cam_stats["exposure"] = cam.ExposureTime.GetValue()
    cam.StartGrabbing()

@app.route('/')
def index():
    return render_template('index.html',cam_stats=cam_stats)

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/cam_res",methods = ['POST'])
def cam_res():
    if request.method == "POST":
        data = request.form
        print(data)
        res = data["resolution"]
        expo = data["exposure"]
        cam.StopGrabbing()
        if res != "":
            res = res.split("x") 
            cam.Width.SetValue(int(res[0]))
            cam.Height.SetValue(int(res[1]))
            cam_stats["width"] = str(cam.Width.GetValue())
            cam_stats["height"] = str(cam.Height.GetValue())
        if expo != "":
            cam.ExposureTime.SetValue(int(expo))
            cam_stats["exposure"] = cam.ExposureTime.GetValue()
        cam.StartGrabbing()
    return render_template('index.html',cam_stats=cam_stats)

def take_img():
    grab_result = cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    image_data = np.asarray(grab_result.Array)
    img = Image.fromarray(image_data)
    img.save("./static/current_cam.png")

def gen():
    while True:
        grab_result = cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        image_data = np.asarray(grab_result.Array)
        img = Image.fromarray(image_data)
        img = img.crop()
        img_byte_arr = io.BytesIO()
        
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr + b'\r\n')
        

if __name__ == '__main__':
    
    app.run(debug=True,host="0.0.0.0")