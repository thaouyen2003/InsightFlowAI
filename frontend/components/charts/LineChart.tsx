"use client";

// import {
//     CartesianGrid,
//     Line,
//     LineChart,
//     ResponsiveContainer,
//     Tooltip,
//     XAxis,
//     YAxis,
// } from "recharts";

import {
    ComposedChart,
    Area,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
interface LineChartPoint {
    x: string;
    y: number;
}


interface LineChartData {
    id?: string;
    type: "line";
    title: string;
    x_axis?: string;
    y_axis?: string;
    aggregation?: string;
    data: LineChartPoint[];
    score?: number;
    reason?: string;
}


interface LineChartComponentProps {
    chart: LineChartData;
}


export default function LineChartComponent({
    chart,
}: LineChartComponentProps) {
    if (
        !chart ||
        !Array.isArray(chart.data) ||
        chart.data.length === 0
    ) {
        return (
            <div className="rounded-xl bg-white p-6 text-slate-900">
                <h2 className="mb-3 text-lg font-bold">
                    {chart?.title ?? "Line Chart"}
                </h2>

                <p className="text-sm text-slate-500">
                    Không có dữ liệu hợp lệ để hiển thị biểu đồ.
                </p>
            </div>
        );
    }

    return (
       <div className="h-[430px] rounded-xl bg-white p-6 text-slate-900 shadow-sm border border-slate-100">
            <div className="mb-5">
                <h2 className="text-lg font-bold">
                    {chart.title}
                </h2>

                {chart.reason && (
                    <p className="mt-1 text-sm text-slate-500">
                        {chart.reason}
                    </p>
                )}
            </div>

            <div className="h-[330px] w-full">
                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >
                    <ComposedChart
                        data={chart.data}
                        margin={{
                            top: 10,
                            right: 25,
                            left: 10,
                            bottom: 20,
                        }}
                    >
                        <defs>

                            {/* Line Gradient */}

                            <linearGradient
                                id="lineGradient"
                                x1="0"
                                y1="0"
                                x2="1"
                                y2="0"
                            >
                                <stop
                                    offset="0%"
                                    stopColor="#06B6D4"
                                />
                                <stop
                                    offset="50%"
                                    stopColor="#3B82F6"
                                />
                                <stop
                                    offset="100%"
                                    stopColor="#7C3AED"
                                />
                            </linearGradient>

                            {/* Area Gradient */}

                            <linearGradient
                                id="areaGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor="#3B82F6"
                                    stopOpacity={0.28}
                                />
                                <stop
                                    offset="100%"
                                    stopColor="#3B82F6"
                                    stopOpacity={0}
                                />
                            </linearGradient>

                            {/* Glow */}

                            {/* <filter
                                id="lineGlow"
                                x="-50%"
                                y="-50%"
                                width="200%"
                                height="200%"
                            >
                                <feGaussianBlur
                                    stdDeviation="4"
                                    result="blur"
                                />

                                <feMerge>
                                    <feMergeNode in="blur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter> */}

                        </defs>

                        <CartesianGrid
                            stroke="#E2E8F0"
                            strokeDasharray="4 4"
                            vertical={false}
                        />

                        <XAxis
                            dataKey="x"
                            axisLine={false}
                            tickLine={false}
                            tick={{
                                fontSize: 12,
                                fill: "#64748B",
                            }}
                            minTickGap={25}
                        />

                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{
                                fontSize: 12,
                                fill: "#64748B",
                            }}
                        />

                        <Tooltip
                            cursor={{
                                stroke: "#93C5FD",
                                strokeWidth: 1,
                            }}
                            contentStyle={{
                                borderRadius: "12px",
                                border: "1px solid #E2E8F0",
                                background: "#FFFFFF",
                                boxShadow:
                                    "0 8px 20px rgba(15,23,42,0.12)",
                            }}
                            labelStyle={{
                                fontWeight: 600,
                                color: "#0F172A",
                            }}
                        />

                        <Area
                            type="monotone"
                            dataKey="y"
                            stroke="none"
                            fill="url(#areaGradient)"
                        />

                        <Line
                            type="monotone"
                            dataKey="y"
                            name={chart.y_axis ?? "Value"}
                            stroke="url(#lineGradient)"
                            strokeWidth={2.5}
                            connectNulls
                            animationDuration={1000}
                            animationEasing="ease-out"
                            dot={{
                                r: 3,
                                fill: "#3B82F6",
                                stroke: "#FFFFFF",
                                strokeWidth: 1.5,
                            }}
                            activeDot={{
                                r: 5,
                                fill: "#3B82F6",
                                stroke: "#FFFFFF",
                                strokeWidth: 2,
                            }}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}