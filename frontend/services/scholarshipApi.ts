import type {
    ScholarshipEvaluationResponse,
} from "@/types/scholarship";


const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000";


async function parseResponse(
    response: Response,
): Promise<ScholarshipEvaluationResponse> {
    let payload: unknown;

    try {
        payload = await response.json();
    } catch {
        throw new Error(
            "Backend trả về dữ liệu không hợp lệ.",
        );
    }

    if (!response.ok) {
        let detail =
            `HTTP ${response.status}`;

        if (
            typeof payload === "object" &&
            payload !== null &&
            "detail" in payload
        ) {
            const rawDetail = (
                payload as {
                    detail: unknown;
                }
            ).detail;

            detail =
                typeof rawDetail === "string"
                    ? rawDetail
                    : JSON.stringify(
                          rawDetail,
                      );
        }

        throw new Error(detail);
    }

    return payload as
        ScholarshipEvaluationResponse;
}


export async function evaluateScholarship(
    file: File,
    ruleSetCode = "scholarship_test",
): Promise<ScholarshipEvaluationResponse> {
    const formData = new FormData();

    formData.append(
        "file",
        file,
    );

    formData.append(
        "rule_set_code",
        ruleSetCode,
    );

    const response = await fetch(
        `${API_BASE_URL}/scholarship/evaluate`,
        {
            method: "POST",
            body: formData,
        },
    );

    return parseResponse(response);
}


export async function evaluateStoredScholarship(
    filename: string,
    ruleSetCode = "scholarship_test",
): Promise<ScholarshipEvaluationResponse> {
    const response = await fetch(
        `${API_BASE_URL}/scholarship/evaluate-stored`,
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json",
            },
            body: JSON.stringify({
                filename,
                rule_set_code:
                    ruleSetCode,
            }),
        },
    );

    return parseResponse(response);
}