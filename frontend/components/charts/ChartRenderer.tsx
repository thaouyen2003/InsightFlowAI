"use client";

import BarChartComponent from "./BarChart";
import LineChartComponent from "./LineChart";
import PieChartComponent from "./PieChart";
import HorizontalBarChartComponent from "./HorizontalBarChart";
import AreaChartComponent from "./AreaChart";
import ScatterChartComponent from "./ScatterChart";


interface ChartRendererProps {
    chart: any;
}


export default function ChartRenderer({
    chart,
}: ChartRendererProps) {
    if (!chart || !chart.type) {
        return null;
    }

    switch (chart.type) {
        case "line":
            return (
                <LineChartComponent
                    chart={chart}
                />
            );

        case "bar":
            return (
                <BarChartComponent
                    chart={chart}
                />
            );

        case "pie":
            return (
                <PieChartComponent
                    chart={chart}
                />
            );
        
        case "horizontal_bar":
            return (
                <HorizontalBarChartComponent
                    chart={chart}
                />
            );

        case "area":
            return (
                <AreaChartComponent
                    chart={chart}
                />
            );

        case "scatter":
            return (
                <ScatterChartComponent
                    chart={chart}
                />
            );

        case "scatter":
        case "histogram":
            return (
                <div className="rounded-xl bg-white p-6 text-slate-900">
                    <h2 className="text-lg font-bold">
                        {chart.title}
                    </h2>

                    <p className="mt-2 text-sm text-slate-500">
                        Biểu đồ {chart.type} sẽ được hỗ trợ
                        ở bước nâng cấp giao diện tiếp theo.
                    </p>
                </div>
            );

        default:
            return (
                <div className="rounded-xl bg-white p-6 text-slate-900">
                    <p className="text-sm text-slate-500">
                        Không hỗ trợ loại biểu đồ:
                        {" "}
                        {chart.type}
                    </p>
                </div>
            );
    }
}