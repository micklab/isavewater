using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace ISaveWater
{

    class AzureCommand
    {
        public string command { get; set; }
    }

    class AzureManualData
    {
        public string area { get; set; }
        public string state { get; set; }
    }

    class AzureManualCommand : AzureCommand
    {
        public AzureManualData data { get; set; }
    }

    class ScheduleData
    {
        public DateTime start_time { get; set; }
        public UInt32 duration { get; set; }
    }

    class AzureScheduleEntry
    {
        public string area { get; set; }
        public ScheduleData data { get; set; }
    }

    class AzureScheduleData
    {
        public List<AzureScheduleEntry> entries { get; set; }
    }
    
    class AzureScheduleCommand : AzureCommand
    {
        public string action { get; set; }
        public AzureScheduleData data { get; set; }
    }
    
    class EventCommand
    {
        public DateTime current_time {get; set;}
        public DateTime schedule_time {get; set;}
        public string area {get; set;}
        public string state {get; set;}
        public int duration { get; set; }
    }


    class FlowData
    {
        public string id { get; set; }
        public string rate { get; set; }
        public string state { get; set; }
    }

    class OverCurrentData
    {
        public string id { get; set; }
        public string state { get; set; }
    }

    class ZoneData
    {
        public string id { get; set; }
        public string state { get; set; }
    }

    class FlowAlert
    {
        public string id { get; set; }
        public FlowData data { get; set; }
    }

    class FlowAlertRoot
    {
        public FlowAlert alert { get; set; }
    }

    class OverrCurrentAlert
    {
        public string id { get; set; }
        public OverCurrentData data { get; set; }
    }

    class OverCurrentAlertRoot
    {
        public OverrCurrentAlert alert { get; set; }
    }

    class Status
    {
        public string id { get; set; }
        public List<ZoneData> zones { get; set; }
        public FlowData flow { get; set; }
        public OverCurrentData overcurrent { get; set; }
    }

    class StatusRoot
    {
        public Status status { get; set; }
    }

}