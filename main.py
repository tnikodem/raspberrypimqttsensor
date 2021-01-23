import time
from datetime import datetime
import json
import paho.mqtt.publish as publish

import numpy as np

# sensors
import picamera
from gpiozero import CPUTemperature, LoadAverage, PingServer
import psutil
from mh_z19 import read_all

import utils


MQTT_SERVER = "192.168.0.53"
MQTT_PATH = "sentinel/sensors"

DISABLE_WIFI_LUMINOSITY = 10

camera = picamera.PiCamera()
#camera.exposure_mode = 'off'
#camera.awb_mode = 'off'
camera.resolution = (320, 240)
camera.start_preview()
time.sleep(2)

cpu_temp = CPUTemperature()
load_average = LoadAverage()
ping_router = PingServer("192.168.0.1")

cache = []


while True:
#  with open ("config.json", "r") as f:
#      config = json.loads(f.read())

  picture = np.empty((240, 320, 3), dtype=np.uint8)
  camera.capture(picture, "rgb")
  camera_gain = float(camera.digital_gain * camera.analog_gain)
  camera_exposure_speed = camera.exposure_speed  # in ms
  luminosity = np.average(picture) / camera_gain / camera_exposure_speed * 2**14
  online = ping_router.value

  sensor_values = read_all(True)

  sensor_values["time"] = datetime.now().astimezone().isoformat()

  sensor_values["wifi"] = online

  sensor_values["luminosity"] = luminosity

  sensor_values["cpu_temperature"] =  cpu_temp.temperature
  sensor_values["cpu_load_percent"] = load_average.load_average * 100
  sensor_values["mem_percent"] = psutil.virtual_memory().percent

  print(sensor_values)

  if online:
      try:
        publish.single(MQTT_PATH, json.dumps(sensor_values), hostname=MQTT_SERVER)
      except Exception as e:
          print(e)
          sensor_values["exception"] = str(e)
          online = False

  if not online:
      cache += [sensor_values]

  if len(cache) > 59 or (online and len(cache) > 0):
    with open (f"""cache/sensors-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json""", "w") as f:
      f.write(json.dumps(cache))
    cache = []

  # change offlien online depending on luminosity
  if luminosity < DISABLE_WIFI_LUMINOSITY:
      if online:
          utils.disable_wifi()
      online = False
  else:
      if not online:
          utils.activate_wifi()
          for i in range(30):
              online = ping_router.value
              if not online:
                  time.sleep(1)
                  continue
              utils.upload_cache()
              break

  if online:
      utils.turn_led_on()
  else:
      utils.turn_led_off()

  time.sleep(30)


camera.stop_preview()
camera.close()
