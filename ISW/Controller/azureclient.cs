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
        private const string DeviceConnectionString = "HostName=IrrigationManagement.azure-devices.net;DeviceId=ISWController;SharedAccessKey=1rLRVVZKrBBoIoaEFHsI3Z1FMTGh+GNL+SnH4upMd78=";
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

                var eventMessage = new Message(Encoding.UTF8.GetBytes(message));
                Debug.WriteLine(message);

                try
                {
                    await deviceClient.SendEventAsync(eventMessage);
                }
                catch
                {
                    Debug.WriteLine("SendEvent: Encountered an exception");
                }
                await Task.Delay(1000);
            }

        }

        private async Task ReceiveCommands(DeviceClient deviceClient)
        {
            Debug.WriteLine("\nDevice waiting for commands from IoTHub...\n");
            Message receivedMessage;

            while (true)
            {
                try
                {
                    receivedMessage = await deviceClient.ReceiveAsync();

                    if (receivedMessage != null)
                    {
                        _callback(Encoding.ASCII.GetString(receivedMessage.GetBytes()));

                        await deviceClient.CompleteAsync(receivedMessage);
                    }

                    //  Note: In this sample, the polling interval is set to 
                    //  10 seconds to enable you to see messages as they are sent.
                    //  To enable an IoT solution to scale, you should extend this 
                    //  interval. For example, to scale to 1 million devices, set 
                    //  the polling interval to 25 minutes.
                    //  For further information, see
                    //  https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
                    //await Task.Delay(TimeSpan.FromSeconds(10));
                }
                catch
                {
                    Debug.WriteLine("ReceiveCommands: Encountered an exception");
                }

            }
        }
    }
}