import os


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
    
