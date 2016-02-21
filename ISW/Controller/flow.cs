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
            _pin.SetDriveMode(GpioPinDriveMode.InputPullUp);
            _pin.ValueChanged += FlowPin_ValueChanged;
            _ma = new MovingAverageFilter(1);
            _avg_flow = 0.0;
            _last_flow_state = GpioPinValue.Low;

        }

        public void Start()
        {
            Task.Run(() => Sample());
        }

        private async Task Sample()
        {
            while (true)
            {
                PulseFrequencyToGpm(_low_to_high_count/5);
                //PulseFrequencyToGpm(_ma.Update((double)frequency));
                _low_to_high_count = 0;


                await Task.Delay(5000);
            }
        }

        public string Id()
        {
            return _id;
        }

        //public double Rate() { return (double) Math.Round((decimal)_avg_flow, 1); }
        public double Rate() { return _avg_flow; }

        private void PulseFrequencyToGpm(double frequency)
        {
            // Convert between pulse frequency and gallons per minute
            // frequency / 7.5 = liters per minute
            // 1 liter = 0.264172 gallons            
            //_avg_flow = (frequency / 7.5) * 0.264172;
            _avg_flow = (frequency / 5.5);
        }

        private void FlowPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            GpioPinValue state = _pin.Read();

            if (_last_flow_state == GpioPinValue.Low && state == GpioPinValue.High)
            {
                _low_to_high_count++;
            }
            _last_flow_state = state;
        }

        private string _id;
        private GpioPin _pin;

        private GpioPinValue _last_flow_state;
        private MovingAverageFilter _ma;
        private double _avg_flow;
        private int _low_to_high_count;
    };
}
