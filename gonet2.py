#!/usr/bin/python

import piexif
import serial
import subprocess
import socket
import os
import time
from time import gmtime, strftime
from PIL import Image, ImageDraw, ImageFont, ExifTags
 

port = "/dev/serial0"
ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)

def lat_long_decode(coord):
    #Converts DDDMM.MMMMM > DD  MM' SS.SSS" 
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    sec = str((float(coord[-6:]) * 60.0))

    #return deg + "  " + min + " " + sec + " "
    return deg + u"\u00b0 " + min + "\' " + sec + "\""

##### end of lat_long_decode #####


def parse_gga(sdata):
     lat = sdata[2]
     lat_dir = sdata[3]
     long = sdata[4]
     long_dir = sdata[5]
     alt = sdata[9]

     return  lat + " " + lat_dir + " " + long + " " + long_dir + " " + alt + " M"

##### end of parse gga #####


def parse_rmc(sdata):
     date = sdata[9]
     time = sdata[1][0:6]

     return date + " " + time

##### end of parse rmc #####

def convert_raw_timestamp_to_filename_timestamp(raw_timestamp):
     time_parts = raw_timestamp.split(" ")

     return time_parts[0] + "_" + time_parts[1]

##### end of convert_raw_to_filename #####


#def  convert_raw_timestamp_to_image_timestamp(raw_timestamp):
#     #180119_214946 DD/MM/YY HH:MM:SS
#     date = raw_timestamp[0:2] + "/" + raw_timestamp[2:4] + "/" + raw_timestamp[4:6]
#     time = raw_timestamp[7:9] + ":" + raw_timestamp[9:11] + ":" + raw_timestamp[11:13]
#
#     return date + " " + time
#
###### end of convert_raw_timestamp_to_image_timestamp #####


def convert_raw_gps_fix_to_image_gps_fix(raw_gps_fix):
     #4203.4338X N 08748.7831X W 215.3 M
     lat = lat_long_decode(raw_gps_fix[0:10])
     lat_dir = raw_gps_fix[11]
     long = lat_long_decode(raw_gps_fix[13:24])
     long_dir = raw_gps_fix[25]
     alt = raw_gps_fix[27:32]

     return  lat + " " + lat_dir + " " + long + " " + long_dir + " " + alt + " M"

##### end of convert_raw_gps_fix_to_image_gps_fix #####

def convert_raw_gps_fix_to_exif_lat(raw_gps_fix):
     raw_lat = (raw_gps_fix.split(" "))[0]
     deg = raw_lat[0:2]
     min = raw_lat[2:4]
     sec = str(int(float(raw_lat[4:9]) * 60.0))
     #sec = str(float(raw_lat[5:9]) * 60.0 / 10000)
     #print sec
     return deg + "/1," + min + "/1," + sec + "/1"

##### end of convert_raw_gps_fix_to_exif_lat #####

def convert_raw_gps_fix_to_exif_long(raw_gps_fix):
     raw_lat = (raw_gps_fix.split(" "))[2]
     deg = raw_lat[0:3]
     min = raw_lat[3:5]
     sec = str(int((float(raw_lat[5:10]) * 60.0)))

     return deg + "/1," + min + "/1," + sec + "/1"

##### end of convert_raw_gps_fix_to_exif_long #####

#################################
##### Start of main program #####
#################################


print  "Looking for GPS Data"

while True:
   time.sleep(0.25)
   data = ser.read_until() 
# Uncomment following line for quick GPS test
#   print data 
   sdata = data.split(",")

   if sdata[0] == "$GPRMC":
          raw_timestamp = parse_rmc(sdata)

   if sdata[0] == "$GPGGA":
          raw_gps_fix  = parse_gga(sdata)
          break 

ser.close()

##### done with gps #####

##### manuipilate gps strings to make them useful #####

filename_timestamp = convert_raw_timestamp_to_filename_timestamp(raw_timestamp)

#image_timestamp = convert_raw_timestamp_to_image_timestamp(raw_timestamp)
#print image_timestamp

image_gps_fix = convert_raw_gps_fix_to_image_gps_fix(raw_gps_fix)
print image_gps_fix

gps_string = raw_timestamp + " " + raw_gps_fix

exif_lat = convert_raw_gps_fix_to_exif_lat(raw_gps_fix)
exif_long = convert_raw_gps_fix_to_exif_long(raw_gps_fix)



##### done with gps string manipulation #####

##### This where the photo loop begins #####

#Create image of a white rectangle for test background
img = Image.new('RGB', (1944, 120), color=(255,255,255))

print "gps_string "
print gps_string


start_time = time.time()
print "start_time = " + str(start_time)
# place black text on white image, rotate and save as foreground.jpg
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",40)
d = ImageDraw.Draw(img)
d.text((20,10), "Adler / Far Horizons GONet hostname: " + socket.gethostname(), font=font, fill=(0,0,0))
d.text((20,70), strftime("%m-%d-%y %H:%M:%S", gmtime()) + " " + image_gps_fix, font=font, fill=(0,0,0))
img.rotate(90,expand = True).save('foreground.jpg', 'JPEG')

# take a picture with pi cam!


#exif_lat = '42/1,03/1,25.86/1'
#exif_long = '087/1,48/1,46.9794/1'

# http://www.ridgesolutions.ie/index.php/2015/03/05/geotag-exif-gps-latitude-field-format/
# https://sno.phy.queensu.ca/~phil/exiftool/TagNames/GPS.html


file_name_date = (strftime("%m%d%y_%H%M%S", gmtime()))
#file_name = socket.gethostname()[-3:] + '_' + file_name_date + '.jpg'

command = ['raspistill', '-v',
                         '-t', '12000',
                         '-ss', '2000000',
                         '-ISO', '800',
                         '-drc', 'off',
                         '-awb', 'sun',
                         '-br', '50',
                         '-r',
                         '-ts',
                         '-x', 'GPS.GPSLatitude=' + exif_lat,
                         '-x', 'GPS.GPSLatitudeRef=' + "N",
                         '-x', 'GPS.GPSLongitude=' + exif_long, 
                         '-x', 'GPS.GPSLongitudeRef=' + "W",
                         '-o', 'cam.jpg']
subprocess.Popen(command)

# open the the image from pi cam 
#background = Image.open(socket.gethostname()[-3:] + '_' + file_name_date + '.jpg').convert("RGB")
background = Image.open("cam.jpg").convert("RGB")

# save its exif
exif = background.info['exif']


# open foreground.jpg and paste it to pi cam image
foreground = Image.open("foreground.jpg")
background.paste(foreground, (0, 0)) #, foreground)

#save the new composite image with pi cam photo's exif



#background.save(socket.gethostname()[-3:] + "_" + file_name_date + ".jpeg", 'JPEG',  exif=exif)
background.save(socket.gethostname()[-3:] + "_" + filename_timestamp + ".jpg", 'JPEG',  exif=exif)

end_time = time.time()
print "end_time = " + str(end_time)

delta_time = end_time - start_time
print "delta_time = " + str(delta_time)


