export type ScholarshipStatus =
    | "eligible"
    | "not_eligible"
    | "insufficient_data";


export interface ScholarshipFailedConditionSummary {
    condition: string;
    student_count: number;
    rate: number;
}


export interface ScholarshipMissingFieldSummary {
    field_name: string;
    student_count: number;
    rate: number;
}


export interface ScholarshipSummary {
    total_students: number;

    eligible_count: number;
    not_eligible_count: number;
    insufficient_data_count: number;

    eligible_rate: number;
    not_eligible_rate: number;
    insufficient_data_rate: number;

    excellent_count: number;
    good_count: number;
    encouragement_count: number;

    top_failed_conditions:
        ScholarshipFailedConditionSummary[];

    top_missing_fields:
        ScholarshipMissingFieldSummary[];
}


export interface ScholarshipConditionResult {
    condition_code: string;
    condition_name: string;

    passed: boolean;

    actual_value:
        | string
        | number
        | boolean
        | null;

    required_value:
        | string
        | number
        | boolean
        | null;

    reason: string | null;
}


export interface StudentScholarshipResult {
    student_id: string;
    student_name: string;

    status: ScholarshipStatus;

    scholarship_type: string | null;
    scholarship_level: string | null;

    ranking_score: number | null;

    missing_fields: string[];
    failed_conditions: string[];

    condition_results:
        ScholarshipConditionResult[];

    recommendation: string;
}


export interface ScholarshipSource {
    document_name: string;
    page_number: number | null;
    chunk_id: string | null;
    evidence_text: string;
    category: string;
}


export interface ScholarshipMetadata {
    major: string | null;
    cohort: string | null;
    program: string | null;

    effective_date: string | null;
    scholarship_type: string | null;
    generated_by: string | null;

    recognized_columns: Record<
        string,
        string
    >;

    unrecognized_columns: string[];

    source_document_count: number;
    rule_count: number;
}


export interface ScholarshipEvaluationResponse {
    success: boolean;

    dataset_name: string;

    rule_set_code: string;
    rule_set_name: string;
    rule_set_version: string;

    summary: ScholarshipSummary;

    students: StudentScholarshipResult[];

    sources: ScholarshipSource[];

    warnings: string[];

    metadata: ScholarshipMetadata;
}