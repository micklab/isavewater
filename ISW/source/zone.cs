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
        public Zone(string id, GpioPin pin, Func<string, int> alert_callback = null)
        {
            _id = id;
            _pin = pin;
            _pin.Write(GpioPinValue.Low);
            _pin.SetDriveMode(GpioPinDriveMode.Output);
            _state = ON_STATE;
            if (alert_callback != null)
            {
                _alert_callbacks.Add(alert_callback);
            }
        }

        public void Enable()
        {

            // Turn on the valve
            _state = ON_STATE;
            _pin.Write(GpioPinValue.High);

            foreach (var callback in _alert_callbacks)
            {
                callback(String.Format("Value ({}): state change {}", _id, _state));
            }
        }

        public void Disable()
        {
            // Turn off the valve
            _state = OFF_STATE;
            _pin.Write(GpioPinValue.Low);

            foreach (var callback in _alert_callbacks)
            {
                callback(String.Format("Value ({}): state change {}", _id, _state));
            }
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
