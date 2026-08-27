# Part 3: Live Train Map

## Introduction

Add a dynamic map, showing the layout of each line with live train positions.

## Requirements

### Home page

- Add a button to display live train maps, where user would have to select the line they would like to view.

### Live Map

- Show one map per line, where nodes represent stations (with station names displayed) and edges represent connections. Since a line can have multiple branches, the maps should be displayed in a way that is human readable. An example is given under `data/live-tube-map-layouts` showing how the nodes are positioned, but you are not strictly required to follow it.
- Users should be able to switch directions (inbound, outbound). Some lines such as the Piccadilly line have different stations displayed depending on this direction.
- Route sections should be highlighted in color depending on the line status affected segments:
  | Disruption type | Highlight Color |
  |--------------------------------|-----------------|
  | Suspended | Red |
  | Planned closure / Part closure | Gray |
  | Severe Delays | Orange |
  | Minor Delays | Yellow |
- If multiple disruptions are affecting a line segment, the more severe one applies. You may assume the lower the "statusSeverity" number returned in the status API, the more severe the disruption is.

- On the map, show train icons representing the real time location of the trains. This can be obtained in the "currentLocation" attribute of arrivals.
- If the "currentLocation" attribute is missing or is empty (""), you can ignore those train entries.
- The currentLocation string does not follow a specific format, but you are required to handle the cases below (which are simplified as it is difficult to determine which branch of the line the train is on). The train icon's location depend on how that string is structured:
  | currentLocation format | Train icon location on the map |
  |--------------------------------------------------------------------|----------------------------------------------------------------|
  | At STATION, At STATION platform X, Approaching STATION | Overlaps the STATION's node |
  | At Platform | Overlaps the STATION's node where the arrival is displayed |
  | Left STATION, Leaving STATION, Departed STATION, Departing STATION | Halfway between the STATION's node and the next STATION's node |
  | Between STATION1 and STATION2 | Halfway between the STATION1's node and STATION2's node |

- The currentLocation string use station names (not id), which can differ from what is in our `data/tube-stations.json`. For simplicity ignore the differences and only consider exact match, case insensitive, after trimming.
- Train entries on the live map should be deduplicated with their vehicle Ids, if the vehicle Id field is missing, is empty or is "000", then do not deduplicate them.
- You can make any reasonable assumption on what to happen when multiple trains show up in the same location, as long as the app does not crash.

## Site hierarchy

Home -> Select Line -> Board (If the station is served by multiple lines)
Home -> Board (If the station is only served by one line)
Home -> Select Line -> Live Map

## API endpoints

You will be using the TfL Unified API which does not require an API key to use for the usage frequency that we need.

1. Get statuses of all lines: https://api.tfl.gov.uk/Line/bakerloo,central,circle,district,hammersmith-city,jubilee,metropolitan,northern,piccadilly,victoria,waterloo-city/Status/2026-07-11/to/2026-07-12?detail=true
   (Replace the date with the actual date).

The meaning of "statusSeverity" is given here:
0 = Special Service
1 = Closed
2 = Suspended
3 = Part Suspended
4 = Planned Closure
5 = Part Closure
6 = Severe Delays
7 = Reduced Service
8 = Bus Service
9 = Minor Delays
10 = Good Service
11 = Part Closed
12 = Exit Only
13 = No Step Free Access
14 = Change of frequency
15 = Diverted
16 = Not Running
17 = Issues Reported
18 = No Issues
19 = Information
20 = Service Closed

This endpoint returns data in the following format:

```
[
    {
    "$type": "Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities",
    "id": "waterloo-city",
    "name": "Waterloo & City",
    "modeName": "tube",
    "disruptions": [],
    "created": "2026-08-04T14:39:19.047Z",
    "modified": "2026-08-04T14:39:19.047Z",
    "lineStatuses": [
      {
        "$type": "Tfl.Api.Presentation.Entities.LineStatus, Tfl.Api.Presentation.Entities",
        "id": 0,
        "lineId": "waterloo-city",
        "statusSeverity": 4,
        "statusSeverityDescription": "Planned Closure",
        "reason": "Waterloo & City line: service operates 06:00 until 00:30, Monday to Friday only. There is no service on Saturdays, Sundays and on bank/public holidays.",
        "created": "0001-01-01T00:00:00",
        "validityPeriods": [
          {
            "$type": "Tfl.Api.Presentation.Entities.ValidityPeriod, Tfl.Api.Presentation.Entities",
            "fromDate": "2026-08-08T23:00:00Z",
            "toDate": "2026-08-09T00:15:00Z",
            "isNow": false
          },
          {
            "$type": "Tfl.Api.Presentation.Entities.ValidityPeriod, Tfl.Api.Presentation.Entities",
            "fromDate": "2026-08-09T03:15:00Z",
            "toDate": "2026-08-09T22:59:00Z",
            "isNow": false
          },
          {
            "$type": "Tfl.Api.Presentation.Entities.ValidityPeriod, Tfl.Api.Presentation.Entities",
            "fromDate": "2026-08-09T23:00:00Z",
            "toDate": "2026-08-09T23:45:00Z",
            "isNow": false
          }
        ],
        "disruption": {
          "$type": "Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities",
          "category": "Information",
          "categoryDescription": "Information",
          "description": "Waterloo & City line: service operates 06:00 until 00:30, Monday to Friday only. There is no service on Saturdays, Sundays and on bank/public holidays.",
          "created": "2026-01-04T01:21:00Z",
          "affectedRoutes": [
            {
              "$type": "Tfl.Api.Presentation.Entities.DisruptedRoute, Tfl.Api.Presentation.Entities",
              "id": "2078",
              "name": "Bank Underground Station - Waterloo Underground Station",
              "direction": "inbound",
              "originationName": "Bank Underground Station",
              "destinationName": "Waterloo Underground Station",
              "isEntireRouteSection": true,
              "routeSectionNaptanEntrySequence": [
                {
                  "$type": "Tfl.Api.Presentation.Entities.RouteSectionNaptanEntrySequence, Tfl.Api.Presentation.Entities",
                  "ordinal": 0,
                  "stopPoint": {
                    "$type": "Tfl.Api.Presentation.Entities.StopPoint, Tfl.Api.Presentation.Entities",
                    "naptanId": "940GZZLUBNK",
                    "modes": [],
                    "icsCode": "1000013",
                    "stationNaptan": "940GZZLUBNK",
                    "hubNaptanCode": "HUBBAN",
                    "lines": [],
                    "lineGroup": [],
                    "lineModeGroups": [],
                    "status": true,
                    "id": "940GZZLUBNK",
                    "commonName": "Bank Underground Station",
                    "placeType": "StopPoint",
                    "additionalProperties": [],
                    "children": [],
                    "lat": 0,
                    "lon": 0
                  }
                },
                {
                  "$type": "Tfl.Api.Presentation.Entities.RouteSectionNaptanEntrySequence, Tfl.Api.Presentation.Entities",
                  "ordinal": 1,
                  "stopPoint": {
                    "$type": "Tfl.Api.Presentation.Entities.StopPoint, Tfl.Api.Presentation.Entities",
                    "naptanId": "940GZZLUWLO",
                    "modes": [],
                    "icsCode": "1000254",
                    "stationNaptan": "940GZZLUWLO",
                    "hubNaptanCode": "HUBWAT",
                    "lines": [],
                    "lineGroup": [],
                    "lineModeGroups": [],
                    "status": true,
                    "id": "940GZZLUWLO",
                    "commonName": "Waterloo Underground Station",
                    "placeType": "StopPoint",
                    "additionalProperties": [],
                    "children": [],
                    "lat": 0,
                    "lon": 0
                  }
                }
              ]
            },
            {
              "$type": "Tfl.Api.Presentation.Entities.DisruptedRoute, Tfl.Api.Presentation.Entities",
              "id": "2079",
              "name": "Waterloo Underground Station - Bank Underground Station",
              "direction": "outbound",
              "originationName": "Waterloo Underground Station",
              "destinationName": "Bank Underground Station",
              "isEntireRouteSection": true,
              "routeSectionNaptanEntrySequence": [
                {
                  "$type": "Tfl.Api.Presentation.Entities.RouteSectionNaptanEntrySequence, Tfl.Api.Presentation.Entities",
                  "ordinal": 0,
                  "stopPoint": {
                    "$type": "Tfl.Api.Presentation.Entities.StopPoint, Tfl.Api.Presentation.Entities",
                    "naptanId": "940GZZLUWLO",
                    "modes": [],
                    "icsCode": "1000254",
                    "stationNaptan": "940GZZLUWLO",
                    "hubNaptanCode": "HUBWAT",
                    "lines": [],
                    "lineGroup": [],
                    "lineModeGroups": [],
                    "status": true,
                    "id": "940GZZLUWLO",
                    "commonName": "Waterloo Underground Station",
                    "placeType": "StopPoint",
                    "additionalProperties": [],
                    "children": [],
                    "lat": 0,
                    "lon": 0
                  }
                },
                {
                  "$type": "Tfl.Api.Presentation.Entities.RouteSectionNaptanEntrySequence, Tfl.Api.Presentation.Entities",
                  "ordinal": 1,
                  "stopPoint": {
                    "$type": "Tfl.Api.Presentation.Entities.StopPoint, Tfl.Api.Presentation.Entities",
                    "naptanId": "940GZZLUBNK",
                    "modes": [],
                    "icsCode": "1000013",
                    "stationNaptan": "940GZZLUBNK",
                    "hubNaptanCode": "HUBBAN",
                    "lines": [],
                    "lineGroup": [],
                    "lineModeGroups": [],
                    "status": true,
                    "id": "940GZZLUBNK",
                    "commonName": "Bank Underground Station",
                    "placeType": "StopPoint",
                    "additionalProperties": [],
                    "children": [],
                    "lat": 0,
                    "lon": 0
                  }
                }
              ]
            }
          ],
          "affectedStops": [],
          "closureText": "plannedClosure"
        }
      }
    ],
    "routeSections": [
      {
        "$type": "Tfl.Api.Presentation.Entities.MatchedRoute, Tfl.Api.Presentation.Entities",
        "name": "Bank Underground Station - Waterloo Underground Station",
        "direction": "inbound",
        "originationName": "Bank Underground Station",
        "destinationName": "Waterloo Underground Station",
        "originator": "940GZZLUBNK",
        "destination": "940GZZLUWLO",
        "serviceType": "Regular",
        "validTo": "2026-12-23T00:00:00Z",
        "validFrom": "2026-08-03T00:00:00Z"
      },
      {
        "$type": "Tfl.Api.Presentation.Entities.MatchedRoute, Tfl.Api.Presentation.Entities",
        "name": "Waterloo Underground Station - Bank Underground Station",
        "direction": "outbound",
        "originationName": "Waterloo Underground Station",
        "destinationName": "Bank Underground Station",
        "originator": "940GZZLUWLO",
        "destination": "940GZZLUBNK",
        "serviceType": "Regular",
        "validTo": "2026-12-23T00:00:00Z",
        "validFrom": "2026-08-03T00:00:00Z"
      }
    ],
    "serviceTypes": [
      {
        "$type": "Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities",
        "name": "Regular",
        "uri": "/Line/Route?ids=Waterloo & City&serviceTypes=Regular"
      }
    ],
    "crowding": {
      "$type": "Tfl.Api.Presentation.Entities.Crowding, Tfl.Api.Presentation.Entities"
    }
  }
]
```

Status severity number should always be preferred rather than directly using the strings such as "Minor Delays".
If the status severity number is missing or does not match 0 to 20, that disruption should be ignored and discarded.
Other than that, there are no strict requirements on how you should handle missing data fields, as long as the application doesnt crash
when some fields are absent from the API, although this is rare.

2. Get all arrivals per line: https://api.tfl.gov.uk/Line/{lineId}/Arrivals/
   After that you can filter arrivals for a specific station matching the "naptanId" field.

This endpoint returns data in the following format:

```
[{
    "id": "string",
    "operationType": 0,
    "vehicleId": "string",
    "naptanId": "string",
    "stationName": "string",
    "lineId": "string",
    "lineName": "string",
    "platformName": "string",
    "direction": "string",
    "bearing": "string",
    "destinationNaptanId": "string",
    "destinationName": "string",
    "timestamp": "string",
    "timeToStation": 0,
    "currentLocation": "string",
    "towards": "string",
    "expectedArrival": "string",
    "timeToLive": "string",
    "modeName": "string",
    "timing": {
        "countdownServerAdjustment": "string",
        "source": "string",
        "insert": "string",
        "read": "string",
        "sent": "string",
        "received": "string"
    }
}]
```

For example:

```
{
    "$type": "Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities",
    "id": "-712910209",
    "operationType": 1,
    "vehicleId": "315",
    "naptanId": "940GZZLUBDS",
    "stationName": "Bounds Green Underground Station",
    "lineId": "piccadilly",
    "lineName": "Piccadilly",
    "platformName": "Westbound - Platform 2",
    "direction": "inbound",
    "bearing": "",
    "destinationNaptanId": "940GZZLUHR5",
    "destinationName": "Heathrow Terminal 5 Underground Station",
    "timestamp": "2026-08-09T22:18:59.6814658Z",
    "timeToStation": 68,
    "currentLocation": "Approaching Bounds Green",
    "towards": "Heathrow T123 + 5",
    "expectedArrival": "2026-08-09T22:20:07Z",
    "timeToLive": "2026-08-09T22:20:07Z",
    "modeName": "tube",
    "timing": {
      "$type": "Tfl.Api.Presentation.Entities.PredictionTiming, Tfl.Api.Presentation.Entities",
      "countdownServerAdjustment": "00:00:00",
      "source": "0001-01-01T00:00:00",
      "insert": "0001-01-01T00:00:00",
      "read": "2026-08-09T22:19:39.176Z",
      "sent": "2026-08-09T22:18:59Z",
      "received": "0001-01-01T00:00:00"
    }
  }
```

Notes:

- direction should either be "inbound" or "outbound": arrivals whose direction is missing or does not match this, should be discarded.
- none of the fields are guaranteed to be present - there are no strict requirements on how you should handle them (except for those mentioned above) as this is rare,
  but it is important to ensure the software does not crash in these cases.

Based on previous implementations, we filtered out all arrivals with invalid directions and statuses with invalid statusSeverity.
Therefore, these fields are guaranteed to be present.
Other than that, you can make any reasonable assumptions to missing fields, as long as the app is robust and does not crash.

## Tech stack

Backend

- Python 3.12
- FastAPI
- httpx
- Pydantic
- uv

Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
