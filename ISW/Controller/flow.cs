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
        public Flow(string id, GpioPin pin)
        {
            _id = id;
            _pin = pin;
            _pin.DebounceTimeout = new TimeSpan(0, 0, 0, 0, 50);
            _pin.SetDriveMode(GpioPinDriveMode.InputPullUp);
            _pin.ValueChanged += FlowPin_ValueChanged;
            _ma = new MovingAverageFilter(10);
            _alert_callbacks = new List<Func<string, int>>();
            _avg_flow = 0.0;

        }

        public void Start()
        {
            Task.Run(() => Sample());
        }

        private async Task Sample()
        {
            int samples = 1;
            int frequency;

            while (true)
            {
                samples++;
                if (samples > 20)
                {
                    lock (_sync_lock)
                    {
                        frequency = _low_to_high_count;
                        _low_to_high_count = 0;
                    }
                    PulseFrequencyToGpm(_ma.Update((double)frequency));
                    samples = 1;

                }
                await Task.Delay(50);
            }
        }

        public string Id()
        {
            return _id;
        }

        public double Rate() { return _avg_flow; }

        public void AddAlertCallback(Func<string, int> callback)
        {
            if (callback != null)
            {
                _alert_callbacks.Add(callback);
            }
        }

        private void PulseFrequencyToGpm(double frequency)
        {
            // Convert between pulse frequency and gallons per minute
            _avg_flow = frequency;
        }

        private void FlowPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            //double frequency;
            GpioPinValue state = _pin.Read();

            if (_last_flow_state == GpioPinValue.Low && state == GpioPinValue.High)
            {
                lock (_sync_lock)
                {
                    _low_to_high_count++;
                }
                /*
                long current_time = DateTime.Now.Ticks / TimeSpan.TicksPerMillisecond;

                frequency = (1.0 / (current_time - _last_time)) * MILLISECONDS_PER_SECOND;
                _avg_flow = PulseFrequencyToGpm(_ma.Update(frequency));
                _last_time = current_time;
                */
            }
            _last_flow_state = state;
        }

        private const int MILLISECONDS_PER_SECOND = 1000;
        private const double MIN_FLOW = 0.0;
        private const double MAX_FLOW = 10.0;

        private System.Object _sync_lock = new System.Object();

        private string _id;
        private GpioPin _pin;
        private List<Func<string, int> > _alert_callbacks;

        private long _last_time;
        private GpioPinValue _last_flow_state;
        private MovingAverageFilter _ma;
        private double _avg_flow;
        private int _low_to_high_count;
    };
}
