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

Get statuses of all lines: https://api.tfl.gov.uk/Line/bakerloo,central,circle,district,hammersmith-city,jubilee,metropolitan,northern,piccadilly,victoria,waterloo-city/Status/2026-07-11/to/2026-07-12?detail=true
(Replace the date with the actual date).
Get all arrivals per line: https://api.tfl.gov.uk/Line/{lineId}/Arrivals/

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
