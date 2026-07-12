export interface Line {
  id: string;
  name: string;
  color: string;
}

export interface Station {
  id: string;
  name: string;
  code: string;
  lines: Line[];
}

export interface ArrivalBoardEntry {
  index: number;
  destination_name: string;
  time_display: string;
  platform: string;
}

export interface ArrivalBoard {
  direction: string;
  entries: ArrivalBoardEntry[];
}
