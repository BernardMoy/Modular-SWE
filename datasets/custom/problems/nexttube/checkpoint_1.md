# Part 1: Displaying arrival boards

## Introduction

You are building a website that shows enhanced London Underground (Tube) information.
You will be working with the 11 underground lines specified in `data/tube-lines.json` and the 272 tube stations listed in `data/tube-stations.json`.

## Requirements

### Home page

- Search for stations using its station name, or its 3 letter code, if the search query is part of the substring of the station name or exactly matches the 3 letter code. Case insensitive.
- The 3 letter code is the last 3 letters for the station id, also known as naptan ID (940GZZLUXXX).
  Except for Nine Elms and Battersea Power Station, use NIE and BPS for their internal 3 letter station code respectively.

### Select line

- Select the line to display arrivals only when the station is served by multiple lines: this data is available in the tube-stations.json file directly.

### Board

- Display tube arrivals, classified by the platform direction (Northbound, Eastbound, Southbound, Westbound, Inner Rail, Outer Rail).
  One board is used per direction, showing all train arrivals sorted by time to station.
- The platform direction and platform number can be inferred from the platformName field:
  It will be in the form of "Eastbound - Platform 2" or "Inner Rail - Platform 3"
- Each train arrival entry / row is displayed with:

1. Index (1,2,3)
2. Destination name. The destination name should be inferred from the "towards" string if the "towards" string is present and is not empty (""),
   otherwise, derive the station name from the destinationNaptanId field. If that is also absent, show "Unknown destination".
3. Time in minutes in the format of X min(s) rounded to the nearest minute. "Due" if the time to station in seconds is less than 30.
4. Platform number obtainable from the platformName field, or '-' if cant be inferred.

- The same train may show up in multiple platforms separately in the data: In this case you should merge them into one arrival board entry.
  Use the vehicle id to group arrivals together. For example, if a vehicle 123 show up in both "Westbound - Platform 1" and "Westbound - Platform 2", the platform number in the arrival board should show "1,2".
  The grouped platform numbers should be sorted numerically, not in their first seen order.
  If no platform numbers can be identified, show "-".
  For entries where the vehicle Id is absent, is empty ("") or is "000", keep them as duplicates and do not merge into them.
- If the board is empty, display a message on the board showing "There are no arrivals."

- The board should poll from the API endpoint continuously, refreshing every 30 seconds.

## Site hierarchy

Home -> Select Line -> Board (If the station is served by multiple lines)
Home -> Board (If the station is only served by one line)

## API endpoints

You will be using the TfL Unified API which does not require an API key to use for the usage frequency that we need.

Get all arrivals per line: https://api.tfl.gov.uk/Line/{lineId}/Arrivals/
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
