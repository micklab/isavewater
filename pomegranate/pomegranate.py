#! /usr/bin/python
"""
Created 3/22/16 by Greg Griffes based on the hackster.io rover pages at
https://www.hackster.io/peejster/rover-c42139 
"""
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import spidev
import Adafruit_ADS1x15
from collections import deque

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

#        print 'flow GPIO # =  '+str(self.flow_gpio)
        
# Done with initialization
                    
    def __del__(self):
        cb.cancel() # Cancel callback.
        pi.stop()   # Disconnect from Pi.
        print 'flow '+str(self.flow_zone)+' closed'

    def flow_callback(self, gpio, level, tick):
        global flow_count
        flow_count += 1

    def flow_calculator (self, freq):
        LPM2GPM = 0.264172  # Liters per minute to gallons per minute factor
    #    return (LPM2GPM*(freq/5.5))    # in GPM
        return float(freq/5.5)               # in LPM

    def get_rate(self):

        global flow_count
        flow_count = 0
#        print ("Checking flow")
        time.sleep(1)   # wait as the interrupts accumulate and increase the flow count
#        print ("flow count = ", str(flow_count))

        return float(self.flow_calculator(flow_count))

############################
class valve_current(object):
############################

    def __init__(self, valve_zone):

        self.valve_zone = valve_zone
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        
        self.adc = Adafruit_ADS1x15.ADS1115()
        # Choose a gain of 1 for reading voltages from 0 to 4.09V.
        # Or pick a different gain to change the range of voltages that are read:
        #  - 2/3 = +/-6.144V
        #  -   1 = +/-4.096V
        #  -   2 = +/-2.048V
        #  -   4 = +/-1.024V
        #  -   8 = +/-0.512V
        #  -  16 = +/-0.256V
        # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
        self.GAIN = 1

# this is a queue that keeps a list of the most recent measurements
        self.current = deque(maxlen = 200)

    def clear_queue(self):
        self.current.clear()
        
    def calculate_milliamps(self, adc_value):
        adc_value_norm = adc_value - 2048
        return float((1000.0 * float(adc_value_norm)) / 89.95)

    def get_current(self):

##        print('Reading ADS1x15 values, press Ctrl-C to quit...')
##        # Print nice channel column headers.
##        print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*range(4)))
##        print('-' * 37)
##        # Main loop.
##        while True:
##            # Read all the ADC channel values in a list.
##            values = [0]*4
##            for i in range(4):
##                # Read the specified ADC channel using the previously set gain value.
##                values[i] = self.adc.read_adc(i, gain=self.GAIN)
##                # Note you can also pass in an optional data_rate parameter that controls
##                # the ADC conversion time (in samples/second). Each chip has a different
##                # set of allowed data rate values, see datasheet Table 9 config register
##                # DR bit values.
##                #values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
##                # Each value will be a 12 or 16 bit signed integer value depending on the
##                # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
##            # Print the ADC values.
##            print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))
##            time.sleep(0.1)
        count = 0
        max = 0.0
        min = 0.0
#        while count < 50:
        response = self.spi.readbytes(2)
        #print response
        lsb = response[1]
        msb = response[0]
        #print hex(msb)
        #print hex(lsb)
        pmod_value = (msb << 8) | lsb
        ma = self.calculate_milliamps(pmod_value)
        self.current.append(ma)

# find the maximum value in the set of measurements
        max_value=0
        for i,value in enumerate(self.current):
            if value>max_value:
                max_value=value
                index=i
#        max_value = max(self.current_list) # this doesn't work returning the error "float object is not callable"

#        print max_value

        return max_value

##########################
class valve_power(object):
##########################

    def __init__(self, valve_zone, valve_gpio):
        self.valve_gpio = valve_gpio
        self.valve_zone = valve_zone

        GPIO.setup(self.valve_gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      
#        print 'valve status GPIO # =  '+str(self.valve_gpio)
        
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
    current = 0.0

    #############
    #### Start of Main Loop
    #############
    try:
        loop = 0
        valve_current_1.clear_queue()
        while True:
            time.sleep(10)
            valve_status = valve_power_1.get_status()
            if (valve_status == 1):
                flow = flow_sensor_1.get_rate()
                current = valve_current_1.get_current()
                print 'Flow rate = {:2.1f}'.format(flow), 'lpm and valve current = {:5.1f}'.format(current)
                loop = 0
            else:
                if loop == 0:
                    valve_current_1.clear_queue()
                    print "Waiting for valve to turn on"
                    loop = 1


    except KeyboardInterrupt:
        exit()

#    except:

    # normal exit
