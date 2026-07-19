"use client";

import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface AreaChartData {
    x: string;
    y: number;
}

interface AreaChartProps {
    chart: {
        title?: string;
        x_axis?: string;
        y_axis?: string;
        data?: AreaChartData[];
    };
}

export default function AreaChartComponent({
    chart,
}: AreaChartProps) {
    const data = Array.isArray(chart?.data)
        ? chart.data
        : [];

    if (data.length === 0) {
        return (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">
                Không có dữ liệu cho Area Chart
            </div>
        );
    }

    return (
        <div className="h-full w-full">
            <h2 className="mb-5 text-lg font-semibold text-slate-800">
                {chart.title || "Area Chart"}
            </h2>

            <div className="h-[340px] w-full">
                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >
                    <AreaChart
                        data={data}
                        margin={{
                            top: 10,
                            right: 20,
                            left: 10,
                            bottom: 35,
                        }}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                        />

                        <XAxis
                            dataKey="x"
                            angle={-25}
                            textAnchor="end"
                            height={70}
                            tick={{
                                fontSize: 12,
                            }}
                        />

                        <YAxis
                            tick={{
                                fontSize: 12,
                            }}
                        />

                        <Tooltip />

                        <Area
                            type="monotone"
                            dataKey="y"
                            stroke="#2563eb"
                            fill="#93c5fd"
                            fillOpacity={0.55}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}