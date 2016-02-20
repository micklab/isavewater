#!/usr/bin/python
from sense_hat import SenseHat
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
from webcolors import name_to_rgb

# Add the directory containing your module to the Python path (wants absolute paths)
scriptpath = "/home/pi/Projects/Adafruit-Raspberry-Pi-Python-Code/Adafruit_ADS1x15"
sys.path.append(os.path.abspath(scriptpath))
from Adafruit_ADS1x15 import ADS1x15

GPIO.setmode(GPIO.BCM)
# Constants
PUMP_GPIO = 17     # GPIO pin
PUMP_OFF = 1
PUMP_ON = 0

VALVE_GPIO = 26     # GPIO pin
VALVE_OFF = 1
VALVE_ON = 0

FLOW_GPIO = 6     # GPIO pin

RUN_GPIO = 27     # GPIO pin
RUN_OFF = 1
RUN_ON = 0

LED_OFF = 1
LED_ON = 0
BAD_VALVE_LED_GPIO = 18     # GPIO pin
BLOCKAGE_LED_GPIO = 14     # GPIO pin
LEAK_LED_GPIO = 15     # GPIO pin
OVERCURRENT_GPIO = 16     # GPIO pin

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

GPIO.setwarnings(False) # warnings off
GPIO.setup(PUMP_GPIO, GPIO.OUT, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VALVE_GPIO, GPIO.OUT, pull_up_down=GPIO.PUD_UP)

GPIO.setup(FLOW_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RUN_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(OVERCURRENT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(BAD_VALVE_LED_GPIO, GPIO.OUT)
GPIO.setup(LEAK_LED_GPIO, GPIO.OUT)
GPIO.setup(BLOCKAGE_LED_GPIO, GPIO.OUT)

GPIO.output(PUMP_GPIO, PUMP_OFF)
GPIO.output(VALVE_GPIO, VALVE_OFF)
GPIO.output(BAD_VALVE_LED_GPIO, LED_OFF)
GPIO.output(LEAK_LED_GPIO, LED_OFF)
GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)

# functions
global flow_count
flow_count = 0
#def cbf(gpio, level, tick):
#   print(gpio, level, tick)
def flow_callback(gpio, level, tick):
    global flow_count
    flow_count += 1

cb = pi.callback(FLOW_GPIO, pigpio.FALLING_EDGE, flow_callback) # interrupt mechanism

BAD_VALVE_COUNT = 0
BLOCKAGE_COUNT = 0
LEAK_COUNT = 0

LPM_LOW_LIMIT = 1
LPM_NOMINAL = 3
LPM_HIGH_LIMIT = 5
LPM2GPM = 0.264172  # Liters per minute to gallons per minute factor
def flow_calculator (freq):
#    return (LPM2GPM*(freq/5.5))    # in GPM
    return (freq/5.5)               # in LPM

valve_mv = 0.0
def flow_measure ():
    global flow_count
    print ("Checking flow")
    flow_count = 0
    time.sleep(1)           # wait 
    gpm_flow_count = int(flow_calculator(flow_count))
    sense.show_message("{}".format(gpm_flow_count), text_colour=name_to_rgb("teal"))

# read A to D converter to measure valve current
    global valve_mv
    valve_mv = 0.0
    valve_mv = DISTANCE_HANDLE.readADCSingleEnded(0, gain, sps)

    print("{} LPM and Valve current = {:4.1f}".format(gpm_flow_count, valve_mv))

    return gpm_flow_count, valve_mv

overcurrent = 1
def check_overcurrent():
    global overcurrent
    print ("Checking overcurrent")
    overcurrent = 1
    overcurrent = GPIO.input(OVERCURRENT_GPIO)
    BAD_VALVE_COUNT = 0
    if (overcurrent == 0):
        GPIO.output(PUMP_GPIO, PUMP_OFF)
        GPIO.output(VALVE_GPIO, VALVE_OFF)
        GPIO.output(BAD_VALVE_LED_GPIO, LED_ON)
        print ("OVERCURRENT WARNING! Zone 1 Valve failure!")
        sense.show_message("OC!", text_colour=name_to_rgb("red"), back_colour=name_to_rgb("black"))
        BAD_VALVE_COUNT += 1
        time.sleep(1)           # wait 
    else:
        GPIO.output(BAD_VALVE_LED_GPIO, LED_OFF)
        BAD_VALVE_COUNT = 0

    return BAD_VALVE_COUNT

#### Start of Main Loop
try:
    print("Turn on the RUN button when ready\n>")        
    while True:

        run_button = 1
        run_button = GPIO.input(RUN_GPIO)
        if (run_button == 0):

# check for Over Current condition on valve
            BAD_VALVE_COUNT = check_overcurrent()
 
# turn on the pump and valve
            if (run_button == 0 and BAD_VALVE_COUNT == 0 and LEAK_COUNT == 0 and BLOCKAGE_COUNT == 0):
                GPIO.output(PUMP_GPIO, PUMP_ON)
                GPIO.output(VALVE_GPIO, VALVE_ON)
                print ("Adjust relief valve until flow is 3 LPM")
                gpm_flow_count = 0
                while (gpm_flow_count >= LPM_HIGH_LIMIT or gpm_flow_count <= LPM_LOW_LIMIT):
                    gpm_flow_count, valve_mv = flow_measure()
                print ("Zone 1 is operating at nominal flow.")

            gpm_flow_count = LPM_NOMINAL
#############
# Inner While loop
#############
            while (run_button == 0 and BAD_VALVE_COUNT == 0 and LEAK_COUNT == 0 and BLOCKAGE_COUNT == 0):

# count the number of pulses in one second
                gpm_flow_count, valve_mv = flow_measure()

                if (gpm_flow_count >= LPM_HIGH_LIMIT):
                    GPIO.output(PUMP_GPIO, PUMP_OFF)
                    GPIO.output(VALVE_GPIO, VALVE_OFF)
                    GPIO.output(LEAK_LED_GPIO, LED_ON)
                    print ("WARNING! Zone 1 exceeding flow limit - possible leak.")
                    sense.show_message("LK!", text_colour=name_to_rgb("red"), back_colour=name_to_rgb("black"))
                    LEAK_COUNT += 1
                    time.sleep(1)           # wait 
                else:
                    GPIO.output(LEAK_LED_GPIO, LED_OFF)
                    LEAK_COUNT = 0

                if (gpm_flow_count <= LPM_LOW_LIMIT):
                    GPIO.output(PUMP_GPIO, PUMP_OFF)
                    GPIO.output(VALVE_GPIO, VALVE_OFF)
                    print ("WARNING! Zone 1 below flow limit - possible blockage.")
                    sense.show_message("BL!", text_colour=name_to_rgb("red"), back_colour=name_to_rgb("black"))
                    GPIO.output(BLOCKAGE_LED_GPIO, LED_ON)
                    BLOCKAGE_COUNT += 1
                    time.sleep(1)           # wait 
                else:
                    GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)
                    BLOCKAGE_COUNT = 0

                BAD_VALVE_COUNT = check_overcurrent()
                run_button = 1
                run_button = GPIO.input(RUN_GPIO)

# turn off the pump and valve
            GPIO.output(PUMP_GPIO, PUMP_OFF)
            GPIO.output(VALVE_GPIO, VALVE_OFF)

            if (LEAK_COUNT != 0):
                GPIO.output(LEAK_LED_GPIO, LED_ON)
                print ("WARNING! Zone 1 exceeding flow limit - possible leak.")
                sense.show_message("LK!", text_colour=name_to_rgb("red"), back_colour=name_to_rgb("black"))
                time.sleep(1)           # wait 

            if (BLOCKAGE_COUNT != 0):
                GPIO.output(BLOCKAGE_LED_GPIO, LED_ON)
                print ("WARNING! Zone 1 below flow limit - possible blockage.")
                sense.show_message("BL!", text_colour=name_to_rgb("red"), back_colour=name_to_rgb("black"))
                time.sleep(1)           # wait 

        else:
            print ("Zone 1 is off")
# turn off the pump and valve
            GPIO.output(PUMP_GPIO, PUMP_OFF)
            GPIO.output(VALVE_GPIO, VALVE_OFF)

            sense.clear
            GPIO.output(BAD_VALVE_LED_GPIO, LED_OFF)
            BAD_VALVE_COUNT = 0
            GPIO.output(LEAK_LED_GPIO, LED_OFF)
            LEAK_COUNT = 0
            GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)
            BLOCKAGE_COUNT = 0
            time.sleep(1)           # wait

#            GPIO.output(BAD_VALVE_LED_GPIO, LED_ON)
#            GPIO.output(LEAK_LED_GPIO, LED_ON)
#            GPIO.output(BLOCKAGE_LED_GPIO, LED_ON)
            
        
except KeyboardInterrupt:
    sense.clear
    GPIO.output(PUMP_GPIO, PUMP_OFF)
    GPIO.output(VALVE_GPIO, VALVE_OFF)
    GPIO.output(BAD_VALVE_LED_GPIO, LED_OFF)
    GPIO.output(LEAK_LED_GPIO, LED_OFF)
    GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)
#    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
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
GPIO.output(BAD_VALVE_LED_GPIO, LED_OFF)
GPIO.output(LEAK_LED_GPIO, LED_OFF)
GPIO.output(BLOCKAGE_LED_GPIO, LED_OFF)
#GPIO.cleanup()       # clean up GPIO on normal exit

