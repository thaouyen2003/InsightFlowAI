"use client";

import {
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
} from "recharts";


interface PieChartPoint {
    name: string;
    value: number;
}


interface PieChartData {
    id?: string;
    type: "pie";
    title: string;
    dimension?: string;
    measure?: string;
    aggregation?: string;
    data: PieChartPoint[];
    score?: number;
    reason?: string;
}


interface PieChartComponentProps {
    chart: PieChartData;
}


const COLORS = [
    "#2563eb",
    "#06b6d4",
    "#8b5cf6",
    "#f59e0b",
    "#10b981",
    "#ef4444",
];


export default function PieChartComponent({
    chart,
}: PieChartComponentProps) {
    if (
        !chart ||
        !Array.isArray(chart.data) ||
        chart.data.length === 0
    ) {
        return (
            <div className="rounded-xl bg-white p-6 text-slate-900">
                <h2 className="mb-3 text-lg font-bold">
                    {chart?.title ?? "Pie Chart"}
                </h2>

                <p className="text-sm text-slate-500">
                    Không có dữ liệu hợp lệ để hiển thị biểu đồ.
                </p>
            </div>
        );
    }

    return (
        <div className="h-[430px] rounded-xl bg-white p-6 text-slate-900">
            <div className="mb-3">
                <h2 className="text-lg font-bold">
                    {chart.title}
                </h2>

                {chart.reason && (
                    <p className="mt-1 text-sm text-slate-500">
                        {chart.reason}
                    </p>
                )}
            </div>

            <div className="h-[340px] w-full">
                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >
                    <PieChart>
                        <Pie
                            data={chart.data}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="45%"
                            outerRadius={110}
                            label
                        >
                            {chart.data.map(
                                (_, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={
                                            COLORS[
                                                index %
                                                COLORS.length
                                            ]
                                        }
                                    />
                                ),
                            )}
                        </Pie>

                        <Tooltip />

                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}