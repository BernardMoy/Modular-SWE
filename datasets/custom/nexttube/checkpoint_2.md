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
Piccadilly
Part Closure
Heathrow Terminal 4 <--> Hammersmith (Dist&Picc Line)
Hammersmith (Dist&Picc Line) <--> Uxbridge
Hammersmith (Dist&Picc Line) <--> Heathrow Terminal 5

[Reason]

Severe Delays
Arnos Grove --> Cockfosters

[Reason]
```

Note that you do not need to strictly follow the order of route sections affected, it would be accepted as long as the displayed information is correct.

### Board

- Display a list of station disruptions above the boards.
- Disruptions with type "Closure" should be colored in red, otherwise they should be colored in blue.

## Site hierarchy

Remains unchanged.

## API endpoints

You will be using the TfL Unified API which does not require an API key to use for the usage frequency that we need.

Get statuses of all lines: https://api.tfl.gov.uk/Line/bakerloo,central,circle,district,hammersmith-city,jubilee,metropolitan,northern,piccadilly,victoria,waterloo-city/Status/2026-07-11/to/2026-07-12?detail=true
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

Get station disruptions: https://api.tfl.gov.uk/stopPoint/mode/tube/disruption

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
