"use client";

type InsightSeverity =
    | "positive"
    | "negative"
    | "warning"
    | "neutral";

type RecommendationPriority =
    | "high"
    | "medium"
    | "low";

interface KeyFinding {
    title: string;
    description: string;
    severity: InsightSeverity;
}

interface Recommendation {
    title: string;
    description: string;
    priority: RecommendationPriority;
}

interface LLMInsight {
    enabled: boolean;
    generated: boolean;
    model?: string | null;
    executive_summary?: string | null;
    key_findings?: KeyFinding[];
    recommendations?: Recommendation[];
    error?: string | null;
}

interface AIInsightPanelProps {
    insight?: LLMInsight | null;
}

const getSeverityStyle = (
    severity: InsightSeverity
): string => {
    switch (severity) {
        case "positive":
            return (
                "border-emerald-400/30 " +
                "bg-emerald-400/10 " +
                "text-emerald-100"
            );

        case "negative":
            return (
                "border-red-400/30 " +
                "bg-red-400/10 " +
                "text-red-100"
            );

        case "warning":
            return (
                "border-amber-400/30 " +
                "bg-amber-400/10 " +
                "text-amber-100"
            );

        default:
            return (
                "border-blue-400/30 " +
                "bg-blue-400/10 " +
                "text-blue-100"
            );
    }
};

const getSeverityIcon = (
    severity: InsightSeverity
): string => {
    switch (severity) {
        case "positive":
            return "↗";

        case "negative":
            return "↘";

        case "warning":
            return "!";

        default:
            return "•";
    }
};

const getPriorityLabel = (
    priority: RecommendationPriority
): string => {
    switch (priority) {
        case "high":
            return "Ưu tiên cao";

        case "medium":
            return "Ưu tiên vừa";

        default:
            return "Ưu tiên thấp";
    }
};

const getPriorityStyle = (
    priority: RecommendationPriority
): string => {
    switch (priority) {
        case "high":
            return "bg-red-400/15 text-red-200";

        case "medium":
            return "bg-amber-400/15 text-amber-200";

        default:
            return "bg-blue-400/15 text-blue-200";
    }
};

export default function AIInsightPanel({
    insight,
}: AIInsightPanelProps) {
    if (!insight) {
        return null;
    }

    if (!insight.enabled) {
        return (
            <section
                className="
                    rounded-2xl
                    border border-white/10
                    bg-white/5
                    p-6
                "
            >
                <h2 className="text-xl font-bold text-white">
                    AI Insight
                </h2>

                <p className="mt-3 text-sm text-slate-300">
                    Tính năng AI Insight hiện đang bị tắt.
                </p>
            </section>
        );
    }

    if (!insight.generated) {
        return (
            <section
                className="
                    overflow-hidden
                    rounded-3xl
                    border border-amber-400/20
                    bg-white/5
                    shadow-2xl
                    shadow-amber-950/10
                "
            >
                <div
                    className="
                        border-b border-white/10
                        bg-gradient-to-r
                        from-amber-500/15
                        via-orange-500/10
                        to-transparent
                        p-6
                    "
                >
                    <div
                        className="
                            flex flex-wrap
                            items-start
                            justify-between
                            gap-4
                        "
                    >
                        <div>
                            <p
                                className="
                                    text-xs font-semibold
                                    uppercase tracking-[0.2em]
                                    text-amber-200
                                "
                            >
                                Trợ lý phân tích dữ liệu
                            </p>

                            <h2
                                className="
                                    mt-2
                                    text-2xl font-bold
                                    text-white
                                "
                            >
                                AI Insight
                            </h2>
                        </div>

                        {insight.model && (
                            <span
                                className="
                                    rounded-full
                                    border border-white/10
                                    bg-black/20
                                    px-3 py-1.5
                                    text-xs text-slate-300
                                "
                            >
                                {insight.model}
                            </span>
                        )}
                    </div>
                </div>

                <div
                    className="
                        grid gap-5
                        p-6
                        lg:grid-cols-[1.35fr_1fr]
                    "
                >
                    <div
                        className="
                            rounded-2xl
                            border border-amber-400/20
                            bg-amber-400/5
                            p-5
                        "
                    >
                        <div
                            className="
                                flex items-start
                                gap-3
                            "
                        >
                            <div
                                className="
                                    flex h-10 w-10
                                    shrink-0
                                    items-center
                                    justify-center
                                    rounded-xl
                                    bg-amber-400/15
                                    text-lg font-bold
                                    text-amber-200
                                "
                            >
                                !
                            </div>

                            <div>
                                <h3
                                    className="
                                        font-semibold
                                        text-amber-100
                                    "
                                >
                                    AI Summary
                                </h3>

                                <p
                                    className="
                                        mt-2
                                        text-sm leading-6
                                        text-amber-100/80
                                    "
                                >
                                    {insight.error ||
                                        "Chưa thể tạo nội dung AI Insight."}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div
                        className="
                            rounded-2xl
                            border border-emerald-400/20
                            bg-emerald-400/5
                            p-5
                        "
                    >
                        <div
                            className="
                                flex items-start
                                gap-3
                            "
                        >
                            <div
                                className="
                                    flex h-10 w-10
                                    shrink-0
                                    items-center
                                    justify-center
                                    rounded-xl
                                    bg-emerald-400/15
                                    text-lg font-bold
                                    text-emerald-200
                                "
                            >
                                ✓
                            </div>

                            <div className="min-w-0">
                                <h3
                                    className="
                                        font-semibold
                                        text-emerald-100
                                    "
                                >
                                    Phân tích nội bộ vẫn hoạt động
                                </h3>

                                <p
                                    className="
                                        mt-2
                                        text-sm leading-6
                                        text-slate-300
                                    "
                                >
                                    InsightFlowAI vẫn phát hiện tri thức
                                    và tạo khuyến nghị bằng các bộ phân
                                    tích nội bộ.
                                </p>
                            </div>
                        </div>

                        <div
                            className="
                                mt-4
                                grid gap-2
                                sm:grid-cols-2
                            "
                        >
                            {[
                                "Missing Detector",
                                "Duplicate Detector",
                                "Numeric Detector",
                                "Category Detector",
                                "Correlation Detector",
                                "Trend Detector",
                                "Recommendation Engine",
                            ].map((item) => (
                                <div
                                    key={item}
                                    className="
                                        flex items-center
                                        gap-2
                                        rounded-xl
                                        border border-white/10
                                        bg-black/10
                                        px-3 py-2
                                        text-xs text-slate-300
                                    "
                                >
                                    <span
                                        className="
                                            text-emerald-300
                                        "
                                    >
                                        ✓
                                    </span>

                                    <span>{item}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div
                    className="
                        border-t border-white/10
                        px-6 py-4
                    "
                >
                    <p
                        className="
                            text-xs leading-5
                            text-slate-400
                        "
                    >
                        Phần dashboard, insight định lượng và khuyến nghị
                        vẫn được tạo bình thường. Chỉ phần diễn giải bằng
                        Gemini đang tạm thời bị giới hạn.
                    </p>
                </div>
            </section>
        );
    }

    const keyFindings = insight.key_findings ?? [];
    const recommendations =
        insight.recommendations ?? [];

    return (
        <section
            className="
                overflow-hidden
                rounded-3xl
                border border-violet-400/20
                bg-white/5
                shadow-2xl
                shadow-violet-950/20
            "
        >
            <div
                className="
                    border-b border-white/10
                    bg-gradient-to-r
                    from-violet-500/20
                    via-blue-500/10
                    to-cyan-500/10
                    p-6
                "
            >
                <div
                    className="
                        flex flex-wrap
                        items-start
                        justify-between
                        gap-4
                    "
                >
                    <div>
                        <p
                            className="
                                text-xs font-semibold
                                uppercase tracking-[0.2em]
                                text-violet-200
                            "
                        >
                            Trợ lý phân tích dữ liệu
                        </p>

                        <h2
                            className="
                                mt-2
                                text-2xl font-bold
                                text-white
                            "
                        >
                            AI Insight
                        </h2>
                    </div>

                    {insight.model && (
                        <span
                            className="
                                rounded-full
                                border border-white/10
                                bg-black/20
                                px-3 py-1.5
                                text-xs text-slate-300
                            "
                        >
                            {insight.model}
                        </span>
                    )}
                </div>

                {insight.executive_summary && (
                    <div
                        className="
                            mt-5
                            rounded-2xl
                            border border-white/10
                            bg-black/15
                            p-5
                        "
                    >
                        <h3
                            className="
                                text-sm font-semibold
                                text-violet-100
                            "
                        >
                            Tổng quan điều hành
                        </h3>

                        <p
                            className="
                                mt-2
                                leading-7
                                text-slate-200
                            "
                        >
                            {insight.executive_summary}
                        </p>
                    </div>
                )}
            </div>

            <div className="space-y-8 p-6">
                {keyFindings.length > 0 && (
                    <div>
                        <div
                            className="
                                flex items-center
                                justify-between
                                gap-3
                            "
                        >
                            <h3
                                className="
                                    text-lg font-bold
                                    text-white
                                "
                            >
                                Phát hiện nổi bật
                            </h3>

                            <span
                                className="
                                    rounded-full
                                    bg-white/10
                                    px-3 py-1
                                    text-xs text-slate-300
                                "
                            >
                                {keyFindings.length} phát hiện
                            </span>
                        </div>

                        <div
                            className="
                                mt-4
                                grid gap-4
                                md:grid-cols-2
                            "
                        >
                            {keyFindings.map(
                                (finding, index) => (
                                    <article
                                        key={`${finding.title}-${index}`}
                                        className={`
                                            rounded-2xl
                                            border
                                            p-5
                                            ${getSeverityStyle(
                                            finding.severity
                                        )}
                                        `}
                                    >
                                        <div
                                            className="
                                                flex
                                                items-start
                                                gap-3
                                            "
                                        >
                                            <div
                                                className="
                                                    flex h-9 w-9
                                                    shrink-0
                                                    items-center
                                                    justify-center
                                                    rounded-xl
                                                    bg-black/20
                                                    font-bold
                                                "
                                            >
                                                {getSeverityIcon(
                                                    finding.severity
                                                )}
                                            </div>

                                            <div>
                                                <h4
                                                    className="
                                                        font-semibold
                                                        text-white
                                                    "
                                                >
                                                    {finding.title}
                                                </h4>

                                                <p
                                                    className="
                                                        mt-2
                                                        text-sm
                                                        leading-6
                                                        text-slate-200
                                                    "
                                                >
                                                    {
                                                        finding.description
                                                    }
                                                </p>
                                            </div>
                                        </div>
                                    </article>
                                )
                            )}
                        </div>
                    </div>
                )}

                {recommendations.length > 0 && (
                    <div>
                        <div
                            className="
                                flex items-center
                                justify-between
                                gap-3
                            "
                        >
                            <h3
                                className="
                                    text-lg font-bold
                                    text-white
                                "
                            >
                                Khuyến nghị hành động
                            </h3>

                            <span
                                className="
                                    rounded-full
                                    bg-white/10
                                    px-3 py-1
                                    text-xs text-slate-300
                                "
                            >
                                {recommendations.length} đề xuất
                            </span>
                        </div>

                        <div className="mt-4 space-y-3">
                            {recommendations.map(
                                (
                                    recommendation,
                                    index
                                ) => (
                                    <article
                                        key={`
                                            ${recommendation.title}
                                            -${index}
                                        `}
                                        className="
                                            rounded-2xl
                                            border border-white/10
                                            bg-white/5
                                            p-5
                                        "
                                    >
                                        <div
                                            className="
                                                flex flex-col
                                                gap-3
                                                sm:flex-row
                                                sm:items-start
                                                sm:justify-between
                                            "
                                        >
                                            <div>
                                                <h4
                                                    className="
                                                        font-semibold
                                                        text-white
                                                    "
                                                >
                                                    {
                                                        recommendation.title
                                                    }
                                                </h4>

                                                <p
                                                    className="
                                                        mt-2
                                                        text-sm
                                                        leading-6
                                                        text-slate-300
                                                    "
                                                >
                                                    {
                                                        recommendation.description
                                                    }
                                                </p>
                                            </div>

                                            <span
                                                className={`
                                                    shrink-0
                                                    rounded-full
                                                    px-3 py-1
                                                    text-xs
                                                    font-medium
                                                    ${getPriorityStyle(
                                                    recommendation.priority
                                                )}
                                                `}
                                            >
                                                {getPriorityLabel(
                                                    recommendation.priority
                                                )}
                                            </span>
                                        </div>
                                    </article>
                                )
                            )}
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}