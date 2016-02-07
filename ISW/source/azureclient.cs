using System;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using Microsoft.Azure.Devices.Client;
using System.Collections.Concurrent;

namespace ISaveWater
{
    class AzureClient
    {
        private const string DeviceConnectionString = "HostName=IrrigationManagement.azure-devices.net;DeviceId=MyNewDevice;SharedAccessKey=7DShm9V6xb4L4HqJ4gii0ER55wriOXhkLfPYJnhwh6c=";
        private BlockingCollection<string> _outgoing_queue = new BlockingCollection<string>();
        private Func<string, int> _callback;
        private Task[] tasks = new Task[2];

        public AzureClient(Func<string, int> callback)
        {
            _callback = callback;
        }
        
        public void Start()
        {
            try
            {
                DeviceClient deviceClient = DeviceClient.CreateFromConnectionString(DeviceConnectionString, TransportType.Http1);

                Task.Run(() => SendEvent(deviceClient));
                Task.Run(() => ReceiveCommands(deviceClient));

                Debug.WriteLine("Exited!\n");
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Error in sample: {0}", ex.Message);
            }
        }
        
        public void SendMessage(string message)
        {
            _outgoing_queue.Add(message);
        }

        private async Task SendEvent(DeviceClient deviceClient)
        {
            Debug.WriteLine("\nDevice waiting to send messages to IoTHub ...\n");
            while (true)
            {
                var message = _outgoing_queue.Take();

                /*
                var telemetryDataPoint = new
                {
                    deviceId = "myFirstDevice",
                    windSpeed = currentWindSpeed
                };
                var messageString = JsonConvert.SerializeObject(telemetryDataPoint);
                */
                var eventMessage = new Message(Encoding.UTF8.GetBytes(message));
                Debug.WriteLine(message);

                await deviceClient.SendEventAsync(eventMessage);
                await Task.Delay(1000);
            }
            
        }

        private async Task ReceiveCommands(DeviceClient deviceClient)
        {
            Debug.WriteLine("\nDevice waiting for commands from IoTHub...\n");

            while (true)
            {
                var receivedMessage = await deviceClient.ReceiveAsync();

                if (receivedMessage != null)
                {
                    _callback(Encoding.ASCII.GetString(receivedMessage.GetBytes()));

                    await deviceClient.CompleteAsync(receivedMessage);
                }

                //  Note: In this sample, the polling interval is set to 
                //  10 seconds to enable you to see messages as they are sent.
                //  To enable an IoT solution to scale, you should extend this //  interval. For example, to scale to 1 million devices, set 
                //  the polling interval to 25 minutes.
                //  For further information, see
                //  https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
                //await Task.Delay(TimeSpan.FromSeconds(10));
            }
        }
    }
}