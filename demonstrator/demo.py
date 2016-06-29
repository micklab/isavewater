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

# for graphics
from webcolors import name_to_rgb
import pygame
from pygame.locals import *

# Global variables
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
    logging.debug('daemon valve # '+str(valve_number)+' running: spi='+str(spi_addr))
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
        time.sleep(0.1)
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

FLOW_NOMINAL = 1.5      #LPM
FLOW_TOLERANCE = 30.0   # %
PUMP_NOMINAL = 1200.0   #ma
PUMP_TOLERANCE = 30.0   # %
VALVE_NOMINAL = 200.0   #ma
VALVE_TOLERANCE = 30.0   # %

VALVE_ON = 0
VALVE_OFF = 1
RELAY_PUMP_GPIO = 22        # GPIO pin #
GPIO.setup(RELAY_PUMP_GPIO, GPIO.OUT)
GPIO.output(RELAY_PUMP_GPIO, VALVE_OFF)

RELAY_VALVE_GPIO = 23        # GPIO pin #
GPIO.setup(RELAY_VALVE_GPIO, GPIO.OUT)
GPIO.output(RELAY_VALVE_GPIO, VALVE_OFF)

RELAY_X_GPIO = 18        # GPIO pin #
GPIO.setup(RELAY_X_GPIO, GPIO.OUT)
GPIO.output(RELAY_X_GPIO, VALVE_OFF)

RELAY_Y_GPIO = 27        # GPIO pin #
GPIO.setup(RELAY_Y_GPIO, GPIO.OUT)
GPIO.output(RELAY_Y_GPIO, VALVE_OFF)

# this is a queue that keeps a list of the most recent measurements
flowq = deque(maxlen = 1)

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
        None
#        self.flow.clear()
##        for i,value in enumerate(self.flow):
##            if value>FLOW_NOMINAL:
##                remove(value)
##                index=i
        
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
        None
#        current_queue.clear()
##        for i,value in enumerate(current_queue):
##            if value>VALVE_NOMINAL:
##                remove(value)
##                index=i
        
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

    NUMBER_OF_VALVES = 2
    VALVE_OFF = 0
    VALVE_ON = 1
    VALVE_POWER_GPIOS = [6, 5]     # GPIO pins assigned to valves
    VALVE_CURRENT_SPI_ADDR = [0, 1]  # SPI addresses assigned to valve current meters

    VALVE_CURRENT_QUEUE_SIZE = 50

    VALVE_NUMBER = 0
    VALVE_STATUS = 1
    VALVE_GPIO = 2
    VALVE_SPI = 3
    
    try:
# Init graphics        
        pygame.init()
        FONT_VALUES = pygame.font.Font(None, 48)
        FONT_DESCRIPTION_HEAD = pygame.font.Font(None, 36)
        FONT_DESCRIPTION_BODY = pygame.font.Font(None, 24)
        pygame.display.set_caption('Internet of Things Project')

# init flow sensor
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
        

        # start the sensor daemons
        measure_flow_1.start()
        # start the valve daemons

# graphics display
        SCREEN_DIMENSIONS = [800, 800]  # setup window [0]= width [1]= height
        event = pygame.event.poll()
        if event.type == VIDEORESIZE:
            xSize = event.dict['size'][0]
            ySize = event.dict['size'][1]
            SCREEN_DIMENSIONS = pygame.display.set_mode((xSize, ySize), HWSURFACE|DOUBLEBUF|RESIZABLE)
        # initialize the location of the message area
        SCREEN_DISPLAY = pygame.display.set_mode(SCREEN_DIMENSIONS)
        # Description area
        DESCRIPTION_AREA =  (0, 0, SCREEN_DIMENSIONS[0], SCREEN_DIMENSIONS[1])  # (left, top, width, height)
        SCREEN_DISPLAY.fill(name_to_rgb('black'), DESCRIPTION_AREA)
        # Header
        DESCRIPTION_HEAD_XY =    (SCREEN_DIMENSIONS[0]/2, 25)   # centered
        SCREEN_TEXT = FONT_DESCRIPTION_HEAD.render("Internet of Things Raspberry Pi Irrigation System", 1, name_to_rgb('white'))
        txtpos = SCREEN_TEXT.get_rect()
        txtpos.center = DESCRIPTION_HEAD_XY
        SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
        # Body
        DESCRIPTION_BODY_XY =    (SCREEN_DIMENSIONS[0]/2, 50)   # centered
        SCREEN_TEXT = FONT_DESCRIPTION_BODY.render("Controls valves, detects Leaks, detects broken wires, cloud connected", 1, name_to_rgb('LightGreen'))
        txtpos = SCREEN_TEXT.get_rect()
        txtpos.center = DESCRIPTION_BODY_XY
        SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
        # Header
        DESCRIPTION_HEAD_XY =    (SCREEN_DIMENSIONS[0]/2, 100)   # centered
        SCREEN_TEXT = FONT_DESCRIPTION_HEAD.render("DEMONSTRATION MODE", 1, name_to_rgb('LightGreen'))
        txtpos = SCREEN_TEXT.get_rect()
        txtpos.center = DESCRIPTION_HEAD_XY
        SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
# update the screen
        pygame.display.update()

        #############
        #### Start of Main Loop
        #############

        loop = 0    # used to determine the first time through each valve_status change
        current = [0.0, 0.0]
        system = 0  # 0 = off
        MAX_ELAPSED_TIME_ON = 20    # in seconds
        MAX_ELAPSED_TIME_OFF = 10    # in seconds
        
        while True:         #Demo loop

            if (system == 0):
                GPIO.output(RELAY_VALVE_GPIO, VALVE_ON)
                GPIO.output(RELAY_PUMP_GPIO, VALVE_ON)
                # work out elapsed time                                                       
                system = 1
            else:
                GPIO.output(RELAY_VALVE_GPIO, VALVE_OFF)
                GPIO.output(RELAY_PUMP_GPIO, VALVE_OFF)
                # work out elapsed time                                                       
                system = 0
                
            # note start time
            start_time = time.time()                                                        
            # note end time
            end_time = time.time()
            elapsed_time = (end_time - start_time)

            while ((system == 0 and elapsed_time < MAX_ELAPSED_TIME_ON) or (system == 1 and elapsed_time < MAX_ELAPSED_TIME_OFF)):     # Measure loop
                time.sleep(3)                      # let the queues fill with values

                for v in range(NUMBER_OF_VALVES):
                    valve_status = valve_power_object[v].get_status()
                    if (valve_status == 0 and loop == 0):    #first time valve turns on
                        print "clearing queue "+str(v)
                        valve_current_object[v].clear_queue
                        flow_sensor_1.clear_queue
                        loop = 1
                    elif (valve_status == 1 and loop == 1):    #first time valve turns off
                        print "clearing queue "+str(v)
                        valve_current_object[v].clear_queue
                        flow_sensor_1.clear_queue
                        loop = 0

                    flow = flow_sensor_1.get_rate()
                    current[v] = valve_current_object[v].get_current()
                    print 'V['+str(v)+','+str(valve_status)+']:F[{:4.4f}'.format(flow)+']:C[{:7.1f}'.format(current[v])+']:T['+str(datetime.datetime.now())+']'

                DESCRIPTION_AREA =  (0, 140, SCREEN_DIMENSIONS[0], SCREEN_DIMENSIONS[1])  # (left, top, width, height)
                SCREEN_DISPLAY.fill(name_to_rgb('black'), DESCRIPTION_AREA)

                # Timer display
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 200)   # centered
                if (system == 0):
                    SCREEN_TEXT = FONT_VALUES.render("System OFF in %02.1f seconds"%(MAX_ELAPSED_TIME_ON-elapsed_time), 1, name_to_rgb('Gold'))
                else:
                    SCREEN_TEXT = FONT_VALUES.render("System ON in %02.1f seconds"%(MAX_ELAPSED_TIME_OFF-elapsed_time), 1, name_to_rgb('Gold'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)

                # Sprinkler Valve display
                if (valve_power_object[0].get_status() == 0):
                    SPRINKLER_STATE = " ON"
                else:
                    SPRINKLER_STATE = "OFF"
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 500)   # centered
                SCREEN_TEXT = FONT_VALUES.render("Sprinkler valve: "+SPRINKLER_STATE+" Current = %06.1f milliamps"%current[0], 1, name_to_rgb('LightSkyBlue'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 530)   # centered
                if (current[0] < 200.0):
                    SCREEN_TEXT = FONT_VALUES.render("LOW CURRENT - Possible broken wire", 1, name_to_rgb('Red'))
                elif (current[0] > 400.0):
                    SCREEN_TEXT = FONT_VALUES.render("HIGH CURRENT - Possible shorted wire or device", 1, name_to_rgb('Red'))
                else:
                    SCREEN_TEXT = FONT_VALUES.render("Current is nominal", 1, name_to_rgb('Green'))
                if (SPRINKLER_STATE == "OFF"):
                    SCREEN_TEXT = FONT_VALUES.render("Sprinkler valve is off", 1, name_to_rgb('Gray'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)

                # Flow display
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 300)   # centered
                SCREEN_TEXT = FONT_VALUES.render("Flow rate = %02.4f liters/minute"%flow, 1, name_to_rgb('LightSkyBlue'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 330)   # centered
                if (flow < 1.0):
                    SCREEN_TEXT = FONT_VALUES.render("LOW FLOW - Possible blockage", 1, name_to_rgb('Red'))
                elif (flow > 2.0):
                    SCREEN_TEXT = FONT_VALUES.render("HIGH FLOW - Possible leak", 1, name_to_rgb('Red'))
                else:
                    SCREEN_TEXT = FONT_VALUES.render("Flow is nominal", 1, name_to_rgb('Green'))
                if (SPRINKLER_STATE == "OFF"):
                    SCREEN_TEXT = FONT_VALUES.render("Sprinkler valve is off", 1, name_to_rgb('Gray'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
                    
                # Pump display
                if (valve_power_object[1].get_status() == 0):
                    PUMP_STATE = " ON"
                else:
                    PUMP_STATE = "OFF"
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 400)   # centered
                SCREEN_TEXT = FONT_VALUES.render("     Pump state: "+PUMP_STATE+" Current = %06.1f milliamps"%current[1], 1, name_to_rgb('LightSkyBlue'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)
                DESCRIPTION_FLOW_XY =    (SCREEN_DIMENSIONS[0]/2, 430)   # centered
                if (current[1] < 1000.0):
                    SCREEN_TEXT = FONT_VALUES.render("LOW CURRENT - Possible broken wire", 1, name_to_rgb('Red'))
                elif (current[1] > 1500.0):
                    SCREEN_TEXT = FONT_VALUES.render("HIGH CURRENT - Possible shorted wire or device", 1, name_to_rgb('Red'))
                else:
                    SCREEN_TEXT = FONT_VALUES.render("Current is nominal", 1, name_to_rgb('Green'))
                if (PUMP_STATE == "OFF"):
                    SCREEN_TEXT = FONT_VALUES.render("Pump is off", 1, name_to_rgb('Gray'))
                txtpos = SCREEN_TEXT.get_rect()
                txtpos.center = DESCRIPTION_FLOW_XY
                SCREEN_DISPLAY.blit(SCREEN_TEXT, txtpos)

        # update the screen
                pygame.display.update()

                # note end time
                end_time = time.time()
                # work out elapsed time                                                       
                elapsed_time = (end_time - start_time)
                print ("Elapsed time = "+str(elapsed_time))
   
###########################################################
# END
###########################################################
    except KeyboardInterrupt:
        GPIO.output(RELAY_VALVE_GPIO, VALVE_ON)
        GPIO.output(RELAY_PUMP_GPIO, VALVE_ON)
        GPIO.output(RELAY_X_GPIO, VALVE_ON)
        GPIO.output(RELAY_Y_GPIO, VALVE_ON)
        pi.stop()   # Disconnect from Pi.
        exit()

    except:
        GPIO.output(RELAY_VALVE_GPIO, VALVE_ON)
        GPIO.output(RELAY_PUMP_GPIO, VALVE_ON)
        GPIO.output(RELAY_X_GPIO, VALVE_ON)
        GPIO.output(RELAY_Y_GPIO, VALVE_ON)

    # normal exit
