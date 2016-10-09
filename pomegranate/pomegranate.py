#! /usr/bin/python
"""
Isavewater controller
- measures water flow
- measures valve current
Created 6/03/16 by Greg Griffes  
"""
import RPi.GPIO as GPIO
import time, sys, os
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import spidev
import Adafruit_ADS1x15
from collections import deque
import threading
import logging
import datetime

global flow_count
flow_count = 0

# Provides a logging solution for troubleshooting
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')

# -----------------------------------
# setup the daemon that measures valve current
# -----------------------------------
# this daemon is a background process that runs continuously makes current measurements
# and fills the queue with current measurements. 
def daemon_valve(valve_number, spi_addr):
#    logging.debug('daemon valve # '+str(valve_number)+' running: spi='+str(spi_addr))
    spi = spidev.SpiDev()
    spi.open(0,spi_addr)
    x = 1
    while True:
        response = spi.readbytes(2)
        lsb = response[1]
        msb = response[0]
        pmod_value = (msb << 8) | lsb
        adc_value_norm = pmod_value - 2048
        ma = float((1000.0 * float(adc_value_norm)) / 89.95)
#        logging.debug('valve['+str(valve_number)+'] = {:5.1f}'.format(ma) + ' ma')
        current_queue[valve_number].append(ma)
    # this has to happen fairly quickly because the measurements vary wildly.
    # the most important measurement is the maximum positive value which corresponds
    # to the actual current measurement and appears about once every 50 - 100 measurements
        time.sleep(0.005)
#        logging.debug(current_queue[valve_number])

# -----------------------------------
# setup the daemon that measures flow
# -----------------------------------
GPIO.setmode(GPIO.BCM)  # set GPIO to use BCM pin numbers
GPIO.setwarnings(False) # warnings off

# this daemon is a background process that runs continuously makes flow measurements

# Constants
FLOW_GPIO = 19               # GPIO pin #
GPIO.setup(FLOW_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

RELAY_PUMP_GPIO = 27        # GPIO pin #
GPIO.setup(RELAY_PUMP_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
RELAY_VALVE_GPIO = 18        # GPIO pin #
GPIO.setup(RELAY_VALVE_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
RELAY_X_GPIO = 22        # GPIO pin #
GPIO.setup(RELAY_X_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
RELAY_Y_GPIO = 23        # GPIO pin #
GPIO.setup(RELAY_Y_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# this is a queue that keeps a list of the most recent measurements
flowq = deque(maxlen = 5)

# this establishes a global variable that counts edges from the flow meter
# when an edge occurs, it generates an interrupt that calls this function
# Use it by setting the global variable to 0 then wait one second and look
# at the count. That is ticks per second which can be converted to gallons per minute.
flow_count = 0
def flow_callback(gpio, level, tick):
    global flow_count
    flow_count += 1

# Initialize
pi = pigpio.pi()           # Connect to Pi.
cb = pi.callback(FLOW_GPIO, pigpio.FALLING_EDGE, flow_callback) # interrupt mechanism

def daemon_flow_1():

    global flow_count

    logging.debug('Starting daemon_flow_1')

    while True:
        flow_count = 0
#        print ("Checking flow")
        time.sleep(1)   # wait as the interrupts accumulate and increase the flow count
        flowq.append(flow_count)
#        print flowq
#        print ("flow count (daemon) = ", str(flow_count))

# create the thread and make it a daemon (doesn't block the main program calling it)
measure_flow_1 = threading.Thread(name='daemon_flow_1', target=daemon_flow_1)
measure_flow_1.setDaemon(True)

##########################
class flow_sensor(object):
##########################

    def __init__(self, flow_zone, flow_queue):
        self.flow_zone = flow_zone
        self.flow = flow_queue
      
    def __del__(self):
        print 'flow '+str(self.flow_zone)+' closed'

    def clear_queue(self):
        self.flow.clear()
        
    def flow_calculator (self, freq):
        LPM2GPM = 0.264172  # Liters per minute to gallons per minute factor
    #    return (LPM2GPM*(freq/5.5))    # in GPM
        return float(freq/5.5)               # in LPM

    def get_rate(self):

# find the maximum value in the set of measurements
        max_value=0
        for i,value in enumerate(self.flow):
            if value>max_value:
                max_value=value
                index=i

        return float(self.flow_calculator(max_value))

############################
class valve_current(object):
############################

    def __init__(self, valve_zone):

        self.valve_zone = valve_zone
        
    def __del__(self):
        print 'valve current '+str(self.valve_zone)+' closed'

    def clear_queue(self):
        self.current.clear()
        
    def get_current(self):

# find the maximum value in the set of measurements
        max_value=-6000.0
        for i,value in enumerate(current_queue[self.valve_zone]):
            if value>max_value:
                max_value=value
                index=i
#        max_value = max(self.current_list) # this doesn't work returning the error "float object is not callable"

#        print current_queue[self.valve_zone]

        return max_value

##########################
class valve_power(object):
##########################

    def __init__(self, valve_zone, valve_gpio):
        self.valve_gpio = valve_gpio
        self.valve_zone = valve_zone

        print 'valve '+str(valve_zone)+' status GPIO # =  '+str(self.valve_gpio)
        
        GPIO.setup(self.valve_gpio, GPIO.IN)
      
# Done with initialization
                    
    def __del__(self):
        print 'valve '+str(self.valve_zone)+' closed'

    def get_status(self):
        return GPIO.input(self.valve_gpio)


###############################################################
# Main program
###############################################################
if __name__ == '__main__':

    NUMBER_OF_VALVES = 1
    VALVE_OFF = 0
    VALVE_ON = 1
    VALVE_POWER_GPIOS = [6, 5]     # GPIO pins assigned to valves
    VALVE_CURRENT_SPI_ADDR = [0, 1]  # SPI addresses assigned to valve current meters

    VALVE_CURRENT_QUEUE_SIZE = 200

    VALVE_NUMBER = 0
    VALVE_STATUS = 1
    VALVE_GPIO = 2
    VALVE_SPI = 3
    
    try:
        
        flow_sensor_1 = flow_sensor(1, flowq)

        # create the data structures
        valves = []
        current_queue = []
        for v in range(NUMBER_OF_VALVES):
            valves.append([v, VALVE_OFF, VALVE_POWER_GPIOS[v], VALVE_CURRENT_SPI_ADDR[v]])   # valve number, valve status, GPIO pin for valve status, SPI address for valve current
            # this is a queue that keeps a list of the most recent measurements
            current_queue.append(deque(maxlen = VALVE_CURRENT_QUEUE_SIZE))

        logging.debug('valves[] = '+str(valves))
        
        # create the objects
        valve_power_object = []
        valve_current_object = []
        for v in range(NUMBER_OF_VALVES):
            valve_power_object.append(valve_power(v, valves[v][VALVE_GPIO]))
            valve_current_object.append(valve_current(v))

        # create the current measurement daemons
        for v in range(NUMBER_OF_VALVES):
            # create the thread and make it a daemon (doesn't block the main program calling it)
#            logging.debug('creating daemon for valve '+str(v))
            valve_current_daemon = threading.Thread(name='daemon_valve', target=daemon_valve, args=(v, valves[v][VALVE_SPI]))
#            logging.debug('setting daemon for valve '+str(v))
            valve_current_daemon.setDaemon(True)
#            logging.debug('starting daemon for valve '+str(v))
            valve_current_daemon.start()
        

        loop = 0    # used to determine the first time through each valve_status change
        current = 0.0

        # start the sensor daemons
        measure_flow_1.start()
        # start the valve daemons

        #############
        #### Start of Main Loop
        #############

        while True:
            time.sleep(10)                      # let the queues fill with values

            for v in range(NUMBER_OF_VALVES):
                valve_status = valve_power_object[v].get_status()
                if (valve_status == 0 and loop == 0):    #first time valve turns on
                    valve_current_object[v].clear_queue
                    flow_sensor_1.clear_queue
                    loop = 1
                elif (valve_status == 1 and loop == 1):    #first time valve turns off
                    valve_current_object[v].clear_queue
                    flow_sensor_1.clear_queue
                    loop = 0

                flow = flow_sensor_1.get_rate()
                current = valve_current_object[v].get_current()

                print 'V['+str(v)+','+str(valve_status)+']:F[{:4.4f}'.format(flow)+']:C[{:7.1f}'.format(current)+']:T['+str(datetime.datetime.now())+']'
   
###########################################################
# END
###########################################################
    except KeyboardInterrupt:
        pi.stop()   # Disconnect from Pi.
        exit()

#    except:

    # normal exit
