import type { ArrivalBoard } from "../types";

export default function ArrivalBoardCard({ board }: { board: ArrivalBoard }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 shadow-sm">
      <div className="bg-slate-900 px-4 py-2 font-semibold text-white">{board.direction}</div>
      <table className="w-full text-left">
        <tbody className="divide-y divide-slate-200">
          {board.entries.map((entry) => (
            <tr key={entry.index}>
              <td className="w-10 px-4 py-3 text-slate-400">{entry.index}</td>
              <td className="px-4 py-3 font-medium text-slate-900">{entry.destination_name}</td>
              <td className="w-20 px-4 py-3 text-right font-mono text-slate-700">
                {entry.time_display}
              </td>
              <td className="w-24 px-4 py-3 text-right text-slate-500">
                Plat. {entry.platform}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
