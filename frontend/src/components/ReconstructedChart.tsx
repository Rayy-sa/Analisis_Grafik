import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TablePayload } from "../lib/types";

const PALETTE = ["#C26A3A", "#3F5C4E", "#8A6A3B", "#6B4F7A", "#2F4A6A"];

function isNumeric(value: unknown): boolean {
  if (value === null || value === "") return false;
  if (typeof value === "number") return Number.isFinite(value);
  const n = Number(String(value).replace("%", "").replace(",", "."));
  return Number.isFinite(n);
}

function toNumber(value: unknown): number | null {
  if (!isNumeric(value)) return null;
  if (typeof value === "number") return value;
  return Number(String(value).replace("%", "").replace(",", "."));
}

type Props = {
  table: TablePayload;
};

export function ReconstructedChart({ table }: Props) {
  if (!table.columns.length || !table.rows.length) {
    return <p className="text-sm text-mute">Belum ada deret yang bisa digambar ulang.</p>;
  }

  const xKey = table.columns[0];
  const series = table.columns.slice(1).filter((col) => table.rows.some((row) => isNumeric(row[col])));

  if (!series.length) {
    return <p className="text-sm text-mute">Kolom numerik tidak terdeteksi untuk rekonstruksi chart.</p>;
  }

  const data = table.rows.map((row) => {
    const point: Record<string, string | number> = { [xKey]: String(row[xKey] ?? "") };
    for (const col of series) {
      const n = toNumber(row[col]);
      if (n !== null) point[col] = n;
    }
    return point;
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E6DCCE" strokeDasharray="3 6" />
          <XAxis dataKey={xKey} tick={{ fill: "#6B645B", fontSize: 12 }} axisLine={{ stroke: "#DDD4C6" }} />
          <YAxis tick={{ fill: "#6B645B", fontSize: 12 }} axisLine={{ stroke: "#DDD4C6" }} />
          <Tooltip
            contentStyle={{
              background: "#FAF7F1",
              border: "1px solid #DDD4C6",
              borderRadius: 12,
              fontSize: 13,
            }}
          />
          <Legend />
          {series.map((col, index) => (
            <Line
              key={col}
              type="monotone"
              dataKey={col}
              stroke={PALETTE[index % PALETTE.length]}
              strokeWidth={2.2}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
