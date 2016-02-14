#!/usr/bin/python
from sense_hat import SenseHat
import RPi.GPIO as GPIO
import time                 # for time delays
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html

# Constants
PUMP_GPIO = 5     # GPIO pin
PUMP_OFF = 1
PUMP_ON = 0

VALVE_GPIO = 6     # GPIO pin
VALVE_OFF = 1
VALVE_ON = 0

FLOW_GPIO = 22     # GPIO pin

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
# GPIO 23 set up as input. It is pulled up to stop false signals  
GPIO.setup(FLOW_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.output(PUMP_GPIO, PUMP_OFF)
GPIO.output(VALVE_GPIO, VALVE_OFF)
#flow_count = 0

cb = pi.callback(FLOW_GPIO) # Default tally callback.
old_flow_count = cb.tally()
new_flow_count = 0

raw_input("Press Enter when ready\n>")
# functions
#def flow_callback(channel):
#    global flow_count
#    flow_count += 1
#GPIO.add_event_detect(FLOW_GPIO, GPIO.RISING, callback=flow_callback)  

try:
    while True:
        new_flow_count = cb.tally()
        sense.show_message("{}".format(new_flow_count), text_colour=red)
        old_flow_count = new_flow_count
        
        time.sleep(1)           # wait 
        GPIO.output(VALVE_GPIO, VALVE_OFF)
        GPIO.output(PUMP_GPIO, PUMP_ON)
        time.sleep(1)           # wait 
        GPIO.output(PUMP_GPIO, PUMP_OFF)
        GPIO.output(VALVE_GPIO, VALVE_ON)

        ##print "During this waiting time, your computer is not" 
        ##print "wasting resources by polling for a button press.\n"
        #            GPIO.wait_for_edge(23, GPIO.FALLING)

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

