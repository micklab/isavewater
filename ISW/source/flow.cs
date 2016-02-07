using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Windows.Devices.Gpio;

namespace ISaveWater
{
    class Flow
    {
        public Flow(string id, GpioPin pin, Func<string, int> alert_callback = null)
        {
            _id = id;
            _pin = pin;
            _pin.DebounceTimeout = new TimeSpan(0, 0, 0, 0, 50);
            _pin.SetDriveMode(GpioPinDriveMode.InputPullUp);
            _pin.ValueChanged += FlowPin_ValueChanged;
            if (alert_callback != null)
            {
                _alert_callbacks.Add(alert_callback);
            }

            var t = Task.Run(async delegate
            {
                while (true)
                {
                    double limit = 0.0;
                    if (_avg_flow > MAX_FLOW)
                    {
                        limit = MAX_FLOW;
                    }
                    if (_avg_flow < MIN_FLOW)
                    {
                        limit = MIN_FLOW;
                    }

                    foreach (var callback in _alert_callbacks)
                    {
                        callback(String.Format("Flow ({}): current flow {} exceeds limit {}", _id, _avg_flow, limit));
                    }
                    await Task.Delay(500);
                }
            });

        }

        public double Rate() { return _avg_flow; }

        public void AddAlertCallback(Func<string, int> callback)
        {
            if (callback != null)
            {
                _alert_callbacks.Add(callback);
            }
        }

        private double PulseFrequencyToGpm(double frequency)
        {
            return frequency;
        }

        private void FlowPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            double frequency;
            GpioPinValue state = _pin.Read();

            if (_last_flow_state == GpioPinValue.Low && state == GpioPinValue.High)
            {
                long current_time = DateTime.Now.Ticks / TimeSpan.TicksPerMillisecond;

                frequency = (1.0 / (current_time - _last_time)) * MILLISECONDS_PER_SECOND;
                _avg_flow = PulseFrequencyToGpm(_ma.Update(frequency));
                _last_time = current_time;
            }
            _last_flow_state = state;
        }

        private const int MILLISECONDS_PER_SECOND = 1000;
        private const double MIN_FLOW = 1.0;
        private const double MAX_FLOW = 10.0;

        private string _id;
        private GpioPin _pin;
        private List<Func<string, int> > _alert_callbacks;

        private long _last_time;
        private GpioPinValue _last_flow_state;
        private MovingAverageFilter _ma;
        private double _avg_flow;
    };
}
