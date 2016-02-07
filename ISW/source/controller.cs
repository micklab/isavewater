using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Collections.Concurrent;
using Windows.System.Threading;
using Windows.Devices.Gpio;

namespace ISaveWater
{
    class Controller
    {
        private BlockingCollection<string> incoming_queue = new BlockingCollection<string>();
        private ThreadPoolTimer _timer;
        private Func<string, int> _callback;
        private GpioController _gpio_controller;
        private List<Area> _areas;

        private const int ZONE_1 = 5;
        private const int FLOW_1 = 6;
        private const int OC_1 = 13;

        public Controller(Func<string, int> callback)
        {
            _callback = callback;
            _timer = ThreadPoolTimer.CreatePeriodicTimer(Timer_Tick, TimeSpan.FromMilliseconds(5000));

            _gpio_controller = GpioController.GetDefault();

            // Create the Area(s)
            _areas = new List<Area>() { new Area( "Area 1",
                                                  new List<Zone>() { new Zone("Zone 1", _gpio_controller.OpenPin(ZONE_1)) },
                                                  new Flow("Flow 1", _gpio_controller.OpenPin(FLOW_1)),
                                                  new OverCurrent("OC 1", _gpio_controller.OpenPin(OC_1)),
                                                  callback )};
        }

        public void Start()
        {
            Task.Run(() => MessageHandler());
            foreach (var area in _areas)
            {
                area.Start();
            }
        }

        public void SendMessage(string message)
        {
            Debug.WriteLine("Controller: adding message to queue\n");
            incoming_queue.Add(message);
        }

        private async Task MessageHandler()
        {
            Debug.WriteLine("Controller: starting message handler");

            while (true)
            {
                var data = incoming_queue.Take();
                Debug.WriteLine("Controller: received message from Azure - " + data);

                // Parse the message
                Debug.WriteLine("\tParsing message");

                // The message can either be a "command" message or a "schedule" message
                // If the message is a "command" it will be in the form:
                //      <override>:<area>:on
                //      <override>:<area>:off
                // If the message is a "schedule" it will be in the form:
                //      <schedule>:<area>:<action>:<date-time>:<duration>
                //      where <action> can be "ADD", "DEL", "CHG"
                Debug.WriteLine("\tMessage is either command or schedule");

                var result = data.Split(':');
                var command = result[0];
                var location = result[1];
                var action = result[2];
                Debug.WriteLine("\tCommand: " + command);
                Debug.WriteLine("\tLocation: " + location);
                Debug.WriteLine("\tAction: " + action);

                // Dispatch the message
                // Use <area> to identify the correct grove object
                // Execute the command
                //    if <area>:on then area.Activate
                //    if <area>:off then area.Deactivate
                //    if <area>:<action>:<date-time>:<duration> then area.AddScheduleEvent(<action>:<date-time>:<duration>
                Debug.WriteLine("\tDispatching message to grove");

                bool match = false;
                foreach (var area in _areas)
                {
                    if (area.Id().ToLower() == location.ToLower())
                    {
                        match = true;

                        if (action.ToLower() == "on")
                        {
                            area.Activate();
                        }
                        if (action.ToLower() == "off")
                        {
                            area.Deactivate();
                        }
                    }
                }

                if (!match)
                {
                    Debug.WriteLine("No matching area " + location + " found");
                }

                await Task.Delay(1000);
            }
        }

        private void Timer_Tick(ThreadPoolTimer timer)
        {
            foreach (var area in _areas)
            {
                _callback(area.Status());
            }
        }

    }
}
