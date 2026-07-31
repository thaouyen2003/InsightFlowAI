"use client";

import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";


interface BarChartPoint {
    label: string;
    value: number;
}


interface BarChartData {
    id?: string;
    type: "bar";
    title: string;
    dimension?: string;
    measure?: string;
    aggregation?: string;
    data: BarChartPoint[];
    score?: number;
    reason?: string;
}


interface BarChartComponentProps {
    chart: BarChartData;
}


export default function BarChartComponent({
    chart,
}: BarChartComponentProps) {
    if (
        !chart ||
        !Array.isArray(chart.data) ||
        chart.data.length === 0
    ) {
        return (
            <div className="rounded-xl bg-white p-6 text-slate-900">
                <h2 className="mb-3 text-lg font-bold">
                    {chart?.title ?? "Bar Chart"}
                </h2>

                <p className="text-sm text-slate-500">
                    Không có dữ liệu hợp lệ để hiển thị biểu đồ.
                </p>
            </div>
        );
    }

    return (
        <div className="h-[430px] rounded-xl bg-white p-6 text-slate-900">
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
                    <BarChart
                        data={chart.data}
                        margin={{
                            top: 16,
                            right: 25,
                            left: 10,
                            bottom: 50,
                        }}
                        barCategoryGap="28%"
                    >
                        <defs>
                            <linearGradient
                                id="barGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="0%"
                                    stopColor="#60A5FA"
                                />
                                <stop
                                    offset="45%"
                                    stopColor="#3B82F6"
                                />
                                <stop
                                    offset="100%"
                                    stopColor="#7C3AED"
                                />
                            </linearGradient>

                            <filter
                                id="barShadow"
                                x="-20%"
                                y="-20%"
                                width="140%"
                                height="140%"
                            >
                                <feDropShadow
                                    dx="0"
                                    dy="4"
                                    stdDeviation="4"
                                    floodColor="#2563EB"
                                    floodOpacity="0.18"
                                />
                            </filter>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="4 4"
                            vertical={false}
                            stroke="#E2E8F0"
                            strokeOpacity={0.8}
                        />

                        <XAxis
                            dataKey="label"
                            angle={-25}
                            textAnchor="end"
                            interval={0}
                            height={70}
                            axisLine={false}
                            tickLine={false}
                            tick={{
                                fontSize: 11,
                                fill: "#64748B",
                                fontWeight: 500,
                            }}
                        />

                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{
                                fontSize: 11,
                                fill: "#64748B",
                            }}
                        />

                        <Tooltip
                            cursor={{
                                fill: "#EFF6FF",
                                opacity: 0.55,
                            }}
                            contentStyle={{
                                borderRadius: "12px",
                                border: "1px solid #DBEAFE",
                                backgroundColor: "rgba(255, 255, 255, 0.96)",
                                boxShadow:
                                    "0 10px 25px rgba(15, 23, 42, 0.12)",
                                padding: "10px 14px",
                            }}
                            labelStyle={{
                                color: "#0F172A",
                                fontWeight: 600,
                                marginBottom: "4px",
                            }}
                            itemStyle={{
                                color: "#25b0eb",
                                fontWeight: 600,
                            }}
                        />

                        <Bar
                            dataKey="value"
                            name={chart.measure ?? "Value"}
                            fill="url(#barGradient)"
                            radius={[10, 10, 2, 2]}
                            maxBarSize={52}
                            filter="url(#barShadow)"
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}