export interface RAGEvaluationMetrics {
    precision_at_5: number;
    recall_at_5: number;
    hit_at_1: number;
    hit_at_3: number;
    hit_at_5: number;
    mrr: number;
}

export interface RAGEvaluationResult {
    id: number;
    question: string;
    category: string;
    rank: number | null;
    precision: number;
    recall: number;
    hit_at_1: number;
    hit_at_3: number;
    hit_at_5: number;
    rr: number;
    retrieved_ids: string[];
}

export interface RAGEvaluation {
    top_k: number;
    evaluated_queries: number;
    metrics: RAGEvaluationMetrics;
    results: RAGEvaluationResult[];
}

interface EvaluationResponse {
    success: boolean;
    evaluation: RAGEvaluation;
}

const API_URL =
    process.env.NEXT_PUBLIC_API_URL ??
    "http://127.0.0.1:8000";

export async function getRAGEvaluation():
    Promise<RAGEvaluation> {

    const response = await fetch(
        `${API_URL}/knowledge/evaluation`,
        {
            method: "GET",
            cache: "no-store",
        }
    );

    if (!response.ok) {
        throw new Error(
            "Không thể tải kết quả RAG Evaluation"
        );
    }

    const data: EvaluationResponse =
        await response.json();

    return data.evaluation;
}