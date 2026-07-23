"use client";

import {
    CartesianGrid,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface ScatterPoint {
    x: number;
    y: number;
}

interface ScatterChartProps {
    chart: {
        title?: string;
        x_axis?: string;
        y_axis?: string;
        data?: ScatterPoint[];
    };
}

export default function ScatterChartComponent({
    chart,
}: ScatterChartProps) {

    const data = Array.isArray(chart?.data)
        ? chart.data
        : [];

    if (data.length === 0) {
        return (
            <div className="flex h-full items-center justify-center text-slate-500">
                Không có dữ liệu Scatter Chart
            </div>
        );
    }

    return (
        <div className="h-full w-full">

            <h2 className="mb-5 text-lg font-semibold">
                {chart.title}
            </h2>

            <div className="h-[380px]">

                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >

                    <ScatterChart>

                        <CartesianGrid strokeDasharray="3 3" />

                        <XAxis
                            type="number"
                            dataKey="x"
                            name={chart.x_axis}
                        />

                        <YAxis
                            type="number"
                            dataKey="y"
                            name={chart.y_axis}
                        />

                        <Tooltip />

                        <Scatter
                            data={data}
                            fill="#2563eb"
                        />

                    </ScatterChart>

                </ResponsiveContainer>

            </div>

        </div>
    );
}