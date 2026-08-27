# Part 2: Line and Station Statuses

## Introduction

The website should now also feature displaying underground line statuses and station statuses.

## Requirements

### Home page

- Add a section displaying underground line statuses. Each line should consist of its line name, followed by multiple disruption severity, and for each severity, indicate the route sections affected, followed by the reason.
- Do not show lines with Good Service.
- Route sections: Only the start and end station names should be displayed on a sequence in the form of start --> end; bidirectional sequences should be merged together in the form of start <--> end.
- Disruption reasons should be toggleable when clicking on the line, either all reasons are visible or all are hidden (by default).

Example:

```
-----------------------------------------------------
Piccadilly
Part Closure
Heathrow Terminal 4 <--> Hammersmith (Dist&Picc Line)
Hammersmith (Dist&Picc Line) <--> Uxbridge
Hammersmith (Dist&Picc Line) <--> Heathrow Terminal 5

[Reason]

Severe Delays
Arnos Grove --> Cockfosters

[Reason]
-----------------------------------------------------
Central
...
```

Note that you do not need to strictly follow the order of route sections affected, it would be accepted as long as the displayed information is correct.

### Board

- Display a list of station disruptions above the boards.
- Disruptions with type "Closure" should be colored in red, otherwise they should be colored in blue.

Example:

```
Southwark: Closed - This station is closed due to planned engineering work.

(Arrival boards below)
...
```

## Site hierarchy

Remains unchanged.

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

2. Get station disruptions: https://api.tfl.gov.uk/stopPoint/mode/tube/disruption

This endpoint returns data in the following format:

```
[
    {
    "$type": "Tfl.Api.Presentation.Entities.DisruptedPoint, Tfl.Api.Presentation.Entities",
    "atcoCode": "940GZZLUBSC",
    "fromDate": "2026-07-06T03:30:00Z",
    "toDate": "2026-11-30T01:29:00Z",
    "description": "BARONS COURT STATION: From Monday 6 July until November, westbound trains will not call at Barons Court. If travelling westbound from the station, please use eastbound District or Piccadilly line trains and change to westbound services at West Kensington (on the District line) or Earls Court (on the Piccadilly line) and change to westbound services. If travelling westbound to the station, please continue to Hammersmith and change for eastbound District or Piccadilly line trains.",
    "commonName": "Barons Court Underground Station",
    "type": "Part Closure",
    "mode": "tube",
    "stationAtcoCode": "940GZZLUBSC",
    "appearance": "PlannedWork",
    "closureText": "partClosure",
    "concernedLines": [
      {
        "$type": "Tfl.Api.Presentation.Entities.ConcernedLine, Tfl.Api.Presentation.Entities",
        "id": "circle",
        "direction": "inbound"
      },
      {
        "$type": "Tfl.Api.Presentation.Entities.ConcernedLine, Tfl.Api.Presentation.Entities",
        "id": "district",
        "direction": "inbound"
      },
      {
        "$type": "Tfl.Api.Presentation.Entities.ConcernedLine, Tfl.Api.Presentation.Entities",
        "id": "piccadilly",
        "direction": "inbound"
      }
    ]
  }
]
```

stationAtcoCode is same as NaptanID, stationID. Use that to filter out the correct station.
Again there are no strict requirements on how you should handle missing fields as long as the app does not crash.

3. Get all arrivals per line: https://api.tfl.gov.uk/Line/{lineId}/Arrivals/
   This endpoint is not used here but is for reference in case previous implementation is modified.
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
