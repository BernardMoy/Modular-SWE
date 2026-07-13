import { useState } from "react";
import type { LineStatusSummary, RouteSection } from "../types";

function formatRouteSection(section: RouteSection): string {
  const arrow = section.bidirectional ? "<-->" : "-->";
  return `${section.start} ${arrow} ${section.end}`;
}

export default function LineStatusCard({ status }: { status: LineStatusSummary }) {
  const [reasonsVisible, setReasonsVisible] = useState(false);

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 shadow-sm">
      <button
        onClick={() => setReasonsVisible((visible) => !visible)}
        className="w-full bg-slate-900 px-4 py-2 text-left font-semibold text-white"
      >
        {status.line_name}
      </button>
      <div className="flex flex-col divide-y divide-slate-200">
        {status.severities.map((severity) => (
          <div key={severity.severity_description} className="px-4 py-3">
            <p className="font-medium text-slate-900">{severity.severity_description}</p>
            <ul className="mt-1 flex flex-col gap-0.5 text-sm text-slate-600">
              {severity.route_sections.map((section) => (
                <li key={`${section.start}-${section.end}`}>{formatRouteSection(section)}</li>
              ))}
            </ul>
            {reasonsVisible && (
              <ul className="mt-2 flex flex-col gap-1 text-sm text-slate-500">
                {severity.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
