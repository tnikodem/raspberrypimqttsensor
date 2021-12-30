#!/home/pi/venv3.7/bin/python

import time
from datetime import datetime
import json
import paho.mqtt.publish as publish


# sensors
from gpiozero import CPUTemperature, LoadAverage, PingServer
import psutil
import mh_z19
import utils

def main():
  lumi_sensor = utils.LuminositySensor()
  cpu_temp = CPUTemperature()
  load_average = LoadAverage()
  
  cache = []
  
  last_luminosity = -1
  last_co2 = -1
  update_frequency = 30 # in s
  
  while True:
    with open ("config.json", "r") as f:
        config = json.loads(f.read())
  
    ping_router = PingServer(config["MQTT_SERVER"])
    online = ping_router.value
  
    luminosity = lumi_sensor.get_luminosity(keep_open=update_frequency < 31)
  
    sensor_values = mh_z19.read_all(True)
    sensor_values["time"] = datetime.now().astimezone().isoformat()
    sensor_values["online"] = online
    sensor_values["luminosity"] = luminosity
    sensor_values["cpu_temperature"] =  cpu_temp.temperature
    sensor_values["cpu_load_percent"] = load_average.load_average * 100
    sensor_values["mem_percent"] = psutil.virtual_memory().percent
  
    #print(sensor_values)
   
    # MQTT publish
    if online:
        try:
          publish.single(config["MQTT_PATH"], json.dumps(sensor_values), hostname=config["MQTT_SERVER"])
        except Exception as e:
            print(e)
            sensor_values["exception"] = str(e)
            online = False
  
    # if not online, write to cache
    if not online:
        cache += [sensor_values]
    if len(cache) > 59 or (online and len(cache) > 0):
      with open (f"""cache/sensors-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json""", "w") as f:
        f.write(json.dumps(cache))
      cache = []
  
    # change off/online depending on luminosity
    if luminosity < config["DISABLE_WIFI_LUMINOSITY"]:
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
                break
  
    if online:
        utils.turn_led_on()
        utils.upload_cache()
    else:
        utils.turn_led_off()
  
    delta_luminosity = luminosity - last_luminosity
    last_luminosity = luminosity
    delta_co2 = sensor_values["co2"] - last_co2 
    last_co2 = sensor_values["co2"]
  
    if abs(delta_luminosity) > 0.01 or abs(delta_co2) > 10:
        update_frequency = 30
    else:
        if luminosity > 0.1:
            update_frequency = 60
        else:
            update_frequency = 60 * 5

  
    utils.wait_for_next_run(seconds=update_frequency)
 
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(f"{e}")
