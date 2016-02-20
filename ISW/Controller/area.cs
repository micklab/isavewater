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
                        _flow_state = FLOW_STATE_BLOCKED;
                        AlertCallback("flow:" + _flow.Id() + ":" + flow_rate.ToString("F1") + ":" + _flow_state);
                    }
                    else
                    {
                        _flow_state = FLOW_STATE_NORMAL;
                    }
                }

                if (_state == INACTIVE_STATE)
                {
                    var flow_rate = _flow.Rate();
                    if (flow_rate > INACTIVE_MAX_THRESHOLD)
                    {
                        _flow_state = FLOW_STATE_LEAKING;
                        AlertCallback("flow:" + _flow.Id() + ":" + flow_rate.ToString("F1") + ":" + _flow_state);
                    }
                    else
                    {
                        _flow_state = FLOW_STATE_NONE;
                    }
                }

                await Task.Delay(1000);
            }
        }

        private async Task ExecuteEvent(EventCommand command)
        {
            if (command.state.ToLower() == "off")
            {
                foreach (var zone in _zones)
                {
                    zone.Disable();
                }
            }

            if (command.state.ToLower() == "on")
            {
                // the zones are sequenced so that only one zone is on at a time
                foreach (var zone in _zones)
                {
                    zone.Enable();
                    await Task.Delay(command.duration * 1000);
                    zone.Disable();
                }
            }
        }

        private void Scheduler_Callback(ThreadPoolTimer timer)
        {
            Task.Run(() => ExecuteEvent(_command));
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

            var status = new Status()
            {
                id = _id,
                zones = zones_status,
                flow = new FlowData()
                {
                    id = _flow.Id(),
                    rate = _flow.Rate(),
                    state = _flow_state
                },
                overcurrent = new OverCurrentData()
                {
                    id = _over_current.Id(),
                    state = _over_current.State()
                }
            };
            return JsonConvert.SerializeObject(status);
        }

        public void ClearSchedule()
        {
            _schedule.Clear();
        }

        public void AddEvent(EventCommand command)
        {
            var start_time = command.schedule_time.Subtract(command.current_time).TotalSeconds;
            if (start_time > 1)
            {
                _command = command;
                if (_timer != null)
                {
                    _timer.Cancel();
                }
                _timer = ThreadPoolTimer.CreateTimer(Scheduler_Callback, TimeSpan.FromSeconds(start_time));
            }
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
                    message = JsonConvert.SerializeObject(new FlowAlert()
                                                                  { id = "alert",
                                                                    data = new FlowData()
                                                                      { id = result[0],
                                                                        rate = Convert.ToDouble(result[1]),
                                                                        state = result[2]
                                                                      }
                                                                  });
                    break;

            case "overcurrent":
                    message = JsonConvert.SerializeObject(new OverrCurrentAlert()
                                                                  { id  = "alert",
                                                                    data = new OverCurrentData()
                                                                      { id = result[1],
                                                                        state = result[2]
                                                                      }
                                                                  });
                    break;

                default:
                    message = "unknown alert type";
                    break;
            }

            return _alert_callback(message);
        }

        private const string ACTIVE_STATE = "active";
        private const string INACTIVE_STATE = "inactive";

        private const string FLOW_STATE_BLOCKED = "blocked";
        private const string FLOW_STATE_NORMAL = "normal";
        private const string FLOW_STATE_NONE = "none";
        private const string FLOW_STATE_LEAKING = "leaking";

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
        private ThreadPoolTimer _timer;
        private EventCommand _command;
    }

}
