// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Net.Http;
using Windows.ApplicationModel.Background;
using Windows.Devices.Gpio;
using Windows.System.Threading;
using System.Diagnostics;

namespace ISaveWater
{
    public sealed class StartupTask : IBackgroundTask
    {
        BackgroundTaskDeferral deferral;
        //private ThreadPoolTimer timer;
        private AzureClient _azure_client;
        private Controller _controller;

        public void Run(IBackgroundTaskInstance taskInstance)
        {
            deferral = taskInstance.GetDeferral();
            //timer = ThreadPoolTimer.CreatePeriodicTimer(Timer_Tick, TimeSpan.FromMilliseconds(500));

            Initialize();
            Start();
        }

        //private void Timer_Tick(ThreadPoolTimer timer)
        //{
        //    Debug.WriteLine("tick, tock");
        //}

        private void Initialize()
        {
            Debug.WriteLine("Main: initializing assets");

            // Create the AzureClient
            Debug.WriteLine("\tCreating Azure client");
            _azure_client = new AzureClient(Azure_Callback);

            // Create the Controller
            Debug.WriteLine("\tCreating Controller");
            _controller = new Controller(Controller_Callback);
        }

        private void Start()
        {
            Debug.WriteLine("\nMain: starting azure asset");
            _azure_client.Start();
            Debug.WriteLine("Main: starting controller asset");
            _controller.Start();
        }

        private int Azure_Callback(string message)
        {
            _controller.SendMessage(message);
            return 0;
        }

        private int Controller_Callback(string message)
        {
            _azure_client.SendMessage(message);
            return 0;
        }

    }
}
