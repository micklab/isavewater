using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Collections.Concurrent;
using Windows.System.Threading;
using Windows.Devices.Gpio;
using Newtonsoft.Json;

namespace ISaveWater
{

    class Controller
    {
        private BlockingCollection<string> incoming_queue = new BlockingCollection<string>();
        private ThreadPoolTimer _timer;
        private Func<string, int> _callback;
        private GpioController _gpio_controller;
        private List<Area> _areas;

        private const int ZONE_1 = 26;
        private const int ZONE_2 = 19;
        private const int ZONE_3 = 13;
        private const int ZONE_4 = 20;
        private const int ZONE_5 = 21;
        private const int FLOW_1 = 6;
        private const int FLOW_2 = 5;
        private const int OC_1 = 16;
        private const int OC_2 = 12;

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
            
            /*
            _areas = new List<Area>() { new Area( "Area 1",
                                                  new List<Zone>() { new Zone("Zone 1", _gpio_controller.OpenPin(ZONE_1)),
                                                                     new Zone("Zone 2", _gpio_controller.OpenPin(ZONE_2)),
                                                                     new Zone("Zone 3", _gpio_controller.OpenPin(ZONE_3))
                                                                   },
                                                  new Flow("Flow 1", _gpio_controller.OpenPin(FLOW_1)),
                                                  new OverCurrent("OC 1", _gpio_controller.OpenPin(OC_1)),
                                                  callback ),
                                        new Area( "Area 2",
                                                  new List<Zone>() { new Zone("Zone 4", _gpio_controller.OpenPin(ZONE_4)),
                                                                     new Zone("Zone 5", _gpio_controller.OpenPin(ZONE_5))
                                                                   },
                                                  new Flow("Flow 2", _gpio_controller.OpenPin(FLOW_1)),
                                                  new OverCurrent("OC 2", _gpio_controller.OpenPin(OC_1)),
                                                  callback )
                                     };
            */
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
                var json = incoming_queue.Take();
                Debug.WriteLine("Controller: received message from Azure - " + json);

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

                //var result = data.Split(':');
                //var command = result[0];
                //var location = result[1];
                //var action = result[2];
                //Debug.WriteLine("\tCommand: " + command);
                //Debug.WriteLine("\tLocation: " + location);
                //Debug.WriteLine("\tAction: " + action);

                // Dispatch the message
                // Use <area> to identify the correct grove object
                // Execute the command
                //    if <area>:on then area.Activate
                //    if <area>:off then area.Deactivate
                //    if <area>:<action>:<date-time>:<duration> then area.AddScheduleEvent(<action>:<date-time>:<duration>
                Debug.WriteLine("\tDispatching message to grove");

                /*
                 What does the JSON  look like coming from Azure?

                    Manual command
                    {
                        "command" : "manual",
                        "action" : "",
                        "data" :
                        {
                            "area" : "Area 1",
                            "state" : "on|off"
                        }
                    }

                    Schedule command
                    {
                        "command" : "schedule",
                        "action"  : "clear|add"
                        "data" :
                        [
                            {
                                "id" : "Area 1",
                                "date/time" : "MM:DD:YYYY, HH:MM:SS",
                                "duration" : 300
                            },
                            {
                            },
                            {
                            }
                        ]
                    }

                    Config command
                    {
                        "command" : "config",
                        "areas" : 
                        [
                            {    
                                zones :
                                [
                                    {
                                        "id" : "Zone N",
                                        "pin" : 4
                                    },
                                    {
                                        "id" : "Zone Z",
                                        "pin" : 5
                                    },
                                    {
                                        "id" : "Zone P",
                                        "pin" : 6
                                    }
                                ],
                                flow :
                                {
                                    "id" : "Flow N",
                                    "pin" : 1
                                }
                                overcurrent:
                                {
                                    "id" : "OC N",
                                    "pin" : 2
                                }
                        ]
                        "flow" : 
                        {
                            "id" : "Flow F",
                            "pin" : 9,
                            "min_flow" : 0.0,
                            "max_flow" : 2.0,
                            "low_threshold" : 0.5,
                            "high_threshold" : 1.5
                        }
                        "overcurrent":
                        {
                            "id" : "OC 1",
                            "pin" : 10
                        }
                    }

                 */

                AzureCommand command = JsonConvert.DeserializeObject<AzureCommand>(json);

                switch (command.command)
                {
                    case "manual":
                        var manual_data = JsonConvert.DeserializeObject<AzureManualData>(command.data);

                        foreach (var area in _areas)
                        {
                            if (area.Id() == manual_data.area)
                            {
                                if (manual_data.state == "on")
                                {
                                    area.Activate();
                                }

                                if (manual_data.state == "off")
                                {
                                    area.Deactivate();
                                }
                            }
                        }
                        break;

                    case "schedule":
                        var schedule_data = JsonConvert.DeserializeObject<AzureScheduleData>(command.data);

                        switch (command.action)
                        {
                            case "clear":                                
                                foreach (var entry in schedule_data.entries)
                                {
                                    foreach (var area in _areas)
                                    {
                                        if (area.Id() == entry.area)
                                        {
                                            area.ClearSchedule();
                                        }
                                    }
                                }
                                break;

                            case "add":
                                foreach (var entry in schedule_data.entries)
                                {
                                    foreach (var area in _areas)
                                    {
                                        if (area.Id() == entry.area)
                                        {
                                            area.AddScheduleEvent(entry.data);
                                        }
                                    }
                                }
                                break;

                            default:
                                break;
                        }
                        break;

                    default:
                        break;
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
