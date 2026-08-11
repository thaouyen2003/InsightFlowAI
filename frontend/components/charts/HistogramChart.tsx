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

type ChartValue =
    | string
    | number
    | boolean
    | null;

interface HistogramChartProps {
    chart: {
        title?: string;
        labels?: Array<string | number>;
        values?: number[];
        x?: Array<string | number>;
        y?: number[];
        data?: Array<Record<string, ChartValue>>;
    };
}

export default function HistogramChart({
    chart,
}: HistogramChartProps) {
    const labels = chart.labels ?? chart.x ?? [];
    const values = chart.values ?? chart.y ?? [];

    const histogramData =
        chart.data?.length
            ? chart.data
            : labels.map((label, index) => ({
                  bin: label,
                  count: values[index] ?? 0,
              }));

    if (!histogramData.length) {
        return (
            <div className="p-6">
                <h2 className="text-lg font-bold text-slate-900">
                    {chart.title ?? "Histogram"}
                </h2>

                <p className="mt-3 text-sm text-slate-500">
                    Không có dữ liệu phù hợp để hiển thị histogram.
                </p>
            </div>
        );
    }

    const firstItem = histogramData[0];

    const xKey =
        "bin" in firstItem
            ? "bin"
            : Object.keys(firstItem)[0];

    const yKey =
        "count" in firstItem
            ? "count"
            : Object.keys(firstItem)[1];

    return (
        <div className="h-[360px] w-full">
            <h2 className="mb-5 text-lg font-bold text-slate-900">
                {chart.title ?? "Histogram"}
            </h2>

            <ResponsiveContainer
                width="100%"
                height="90%"
            >
                <BarChart
                    data={histogramData}
                    margin={{
                        top: 10,
                        right: 20,
                        left: 0,
                        bottom: 40,
                    }}
                >
                    <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                    />

                    <XAxis
                        dataKey={xKey}
                        angle={-35}
                        textAnchor="end"
                        interval={0}
                        height={70}
                        tick={{
                            fontSize: 11,
                        }}
                    />

                    <YAxis
                        allowDecimals={false}
                        tick={{
                            fontSize: 11,
                        }}
                    />

                    <Tooltip />

                    <Bar
                        dataKey={yKey}
                        fill="#3b82f6"
                        radius={[6, 6, 0, 0]}
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}