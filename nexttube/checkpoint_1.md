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
