export interface FusionSource {
    document: string;
    page: number | null;
    category: string | null;
}

export interface FusionResponse {
    success: boolean;
    dataset_name: string;
    data_findings: string[];
    knowledge_query: string;
    knowledge_answer: string;
    recommendations: string[];
    sources: FusionSource[];
    metadata: Record<string, unknown>;
}

interface AIKnowledgeInsightCardProps {
    fusion: FusionResponse;
}

export default function AIKnowledgeInsightCard({
    fusion,
}: AIKnowledgeInsightCardProps) {
    return (
        <div
            className="
                overflow-hidden
                rounded-3xl
                border
                border-cyan-400/20
                bg-gradient-to-br
                from-slate-900
                via-slate-900
                to-cyan-950/40
                shadow-2xl
                shadow-black/20
            "
        >
            <div
                className="
                    border-b
                    border-white/10
                    px-6 py-5
                    lg:px-8
                "
            >
                <div
                    className="
                        flex flex-col
                        gap-3
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
                                tracking-[0.18em]
                                text-cyan-300
                            "
                        >
                            Insight + RAG Fusion
                        </p>

                        <h3
                            className="
                                mt-2
                                text-xl
                                font-bold
                                text-white
                            "
                        >
                            AI Knowledge Insight
                        </h3>

                        <p
                            className="
                                mt-2
                                max-w-3xl
                                text-sm
                                leading-6
                                text-slate-400
                            "
                        >
                            Kết hợp phát hiện từ dữ liệu
                            với tri thức được truy xuất từ
                            tài liệu để hỗ trợ ra quyết định.
                        </p>
                    </div>

                    <div
                        className="
                            rounded-full
                            border
                            border-emerald-400/20
                            bg-emerald-400/10
                            px-4 py-2
                            text-xs
                            font-medium
                            text-emerald-300
                        "
                    >
                        Fusion hoàn tất
                    </div>
                </div>
            </div>

            <div
                className="
                    grid
                    grid-cols-1
                    gap-6
                    p-6
                    lg:grid-cols-2
                    lg:p-8
                "
            >
                <section
                    className="
                        rounded-2xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-5
                    "
                >
                    <p
                        className="
                            text-xs
                            font-semibold
                            uppercase
                            tracking-wider
                            text-blue-300
                        "
                    >
                        Data Findings
                    </p>

                    <h4
                        className="
                            mt-2
                            font-semibold
                            text-white
                        "
                    >
                        Phát hiện từ dữ liệu
                    </h4>

                    {fusion.data_findings.length > 0 ? (
                        <ul
                            className="
                                mt-4
                                space-y-3
                            "
                        >
                            {fusion.data_findings.map(
                                (finding, index) => (
                                    <li
                                        key={index}
                                        className="
                                            flex
                                            gap-3
                                            text-sm
                                            leading-6
                                            text-slate-300
                                        "
                                    >
                                        <span
                                            className="
                                                mt-2
                                                h-2 w-2
                                                shrink-0
                                                rounded-full
                                                bg-blue-400
                                            "
                                        />

                                        <span>{finding}</span>
                                    </li>
                                )
                            )}
                        </ul>
                    ) : (
                        <p
                            className="
                                mt-4
                                text-sm
                                text-slate-500
                            "
                        >
                            Chưa có phát hiện nổi bật từ
                            dữ liệu.
                        </p>
                    )}
                </section>

                <section
                    className="
                        rounded-2xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-5
                    "
                >
                    <p
                        className="
                            text-xs
                            font-semibold
                            uppercase
                            tracking-wider
                            text-violet-300
                        "
                    >
                        Knowledge Retrieval
                    </p>

                    <h4
                        className="
                            mt-2
                            font-semibold
                            text-white
                        "
                    >
                        Tri thức từ tài liệu
                    </h4>

                    {fusion.knowledge_query && (
                        <div
                            className="
                                mt-4
                                rounded-xl
                                border
                                border-violet-400/10
                                bg-violet-400/5
                                p-4
                            "
                        >
                            <p
                                className="
                                    text-xs
                                    font-medium
                                    text-violet-300
                                "
                            >
                                Câu hỏi truy xuất
                            </p>

                            <p
                                className="
                                    mt-2
                                    text-sm
                                    leading-6
                                    text-slate-300
                                "
                            >
                                {fusion.knowledge_query}
                            </p>
                        </div>
                    )}

                    <p
                        className="
                            mt-4
                            whitespace-pre-line
                            text-sm
                            leading-7
                            text-slate-300
                        "
                    >
                        {fusion.knowledge_answer ||
                            "Chưa tìm thấy tri thức phù hợp trong kho tài liệu."}
                    </p>
                </section>

                <section
                    className="
                        rounded-2xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-5
                        lg:col-span-2
                    "
                >
                    <p
                        className="
                            text-xs
                            font-semibold
                            uppercase
                            tracking-wider
                            text-emerald-300
                        "
                    >
                        Recommendations
                    </p>

                    <h4
                        className="
                            mt-2
                            font-semibold
                            text-white
                        "
                    >
                        Khuyến nghị
                    </h4>

                    {fusion.recommendations.length > 0 ? (
                        <div
                            className="
                                mt-4
                                grid
                                grid-cols-1
                                gap-4
                                lg:grid-cols-2
                            "
                        >
                            {fusion.recommendations.map(
                                (
                                    recommendation,
                                    index
                                ) => (
                                    <article
                                        key={index}
                                        className="
                                            rounded-xl
                                            border
                                            border-emerald-400/10
                                            bg-emerald-400/5
                                            p-4
                                        "
                                    >
                                        <div
                                            className="
                                                flex
                                                gap-3
                                            "
                                        >
                                            <span
                                                className="
                                                    flex
                                                    h-7 w-7
                                                    shrink-0
                                                    items-center
                                                    justify-center
                                                    rounded-full
                                                    bg-emerald-400/10
                                                    text-xs
                                                    font-bold
                                                    text-emerald-300
                                                "
                                            >
                                                {index + 1}
                                            </span>

                                            <p
                                                className="
                                                    text-sm
                                                    leading-6
                                                    text-slate-300
                                                "
                                            >
                                                {
                                                    recommendation
                                                }
                                            </p>
                                        </div>
                                    </article>
                                )
                            )}
                        </div>
                    ) : (
                        <p
                            className="
                                mt-4
                                text-sm
                                text-slate-500
                            "
                        >
                            Chưa có khuyến nghị phù hợp.
                        </p>
                    )}
                </section>

                <section
                    className="
                        rounded-2xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-5
                        lg:col-span-2
                    "
                >
                    <p
                        className="
                            text-xs
                            font-semibold
                            uppercase
                            tracking-wider
                            text-amber-300
                        "
                    >
                        References
                    </p>

                    <h4
                        className="
                            mt-2
                            font-semibold
                            text-white
                        "
                    >
                        Nguồn tham khảo
                    </h4>

                    {fusion.sources.length > 0 ? (
                        <div
                            className="
                                mt-4
                                flex
                                flex-wrap
                                gap-3
                            "
                        >
                            {fusion.sources.map(
                                (source, index) => (
                                    <div
                                        key={`${source.document}-${index}`}
                                        className="
                                            rounded-xl
                                            border
                                            border-white/10
                                            bg-black/20
                                            px-4 py-3
                                        "
                                    >
                                        <p
                                            className="
                                                text-sm
                                                font-medium
                                                text-slate-200
                                            "
                                        >
                                            {source.document}
                                        </p>

                                        <p
                                            className="
                                                mt-1
                                                text-xs
                                                text-slate-500
                                            "
                                        >
                                            {source.page !== null
                                                ? `Trang ${source.page}`
                                                : "Không xác định trang"}

                                            {source.category
                                                ? ` · ${source.category}`
                                                : ""}
                                        </p>
                                    </div>
                                )
                            )}
                        </div>
                    ) : (
                        <p
                            className="
                                mt-4
                                text-sm
                                text-slate-500
                            "
                        >
                            Chưa có nguồn tài liệu tham khảo.
                        </p>
                    )}
                </section>
            </div>
        </div>
    );
}