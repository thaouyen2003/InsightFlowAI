"use client";

import {
    useEffect,
    useState,
    useSyncExternalStore,
} from "react";

import type { ComponentProps } from "react";

import AIKnowledgeInsightCard from
    "@/components/dashboard/AIKnowledgeInsightCard";

import type { FusionResponse } from
    "@/components/dashboard/AIKnowledgeInsightCard";

import AIInsightPanel from
    "@/components/dashboard/AIInsightPanel";

import KPICard from
    "@/components/dashboard/KPICard";

import ChartRenderer from
    "@/components/charts/ChartRenderer";

import Header from
    "@/components/layout/Header";

import Sidebar from
    "@/components/layout/Sidebar";


type DashboardChart =
    ComponentProps<typeof ChartRenderer>["chart"];

type AIInsight =
    ComponentProps<typeof AIInsightPanel>["insight"];

type KPITitle =
    ComponentProps<typeof KPICard>["title"];

type KPIValue =
    ComponentProps<typeof KPICard>["value"];


interface DashboardKPI {
    title: KPITitle;
    value: KPIValue;
}


interface DashboardResponse {
    charts?: DashboardChart[];
    kpis?: DashboardKPI[];
    llm_insight?: AIInsight | null;
}


const subscribeUploadedFile = () => {
    return () => {};
};


const getUploadedFileSnapshot = () => {
    return localStorage.getItem(
        "uploadedFile"
    );
};


const getUploadedFileServerSnapshot = () => {
    return null;
};


export default function DashboardPage() {
    const uploadedFile = useSyncExternalStore(
        subscribeUploadedFile,
        getUploadedFileSnapshot,
        getUploadedFileServerSnapshot
    );

    const [dashboard, setDashboard] =
        useState<DashboardResponse | null>(
            null
        );

    const [fusion, setFusion] =
        useState<FusionResponse | null>(
            null
        );

    const [loading, setLoading] =
        useState(true);

    const [fusionLoading, setFusionLoading] =
        useState(true);

    const [error, setError] =
        useState("");

    const [fusionError, setFusionError] =
        useState("");

    useEffect(() => {
        if (!uploadedFile) {
            return;
        }

        let isActive = true;

    const loadDashboard = async () => {
        try {
            const response = await fetch(
                "http://127.0.0.1:8000/dashboard",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        filename:
                            uploadedFile,
                    }),
                }
            );

            if (!response.ok) {
                const errorText =
                    await response.text();

                throw new Error(
                    `HTTP ${response.status}: ` +
                    errorText
                );
            }

            const data =
                await response.json() as
                    DashboardResponse;

            if (!isActive) {
                return;
            }

            setDashboard(data);
        } catch (requestError) {
            console.error(
                "Dashboard fetch error:",
                requestError
            );

            if (!isActive) {
                return;
            }

            setError(
                "Không thể tạo dashboard. " +
                "Hãy kiểm tra backend " +
                "và thử lại."
            );
        } finally {
            if (isActive) {
                setLoading(false);
            }
        }
    };

    const loadFusion = async () => {
        try {
            const response = await fetch(
                "http://127.0.0.1:8000/insight-fusion",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        filename:
                            uploadedFile,
                    }),
                }
            );

            if (!response.ok) {
                const errorText =
                    await response.text();

                throw new Error(
                    `HTTP ${response.status}: ` +
                    errorText
                );
            }

            const data =
                await response.json() as
                    FusionResponse;

            if (!isActive) {
                return;
            }

            setFusion(data);
        } catch (requestError) {
            console.error(
                "Insight Fusion fetch error:",
                requestError
            );

            if (!isActive) {
                return;
            }

            setFusionError(
                "Không thể tạo AI Knowledge " +
                "Insight. Hãy kiểm tra dịch vụ " +
                "RAG và thử lại."
            );
        } finally {
            if (isActive) {
                setFusionLoading(false);
            }
        }
    };

        void loadDashboard();
        void loadFusion();

        return () => {
            isActive = false;
        };
    }, [uploadedFile]);

    const datasetName =
        uploadedFile ?? "";

    const displayError =
        !uploadedFile
            ? "Không tìm thấy dữ liệu đã tải lên."
            : error;

    const isDashboardLoading =
        Boolean(uploadedFile) && loading;

    const charts =
        dashboard?.charts ?? [];

    const kpis =
        dashboard?.kpis ?? [];

    const lineCharts = charts.filter(
        (chart) => chart.type === "line"
    );

    const otherCharts = charts.filter(
        (chart) => chart.type !== "line"
    );


    return (
        <div
            className="
                flex min-h-screen
                bg-slate-950
                text-white
            "
        >
            <Sidebar />

            <main
                className="
                    min-w-0
                    flex-1
                    overflow-hidden
                "
            >
                <Header />

                <div
                    className="
                        mx-auto
                        max-w-[1600px]
                        space-y-8
                        px-6 py-8
                        lg:px-10
                    "
                >
                    <section
                        className="
                            relative
                            overflow-hidden
                            rounded-3xl
                            border
                            border-white/10
                            bg-gradient-to-br
                            from-slate-900
                            via-slate-900
                            to-blue-950
                            p-6
                            shadow-2xl
                            shadow-black/20
                            lg:p-8
                        "
                    >
                        <div
                            className="
                                absolute
                                -right-24
                                -top-24
                                h-72 w-72
                                rounded-full
                                bg-blue-500/10
                                blur-3xl
                            "
                        />

                        <div
                            className="
                                relative
                                flex flex-col
                                gap-6
                                lg:flex-row
                                lg:items-center
                                lg:justify-between
                            "
                        >
                            <div>
                                <p
                                    className="
                                        text-xs
                                        font-semibold
                                        uppercase
                                        tracking-[0.2em]
                                        text-blue-300
                                    "
                                >
                                    InsightFlowAI
                                </p>

                                <h1
                                    className="
                                        mt-3
                                        text-3xl
                                        font-bold
                                        tracking-tight
                                        text-white
                                        lg:text-4xl
                                    "
                                >
                                    Smart Data Dashboard
                                </h1>

                                <p
                                    className="
                                        mt-3
                                        max-w-2xl
                                        text-sm
                                        leading-6
                                        text-slate-400
                                        lg:text-base
                                    "
                                >
                                    Tổng hợp KPI, biểu đồ
                                    và nhận định AI từ
                                    dữ liệu đã tải lên.
                                </p>
                            </div>

                            <div
                                className="
                                    min-w-[260px]
                                    rounded-2xl
                                    border
                                    border-white/10
                                    bg-white/5
                                    p-4
                                    backdrop-blur
                                "
                            >
                                <p
                                    className="
                                        text-xs
                                        uppercase
                                        tracking-wider
                                        text-slate-500
                                    "
                                >
                                    Dataset đang phân tích
                                </p>

                                <p
                                    className="
                                        mt-2
                                        truncate
                                        font-semibold
                                        text-blue-300
                                    "
                                    title={datasetName}
                                >
                                    {datasetName ||
                                        "No dataset"}
                                </p>

                                <div
                                    className="
                                        mt-3
                                        flex items-center
                                        gap-2
                                        text-xs
                                        text-emerald-300
                                    "
                                >
                                    <span
                                        className="
                                            h-2 w-2
                                            rounded-full
                                            bg-emerald-400
                                        "
                                    />

                                    Hệ thống sẵn sàng
                                </div>
                            </div>
                        </div>
                    </section>

                    {isDashboardLoading && (
                        <section
                            className="
                                flex min-h-[340px]
                                items-center
                                justify-center
                                rounded-3xl
                                border
                                border-white/10
                                bg-white/[0.03]
                            "
                        >
                            <div className="text-center">
                                <div
                                    className="
                                        mx-auto
                                        h-10 w-10
                                        animate-spin
                                        rounded-full
                                        border-4
                                        border-slate-700
                                        border-t-blue-400
                                    "
                                />

                                <p
                                    className="
                                        mt-4
                                        text-sm
                                        text-slate-400
                                    "
                                >
                                    Đang phân tích dữ liệu
                                    và tạo dashboard...
                                </p>
                            </div>
                        </section>
                    )}

                    {!isDashboardLoading && displayError && (
                        <section
                            className="
                                rounded-3xl
                                border
                                border-red-400/20
                                bg-red-400/5
                                p-6
                            "
                        >
                            <h2
                                className="
                                    font-semibold
                                    text-red-200
                                "
                            >
                                Không thể tải dashboard
                            </h2>

                            <p
                                className="
                                    mt-2
                                    text-sm
                                    text-red-100/70
                                "
                            >
                                {displayError}
                            </p>
                        </section>
                    )}

                    {!isDashboardLoading &&
                    !displayError &&
                    dashboard && (
                            <>
                                <section>
                                    <div
                                        className="
                                            mb-4
                                            flex items-end
                                            justify-between
                                            gap-4
                                        "
                                    >
                                        <div>
                                            <p
                                                className="
                                                    text-xs
                                                    font-semibold
                                                    uppercase
                                                    tracking-[0.18em]
                                                    text-blue-300
                                                "
                                            >
                                                Overview
                                            </p>

                                            <h2
                                                className="
                                                    mt-1
                                                    text-xl
                                                    font-bold
                                                    text-white
                                                "
                                            >
                                                Chỉ số tổng quan
                                            </h2>
                                        </div>

                                        <span
                                            className="
                                                rounded-full
                                                border
                                                border-white/10
                                                bg-white/5
                                                px-3 py-1
                                                text-xs
                                                text-slate-400
                                            "
                                        >
                                            {kpis.length} KPI
                                        </span>
                                    </div>

                                    <div
                                        className="
                                            grid
                                            grid-cols-1
                                            gap-4
                                            sm:grid-cols-2
                                            xl:grid-cols-4
                                        "
                                    >
                                       {kpis.map(
                                            (
                                                kpi,
                                                index
                                            ) => (
                                                <KPICard
                                                    key={
                                                        index
                                                    }
                                                    title={
                                                        kpi.title
                                                    }
                                                    value={
                                                        kpi.value
                                                    }
                                                />
                                            )
                                        )}
                                    </div>
                                </section>

                                {lineCharts.length >
                                    0 && (
                                        <section>
                                            <div className="mb-4">
                                                <p
                                                    className="
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-[0.18em]
                                                        text-blue-300
                                                    "
                                                >
                                                    Trend Analysis
                                                </p>

                                                <h2
                                                    className="
                                                        mt-1
                                                        text-xl
                                                        font-bold
                                                        text-white
                                                    "
                                                >
                                                    Phân tích xu hướng
                                                </h2>
                                            </div>

                                            <div className="space-y-6">
                                                {lineCharts.map(
                                                    (
                                                        chart,
                                                        index:
                                                            number
                                                    ) => (
                                                        <article
                                                            key={
                                                                index
                                                            }
                                                            className="
                                                                min-h-[420px]
                                                                overflow-hidden
                                                                rounded-3xl
                                                                border
                                                                border-white/10
                                                                bg-white
                                                                p-5
                                                                shadow-xl
                                                                shadow-black/20
                                                                lg:p-6
                                                            "
                                                        >
                                                            <ChartRenderer
                                                                chart={
                                                                    chart
                                                                }
                                                            />
                                                        </article>
                                                    )
                                                )}
                                            </div>
                                        </section>
                                    )}

                                {otherCharts.length >
                                    0 && (
                                        <section>
                                            <div
                                                className="
                                                    mb-4
                                                    flex items-end
                                                    justify-between
                                                    gap-4
                                                "
                                            >
                                                <div>
                                                    <p
                                                        className="
                                                            text-xs
                                                            font-semibold
                                                            uppercase
                                                            tracking-[0.18em]
                                                            text-violet-300
                                                        "
                                                    >
                                                        Data Distribution
                                                    </p>

                                                    <h2
                                                        className="
                                                            mt-1
                                                            text-xl
                                                            font-bold
                                                            text-white
                                                        "
                                                    >
                                                        Cơ cấu dữ liệu
                                                    </h2>
                                                </div>

                                                <span
                                                    className="
                                                        text-xs
                                                        text-slate-500
                                                    "
                                                >
                                                    {
                                                        otherCharts.length
                                                    }{" "}
                                                    biểu đồ
                                                </span>
                                            </div>

                                            <div
                                                className="
                                                    grid
                                                    grid-cols-1
                                                    gap-6
                                                    xl:grid-cols-2
                                                "
                                            >
                                                {otherCharts.map(
                                                    (
                                                        chart,
                                                        index:
                                                            number
                                                    ) => (
                                                        <article
                                                            key={
                                                                index
                                                            }
                                                            className="
                                                                min-h-[390px]
                                                                overflow-hidden
                                                                rounded-3xl
                                                                border
                                                                border-white/10
                                                                bg-white
                                                                p-5
                                                                shadow-xl
                                                                shadow-black/20
                                                                lg:p-6
                                                            "
                                                        >
                                                            <ChartRenderer
                                                                chart={
                                                                    chart
                                                                }
                                                            />
                                                        </article>
                                                    )
                                                )}
                                            </div>
                                        </section>
                                    )}

                                {charts.length ===
                                    0 && (
                                        <section
                                            className="
                                                rounded-3xl
                                                border
                                                border-dashed
                                                border-white/15
                                                bg-white/[0.03]
                                                p-10
                                                text-center
                                            "
                                        >
                                            <h2
                                                className="
                                                    text-lg
                                                    font-semibold
                                                    text-white
                                                "
                                            >
                                                Chưa có biểu đồ phù hợp
                                            </h2>

                                            <p
                                                className="
                                                    mt-2
                                                    text-sm
                                                    text-slate-400
                                                "
                                            >
                                                Dataset hiện tại chưa
                                                có đủ trường dữ liệu
                                                phù hợp để trực quan hóa.
                                            </p>
                                        </section>
                                    )}

                                {dashboard
                                    ?.llm_insight && (
                                        <section>
                                            <div className="mb-4">
                                                <p
                                                    className="
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-[0.18em]
                                                        text-violet-300
                                                    "
                                                >
                                                    AI Decision Support
                                                </p>

                                                <h2
                                                    className="
                                                        mt-1
                                                        text-xl
                                                        font-bold
                                                        text-white
                                                    "
                                                >
                                                    Phân tích và khuyến nghị
                                                </h2>
                                            </div>

                                            <AIInsightPanel
                                                insight={
                                                    dashboard.llm_insight
                                                }
                                            />
                                        </section>
                                    )}

                                <section>
                                    <div className="mb-4">
                                        <p
                                            className="
                                                text-xs
                                                font-semibold
                                                uppercase
                                                tracking-[0.18em]
                                                text-cyan-300
                                            "
                                        >
                                            Knowledge Decision Support
                                        </p>

                                        <h2
                                            className="
                                                mt-1
                                                text-xl
                                                font-bold
                                                text-white
                                            "
                                        >
                                            Phân tích dữ liệu kết hợp tri thức
                                        </h2>

                                        <p
                                            className="
                                                mt-2
                                                text-sm
                                                leading-6
                                                text-slate-400
                                            "
                                        >
                                            Insight được tổng hợp từ dữ liệu
                                            đã tải lên và kho tri thức RAG.
                                        </p>
                                    </div>

                                    {fusionLoading && (
                                        <div
                                            className="
                                                flex
                                                min-h-[260px]
                                                items-center
                                                justify-center
                                                rounded-3xl
                                                border
                                                border-cyan-400/10
                                                bg-cyan-400/[0.03]
                                            "
                                        >
                                            <div className="text-center">
                                                <div
                                                    className="
                                                        mx-auto
                                                        h-9 w-9
                                                        animate-spin
                                                        rounded-full
                                                        border-4
                                                        border-slate-700
                                                        border-t-cyan-400
                                                    "
                                                />

                                                <p
                                                    className="
                                                        mt-4
                                                        text-sm
                                                        text-slate-400
                                                    "
                                                >
                                                    Đang kết hợp dữ liệu
                                                    với kho tri thức...
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {!fusionLoading &&
                                        fusionError && (
                                            <div
                                                className="
                                                    rounded-3xl
                                                    border
                                                    border-amber-400/20
                                                    bg-amber-400/5
                                                    p-6
                                                "
                                            >
                                                <h3
                                                    className="
                                                        font-semibold
                                                        text-amber-200
                                                    "
                                                >
                                                    AI Knowledge Insight chưa sẵn sàng
                                                </h3>

                                                <p
                                                    className="
                                                        mt-2
                                                        text-sm
                                                        leading-6
                                                        text-amber-100/70
                                                    "
                                                >
                                                    {fusionError}
                                                </p>

                                                <p
                                                    className="
                                                        mt-3
                                                        text-xs
                                                        text-slate-500
                                                    "
                                                >
                                                    Các KPI, biểu đồ và AI Insight
                                                    phía trên vẫn hoạt động bình thường.
                                                </p>
                                            </div>
                                        )}

                                    {!fusionLoading &&
                                        !fusionError &&
                                        fusion && (
                                            <AIKnowledgeInsightCard
                                                fusion={fusion}
                                            />
                                        )}
                                </section>
                            </>
                        )}
                </div>
            </main>
        </div>
    );
}