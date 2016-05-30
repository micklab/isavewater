#! /usr/bin/python
"""
Created 3/22/16 by Greg Griffes based on the hackster.io rover pages at
https://www.hackster.io/peejster/rover-c42139 
"""
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html

# Add the directory containing your module to the Python path (wants absolute paths)
#scriptpath = "/home/pi/projects/Adafruit-Raspberry-Pi-Python-Code/Adafruit_ADS1x15"
#sys.path.append(os.path.abspath(scriptpath))
#
# Install using this:
# sudo apt-get update
# sudo apt-get install -y python3 python3-pip python-dev
# sudo pip3 install rpi.gpio
# sudo pip install adafruit-ads1x15
# Import the ADS1x15 module.
import Adafruit_ADS1x15

global flow_count
flow_count = 0

##########################
class flow_sensor(object):
##########################

    def __init__(self, flow_zone, flow_gpio):
        self.flow_gpio = flow_gpio
        self.flow_zone = flow_zone
      
        GPIO.setup(self.flow_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Initialize
        pi = pigpio.pi()           # Connect to Pi.
        cb = pi.callback(self.flow_gpio, pigpio.FALLING_EDGE, self.flow_callback) # interrupt mechanism

        print 'flow GPIO # =  '+str(self.flow_gpio)
        
# Done with initialization
                    
    def __del__(self):
        print 'flow '+str(self.flow_zone)+' closed'

    def flow_callback(self):
        global flow_count
        flow_count += 1

    def flow_calculator (self, freq):
        LPM2GPM = 0.264172  # Liters per minute to gallons per minute factor
    #    return (LPM2GPM*(freq/5.5))    # in GPM
        return (freq/5.5)               # in LPM

    def get_rate(self):

        global flow_count
        print ("Checking flow")
        flow_count = 0
        time.sleep(1)   # wait as the interrupts accumulate and increase the flow count 
        return int(self.flow_calculator(flow_count))

############################
class valve_current(object):
############################

    def __init__(self, valve_zone):

        self.valve_zone = valve_zone

        # Initialize the Analog to Digital converter for reading the current sensor
        self.ADS1015 = 0x00  # 12-bit ADC
        self.ADS1115 = 0x01	# 16-bit ADC

        # Select the gain
        # gain = 6144  # +/- 6.144V
        self.gain = 4096  # +/- 4.096V
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
        self.sps = 250  # 250 samples per second
        # sps = 475  # 475 samples per second
        # sps = 860  # 860 samples per second

        # Initialise the ADC using the default mode (use default I2C address)
        # Set this to ADS1015 or ADS1115 depending on the ADC you are using!

        #DISTANCE_HANDLE = ADS1x15(ic=ADS1115)

    def get_current(self):
        self.current = 0.0

        print 'valve current = '+str(self.current)+' in amps'
        return self.current

##########################
class valve_power(object):
##########################

    def __init__(self, valve_zone, valve_gpio):
        self.valve_gpio = valve_gpio
        self.valve_zone = valve_zone

        GPIO.setup(self.valve_gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      
        print 'valve status GPIO # =  '+str(self.valve_gpio)
        
# Done with initialization
                    
    def __del__(self):
        print 'valve '+str(self.valve_zone)+' closed'

    def get_status(self):
        return GPIO.input(self.valve_gpio)


###############################################################
# Main program
###############################################################
if __name__ == '__main__':

    GPIO.setmode(GPIO.BCM)  # set GPIO to use BCM pin numbers
    GPIO.setwarnings(False) # warnings off

    # Constants
    FLOW_GPIO = 6               # GPIO pin #
    flow_sensor_1 = flow_sensor(1, FLOW_GPIO)

    VALVE_1_POWER_GPIO = 27     # GPIO pin #
    valve_power_1 = valve_power(1, VALVE_1_POWER_GPIO)

    valve_current_1 = valve_current(1)

    #############
    #### Start of Main Loop
    #############
    try:
        print("Turn on the PUMP/MV switch when ready\n>")        
        while True:

            print("Valve power status = ", str(valve_power_1.get_status()))        
        #            if (valve_power_1.get_status == 1):

        # check for Over Current condition on valve

            print("Valve current = ", str(valve_current_1.get_current()))        
        #            if (valve_current_1.get_current >= 0.0):

        # get the flow rate
            print("Flow rate = ", str(flow_sensor_1.get_rate()))        
        #            if (flow_sensor_1.get_rate >= 0.0):

            time.sleep(0.5)
            
    except KeyboardInterrupt:
        cb.cancel() # Cancel callback.
        pi.stop()   # Disconnect from Pi.
        exit()

#    except:

    # normal exit
