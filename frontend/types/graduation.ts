export type GraduationStatus =
    | "eligible"
    | "not_eligible"
    | "insufficient_data";


export interface FailedConditionSummary {
    condition: string;
    student_count: number;
    rate: number;
}


export interface GraduationSummary {
    total_students: number;
    eligible_count: number;
    not_eligible_count: number;
    insufficient_data_count: number;

    eligible_rate: number;
    not_eligible_rate: number;
    insufficient_data_rate: number;

    top_failed_conditions: FailedConditionSummary[];
}


export interface GraduationConditionResult {
    condition_code: string;
    condition_name: string;
    passed: boolean;

    actual_value: string | number | boolean | null;
    required_value: string | number | boolean | null;

    reason: string | null;
}


export interface StudentGraduationResult {
    student_id: string;
    student_name: string;

    status: GraduationStatus;

    conditions: GraduationConditionResult[];

    recommendation: string | null;
}


export interface GraduationSource {
    document_name: string;
    page_number: number | null;
    chunk_id: string;
    evidence_text: string;
    category: string;
}


export interface GraduationMetadata {
    major: string | null;
    cohort: string | null;
    program: string | null;

    effective_date: string | null;
    generated_by: string | null;

    recognized_columns: Record<
        string,
        string
    >;

    unrecognized_columns: string[];

    source_document_count: number;
    rule_count: number;
}


export interface GraduationEvaluationResponse {
    success: boolean;

    dataset_name: string;

    rule_set_code: string;
    rule_set_name: string;
    rule_set_version: string;

    summary: GraduationSummary;

    students: StudentGraduationResult[];

    sources: GraduationSource[];

    warnings: string[];

    metadata: GraduationMetadata;
}
