import type {
    LLMInsightResult,
} from "@/types/fusion"

interface AIInsightCardProps {
    insight?: LLMInsightResult
}

export default function AIInsightCard({
    insight,
}: AIInsightCardProps) {
    if (!insight) {
        return null
    }

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <p className="text-sm font-semibold text-indigo-600">
                        Phân tích và khuyến nghị
                    </p>

                    <h2 className="mt-1 text-xl font-bold text-slate-900">
                        AI Insight
                    </h2>
                </div>

                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                    {insight.model}
                </span>
            </div>

            {!insight.generated ? (
                <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <p className="font-semibold text-amber-800">
                        AI Insight tạm thời chưa khả dụng
                    </p>

                    <p className="mt-1 text-sm leading-6 text-amber-700">
                        {insight.error ??
                            "Không thể tạo nội dung AI Insight vào lúc này."}
                    </p>
                </div>
            ) : (
                <div className="mt-6 space-y-6">
                    {insight.executive_summary && (
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Tổng quan điều hành
                            </h3>

                            <p className="mt-2 text-sm leading-7 text-slate-600">
                                {insight.executive_summary}
                            </p>
                        </div>
                    )}

                    {insight.key_findings.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Phát hiện chính
                            </h3>

                            <div className="mt-3 grid gap-3 lg:grid-cols-2">
                                {insight.key_findings.map(
                                    (finding, index) => (
                                        <article
                                            key={`${finding.title}-${index}`}
                                            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <h4 className="font-semibold text-slate-800">
                                                    {finding.title}
                                                </h4>

                                                <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-slate-600">
                                                    {finding.severity}
                                                </span>
                                            </div>

                                            <p className="mt-2 text-sm leading-6 text-slate-600">
                                                {finding.description}
                                            </p>
                                        </article>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    {insight.recommendations.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Khuyến nghị từ AI
                            </h3>

                            <div className="mt-3 space-y-3">
                                {insight.recommendations.map(
                                    (
                                        recommendation,
                                        index
                                    ) => (
                                        <article
                                            key={`${recommendation.title}-${index}`}
                                            className="rounded-xl border border-indigo-100 bg-indigo-50 p-4"
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <h4 className="font-semibold text-indigo-950">
                                                    {recommendation.title}
                                                </h4>

                                                <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-indigo-700">
                                                    {recommendation.priority}
                                                </span>
                                            </div>

                                            <p className="mt-2 text-sm leading-6 text-indigo-900/70">
                                                {recommendation.description}
                                            </p>
                                        </article>
                                    )
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </section>
    )
}