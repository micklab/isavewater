using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Windows.Devices.Gpio;

namespace ISaveWater
{
    class OverCurrent
    {
        public OverCurrent(string id, GpioPin pin)
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
            bool state_changed = false;
            GpioPinValue curr_pin_value = _pin.Read();

            // Detect a change in pin state
            if ( (_last_pin_value == INACTIVE &&  curr_pin_value == ACTIVE) ||
                 (_last_pin_value == ACTIVE && curr_pin_value == INACTIVE) )
            {
                state_changed = true;
            }

            _last_pin_value = curr_pin_value;

            if (curr_pin_value == ACTIVE)
            {
                _state = DETECT_STATE;
            }
            else
            {
                _state = NO_DETECT_STATE;
            }

            // Send an alert only on a change
            if (state_changed)
            {                
                foreach (var callback in _alert_callbacks)
                {
                    callback("overcurrent:" + _id + ":" + _state);
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

        private const string NO_DETECT_STATE = "none";
        private const string DETECT_STATE = "detect";
        //private const GpioPinValue INACTIVE = GpioPinValue.Low;
        private const GpioPinValue INACTIVE = GpioPinValue.High;
        //private const GpioPinValue ACTIVE = GpioPinValue.High;
        private const GpioPinValue ACTIVE = GpioPinValue.Low;

        private string _id;
        private GpioPin _pin;
        private List<Func<string, int> > _alert_callbacks;
        private string _state;
        private GpioPinValue _last_pin_value = INACTIVE;

    };
}
