export type InsightSeverity =
    | "low"
    | "medium"
    | "high"
    | "critical"

export type InsightType =
    | "information"
    | "positive"
    | "warning"
    | "critical"

export interface InsightEvidence {
    column?: string | null
    related_columns?: string[]
    affected_rows?: number | null
    total_rows?: number | null
    calculation?: string | null
    sample_values?: unknown[]
}

export interface InsightObject {
    id: string
    type: InsightType
    category: string
    title: string
    description: string
    metric?: string | null
    value?: number | string | null
    unit?: string | null
    threshold?: string | number | null
    severity: InsightSeverity
    evidence?: InsightEvidence | null
    metadata?: Record<string, unknown>
}

export interface RecommendationObject {
    id: string
    source_insight_id: string
    category: string
    title: string
    description: string
    priority: InsightSeverity
    actions: string[]
    metadata?: Record<string, unknown>
}

export interface FusionResponse {
    dataset_name: string
    total_insights: number
    insights: InsightObject[]
    recommendations: RecommendationObject[]
    summary: Record<string, number>
    llm_insight?: LLMInsightResult
}

export interface LLMKeyFinding {
    title: string
    description: string
    severity: string
}

export interface LLMRecommendation {
    title: string
    description: string
    priority: string
}

export interface LLMInsightResult {
    enabled: boolean
    generated: boolean
    model: string
    executive_summary: string | null
    key_findings: LLMKeyFinding[]
    recommendations: LLMRecommendation[]
    error: string | null
}