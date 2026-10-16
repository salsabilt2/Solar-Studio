import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Daily } from "./api";

export default function EnergyChart({ data }: { data: Daily[] }) {
  return (
    <div
      className="energy-chart"
      role="img"
      aria-label="Estimated daily electricity in kilowatt-hours"
    >
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart
          data={data}
          margin={{ top: 16, right: 5, left: -25, bottom: 0 }}
        >
          <defs>
            <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#dfb85b" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#dfb85b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#e4e9df" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => date.slice(5)}
            minTickGap={24}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#72847b", fontSize: 11 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#72847b", fontSize: 11 }}
          />
          <ChartTooltip
            formatter={(value) => [
              `${Number(value).toFixed(2)} kWh`,
              "Estimated",
            ]}
          />
          <Area
            type="monotone"
            dataKey="kwh"
            stroke="#b9862d"
            strokeWidth={3}
            fill="url(#chartFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
