import type {
    InsightSeverity,
    RecommendationObject,
} from "@/types/fusion"

interface RecommendationCardProps {
    recommendation: RecommendationObject
}

const priorityStyles: Record<
    InsightSeverity,
    string
> = {
    low: "bg-slate-100 text-slate-700",
    medium: "bg-amber-100 text-amber-800",
    high: "bg-orange-100 text-orange-800",
    critical: "bg-red-100 text-red-800",
}

const priorityLabels: Record<
    InsightSeverity,
    string
> = {
    low: "Ưu tiên thấp",
    medium: "Ưu tiên vừa",
    high: "Ưu tiên cao",
    critical: "Ưu tiên khẩn cấp",
}

export default function RecommendationCard({
    recommendation,
}: RecommendationCardProps) {
    return (
        <article className="rounded-2xl border border-indigo-100 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-indigo-500">
                        Recommendation
                    </p>

                    <h3 className="mt-1 text-base font-bold text-slate-900">
                        {recommendation.title}
                    </h3>
                </div>

                <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityStyles[recommendation.priority]}`}
                >
                    {
                        priorityLabels[
                            recommendation.priority
                        ]
                    }
                </span>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-600">
                {recommendation.description}
            </p>

            {recommendation.actions.length > 0 && (
                <div className="mt-4">
                    <p className="text-sm font-semibold text-slate-800">
                        Hành động đề xuất
                    </p>

                    <ol className="mt-2 space-y-2">
                        {recommendation.actions.map(
                            (action, index) => (
                                <li
                                    key={`${recommendation.id}-${index}`}
                                    className="flex gap-3 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-slate-700"
                                >
                                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                                        {index + 1}
                                    </span>

                                    <span>{action}</span>
                                </li>
                            )
                        )}
                    </ol>
                </div>
            )}
        </article>
    )
}