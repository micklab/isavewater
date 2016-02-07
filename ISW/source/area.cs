using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;

namespace ISaveWater
{
    class Area
    {
        public Area(string id, List<Valve> zones, Flow flow, OverCurrent over_current, Func<string, int> alert_callback)
        {
            _id = id;
            _zones = zones;
            _flow = flow;
            _over_current = over_current;
            _alert_callback = alert_callback;

            foreach (var valve in _valves)
            {
                valve.AddAlertCallback(AlertCallback);
            }
            _flow_meter.AddAlertCallback(AlertCallback);
            _over_current.AddAlertCallback(AlertCallback);
            _state = INACTIVE_STATE;

            var t = Task.Run(async delegate
            {
                while (true)
                {
                    if (_state == ACTIVE_STATE)
                    {
                        var flow_rate = _flow.Rate();
                        if (flow_rate < ACTIVE_MIN_THRESHOLD)
                        {
                            _alert_callback(String.Format("Area ({}): blockage detected {}", _id, flow_rate));
                        }
                    }

                    if (_state == INACTIVE_STATE)
                    {
                        var flow_rate = _flow.Rate();
                        if (flow_rate > INACTIVE_MAX_THRESHOLD)
                        {
                            _alert_callback(String.Format("Area ({}): leak detected {}", _id, flow_rate));
                        }
                    }

                    // execute watering schedule
                    // How to find the next watering event?
                    // What should the thread do in the mean time?
                    //   - find the next watering event.  The event will contains the following information:
                    //       1. the valve or valves to be enabled
                    //       2. the duration of the watering
                    //   - start a timer which when it expires will
                    //       1. enable the relevant valves
                    //       2. start a timer for the specified duration which upon expiry will turn off the valves

                    await Task.Delay(500);
                }
            });

        }

        public void Activate()
        {
            Debug.WriteLine("Activating Area {}", _id);

            foreach (var valve in _valves)
            {
                valve.Enable();
            }
        }

        public void Deactivate()
        {
            Debug.WriteLine("Deactivating Area {}", _id);

            foreach (var valve in _valves)
            {
                valve.Disable();
            }
        }

        public string Status()
        {
            string status = "";

            /* I think a json string would be good here */
            /* <area id>/<zone 1 id>:<state>, <zone 2 id>:<state>/<flow id>:<flow>/<health id>:<state> */

            return status;
        }

        public void AddScheduleEvent(string sch_event)
        {
            // Insert the event into the schedule
        }

        private int AlertCallback(string value)
        {
            return _alert_callback(String.Format("Area ({}): {}", _id, value));
        }

        private const string ACTIVE_STATE = "ACTIVE";
        private const string INACTIVE_STATE = "INACTIVE";

        private double INACTIVE_MAX_THRESHOLD = 1.0;
        private double ACTIVE_MIN_THRESHOLD = 3.0;

        private string _id;
        private List<Zone> _zones;
        private Flow _flow;
        private OverCurrent _over_current;
        private Func<string, int> _alert_callback;
        private string _state;

    }

}
