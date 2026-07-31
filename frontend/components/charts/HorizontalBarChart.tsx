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

interface HorizontalBarData {
    label: string;
    value: number;
}

interface HorizontalBarChartProps {
    chart: {
        title?: string;
        data?: HorizontalBarData[];
    };
}

export default function HorizontalBarChartComponent({
    chart,
}: HorizontalBarChartProps) {
    const data = Array.isArray(chart?.data)
        ? chart.data
        : [];

    console.log(
        "HORIZONTAL BAR DATA:",
        data
    );

    if (data.length === 0) {
        return (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">
                Không có dữ liệu cho Horizontal Bar
            </div>
        );
    }

    return (
        <div className="h-full w-full">
            <h2 className="mb-5 text-lg font-semibold text-slate-800">
                {chart.title ||
                    "Horizontal Bar Chart"}
            </h2>

            <div className="h-[420px] w-full">
                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{
                            top: 10,
                            right: 30,
                            left: 70,
                            bottom: 10,
                        }}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                        />

                        <XAxis
                            type="number"
                            tick={{
                                fontSize: 12,
                            }}
                        />

                        <YAxis
                            type="category"
                            dataKey="label"
                            width={180}
                            tick={{
                                fontSize: 11,
                            }}
                        />

                        <Tooltip />

                        <Bar
                            dataKey="value"
                            fill="#44bbff"
                            radius={[
                                0,
                                6,
                                6,
                                0,
                            ]}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}