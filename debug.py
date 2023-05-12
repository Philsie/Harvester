from GeniCam import GenICam as HfF

hff = HfF()


print("=====>",hff.ia)
print("=====>",hff.cam.vendor)
print("=====>",hff.width,hff.height,hff.exposure)
print("=====>", hff.width)
hff.width = 1000
print("=====>", hff.width)
print("=====>", hff.height)
hff.height = 500
print("=====>", hff.height)
print("=====>", hff.exposure)
hff.exposure = 10000
print("=====>", hff.exposure)
print("=====>", hff.gain)
hff.gain = 2.0
print("=====>", hff.gain)
print("=====> done")
print("=====>", hff.get_frame())


"""
<!--
<form action="/cam_res" method = "POST">
<p><input type = "text" name = "resolution" placeholder="{{(cam_stats['width']+'x'+cam_stats['height'])}}"/> Resolution (Width x Height) </p>
<p><input type = "number" name = "exposure" placeholder="{{cam_stats['exposure']}}" /> Exposure</p>
<p><input type = "submit" value = "Submit" /></p>  
</form>
-->
"""
