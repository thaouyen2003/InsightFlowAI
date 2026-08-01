import type {
    GraduationEvaluationResponse,
} from "@/types/graduation";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000";

export async function evaluateGraduation(
    file: File,
    ruleSetCode =
        "qd_xtn_dh_chinh_quy_vhu",
): Promise<GraduationEvaluationResponse> {
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
        `${API_BASE_URL}/graduation/evaluate`,
        {
            method: "POST",
            body: formData,
        },
    );

    let payload: unknown;

    try {
        payload =
            await response.json();
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
            const rawDetail =
                (
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

    return payload as GraduationEvaluationResponse;
}


export async function evaluateStoredGraduation(
    filename: string,
    ruleSetCode =
        "qd_xtn_dh_chinh_quy_vhu",
): Promise<GraduationEvaluationResponse> {
    const response = await fetch(
        `${API_BASE_URL}/graduation/evaluate-stored`,
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

    let payload: unknown;

    try {
        payload =
            await response.json();
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
            const rawDetail =
                (
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
        GraduationEvaluationResponse;
}