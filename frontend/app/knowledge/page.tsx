"use client"

import { useState } from "react"


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


export default function KnowledgePage() {
    const [question, setQuestion] = useState("")
    const [category, setCategory] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [result, setResult] =
        useState<KnowledgeResponse | null>(null)

        const generationMode =
            result?.metadata?.generation_mode

        const isGeminiMode =
            generationMode === "gemini"

        const isFallbackMode =
            generationMode === "retrieval_fallback"

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

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
            <div className="mx-auto max-w-5xl">
                <div className="mb-8">
                    <p className="text-sm font-medium uppercase tracking-[0.25em] text-cyan-400">
                        InsightFlowAI
                    </p>

                    <h1 className="mt-3 text-3xl font-bold">
                        Knowledge Assistant
                    </h1>

                    <p className="mt-3 max-w-3xl text-slate-400">
                        Đặt câu hỏi về quy định đào tạo,
                        học vụ, học bổng và tốt nghiệp
                        dựa trên kho tri thức Đại học
                        Văn Hiến.
                    </p>
                </div>

                <form
                    onSubmit={handleSubmit}
                    className="rounded-2xl border border-white/10 bg-white/5 p-6"
                >
                    <label
                        htmlFor="category"
                        className="mb-2 block text-sm font-medium text-slate-300"
                    >
                        Danh mục tài liệu
                    </label>

                    <select
                        id="category"
                        value={category}
                        onChange={(event) =>
                            setCategory(
                                event.target.value
                            )
                        }
                        className="mb-5 w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none"
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

                    <label
                        htmlFor="question"
                        className="mb-2 block text-sm font-medium text-slate-300"
                    >
                        Câu hỏi
                    </label>

                    <textarea
                        id="question"
                        value={question}
                        onChange={(event) =>
                            setQuestion(
                                event.target.value
                            )
                        }
                        rows={5}
                        placeholder="Ví dụ: Điều kiện xét tốt nghiệp của sinh viên là gì?"
                        className="w-full resize-none rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500"
                    />

                    <div className="mt-5 flex justify-end">
                        <button
                            type="submit"
                            disabled={loading}
                            className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading
                                ? "Đang truy xuất..."
                                : "Gửi câu hỏi"}
                        </button>
                    </div>
                </form>

                {error && (
                    <div className="mt-6 rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-red-200">
                        {error}
                    </div>
                )}

                {result && (
                    <section className="mt-8 space-y-6">
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <p className="text-sm font-medium text-cyan-400">
                                    Câu trả lời
                                </p>

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

                            <div className="mt-4 whitespace-pre-wrap leading-7 text-slate-200">
                                {result.answer}
                            </div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold">
                                    Nguồn tham khảo
                                </h2>

                                <span className="text-sm text-slate-400">
                                    {
                                        result.retrieved_count
                                    }{" "}
                                    đoạn tri thức
                                </span>
                            </div>

                            <div className="mt-5 space-y-3">
                                {result.sources.length === 0 ? (
                                    <p className="text-slate-400">
                                        Không có nguồn tài liệu.
                                    </p>
                                ) : (
                                    result.sources.map(
                                        (
                                            source,
                                            index
                                        ) => (
                                            <div
                                                key={
                                                    source.chunk_id
                                                }
                                                className="rounded-xl border border-white/10 bg-slate-900/70 p-4"
                                            >
                                                <p className="font-medium">
                                                    {index + 1}.{" "}
                                                    {
                                                        source.source
                                                    }
                                                </p>

                                                <div className="mt-2 flex flex-wrap gap-3 text-sm text-slate-400">
                                                    {source.page !==
                                                        null &&
                                                        source.page !==
                                                        undefined && (
                                                            <span>
                                                                Trang{" "}
                                                                {
                                                                    source.page
                                                                }
                                                            </span>
                                                        )}

                                                    {source.category && (
                                                        <span>
                                                            Danh mục:{" "}
                                                            {
                                                                source.category
                                                            }
                                                        </span>
                                                    )}

                                                    {source.distance !==
                                                        null &&
                                                        source.distance !==
                                                        undefined && (
                                                            <span>
                                                                Khoảng cách:{" "}
                                                                {source.distance.toFixed(
                                                                    4
                                                                )}
                                                            </span>
                                                        )}
                                                </div>
                                            </div>
                                        )
                                    )
                                )}
                            </div>
                        </div>
                    </section>
                )}
            </div>
        </main>
    )
}