import type { Line } from "../types";

export default function LineList({
  lines,
  onSelect,
}: {
  lines: Line[];
  onSelect: (line: Line) => void;
}) {
  return (
    <ul className="flex flex-col gap-3">
      {lines.map((line) => (
        <li key={line.id}>
          <button
            onClick={() => onSelect(line)}
            className="flex w-full items-center gap-4 rounded-lg border border-slate-200 px-4 py-4 text-left shadow-sm hover:bg-slate-50"
          >
            <span
              className="h-4 w-4 shrink-0 rounded-full"
              style={{ backgroundColor: line.color }}
            />
            <span className="font-medium text-slate-900">{line.name}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
