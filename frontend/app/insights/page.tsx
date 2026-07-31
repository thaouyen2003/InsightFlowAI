"use client"

import { useEffect, useState } from "react"

import FusionSummary from "@/components/insight/FusionSummary"
import InsightCard from "@/components/insight/InsightCard"
import RecommendationCard from "@/components/insight/RecommendationCard"
import AIInsightCard from "@/components/insight/AIInsightCard"

import type {
    FusionResponse,
} from "@/types/fusion"

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL ??
    "http://127.0.0.1:8000"

export default function InsightsPage() {
    const [data, setData] =
        useState<FusionResponse | null>(null)

    const [loading, setLoading] =
        useState(true)

    const [error, setError] =
        useState<string | null>(null)

    useEffect(() => {
        const loadFusion = async () => {
            const filename =
                localStorage.getItem(
                    "uploadedFile"
                )

            if (!filename) {
                setError(
                    "Chưa có dataset được tải lên."
                )
                setLoading(false)
                return
            }

            try {
                const response = await fetch(
                    `${API_BASE_URL}/fusion`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",
                        },
                        body: JSON.stringify({
                            filename,
                        }),
                    }
                )

                if (!response.ok) {
                    const errorData =
                        await response.json()

                    throw new Error(
                        errorData.detail ??
                            "Không thể tạo Insight Fusion."
                    )
                }

                const fusionData: FusionResponse =
                    await response.json()

                setData(fusionData)
            } catch (requestError) {
                const message =
                    requestError instanceof Error
                        ? requestError.message
                        : "Đã xảy ra lỗi không xác định."

                setError(message)
            } finally {
                setLoading(false)
            }
        }

        loadFusion()
    }, [])

    if (loading) {
        return (
            <main className="min-h-screen bg-slate-50 p-6">
                <div className="mx-auto max-w-7xl">
                    <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
                        <p className="text-lg font-semibold text-slate-800">
                            Đang phân tích tri thức...
                        </p>

                        <p className="mt-2 text-sm text-slate-500">
                            InsightFlowAI đang phát hiện
                            insight và khuyến nghị.
                        </p>
                    </div>
                </div>
            </main>
        )
    }

    if (error) {
        return (
            <main className="min-h-screen bg-slate-50 p-6">
                <div className="mx-auto max-w-7xl">
                    <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                        <h1 className="text-lg font-bold text-red-800">
                            Không thể tải Insight Fusion
                        </h1>

                        <p className="mt-2 text-sm text-red-700">
                            {error}
                        </p>
                    </div>
                </div>
            </main>
        )
    }

    if (!data) {
        return null
    }

    return (
        <main className="min-h-screen bg-slate-50 p-6">
            <div className="mx-auto max-w-7xl space-y-8">
                <header>
                    <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
                        InsightFlowAI
                    </p>

                    <h1 className="mt-2 text-3xl font-bold text-slate-900">
                        Insight Fusion
                    </h1>

                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                        Tri thức được phát hiện từ dữ
                        liệu và chuyển thành các khuyến
                        nghị hành động.
                    </p>
                </header>

                <FusionSummary
                    datasetName={
                        data.dataset_name
                    }
                    totalInsights={
                        data.total_insights
                    }
                    totalRecommendations={
                        data.recommendations.length
                    }
                />
                <AIInsightCard
                    insight={data.llm_insight}
                />

                <section>
                    <div className="mb-4">
                        <h2 className="text-xl font-bold text-slate-900">
                            Insights
                        </h2>

                        <p className="mt-1 text-sm text-slate-500">
                            Các mẫu, vấn đề và mối quan
                            hệ được phát hiện từ dataset.
                        </p>
                    </div>

                    {data.insights.length === 0 ? (
                        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
                            Không phát hiện insight phù
                            hợp với các ngưỡng hiện tại.
                        </div>
                    ) : (
                        <div className="grid gap-5 lg:grid-cols-2">
                            {data.insights.map(
                                (insight) => (
                                    <InsightCard
                                        key={
                                            insight.id
                                        }
                                        insight={
                                            insight
                                        }
                                    />
                                )
                            )}
                        </div>
                    )}
                </section>

                <section>
                    <div className="mb-4">
                        <h2 className="text-xl font-bold text-slate-900">
                            Recommendations
                        </h2>

                        <p className="mt-1 text-sm text-slate-500">
                            Các hành động được đề xuất
                            dựa trên insight đã phát hiện.
                        </p>
                    </div>

                    {data.recommendations.length ===
                    0 ? (
                        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
                            Chưa có khuyến nghị cho
                            dataset này.
                        </div>
                    ) : (
                        <div className="grid gap-5 lg:grid-cols-2">
                            {data.recommendations.map(
                                (
                                    recommendation
                                ) => (
                                    <RecommendationCard
                                        key={
                                            recommendation.id
                                        }
                                        recommendation={
                                            recommendation
                                        }
                                    />
                                )
                            )}
                        </div>
                    )}
                </section>
            </div>
        </main>
    )
}