_TRACKERNET_CODES_BY_LINE_ID = {
    "bakerloo": "B",
    "central": "C",
    "circle": "H",
    "district": "D",
    "hammersmith-city": "H",
    "jubilee": "J",
    "metropolitan": "M",
    "northern": "N",
    "piccadilly": "P",
    "victoria": "V",
    "waterloo-city": "W",
}


def get_trackernet_code(line_id: str) -> str:
    return _TRACKERNET_CODES_BY_LINE_ID[line_id]
