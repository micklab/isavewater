using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Windows.Devices.Gpio;

namespace ISaveWater
{

    class Zone
    {
        public Zone(string id, GpioPin pin)
        {
            _id = id;
            _pin = pin;
            _pin.Write(GpioPinValue.Low);
            _pin.SetDriveMode(GpioPinDriveMode.Output);
            _pin.Write(GpioPinValue.High);
            _state = OFF_STATE;
        }

        public string Id()
        {
            return _id;
        }

        public string State()
        {
            return _state;
        }

        public void Enable()
        {

            // Turn on the zone
            _state = ON_STATE;
            _pin.Write(GpioPinValue.Low);
        }

        public void Disable()
        {
            // Turn off the valve
            _state = OFF_STATE;
            _pin.Write(GpioPinValue.High);
        }

        private const string ON_STATE = "on";
        private const string OFF_STATE = "off";

        private string _id;
        private GpioPin _pin;
        private string _state;

    };

}
