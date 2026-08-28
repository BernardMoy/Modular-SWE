# Part 4: Delay Estimates

## Introduction

Add delay estimates to the live map - an unique feature of the website.

## Requirements

### Live Map

- On the live map, add a number beside each station, or beside the edge between two nodes, indicating the average delays of trains in minutes staying at the station or running in between 2 stations.
- The number is formatted as "+3", "+0", etc. Negative delays should be displayed as "+0". The number should be indicated red if the delay is larger than 10 minutes.
- If there is no data around a station or around a section between 2 stations, do not need to show anything.
- You will be fetching this data from a remote database, showing the current locations of trains with their delays in seconds over the past 10 minutes. The current location controls where the delays are displayed on the live map.
- The data use "trackernetCode" to identify the line instead of line id. Their relation is shown below:
  | lineId | trackernetCode |
  |------------------|----------------|
  | bakerloo | B |
  | central | C |
  | circle | H |
  | district | D |
  | hammersmith-city | H |
  | jubilee | J |
  | metropolitan | M |
  | northern | N |
  | piccadilly | P |
  | victoria | V |
  | waterloo-city | W |
  Because circle and hammersmith-city share the same code, the raw delay estimates data on both lines should be the same. What differs is what stations are present on the line.

## Site hierarchy

Unchanged.

## Redis

You will be fetching the delay estimates from upstash redis with the key `delay-estimates`:

Data format:

```
{
  "data": [
    {
      "trackernetCode": "W",
      "vehicleId": "011",
      "closestStationIdToArrival": "940GZZLUBNK",
      "currentLocation": "At Platform",
      "timeToStation": 0,
      "direction": "inbound",
      "timestamp": 1783857844372,
      "delayedSeconds": 135.23699999976
    },
    {
      "trackernetCode": "V",
      "vehicleId": "216",
      "closestStationIdToArrival": "940GZZLUFPK",
      "currentLocation": "Between Seven Sisters and Finsbury Park",
      "timeToStation": 150,
      "direction": "inbound",
      "timestamp": 1783857907304,
      "delayedSeconds": 0
    }
  ]
  "lastUpdated": 1783857907579
}
```

All of these fields are guaranteed to be present.

`UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` environment variables should be supplied at runtime for the fetch to work.

## Tech stack

Backend

- Python 3.12
- FastAPI
- httpx
- Pydantic
- uv
- Upstash Redis

Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
