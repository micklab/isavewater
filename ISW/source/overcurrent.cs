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
            if (alert_callback != null)
            {
                _alert_callbacks.Add(alert_callback);
            }
        }


        private void OverCurrentPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs args)
        {
            if (_pin.Read() == GpioPinValue.High)
            {
                foreach (var callback in _alert_callbacks)
                {
                    callback("over current detected");
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

        private string _id;
        private GpioPin _pin;
        private List<Func<string, int> > _alert_callbacks;

    };
}
