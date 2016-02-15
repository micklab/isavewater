#!/usr/bin/python
from sense_hat import SenseHat
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
# Add the directory containing your module to the Python path (wants absolute paths)
scriptpath = "/home/pi/Projects/Adafruit-Raspberry-Pi-Python-Code/Adafruit_ADS1x15"
sys.path.append(os.path.abspath(scriptpath))
from Adafruit_ADS1x15 import ADS1x15

# Constants
PUMP_GPIO = 4     # GPIO pin
PUMP_OFF = 1
PUMP_ON = 0

VALVE_GPIO = 17     # GPIO pin
VALVE_OFF = 1
VALVE_ON = 0

FLOW_GPIO = 22     # GPIO pin

RUN_GPIO = 27     # GPIO pin
RUN_OFF = 1
RUN_ON = 0

LED_OFF = 1
LED_ON = 0
OPEN_VALVE_LED_GPIO = 23     # GPIO pin
SHORTED_VALVE_LED_GPIO = 24     # GPIO pin
LEAK_LED_GPIO = 25     # GPIO pin
BLOCKAGE_LED_GPIO = 8     # GPIO pin
HEARTBEAT_LED_GPIO = 7     # GPIO pin

# Initialize the Analog to Digital converter for reading the current sensor
ADS1015 = 0x00  # 12-bit ADC
ADS1115 = 0x01	# 16-bit ADC

# Select the gain
# gain = 6144  # +/- 6.144V
gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
# gain = 1024  # +/- 1.024V
# gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
# sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

# Initialise the ADC using the default mode (use default I2C address)
# Set this to ADS1015 or ADS1115 depending on the ADC you are using!
DISTANCE_HANDLE = ADS1x15(ic=ADS1115)

# Initialize
pi = pigpio.pi()           # Connect to Pi.

sense = SenseHat()
sense.set_rotation(180)
red = (255, 0, 0)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # warnings off
GPIO.setup(PUMP_GPIO, GPIO.OUT, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VALVE_GPIO, GPIO.OUT, pull_up_down=GPIO.PUD_UP)

GPIO.setup(FLOW_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RUN_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(OPEN_VALVE_LED_GPIO, GPIO.OUT)
GPIO.setup(SHORTED_VALVE_LED_GPIO, GPIO.OUT)
GPIO.setup(LEAK_LED_GPIO, GPIO.OUT)
GPIO.setup(BLOCKAGE_LED_GPIO, GPIO.OUT)
GPIO.setup(HEARTBEAT_LED_GPIO, GPIO.OUT)

GPIO.output(PUMP_GPIO, PUMP_OFF)
GPIO.output(VALVE_GPIO, VALVE_OFF)
GPIO.output(OPEN_VALVE_LED_GPIO, LED_OFF)
GPIO.output(SHORTED_VALVE_LED_GPIO, LED_OFF)
GPIO.output(LEAK_LED_GPIO, LED_OFF)
GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)
GPIO.output(HEARTBEAT_LED_GPIO, LED_ON)

# functions
global flow_count
flow_count = 0
#def cbf(gpio, level, tick):
#   print(gpio, level, tick)
def flow_callback(gpio, level, tick):
    global flow_count
    flow_count += 1

cb = pi.callback(FLOW_GPIO, pigpio.FALLING_EDGE, flow_callback) # interrupt mechanism

try:
    print("Turn on the RUN button when ready\n>")        
    while True:

        run_button = 1
        run_button = GPIO.input(RUN_GPIO)
        if (run_button == 0):

# turn on the pump and valve
            GPIO.output(PUMP_GPIO, PUMP_ON)
            GPIO.output(VALVE_GPIO, VALVE_ON)

            while run_button == 0:
# read A to D converter to measure valve current
                valve_mv = DISTANCE_HANDLE.readADCSingleEnded(0, gain, sps)

# count the number of pulses in one second
                flow_count = 0
                time.sleep(1)           # wait 
                gpm_flow_count = flow_count
#                sense.show_message("{} GPM {}mv".format(gpm_flow_count, valve_mv), text_colour=red)
                print ("{} GPM {}mv".format(gpm_flow_count, valve_mv))

                run_button = GPIO.input(RUN_GPIO)

# turn off the pump and valve
            GPIO.output(PUMP_GPIO, PUMP_OFF)
            GPIO.output(VALVE_GPIO, VALVE_OFF)

        else:
            time.sleep(1)           # wait 
            
        
except KeyboardInterrupt:
    sense.clear
    GPIO.output(PUMP_GPIO, PUMP_OFF)
    GPIO.output(VALVE_GPIO, VALVE_OFF)
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
    cb.cancel() # Cancel callback.
    pi.stop()   # Disconnect from Pi.
    exit()

# normal exit
sense.clear
GPIO.setmode(GPIO.BCM)
cb.cancel() # Cancel callback.
pi.stop()   # Disconnect from Pi.
GPIO.output(PUMP_GPIO, PUMP_OFF)
GPIO.output(VALVE_GPIO, VALVE_OFF)
GPIO.cleanup()       # clean up GPIO on normal exit

