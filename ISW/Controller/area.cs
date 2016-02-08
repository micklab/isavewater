using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using Newtonsoft.Json;
using Windows.System.Threading;

namespace ISaveWater
{

    class Area
    {
        public Area(string id, List<Zone> zones, Flow flow, OverCurrent over_current, Func<string, int> alert_callback)
        {
            _id = id;
            _zones = zones;
            _flow = flow;
            _over_current = over_current;
            _alert_callback = alert_callback;

            _over_current.AddAlertCallback(AlertCallback);
            _state = INACTIVE_STATE;
            _schedule = new List<ScheduleData>();
        }

        public void Start()
        {
            // Start the flow object to calculate any water flow
            _flow.Start();

            // Start the sample task to detect abnormal flow rates and execute the schedule
            Task.Run(() => Sample());
        }

        private async Task Sample()
        {
            while (true)
            {
                if (_state == ACTIVE_STATE)
                {
                    var flow_rate = _flow.Rate();
                    if (flow_rate < ACTIVE_MIN_THRESHOLD)
                    {
                        _flow_state = "blocked";
                        AlertCallback("flow:" + _flow.Id() + ":" + flow_rate.ToString("F1") + ":" + _flow_state);
                    }
                    else
                    {
                        _flow_state = "normal";
                    }
                }

                if (_state == INACTIVE_STATE)
                {
                    var flow_rate = _flow.Rate();
                    if (flow_rate > INACTIVE_MAX_THRESHOLD)
                    {
                        _flow_state = "leaking";
                        AlertCallback("flow:" + _flow.Id() + ":" + flow_rate.ToString("F1") + ":" + _flow_state);
                    }
                    else
                    {
                        _flow_state = "none";
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

                if (!_is_event_scheduled)
                {
                    if (_schedule.Count > 1)
                    {
                        var entry = _schedule.ElementAt(0);

                        var start_time = DateTime.Now.Subtract(entry.start_time).Seconds;
                        _duration = (int) entry.duration;
                        if (_timer != null)
                        {
                            _timer.Cancel();
                        }
                        _timer = ThreadPoolTimer.CreateTimer(Scheduler_Callback, TimeSpan.FromSeconds(start_time));

                        _is_event_scheduled = true;
                    }
                }

                await Task.Delay(1000);
            }
        }

        private async Task ExecuteEvent(int duration)
        {
            foreach (var zone in _zones)
            {
                zone.Enable();
            }

            await Task.Delay(duration * 1000);

            foreach (var zone in _zones)
            {
                zone.Disable();
            }

            _is_event_scheduled = false;
        }

        private void Scheduler_Callback(ThreadPoolTimer timer)
        {
            Task.Run(() => ExecuteEvent(_duration));
        }

        public string Id()
        {
            return _id;
        }

        public void Activate()
        {
            Debug.WriteLine("Activating Area " + _id);

            _state = ACTIVE_STATE;

            foreach (var zone in _zones)
            {
                zone.Enable();
            }
        }

        public void Deactivate()
        {
            Debug.WriteLine("Deactivating Area " + _id);

            _state = INACTIVE_STATE;

            foreach (var zone in _zones)
            {
                zone.Disable();
            }
        }

        public string Status()
        {
            var zones_status = new List<ZoneData>();
            foreach (var zone in _zones)
            {
                zones_status.Add(new ZoneData() { id = zone.Id(), state = zone.State() });
            }

            var status = new StatusRoot() { status = new Status() { id = "status",
                                                                    zones = zones_status,
                                                                    flow = new FlowData() { id = _flow.Id(), rate = _flow.Rate(), state = _flow_state },
                                                                    overcurrent = new OverCurrentData() { id = _over_current.Id(), state = _over_current.State() } } };

            return JsonConvert.SerializeObject(status);
        }

        public void ClearSchedule()
        {
            _schedule.Clear();
        }

        public void AddScheduleEvent(ScheduleData entry)
        {
            _schedule.Add(entry);
            _schedule.Sort(delegate (ScheduleData x, ScheduleData y)
            {
                if (x.start_time == null && y.start_time == null)
                    return 0;
                else if (x.start_time == null)
                    return -1;
                else if (y.start_time == null)
                    return 1;
                else
                    return x.start_time.CompareTo(y.start_time);
            });
        }

        private int AlertCallback(string value)
        {
            /*
            split value on ':' to get either id, state for over current or id, rate, state for flow

            */
            string message = "";
            var result = value.Split(':');

            switch (result[0])
            {
                case "flow":
                    message = JsonConvert.SerializeObject(new FlowAlertRoot()
                                                              { alert = new FlowAlert()
                                                                  { id = "alert",
                                                                    data = new FlowData()
                                                                      { id = result[0],
                                                                        rate = Convert.ToDouble(result[1]),
                                                                        state = result[2]
                                                                      }
                                                                  }
                                                              }, 
                                                          Formatting.Indented);
                    break;

                case "overcurrent":
                    message = JsonConvert.SerializeObject(new OverCurrentAlertRoot()
                                                              { alert = new OverrCurrentAlert()
                                                                  { id  = "alert",
                                                                    data = new OverCurrentData()
                                                                      { id = result[0],
                                                                        state = result[1]
                                                                      }
                                                                  } 
                                                              },
                                                          Formatting.Indented);
                    break;

                default:
                    message = "unknown alert type";
                    break;
            }

            return _alert_callback(message);
        }

        private const string ACTIVE_STATE = "ACTIVE";
        private const string INACTIVE_STATE = "INACTIVE";

        private double INACTIVE_MAX_THRESHOLD = 2.0;
        private double ACTIVE_MIN_THRESHOLD = 3.0;

        private string _id;
        private List<Zone> _zones;
        private Flow _flow;
        private OverCurrent _over_current;
        private Func<string, int> _alert_callback;
        private string _state;
        private string _flow_state = "none";
        private List<ScheduleData> _schedule;
        private bool _is_event_scheduled;
        private int _duration;
        private ThreadPoolTimer _timer;
    }

}
