import type {
    InsightObject,
    InsightSeverity,
} from "@/types/fusion"

interface InsightCardProps {
    insight: InsightObject
}

const severityStyles: Record<
    InsightSeverity,
    string
> = {
    low: "border-slate-200 bg-slate-50 text-slate-700",
    medium: "border-amber-200 bg-amber-50 text-amber-800",
    high: "border-orange-200 bg-orange-50 text-orange-800",
    critical: "border-red-200 bg-red-50 text-red-800",
}

const severityLabels: Record<
    InsightSeverity,
    string
> = {
    low: "Thấp",
    medium: "Trung bình",
    high: "Cao",
    critical: "Nghiêm trọng",
}

export default function InsightCard({
    insight,
}: InsightCardProps) {
    const evidence = insight.evidence

    return (
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        {insight.category}
                    </p>

                    <h3 className="mt-1 text-base font-bold text-slate-900">
                        {insight.title}
                    </h3>
                </div>

                <span
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${severityStyles[insight.severity]}`}
                >
                    {severityLabels[insight.severity]}
                </span>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-600">
                {insight.description}
            </p>

            {(insight.metric ||
                insight.value !== null) && (
                    <div className="mt-4 rounded-xl bg-slate-50 p-4">
                        <p className="text-xs font-medium uppercase text-slate-500">
                            Chỉ số
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                            {insight.metric ?? "Giá trị"}
                            {": "}
                            {String(
                                insight.value ?? "N/A"
                            )}
                            {insight.unit
                                ? ` ${insight.unit}`
                                : ""}
                        </p>
                    </div>
                )}

            {evidence && (
                <div className="mt-4 border-t border-slate-100 pt-4">
                    <p className="text-sm font-semibold text-slate-800">
                        Bằng chứng
                    </p>

                    <div className="mt-2 space-y-1 text-sm text-slate-600">
                        {evidence.column && (
                            <p>
                                Cột:{" "}
                                <span className="font-medium text-slate-800">
                                    {evidence.column}
                                </span>
                            </p>
                        )}

                        {evidence.related_columns &&
                            evidence.related_columns
                                .length > 0 && (
                                <p>
                                    Cột liên quan:{" "}
                                    <span className="font-medium text-slate-800">
                                        {evidence.related_columns.join(
                                            ", "
                                        )}
                                    </span>
                                </p>
                            )}

                        {evidence.calculation && (
                            <p className="break-words">
                                Tính toán:{" "}
                                {evidence.calculation}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </article>
    )
}