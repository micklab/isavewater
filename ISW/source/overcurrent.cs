using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Windows.Devices.Gpio;

namespace ISaveWater
{
    class OverCurrent
    {
        public OverCurrent(string id, GpioPin pin, Func<string, int> alert_callback = null)
        {
            _id = id;
            _pin = pin;
            _pin.SetDriveMode(GpioPinDriveMode.InputPullUp);
            _pin.ValueChanged += OverCurrentPin_ValueChanged;
            _alert_callbacks = new List<Func<string, int>>();
            _state = NO_DETECT_STATE;
        }

        public string Id()
        {
            return _id;
        }

        public string State()
        {
            return _state;
        }

        private void OverCurrentPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            _state = NO_DETECT_STATE;
            if (_pin.Read() == GpioPinValue.High)
            {
                _state = DETECT_STATE;
                foreach (var callback in _alert_callbacks)
                {
                    callback(_id + ":" + _state);
                }
            }
        }

        public void AddAlertCallback(Func<string, int> callback)
        {
            if (callback != null)
            {
                _alert_callbacks.Add(callback);
            }
        }

        private const string NO_DETECT_STATE = "NONE";
        private const string DETECT_STATE = "DETECT";

        private string _id;
        private GpioPin _pin;
        private List<Func<string, int> > _alert_callbacks;
        private string _state;

    };
}
