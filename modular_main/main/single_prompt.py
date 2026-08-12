PROMPT = """Help me fix an issue happening in arrival board displays. 
Project: /modular-SWE/datasets/custom/problems/nexttube/implementations_noDesign/checkpoint_1

Given that the tfl api used for displaying live arrivals returns the following format in the /Arrivals endpoint: 
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

Currently, some stations are displayed as Unknown, and I realised that the destination seems to be translated from the destination station (naptan) ID. I want the "towards" string to be displayed as the destination instead as it includes more comprehensive information. Help me implement that change. """

import subprocess 
from ..workspace_helpers.run_agent import run_agent
from ..settings import MODEL, AGENT
import asyncio 

def workflow(): 
    print("[1/2] Agent sign in")
    subprocess.run([
            "python", "-m", "modular_main.login"
        ], check=True)

    print("[2/2] Run prompt")
    result = asyncio.run(run_agent(AGENT, MODEL, PROMPT))
    print(result) 

if __name__ == "__main__": 
    workflow() 