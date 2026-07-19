"use client";

import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
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
                    <LineChart
                        data={chart.data}
                        margin={{
                            top: 10,
                            right: 25,
                            left: 10,
                            bottom: 20,
                        }}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                        />

                        <XAxis
                            dataKey="x"
                            tick={{
                                fontSize: 12,
                            }}
                            minTickGap={25}
                        />

                        <YAxis
                            tick={{
                                fontSize: 12,
                            }}
                        />

                        <Tooltip />

                        <Line
                            type="monotone"
                            dataKey="y"
                            name={chart.y_axis ?? "Value"}
                            stroke="#2563eb"
                            strokeWidth={3}
                            dot={{
                                r: 3,
                            }}
                            activeDot={{
                                r: 6,
                            }}
                            connectNulls
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}