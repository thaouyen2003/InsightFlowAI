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
                            top: 10,
                            right: 25,
                            left: 10,
                            bottom: 50,
                        }}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                        />

                        <XAxis
                            dataKey="label"
                            angle={-25}
                            textAnchor="end"
                            interval={0}
                            height={70}
                            tick={{
                                fontSize: 11,
                            }}
                        />

                        <YAxis />

                        <Tooltip />

                        <Bar
                            dataKey="value"
                            name={chart.measure ?? "Value"}
                            fill="#2563eb"
                            radius={[6, 6, 0, 0]}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}