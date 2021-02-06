import os
import time
import json

import psycopg2
import numpy as np
import picamera


class LuminositySensor:
    def __init__(self):
        self.camera = None
        
    def open_camera(self):
        if self.camera and not self.camera.closed:
            return
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        #self.camera.exposure_mode = 'off'
        #self.camera.awb_mode = 'off'
        self.camera.start_preview()
        time.sleep(2)
        
    def get_luminosity(self, keep_open=False):
        self.open_camera()
        picture = np.empty((240, 320, 3), dtype=np.uint8)
        self.camera.capture(picture, "rgb")
        camera_gain = float(self.camera.digital_gain * self.camera.analog_gain)
        camera_exposure_speed = self.camera.exposure_speed  # in ms
        luminosity = np.average(picture) / camera_gain / camera_exposure_speed * 2**14
        if not keep_open:
            self.camera.stop_preview()
            self.camera.close()
        return luminosity


def wait_for_next_run(seconds=1):
    sleep_for = int(seconds) - int(time.time()) % int(seconds)
    time.sleep(sleep_for)
    

def turn_led_off():
    with open("/sys/class/leds/led0/brightness", "r") as f:
        data = f.read()
        if not ('0' in data):
            os.popen("sudo sh -c 'echo 0 > /sys/class/leds/led0/brightness'")


def turn_led_on():
    with open("/sys/class/leds/led0/brightness", "r") as f:
        data = f.read()
        if not ('255' in data):
            os.popen("sudo sh -c 'echo 255 > /sys/class/leds/led0/brightness'")
    
    
def disable_wifi():
    os.popen("sudo ifconfig wlan0 down")

    
def activate_wifi():
    os.popen("sudo ifconfig wlan0 up")
    

def upload_data(data, entity_id, value_name):
    warning = False
    
    domain = "sensor"
    with open ("config.json", "r") as f:
        config = json.loads(f.read())

    try:
        connection = psycopg2.connect(config["db_connect_str"])
        cursor = connection.cursor()

        # get attributes
        sql = f""" SELECT attributes
        FROM public.states
        WHERE entity_id = '{entity_id}'
        ORDER BY state_id DESC
        limit 1;
        """
        cursor.execute(sql)
        response = cursor.fetchall()
        attributes =response[0][0]

        for row in data:
            sql = f""" INSERT INTO public.states (domain, entity_id, state, attributes, last_changed, last_updated, created)
            SELECT 'sensor', '{entity_id}', {row[value_name]}, '{attributes}', '{row["time"]}', '{row["time"]}', '{row["time"]}'
            WHERE
              NOT EXISTS (
                SELECT state_id FROM public.states WHERE entity_id = '{entity_id}' AND last_updated = '{row["time"]}'
              )
            RETURNING state_id;
            """
            cursor.execute(sql)
            resp = cursor.fetchone()
            if resp is None:
                print(f"""Warning: Could not insert {entity_id}, time: {row["time"]}""")
                warning = True

        connection.commit()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        warning = True
    finally:
        if (connection):
            cursor.close()
            connection.close()
            
    return warning


def upload_cache(directory="cache"):
    with open ("config.json", "r") as f:
        config = json.loads(f.read())
    
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.loads(f.read())
                warning = False
                for sensor in config["sensors"]:
                    warning &= upload_data(data, **sensor)

            if not warning:
                os.remove(filepath)
