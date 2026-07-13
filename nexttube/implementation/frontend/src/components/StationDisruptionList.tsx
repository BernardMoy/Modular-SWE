import type { StationDisruption } from "../types";

export default function StationDisruptionList({
  disruptions,
}: {
  disruptions: StationDisruption[];
}) {
  return (
    <ul className="flex flex-col gap-2">
      {disruptions.map((disruption, index) => (
        <li
          key={index}
          className={disruption.type === "Closure" ? "text-red-600" : "text-blue-600"}
        >
          {disruption.description}
        </li>
      ))}
    </ul>
  );
}
