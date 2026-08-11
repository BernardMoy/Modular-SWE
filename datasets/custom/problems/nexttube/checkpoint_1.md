# Part 1: Displaying arrival boards

## Introduction

You are building a website that shows enhanced London Underground (Tube) information.
Across the entire project, you will only be working with the 11 underground lines specified in `data/tube-lines.json`.
You will also only be working with 272 tube stations listed in `data/tube-stations.json`.

## Requirements

### Home page

- Search for stations using its station name, or its 3 letter code.
- The 3 letter code is the last 3 letters for the station id (940GZZLUXXX). Except for Nine Elms and Battersea Power Station, use NIE and BPS for their internal station code respectively.

### Select line

- Select the line to display arrivals only when the station is served by multiple lines.

### Board

- Display tube arrivals, classified by the platform direction (Northbound, Eastbound, Southbound, Westbound). One board is used per direction, showing all train arrivals sorted by time.
- Each train arrival is displayed with: 1. Index (1,2,3) 2. Destination name 3. Time in minutes in the format of X min (Due if less than 30 seconds) 4. Platform number
- The same train may show up in multiple platforms separately in the data: In this case you should merge them into one arrival board entry. Use the vehicle id to group arrivals together. For example, if a vehicle 123 show up in both "Westbound - Platform 1" and "Westbound - Platform 2", the platform number in the arrival board should show "1,2". If no platform numbers can be identified, show "-"

## Site hierarchy

Home -> Select Line -> Board (If the station is served by multiple lines)
Home -> Board (If the station is only served by one line)

## API endpoints

You will be using the TfL Unified API which does not require an API key to use for the usage frequency that we need.

Get all arrivals per line: https://api.tfl.gov.uk/Line/{lineId}/Arrivals/

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

Note that none of the fields are guaranteed to be present.

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
