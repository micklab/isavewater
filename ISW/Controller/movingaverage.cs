using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ISaveWater
{
    class MovingAverageFilter
    {
        public MovingAverageFilter(int n)
        {
            _n = n;
            _last = 0;
        }

        public double Update(double value)
        {
            /*
            MA*[i]= MA*[i-1] +X[i] - MA*[i-1]/N

            where MA* is the moving average*N. 

            MA[i]= MA*[i]/N
            */
            double ma_curr;

            ma_curr = _last + value - _last / _n;
            _last = ma_curr;

            return ma_curr / _n;
        }

        private int _n;
        private double _last;
    };
}