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
            _avg_flow = 0.0;
        }

        public void Start()
        {
            Task.Run(() => Sample());
        }

        private async Task Sample()
        {
            int frequency;

            while (true)
            {
                lock (_sync_lock)
                {
                    frequency = _low_to_high_count;
                    _low_to_high_count = 0;
                }

                PulseFrequencyToGpm(_ma.Update((double)frequency));

                await Task.Delay(1000);
            }
        }

        public string Id()
        {
            return _id;
        }

        public double Rate() { return _avg_flow; }

        private void PulseFrequencyToGpm(double frequency)
        {
            // Convert between pulse frequency and gallons per minute
            // frequency / 7.5 = liters per minute
            // 1 liter = 0.264172 gallons            
            _avg_flow = (frequency / 7.5) * 0.264172;
        }

        private void FlowPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            GpioPinValue state = _pin.Read();

            if (_last_flow_state == GpioPinValue.Low && state == GpioPinValue.High)
            {
                lock (_sync_lock)
                {
                    _low_to_high_count++;
                }
            }
            _last_flow_state = state;
        }

        private Object _sync_lock = new Object();

        private string _id;
        private GpioPin _pin;

        private GpioPinValue _last_flow_state;
        private MovingAverageFilter _ma;
        private double _avg_flow;
        private int _low_to_high_count;
    };
}
