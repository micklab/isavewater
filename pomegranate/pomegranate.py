#! /usr/bin/python
"""
Created 3/22/16 by Greg Griffes based on the hackster.io rover pages at
https://www.hackster.io/peejster/rover-c42139 
"""
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import spidev

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
        cb.cancel() # Cancel callback.
        pi.stop()   # Disconnect from Pi.
        print 'flow '+str(self.flow_zone)+' closed'

    def flow_callback(self, gpio, level, tick):
        global flow_count
        flow_count += 1

    def flow_calculator (self, freq):
        LPM2GPM = 0.264172  # Liters per minute to gallons per minute factor
    #    return (LPM2GPM*(freq/5.5))    # in GPM
        return (freq/5.5)               # in LPM

    def get_rate(self):

        global flow_count
        flow_count = 0
        print ("Checking flow")
        time.sleep(1)   # wait as the interrupts accumulate and increase the flow count
        print ("flow count = ", str(flow_count))

        return int(self.flow_calculator(flow_count))

############################
class valve_current(object):
############################

    def __init__(self, valve_zone):

        self.valve_zone = valve_zone
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)

    def calculate_milliamps(self, adc_value):
        adc_value_norm = adc_value - 2048
        return float((1000.0 * float(adc_value_norm)) / 89.95)

    def get_current(self):
        self.current = 0.0

        while True:
            response = self.spi.readbytes(2)
            print response
            lsb = response[1]
            msb = response[0]
            print hex(msb)
            print hex(lsb)
            pmod_value = (msb << 8) | lsb
            print hex(pmod_value)
            print self.calculate_milliamps(pmod_value)
            time.sleep(1)

#        print 'valve current = '+str(self.current)+' in amps'
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
        exit()

#    except:

    # normal exit
