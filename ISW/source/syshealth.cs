using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace ISaveWater
{
    class SystemHealth
    {
        public SystemHealth(Func<string, int> callback)
        {
            _timer = new Timer(Timer_Callback, this, 0, 1000);
            _callback = callback;
        }

        public void AddGrove(Grove grove)
        {
            if (grove != null)
            {
                _groves.Add(grove);
            }
        }

        private void Timer_Callback(object state)
        {
            // Perform system health checks
            foreach (var grove in _groves)
            {
                // Get status from Grove
                _callback(String.Format("System: {}", grove.Status()));
            }
        }

        private Timer _timer;
        private List<Grove> _groves;
        private Func<string, int> _callback;
    }
}
