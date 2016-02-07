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
            _state = OFF_STATE;
            _alert_callbacks = new List<Func<string, int>>();
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
            _pin.Write(GpioPinValue.High);
        }

        public void Disable()
        {
            // Turn off the valve
            _state = OFF_STATE;
            _pin.Write(GpioPinValue.Low);
        }

        public void AddAlertCallback(Func<string, int> callback)
        {
            if (callback != null)
            {
                _alert_callbacks.Add(callback);
            }
        }

        private const string ON_STATE = "ON";
        private const string OFF_STATE = "OFF";

        private string _id;
        private GpioPin _pin;
        private string _state;
        private List<Func<string, int> > _alert_callbacks;

    };

}
