#!/usr/bin/python
from sense_hat import SenseHat
import RPi.GPIO as GPIO
import time                 # for time delays
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html

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

#global flow_count
#flow_count = 0

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
                run_button = GPIO.input(RUN_GPIO)
# count the number of pulses in one second
                flow_count = 0
                time.sleep(1)           # wait 
                gpm_flow_count = flow_count
                sense.show_message("{}".format(gpm_flow_count), text_colour=red)
                print ("{}".format(gpm_flow_count))

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

