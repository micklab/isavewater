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
                var json = incoming_queue.Take().ToLower();
                Debug.WriteLine("Controller: received message from Azure - " + json);

                var command = JsonConvert.DeserializeObject<EventCommand>(json);

                foreach (var area in _areas)
                {
                    if (area.Id() == command.area)
                    {
                        area.AddEvent(command);
                    }
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
