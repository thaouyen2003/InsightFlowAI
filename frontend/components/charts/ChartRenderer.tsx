"use client";

import type {
    ComponentProps,
} from "react";

import AreaChartComponent from "./AreaChart";
import BarChartComponent from "./BarChart";
import HistogramChart from "./HistogramChart";
import HorizontalBarChartComponent from "./HorizontalBarChart";
import LineChartComponent from "./LineChart";
import PieChartComponent from "./PieChart";
import ScatterChartComponent from "./ScatterChart";

type LineChartData =
    ComponentProps<
        typeof LineChartComponent
    >["chart"] & {
        type: "line";
    };

type BarChartData =
    ComponentProps<
        typeof BarChartComponent
    >["chart"] & {
        type: "bar";
    };

type PieChartData =
    ComponentProps<
        typeof PieChartComponent
    >["chart"] & {
        type: "pie";
    };

type HorizontalBarChartData =
    ComponentProps<
        typeof HorizontalBarChartComponent
    >["chart"] & {
        type: "horizontal_bar";
    };

type AreaChartData =
    ComponentProps<
        typeof AreaChartComponent
    >["chart"] & {
        type: "area";
    };

type ScatterChartData =
    ComponentProps<
        typeof ScatterChartComponent
    >["chart"] & {
        type: "scatter";
    };

type HistogramChartData =
    ComponentProps<
        typeof HistogramChart
    >["chart"] & {
        type: "histogram";
    };

type ChartRendererData =
    | LineChartData
    | BarChartData
    | PieChartData
    | HorizontalBarChartData
    | AreaChartData
    | ScatterChartData
    | HistogramChartData;

interface ChartRendererProps {
    chart: ChartRendererData;
}

export default function ChartRenderer({
    chart,
}: ChartRendererProps) {
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

        case "histogram":
            return (
                <HistogramChart
                    chart={chart}
                />
            );

        default: {
            const unsupportedChart: never =
                chart;

            return (
                <div className="rounded-xl bg-white p-6 text-slate-900">
                    <p className="text-sm text-slate-500">
                        Không hỗ trợ loại biểu đồ.
                    </p>

                    <span className="hidden">
                        {String(
                            unsupportedChart,
                        )}
                    </span>
                </div>
            );
        }
    }
}