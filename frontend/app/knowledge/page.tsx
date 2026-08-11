"use client"

import { useEffect, useState } from "react"

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"

import {
    BookOpen,
    FolderOpen,
    Bot,
} from "lucide-react"

type KnowledgeSource = {
    source: string
    page?: number | null
    category?: string | null
    chunk_id: string
    distance?: number | null
}


type KnowledgeResponse = {
    success: boolean
    question: string
    answer: string
    sources: KnowledgeSource[]
    retrieved_count: number
    metadata: Record<string, unknown>
}

type KnowledgeDocument = {
    filename: string
    category: string
    file_type: string
    size_bytes: number
}

type KnowledgeDocumentListResponse = {
    success: boolean
    documents: KnowledgeDocument[]
    total_documents: number
}

type KnowledgeStatsResponse = {
    success: boolean
    total_documents: number
    total_categories: number
    ai_query_count: number
}

type KnowledgeActivity = {
    question: string
    category?: string | null
    retrieved_count: number
    created_at: string
}

type KnowledgeActivityResponse = {
    success: boolean
    activities: KnowledgeActivity[]
    total: number
}

type KnowledgeSearchResult = {
    chunk_id: string
    content: string
    source: string
    page?: number | null
    category?: string | null
    distance?: number | null
}

type KnowledgeSearchResponse = {
    success: boolean
    query: string
    results: KnowledgeSearchResult[]
    retrieved_count: number
}

export default function KnowledgePage() {
    const [question, setQuestion] = useState("")
    const [category, setCategory] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [result, setResult] =
        useState<KnowledgeResponse | null>(null)

    const [documents, setDocuments] = useState<
        KnowledgeDocument[]
    >([])

    const [documentSearch, setDocumentSearch] =
        useState("")

    const [documentCategory, setDocumentCategory] =
        useState("")

    const [knowledgeStats, setKnowledgeStats] =
    useState<KnowledgeStatsResponse | null>(null)

    const [statsLoading, setStatsLoading] =
    useState(true)

    const [activities, setActivities] = useState<
        KnowledgeActivity[]
    >([])

    const [activitiesLoading, setActivitiesLoading] =
        useState(true)

    const [activitiesError, setActivitiesError] =
        useState("")

    const [searchQuery, setSearchQuery] = useState("")
    const [searchCategory, setSearchCategory] =
        useState("")

    const [searchLoading, setSearchLoading] =
        useState(false)

    const [searchError, setSearchError] =
        useState("")

    const [searchResult, setSearchResult] =
        useState<KnowledgeSearchResponse | null>(null)

    const [documentsLoading, setDocumentsLoading] =
        useState(true)

    const [documentsError, setDocumentsError] =
        useState("")

        const generationMode =
            result?.metadata?.generation_mode

        const isGeminiMode =
            generationMode === "gemini"

        const isFallbackMode =
            generationMode === "retrieval_fallback"

    
    function formatFileSize(sizeBytes: number) {
        if (sizeBytes < 1024) {
            return `${sizeBytes} B`
        }

        const sizeKb = sizeBytes / 1024

        if (sizeKb < 1024) {
            return `${sizeKb.toFixed(1)} KB`
        }

        return `${(sizeKb / 1024).toFixed(1)} MB`
    }

    async function loadKnowledgeStats() {
        try {
            setStatsLoading(true)

            const response = await fetch(
                "http://127.0.0.1:8000/knowledge/stats"
            )

            const data: KnowledgeStatsResponse =
                await response.json()

            if (!response.ok) {
                throw new Error(
                    "Không thể tải Knowledge KPI."
                )
            }

            setKnowledgeStats(data)
        } catch (requestError) {
            console.error(
                "Knowledge stats error:",
                requestError
            )
        } finally {
            setStatsLoading(false)
        }
    }

    async function loadKnowledgeActivities() {
        try {
            setActivitiesLoading(true)
            setActivitiesError("")

            const response = await fetch(
                "http://127.0.0.1:8000/knowledge/activities"
            )

            const data: KnowledgeActivityResponse =
                await response.json()

            if (!response.ok) {
                throw new Error(
                    "Không thể tải lịch sử truy vấn."
                )
            }

            setActivities(data.activities)
        } catch (requestError) {
            const message =
                requestError instanceof Error
                    ? requestError.message
                    : "Không thể tải Knowledge Activity."

            setActivitiesError(message)
        } finally {
            setActivitiesLoading(false)
        }
    }

    useEffect(() => {
        async function loadDocuments() {
            try {
                setDocumentsLoading(true)
                setDocumentsError("")

                const response = await fetch(
                    "http://127.0.0.1:8000/knowledge/documents"
                )

                const data: KnowledgeDocumentListResponse =
                    await response.json()

                if (!response.ok) {
                    throw new Error(
                        "Không thể tải danh sách tài liệu."
                    )
                }

                setDocuments(data.documents)
            } catch (requestError) {
                const message =
                    requestError instanceof Error
                        ? requestError.message
                        : "Không thể tải Knowledge Base."

                setDocumentsError(message)
            } finally {
                setDocumentsLoading(false)
            }
        }
        loadDocuments()
        loadKnowledgeStats()
        loadKnowledgeActivities()
    }, [])


    async function handleSearch(
        event: React.FormEvent<HTMLFormElement>
    ) {
        event.preventDefault()

        const cleanQuery = searchQuery.trim()

        if (!cleanQuery) {
            setSearchError(
                "Vui lòng nhập nội dung cần tìm."
            )
            return
        }

        setSearchLoading(true)
        setSearchError("")
        setSearchResult(null)

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/knowledge/search",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        query: cleanQuery,
                        top_k: 5,
                        category:
                            searchCategory || null,
                    }),
                }
            )

            const data: KnowledgeSearchResponse =
                await response.json()

            if (!response.ok) {
                throw new Error(
                    "Không thể tìm kiếm tri thức."
                )
            }

            setSearchResult(data)
        } catch (requestError) {
            const message =
                requestError instanceof Error
                    ? requestError.message
                    : "Đã xảy ra lỗi khi tìm kiếm."

            setSearchError(message)
        } finally {
            setSearchLoading(false)
        }
    }

    
    function formatCategory(
        value?: string | null
    ) {
        const labels: Record<string, string> = {
            dao_tao: "Đào tạo",
            hoc_bong: "Học bổng",
            hoc_vu: "Học vụ",
            tot_nghiep: "Tốt nghiệp",
        }

        if (!value) {
            return "Không xác định"
        }

        return labels[value] || value
    }


    function formatActivityTime(
        value: string
    ) {
        const date = new Date(value)

        if (Number.isNaN(date.getTime())) {
            return value
        }

        return date.toLocaleString(
            "vi-VN",
            {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            }
        )
    }

    const categoryChartData = [
        "dao_tao",
        "hoc_bong",
        "hoc_vu",
        "tot_nghiep",
    ].map((item) => ({
        category: formatCategory(item),

        documents: documents.filter(
            (document) =>
                document.category === item
        ).length,
    }))

    const filteredDocuments = documents.filter(
        (document) => {
            const matchesSearch =
                document.filename
                    .toLowerCase()
                    .includes(
                        documentSearch
                            .trim()
                            .toLowerCase()
                    )

            const matchesCategory =
                !documentCategory ||
                document.category ===
                    documentCategory

            return (
                matchesSearch &&
                matchesCategory
            )
        }
    )

    const documentCategoryCounts = {
        all: documents.length,

        dao_tao: documents.filter(
            (document) =>
                document.category === "dao_tao"
        ).length,

        hoc_bong: documents.filter(
            (document) =>
                document.category === "hoc_bong"
        ).length,

        hoc_vu: documents.filter(
            (document) =>
                document.category === "hoc_vu"
        ).length,

        tot_nghiep: documents.filter(
            (document) =>
                document.category ===
                "tot_nghiep"
        ).length,
    }

    const categoryStats = [
        {
            key: "dao_tao",
            label: "Đào tạo",
            count: documentCategoryCounts.dao_tao,
        },
        {
            key: "hoc_bong",
            label: "Học bổng",
            count: documentCategoryCounts.hoc_bong,
        },
        {
            key: "hoc_vu",
            label: "Học vụ",
            count: documentCategoryCounts.hoc_vu,
        },
        {
            key: "tot_nghiep",
            label: "Tốt nghiệp",
            count: documentCategoryCounts.tot_nghiep,
        },
    ]

    const largestKnowledgeCategory =
        categoryStats.reduce(
            (largest, current) =>
                current.count > largest.count
                    ? current
                    : largest,
            categoryStats[0]
        )

    const smallestKnowledgeCategory =
        categoryStats.reduce(
            (smallest, current) =>
                current.count < smallest.count
                    ? current
                    : smallest,
            categoryStats[0]
        )

    const largestCategoryPercentage =
        documents.length > 0
            ? (
                (largestKnowledgeCategory.count /
                    documents.length) *
                100
            ).toFixed(1)
            : "0"



    async function handleSubmit(
        event: React.FormEvent<HTMLFormElement>
    ) {
        event.preventDefault()

        const cleanQuestion = question.trim()

        if (!cleanQuestion) {
            setError("Vui lòng nhập câu hỏi.")
            return
        }

        setLoading(true)
        setError("")
        setResult(null)

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/knowledge/ask",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        question,
                        category:
                            category || null,
                    }),
                }
            )

            const data = await response.json()

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "Không thể xử lý câu hỏi."
                )
            }

            setResult(data)
            setKnowledgeStats((current) => {
                if (!current) {
                    return current
                }

                return {
                    ...current,
                    ai_query_count:
                        current.ai_query_count + 1,
                }
            })
            await loadKnowledgeActivities()

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

    type KnowledgeTab =
    | "overview"
    | "assistant"
    | "repository"

    const [activeTab, setActiveTab] =
    useState<KnowledgeTab>("overview")

    const sourceChartData =
        result?.sources.map(
            (source, index) => ({
                name: `Nguồn ${index + 1}`,
                source: source.source,
                relevance:
                    source.distance !== null &&
                    source.distance !== undefined
                        ? Math.max(
                            0,
                            Math.min(
                                100,
                                (1 - source.distance) *
                                    100
                            )
                        )
                        : 0,
            })
    ) ?? []

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
            <div className="mx-auto max-w-7xl">
                {/* HEADER */}
                <div className="mb-8">
                    <p className="text-sm font-medium uppercase tracking-[0.25em] text-cyan-400">
                        InsightFlowAI
                    </p>

                    <h1 className="mt-3 text-3xl font-bold">
                        Knowledge Assistant
                    </h1>

                    <p className="mt-3 max-w-3xl text-slate-400">
                        Tìm kiếm, khai thác và quản trị tri thức
                        về đào tạo, học vụ, học bổng và tốt nghiệp
                        từ kho tri thức Đại học Văn Hiến.
                    </p>
                </div>

                {/* KPI */}
                <section className="mb-8">
                    <div className="mb-4">
                        <p className="text-sm font-medium text-cyan-400">
                            Knowledge Management
                        </p>

                        <h2 className="mt-1 text-xl font-semibold">
                            Tổng quan kho tri thức
                        </h2>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-cyan-500/10 blur-2xl" />

                            <div className="relative">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm text-slate-400">
                                            Tài liệu tri thức
                                        </p>

                                        <p className="mt-3 text-3xl font-bold text-white">
                                            {statsLoading
                                                ? "..."
                                                : knowledgeStats
                                                    ?.total_documents ?? 0}
                                        </p>
                                    </div>
                                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-500/10">
                                        <BookOpen
                                            size={22}
                                            className="text-cyan-300"
                                        />
                                    </div>

                                </div>

                                <p className="mt-4 text-xs text-slate-500">
                                    Tài liệu đang được quản lý trong Knowledge Base
                                </p>
                            </div>
                        </div>

                        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-indigo-500/10 blur-2xl" />

                            <div className="relative">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm text-slate-400">
                                            Danh mục tri thức
                                        </p>

                                        <p className="mt-3 text-3xl font-bold text-white">
                                            {statsLoading
                                                ? "..."
                                                : knowledgeStats
                                                    ?.total_categories ?? 0}
                                        </p>
                                    </div>
                                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-500/10">
                                        <FolderOpen
                                            size={22}
                                            className="text-cyan-300"
                                        />
                                    </div>

                                   
                                </div>

                                <p className="mt-4 text-xs text-slate-500">
                                    Nhóm tri thức đã được
                                    tổ chức và phân loại
                                </p>
                            </div>
                        </div>

                        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-emerald-500/10 blur-2xl" />

                            <div className="relative">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm text-slate-400">
                                            Truy vấn Knowledge AI
                                        </p>

                                        <p className="mt-3 text-3xl font-bold text-white">
                                            {statsLoading
                                                ? "..."
                                                : knowledgeStats
                                                    ?.ai_query_count ?? 0}
                                        </p>
                                    </div>

                                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-500/10">
                                        <Bot
                                            size={22}
                                            className="text-cyan-300"
                                        />
                                    </div>
                                </div>

                                <p className="mt-4 text-xs text-slate-500">
                                    Câu hỏi đã được xử lý
                                    bằng RAG và AI
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* TABS */}
                <div className="mb-8 rounded-2xl border border-white/10 bg-white/[0.03] p-2">
                    <div className="flex flex-wrap gap-2">
                        <button
                            type="button"
                            onClick={() =>
                                setActiveTab("overview")
                            }
                            className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
                                activeTab === "overview"
                                    ? "bg-cyan-500 text-slate-950"
                                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                            }`}
                        >
                            Tổng quan
                        </button>

                        <button
                            type="button"
                            onClick={() =>
                                setActiveTab("assistant")
                            }
                            className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
                                activeTab === "assistant"
                                    ? "bg-cyan-500 text-slate-950"
                                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                            }`}
                        >
                            Tra cứu & AI
                        </button>

                        <button
                            type="button"
                            onClick={() =>
                                setActiveTab("repository")
                            }
                            className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
                                activeTab === "repository"
                                    ? "bg-cyan-500 text-slate-950"
                                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                            }`}
                        >
                            Kho tài liệu
                        </button>
                    </div>
                </div>

                {/* TAB 1: OVERVIEW */}
                {activeTab === "overview" && (
                    <>
                        <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
                            {/* ANALYTICS */}
                            <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <div className="mb-6">
                                    <p className="text-sm font-medium text-cyan-400">
                                        Knowledge Analytics
                                    </p>

                                    <h2 className="mt-1 text-xl font-semibold">
                                        Phân bố tài liệu theo danh mục
                                    </h2>

                                    <p className="mt-2 text-sm text-slate-400">
                                        Thống kê số lượng tài liệu tri thức
                                        trong từng nhóm kiến thức.
                                    </p>
                                </div>

                                {documentsLoading ? (
                                    <div className="flex h-[320px] items-center justify-center text-sm text-slate-500">
                                        Đang tải dữ liệu Knowledge Base...
                                    </div>
                                ) : documentsError ? (
                                    <div className="flex h-[320px] items-center justify-center text-sm text-red-300">
                                        {documentsError}
                                    </div>
                                ) : (
                                    <div className="h-[320px] w-full">
                                        <ResponsiveContainer
                                            width="100%"
                                            height="100%"
                                        >
                                            <BarChart
                                                data={categoryChartData}
                                                margin={{
                                                    top: 10,
                                                    right: 20,
                                                    left: 0,
                                                    bottom: 10,
                                                }}
                                            >
                                                <CartesianGrid
                                                    strokeDasharray="3 3"
                                                    stroke="#334155"
                                                    vertical={false}
                                                />

                                                <XAxis
                                                    dataKey="category"
                                                    stroke="#94a3b8"
                                                    tickLine={false}
                                                    axisLine={false}
                                                />

                                                <YAxis
                                                    allowDecimals={false}
                                                    stroke="#94a3b8"
                                                    tickLine={false}
                                                    axisLine={false}
                                                />

                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor:
                                                            "#0f172a",
                                                        border:
                                                            "1px solid rgba(255,255,255,0.1)",
                                                        borderRadius:
                                                            "12px",
                                                    }}
                                                    labelStyle={{
                                                        color: "#ffffff",
                                                    }}
                                                />

                                                <Bar
                                                    dataKey="documents"
                                                    name="Số tài liệu"
                                                    fill="#22d3ee"
                                                    radius={[8, 8, 0, 0]}
                                                />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </section>

                            {/* INSIGHTS */}
                            <section className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-500/[0.08] via-white/[0.03] to-indigo-500/[0.05] p-6">
                                <div className="flex flex-col gap-6">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-500/10 text-xl">
                                                ✦
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-cyan-400">
                                                    Knowledge Insights
                                                </p>

                                                <h2 className="mt-1 text-xl font-semibold text-white">
                                                    Phân tích kho tri thức
                                                </h2>
                                            </div>
                                        </div>

                                        <div className="mt-6 space-y-4 text-sm leading-7 text-slate-300">
                                            <p>
                                                Kho tri thức hiện có{" "}
                                                <strong className="text-white">
                                                    {documents.length} tài liệu
                                                </strong>{" "}
                                                thuộc{" "}
                                                <strong className="text-white">
                                                    {knowledgeStats
                                                        ?.total_categories ?? 0}{" "}
                                                    danh mục
                                                </strong>.
                                            </p>

                                            <p>
                                                <strong className="text-cyan-300">
                                                    {
                                                        largestKnowledgeCategory.label
                                                    }
                                                </strong>{" "}
                                                là nhóm lớn nhất với{" "}
                                                <strong className="text-white">
                                                    {
                                                        largestKnowledgeCategory.count
                                                    }{" "}
                                                    tài liệu
                                                </strong>
                                                , chiếm khoảng{" "}
                                                <strong className="text-white">
                                                    {
                                                        largestCategoryPercentage
                                                    }
                                                    %
                                                </strong>.
                                            </p>

                                            <p>
                                                <strong className="text-amber-300">
                                                    {
                                                        smallestKnowledgeCategory.label
                                                    }
                                                </strong>{" "}
                                                hiện có{" "}
                                                <strong className="text-white">
                                                    {
                                                        smallestKnowledgeCategory.count
                                                    }{" "}
                                                    tài liệu
                                                </strong>
                                                , là nhóm có mức bao phủ thấp nhất.
                                            </p>

                                            <p>
                                                Knowledge AI đã ghi nhận{" "}
                                                <strong className="text-emerald-300">
                                                    {knowledgeStats
                                                        ?.ai_query_count ?? 0}{" "}
                                                    lượt truy vấn
                                                </strong>.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="rounded-2xl border border-amber-400/20 bg-amber-500/[0.07] p-5">
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-300">
                                            Khuyến nghị
                                        </p>

                                        <p className="mt-3 text-sm leading-7 text-slate-300">
                                            Ưu tiên bổ sung và cập nhật tài liệu
                                            cho nhóm{" "}
                                            <strong className="text-white">
                                                {
                                                    smallestKnowledgeCategory.label
                                                }
                                            </strong>{" "}
                                            nhằm cải thiện mức độ bao phủ
                                            và cân bằng Knowledge Base.
                                        </p>
                                    </div>
                                </div>
                            </section>
                        </div>

                        {/* ACTIVITY */}
                        <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
                                <div>
                                    <p className="text-sm font-medium text-cyan-400">
                                        Knowledge Activity
                                    </p>

                                    <h2 className="mt-1 text-xl font-semibold">
                                        Hoạt động khai thác tri thức
                                    </h2>

                                    <p className="mt-2 text-sm leading-6 text-slate-400">
                                        Theo dõi các câu hỏi đã được xử lý
                                        bởi hệ thống RAG và Knowledge AI.
                                    </p>
                                </div>

                                <div className="rounded-full border border-white/10 bg-slate-900 px-4 py-2 text-sm text-slate-300">
                                    {activities.length} hoạt động gần nhất
                                </div>
                            </div>

                            {activitiesLoading ? (
                                <div className="flex min-h-[180px] items-center justify-center text-sm text-slate-500">
                                    Đang tải lịch sử khai thác tri thức...
                                </div>
                            ) : activitiesError ? (
                                <div className="rounded-xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-200">
                                    {activitiesError}
                                </div>
                            ) : activities.length === 0 ? (
                                <div className="rounded-xl border border-dashed border-white/10 bg-slate-950/40 p-8 text-center">
                                    <p className="text-slate-300">
                                        Chưa có hoạt động truy vấn.
                                    </p>

                                    <p className="mt-2 text-sm text-slate-500">
                                        Hãy đặt câu hỏi cho Knowledge AI
                                        để bắt đầu ghi nhận hoạt động.
                                    </p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full min-w-[760px] text-left">
                                        <thead>
                                            <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
                                                <th className="px-4 py-3 font-medium">
                                                    Câu hỏi
                                                </th>

                                                <th className="px-4 py-3 font-medium">
                                                    Danh mục
                                                </th>

                                                <th className="px-4 py-3 text-center font-medium">
                                                    Nguồn
                                                </th>

                                                <th className="px-4 py-3 font-medium">
                                                    Thời gian
                                                </th>
                                            </tr>
                                        </thead>

                                        <tbody>
                                            {activities
                                                .slice(0, 6)
                                                .map(
                                                    (
                                                        activity,
                                                        index
                                                    ) => (
                                                        <tr
                                                            key={`${activity.created_at}-${index}`}
                                                            className="border-b border-white/5 transition hover:bg-white/[0.03]"
                                                        >
                                                            <td className="max-w-md px-4 py-4">
                                                                <p className="line-clamp-2 text-sm font-medium text-slate-200">
                                                                    {
                                                                        activity.question
                                                                    }
                                                                </p>
                                                            </td>

                                                            <td className="px-4 py-4">
                                                                <span className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-200">
                                                                    {activity.category
                                                                        ? formatCategory(
                                                                            activity.category
                                                                        )
                                                                        : "Tất cả"}
                                                                </span>
                                                            </td>

                                                            <td className="px-4 py-4 text-center">
                                                                <span className="font-semibold text-white">
                                                                    {
                                                                        activity.retrieved_count
                                                                    }
                                                                </span>

                                                                <span className="ml-1 text-xs text-slate-500">
                                                                    đoạn
                                                                </span>
                                                            </td>

                                                            <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-400">
                                                                {formatActivityTime(
                                                                    activity.created_at
                                                                )}
                                                            </td>
                                                        </tr>
                                                    )
                                                )}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </section>
                    </>
                )}

                {/* TAB 2: ASSISTANT */}
                {activeTab === "assistant" && (
                    <>
                        <div className="grid gap-6 xl:grid-cols-2">
                            {/* SEMANTIC SEARCH */}
                            <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <div className="mb-6">
                                    <p className="text-sm font-medium text-cyan-400">
                                        Semantic Search
                                    </p>

                                    <h2 className="mt-1 text-xl font-semibold">
                                        Tìm kiếm tri thức
                                    </h2>

                                    <p className="mt-2 text-sm leading-6 text-slate-400">
                                        Tìm các đoạn nội dung liên quan
                                        bằng tìm kiếm ngữ nghĩa.
                                    </p>
                                </div>

                                <form onSubmit={handleSearch}>
                                    <div className="space-y-4">
                                        <div>
                                            <label
                                                htmlFor="search-query"
                                                className="mb-2 block text-sm font-medium text-slate-300"
                                            >
                                                Nội dung tìm kiếm
                                            </label>

                                            <input
                                                id="search-query"
                                                type="text"
                                                value={searchQuery}
                                                onChange={(event) =>
                                                    setSearchQuery(
                                                        event.target.value
                                                    )
                                                }
                                                placeholder="Ví dụ: Điều kiện xét tốt nghiệp"
                                                className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-500/50"
                                            />
                                        </div>

                                        <div>
                                            <label
                                                htmlFor="search-category"
                                                className="mb-2 block text-sm font-medium text-slate-300"
                                            >
                                                Danh mục
                                            </label>

                                            <select
                                                id="search-category"
                                                value={searchCategory}
                                                onChange={(event) =>
                                                    setSearchCategory(
                                                        event.target.value
                                                    )
                                                }
                                                className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none"
                                            >
                                                <option value="">
                                                    Tất cả
                                                </option>

                                                <option value="dao_tao">
                                                    Đào tạo
                                                </option>

                                                <option value="hoc_bong">
                                                    Học bổng
                                                </option>

                                                <option value="hoc_vu">
                                                    Học vụ
                                                </option>

                                                <option value="tot_nghiep">
                                                    Tốt nghiệp
                                                </option>
                                            </select>
                                        </div>

                                        <button
                                            type="submit"
                                            disabled={searchLoading}
                                            className="w-full rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                                        >
                                            {searchLoading
                                                ? "Đang tìm kiếm..."
                                                : "Tìm kiếm"}
                                        </button>
                                    </div>
                                </form>

                                {searchError && (
                                    <div className="mt-5 rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-red-200">
                                        {searchError}
                                    </div>
                                )}
                            </section>

                            {/* AI ASSISTANT */}
                            <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <div className="mb-6">
                                    <p className="text-sm font-medium text-cyan-400">
                                        Generative AI + RAG
                                    </p>

                                    <h2 className="mt-1 text-xl font-semibold">
                                        AI Knowledge Assistant
                                    </h2>

                                    <p className="mt-2 text-sm leading-6 text-slate-400">
                                        AI tổng hợp câu trả lời từ
                                        Knowledge Base và cung cấp nguồn.
                                    </p>
                                </div>

                                <form onSubmit={handleSubmit}>
                                    <div className="space-y-4">
                                        <select
                                            value={category}
                                            onChange={(event) =>
                                                setCategory(
                                                    event.target.value
                                                )
                                            }
                                            className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white outline-none"
                                        >
                                            <option value="">
                                                Tất cả danh mục
                                            </option>

                                            <option value="dao_tao">
                                                Đào tạo
                                            </option>

                                            <option value="hoc_bong">
                                                Học bổng
                                            </option>

                                            <option value="hoc_vu">
                                                Học vụ
                                            </option>

                                            <option value="tot_nghiep">
                                                Tốt nghiệp
                                            </option>
                                        </select>

                                        <textarea
                                            id="question"
                                            value={question}
                                            onChange={(event) =>
                                                setQuestion(
                                                    event.target.value
                                                )
                                            }
                                            rows={6}
                                            placeholder="Ví dụ: Sinh viên cần đáp ứng những điều kiện nào để được xét tốt nghiệp?"
                                            className="w-full resize-none rounded-xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none placeholder:text-slate-500"
                                        />

                                        <button
                                            type="submit"
                                            disabled={loading}
                                            className="w-full rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                                        >
                                            {loading
                                                ? "Đang xử lý..."
                                                : "Hỏi AI"}
                                        </button>
                                    </div>
                                </form>

                                {error && (
                                    <div className="mt-5 rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-red-200">
                                        {error}
                                    </div>
                                )}
                            </section>
                        </div>

                        {/* SEARCH RESULTS */}
                        {searchResult && (
                            <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <p className="text-sm text-slate-400">
                                            Kết quả tìm kiếm
                                        </p>

                                        <p className="mt-1 font-medium text-white">
                                            “{searchResult.query}”
                                        </p>
                                    </div>

                                    <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-sm text-cyan-200">
                                        {searchResult.retrieved_count} kết quả
                                    </span>
                                </div>

                                {searchResult.results.length === 0 ? (
                                    <div className="mt-5 rounded-xl border border-white/10 bg-slate-900/70 p-5 text-slate-400">
                                        Không tìm thấy tri thức phù hợp.
                                    </div>
                                ) : (
                                    <div className="mt-5 grid gap-4 lg:grid-cols-2">
                                        {searchResult.results.map(
                                            (item, index) => (
                                                <article
                                                    key={item.chunk_id}
                                                    className="rounded-xl border border-white/10 bg-slate-900/70 p-5"
                                                >
                                                    <div className="flex flex-wrap items-start justify-between gap-4">
                                                        <div>
                                                            <p className="text-sm font-semibold text-cyan-300">
                                                                Kết quả{" "}
                                                                {index + 1}
                                                            </p>

                                                            <p className="mt-1 font-medium text-white">
                                                                {item.source}
                                                            </p>
                                                        </div>

                                                        {item.distance !== null &&
                                                            item.distance !==
                                                                undefined && (
                                                                <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                                                                    Distance:{" "}
                                                                    {item.distance.toFixed(
                                                                        4
                                                                    )}
                                                                </span>
                                                            )}
                                                    </div>

                                                    <p className="mt-4 line-clamp-6 whitespace-pre-wrap text-sm leading-7 text-slate-300">
                                                        {item.content}
                                                    </p>

                                                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-400">
                                                        {item.page !== null &&
                                                            item.page !==
                                                                undefined && (
                                                                <span className="rounded-full border border-white/10 px-3 py-1">
                                                                    Trang{" "}
                                                                    {item.page}
                                                                </span>
                                                            )}

                                                        {item.category && (
                                                            <span className="rounded-full border border-white/10 px-3 py-1">
                                                                {formatCategory(
                                                                    item.category
                                                                )}
                                                            </span>
                                                        )}
                                                    </div>
                                                </article>
                                            )
                                        )}
                                    </div>
                                )}
                            </section>
                        )}

                        {/* AI ANSWER */}
                        {result && (
                            <section className="mt-6 space-y-6">
                                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/[0.05] p-6">
                                    <div className="flex flex-wrap items-center justify-between gap-3">
                                        <div>
                                            <p className="text-sm font-medium text-cyan-400">
                                                AI Response
                                            </p>

                                            <h2 className="mt-1 text-xl font-semibold">
                                                Câu trả lời
                                            </h2>
                                        </div>

                                        {isGeminiMode && (
                                            <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                                                ● Gemini AI
                                            </span>
                                        )}

                                        {isFallbackMode && (
                                            <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
                                                ● Truy xuất trực tiếp
                                            </span>
                                        )}
                                    </div>

                                    <div className="mt-5 whitespace-pre-wrap leading-7 text-slate-200">
                                        {result.answer}
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                    {/* HEADER */}
                                    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
                                        <div>
                                            <p className="text-sm font-medium text-cyan-400">
                                                Nguồn tham khảo
                                            </p>

                                            <h2 className="mt-1 text-xl font-semibold text-white">
                                                Mức độ liên quan của nguồn tri thức
                                            </h2>

                                            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                                                So sánh mức độ liên quan của các nguồn được
                                                hệ thống RAG truy xuất để tạo câu trả lời.
                                            </p>
                                        </div>

                                        <div className="rounded-full border border-white/10 bg-slate-900 px-4 py-2 text-sm text-slate-300">
                                            {result.retrieved_count} đoạn tri thức
                                        </div>
                                    </div>

                                    {/* CHART */}
                                    {sourceChartData.length > 0 && (
                                        <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-6">
                                            <div className="space-y-5">
                                                {sourceChartData.map(
                                                    (item, index) => (
                                                        <div
                                                            key={`${item.source}-${index}`}
                                                        >
                                                            <div className="mb-2 flex items-center justify-between gap-4">
                                                                <div className="flex min-w-0 items-center gap-3">
                                                                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-xs font-bold text-cyan-300">
                                                                        {index + 1}
                                                                    </span>

                                                                    <p
                                                                        className="truncate text-sm font-medium text-slate-200"
                                                                        title={item.source}
                                                                    >
                                                                        {item.source}
                                                                    </p>
                                                                </div>

                                                                <span className="shrink-0 text-sm font-semibold text-emerald-300">
                                                                    {item.relevance.toFixed(1)}%
                                                                </span>
                                                            </div>

                                                            <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                                                                <div
                                                                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-400 transition-all duration-700"
                                                                    style={{
                                                                        width: `${item.relevance}%`,
                                                                    }}
                                                                />
                                                            </div>
                                                        </div>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    )}


                                    {/* SOURCE DETAIL CARDS */}
                                    <div className="mt-6">
                                        <div className="mb-4 flex items-center justify-between">
                                            <h3 className="text-base font-semibold text-white">
                                                Chi tiết nguồn
                                            </h3>

                                            <span className="text-sm text-slate-500">
                                                {result.sources.length} nguồn
                                            </span>
                                        </div>

                                        <div className="grid gap-4 lg:grid-cols-2">
                                            {result.sources.length === 0 ? (
                                                <p className="text-slate-400">
                                                    Không có nguồn tài liệu.
                                                </p>
                                            ) : (
                                                result.sources.map(
                                                    (source, index) => (
                                                        <div
                                                            key={source.chunk_id}
                                                            className="rounded-xl border border-white/10 bg-slate-900/70 p-5 transition hover:border-cyan-400/20"
                                                        >
                                                            <div className="flex flex-wrap items-start justify-between gap-3">
                                                                <div className="min-w-0">
                                                                    <p className="text-xs font-medium uppercase tracking-wider text-cyan-400">
                                                                        Nguồn {index + 1}
                                                                    </p>

                                                                    <p
                                                                        className="mt-1 truncate font-semibold text-white"
                                                                        title={source.source}
                                                                    >
                                                                        {source.source}
                                                                    </p>
                                                                </div>

                                                                {source.distance !== null &&
                                                                    source.distance !== undefined && (
                                                                        <span className="shrink-0 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                                                                            Liên quan{" "}
                                                                            {Math.max(
                                                                                0,
                                                                                Math.min(
                                                                                    100,
                                                                                    (1 -
                                                                                        source.distance) *
                                                                                        100
                                                                                )
                                                                            ).toFixed(1)}
                                                                            %
                                                                        </span>
                                                                    )}
                                                            </div>

                                                            <div className="mt-5 grid gap-4 sm:grid-cols-3">
                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Trang
                                                                    </p>

                                                                    <p className="mt-1 text-sm font-medium text-slate-200">
                                                                        {source.page ?? "—"}
                                                                    </p>
                                                                </div>

                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Danh mục
                                                                    </p>

                                                                    <p className="mt-1 text-sm font-medium text-slate-200">
                                                                        {formatCategory(
                                                                            source.category
                                                                        )}
                                                                    </p>
                                                                </div>

                                                                <div>
                                                                    <p className="text-xs text-slate-500">
                                                                        Distance
                                                                    </p>

                                                                    <p className="mt-1 text-sm font-medium text-slate-200">
                                                                        {source.distance !== null &&
                                                                        source.distance !== undefined
                                                                            ? source.distance.toFixed(
                                                                                4
                                                                            )
                                                                            : "—"}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            <details className="mt-5 border-t border-white/10 pt-4">
                                                                <summary className="cursor-pointer text-sm font-medium text-cyan-300">
                                                                    Xem thông tin truy xuất
                                                                </summary>

                                                                <div className="mt-3 rounded-lg bg-slate-950 p-3 text-xs leading-6 text-slate-400">
                                                                    Chunk ID:{" "}
                                                                    {source.chunk_id}
                                                                </div>
                                                            </details>
                                                        </div>
                                                    )
                                                )
                                            )}
                                        </div>
                                    </div>

                                </div>

                                
                            </section>
                        )}
                    </>
                )}

                {/* TAB 3: REPOSITORY */}
                {activeTab === "repository" && (
                    <section>
                        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
                            <div>
                                <p className="text-sm font-medium text-cyan-400">
                                    Knowledge Repository
                                </p>

                                <h2 className="mt-1 text-xl font-semibold">
                                    Kho tài liệu tri thức
                                </h2>

                                <p className="mt-2 text-sm text-slate-400">
                                    Tìm kiếm và lọc tài liệu theo
                                    tên hoặc danh mục tri thức.
                                </p>
                            </div>

                            <div className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-200">
                                {filteredDocuments.length}/
                                {documents.length} tài liệu
                            </div>
                        </div>

                        <div className="mb-6 rounded-2xl border border-white/10 bg-white/5 p-5">
                            <div className="grid gap-4 lg:grid-cols-[1fr_240px]">
                                <div>
                                    <label
                                        htmlFor="document-search"
                                        className="mb-2 block text-sm font-medium text-slate-300"
                                    >
                                        Tìm tài liệu
                                    </label>

                                    <input
                                        id="document-search"
                                        type="text"
                                        value={documentSearch}
                                        onChange={(event) =>
                                            setDocumentSearch(
                                                event.target.value
                                            )
                                        }
                                        placeholder="Nhập tên tài liệu..."
                                        className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-500/50"
                                    />
                                </div>

                                <div>
                                    <label
                                        htmlFor="document-category"
                                        className="mb-2 block text-sm font-medium text-slate-300"
                                    >
                                        Danh mục
                                    </label>

                                    <select
                                        id="document-category"
                                        value={documentCategory}
                                        onChange={(event) =>
                                            setDocumentCategory(
                                                event.target.value
                                            )
                                        }
                                        className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none"
                                    >
                                        <option value="">
                                            Tất cả danh mục
                                        </option>

                                        <option value="dao_tao">
                                            Đào tạo
                                        </option>

                                        <option value="hoc_bong">
                                            Học bổng
                                        </option>

                                        <option value="hoc_vu">
                                            Học vụ
                                        </option>

                                        <option value="tot_nghiep">
                                            Tốt nghiệp
                                        </option>
                                    </select>
                                </div>
                            </div>

                            <div className="mt-4 flex flex-wrap gap-2">
                                {[
                                    {
                                        key: "",
                                        label: "Tất cả",
                                        count:
                                            documentCategoryCounts.all,
                                    },
                                    {
                                        key: "dao_tao",
                                        label: "Đào tạo",
                                        count:
                                            documentCategoryCounts.dao_tao,
                                    },
                                    {
                                        key: "hoc_bong",
                                        label: "Học bổng",
                                        count:
                                            documentCategoryCounts.hoc_bong,
                                    },
                                    {
                                        key: "hoc_vu",
                                        label: "Học vụ",
                                        count:
                                            documentCategoryCounts.hoc_vu,
                                    },
                                    {
                                        key: "tot_nghiep",
                                        label: "Tốt nghiệp",
                                        count:
                                            documentCategoryCounts.tot_nghiep,
                                    },
                                ].map((item) => (
                                    <button
                                        key={item.key}
                                        type="button"
                                        onClick={() =>
                                            setDocumentCategory(
                                                item.key
                                            )
                                        }
                                        className={`rounded-full border px-3 py-1.5 text-xs transition ${
                                            documentCategory ===
                                            item.key
                                                ? "border-cyan-400/30 bg-cyan-500/15 text-cyan-200"
                                                : "border-white/10 bg-slate-900 text-slate-400 hover:text-white"
                                        }`}
                                    >
                                        {item.label} {item.count}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {documentsLoading ? (
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-slate-400">
                                Đang tải danh sách tài liệu...
                            </div>
                        ) : documentsError ? (
                            <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-6 text-red-200">
                                {documentsError}
                            </div>
                        ) : filteredDocuments.length === 0 ? (
                            <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
                                <p className="font-medium text-slate-300">
                                    Không tìm thấy tài liệu
                                </p>

                                <p className="mt-2 text-sm text-slate-500">
                                    Thử thay đổi từ khóa
                                    hoặc danh mục tìm kiếm.
                                </p>
                            </div>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                                {filteredDocuments.map(
                                    (document) => (
                                        <div
                                            key={`${document.category}-${document.filename}`}
                                            className="rounded-2xl border border-white/10 bg-white/5 p-5 transition hover:border-cyan-400/20 hover:bg-white/[0.07]"
                                        >
                                            <div className="flex h-full flex-col">
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="min-w-0">
                                                        <p
                                                            className="truncate font-semibold text-white"
                                                            title={
                                                                document.filename
                                                            }
                                                        >
                                                            {
                                                                document.filename
                                                            }
                                                        </p>

                                                        <div className="mt-3 flex flex-wrap gap-2">
                                                            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                                                                {formatCategory(
                                                                    document.category
                                                                )}
                                                            </span>

                                                            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                                                                {document.file_type.toUpperCase()}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <div className="text-xl">
                                                        📄
                                                    </div>
                                                </div>

                                                <p className="mt-auto pt-5 text-sm text-slate-500">
                                                    {formatFileSize(
                                                        document.size_bytes
                                                    )}
                                                </p>
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        )}
                    </section>
                )}
            </div>
        </main>
    )
    
}