interface FusionSummaryProps {
    datasetName: string
    totalInsights: number
    totalRecommendations: number
}

export default function FusionSummary({
    datasetName,
    totalInsights,
    totalRecommendations,
}: FusionSummaryProps) {
    return (
        <section className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <p className="text-sm text-slate-500">
                    Dataset
                </p>

                <p className="mt-2 truncate text-lg font-bold text-slate-900">
                    {datasetName}
                </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <p className="text-sm text-slate-500">
                    Tổng Insight
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900">
                    {totalInsights}
                </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <p className="text-sm text-slate-500">
                    Khuyến nghị
                </p>

                <p className="mt-2 text-3xl font-bold text-indigo-600">
                    {totalRecommendations}
                </p>
            </div>
        </section>
    )
}