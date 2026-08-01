"use client";

import {
    useEffect,
    useState,
} from "react";

import {
    evaluateStoredGraduation,
} from "@/services/graduationApi";

import type {
    GraduationEvaluationResponse,
} from "@/types/graduation";


export default function EvaluationPage() {
    const [
        uploadedFilename,
        setUploadedFilename,
    ] = useState("");

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    const [result, setResult] =
        useState<
            GraduationEvaluationResponse | null
        >(null);


    useEffect(() => {
        const storedFilename =
            localStorage.getItem(
                "uploadedFile",
            );

        if (storedFilename) {
            setUploadedFilename(
                storedFilename,
            );
        }
    }, []);


    async function handleEvaluate() {
        if (!uploadedFilename) {
            setError(
                "Không tìm thấy file đã tải lên. " +
                "Vui lòng quay lại trang Upload.",
            );
            return;
        }

        try {
            setLoading(true);
            setError("");
            setResult(null);

            const response =
                await evaluateStoredGraduation(
                    uploadedFilename,
                );

            setResult(response);
        } catch (err: unknown) {
            const message =
                err instanceof Error
                    ? err.message
                    : (
                        "Không thể đánh giá " +
                        "dữ liệu."
                    );

            setError(message);
        } finally {
            setLoading(false);
        }
    }


    return (
        <main
            className="
                min-h-screen
                bg-slate-50
                px-6 py-10
            "
        >
            <div
                className="
                    mx-auto
                    max-w-6xl
                "
            >
                <section
                    className="
                        rounded-3xl
                        bg-white
                        p-8
                        shadow-sm
                    "
                >
                    <div>
                        <p
                            className="
                                text-sm
                                font-semibold
                                uppercase
                                tracking-wider
                                text-blue-600
                            "
                        >
                            InsightFlowAI
                        </p>

                        <h1
                            className="
                                mt-2
                                text-3xl
                                font-bold
                                text-slate-900
                            "
                        >
                            Đánh giá điều kiện tốt nghiệp
                        </h1>

                        <p
                            className="
                                mt-3
                                max-w-3xl
                                text-sm
                                leading-6
                                text-slate-600
                            "
                        >
                            Hệ thống sử dụng dataset
                            đã được tải lên, đối chiếu
                            dữ liệu với bộ luật được
                            trích xuất từ kho tri thức
                            PDF và trả về kết quả đánh
                            giá chi tiết.
                        </p>
                    </div>

                    <div
                        className="
                            mt-8
                            rounded-2xl
                            border
                            border-slate-200
                            bg-slate-50
                            p-6
                        "
                    >
                        <p
                            className="
                                text-sm
                                font-semibold
                                text-slate-800
                            "
                        >
                            Dataset đang được đánh giá
                        </p>

                        <p
                            className="
                                mt-2
                                break-all
                                text-sm
                                text-blue-700
                            "
                        >
                            {uploadedFilename ||
                                (
                                    "Chưa có file nào " +
                                    "được tải lên"
                                )}
                        </p>

                        {!uploadedFilename && (
                            <p
                                className="
                                    mt-3
                                    text-sm
                                    text-amber-600
                                "
                            >
                                Vui lòng quay lại trang
                                Upload và tải dataset
                                trước khi đánh giá.
                            </p>
                        )}

                        <button
                            type="button"
                            onClick={handleEvaluate}
                            disabled={
                                loading ||
                                !uploadedFilename
                            }
                            className="
                                mt-5
                                rounded-xl
                                bg-blue-600
                                px-6 py-3
                                text-sm
                                font-semibold
                                text-white
                                transition
                                hover:bg-blue-700
                                disabled:cursor-not-allowed
                                disabled:bg-slate-300
                            "
                        >
                            {loading
                                ? "Đang đánh giá..."
                                : "Bắt đầu đánh giá"}
                        </button>
                    </div>

                    {error && (
                        <div
                            className="
                                mt-6
                                rounded-xl
                                border
                                border-red-200
                                bg-red-50
                                p-4
                            "
                        >
                            <p
                                className="
                                    text-sm
                                    font-semibold
                                    text-red-700
                                "
                            >
                                Không thể xử lý yêu cầu
                            </p>

                            <p
                                className="
                                    mt-1
                                    text-sm
                                    text-red-600
                                "
                            >
                                {error}
                            </p>
                        </div>
                    )}
                </section>

                {result && (
                    <section
                        className="
                            mt-8
                            rounded-3xl
                            bg-white
                            p-8
                            shadow-sm
                        "
                    >
                        <div>
                            <p
                                className="
                                    text-sm
                                    font-semibold
                                    text-emerald-600
                                "
                            >
                                Đánh giá thành công
                            </p>

                            <h2
                                className="
                                    mt-2
                                    text-2xl
                                    font-bold
                                    text-slate-900
                                "
                            >
                                {result.rule_set_name}
                            </h2>

                            <p
                                className="
                                    mt-2
                                    text-sm
                                    text-slate-500
                                "
                            >
                                Dataset:{" "}
                                {result.dataset_name}
                            </p>
                        </div>

                        <div
                            className="
                                mt-8
                                grid
                                gap-4
                                sm:grid-cols-2
                                lg:grid-cols-4
                            "
                        >
                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-slate-200
                                    p-5
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-slate-500
                                    "
                                >
                                    Tổng sinh viên
                                </p>

                                <p
                                    className="
                                        mt-2
                                        text-3xl
                                        font-bold
                                        text-slate-900
                                    "
                                >
                                    {
                                        result.summary
                                            .total_students
                                    }
                                </p>
                            </div>

                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-emerald-200
                                    bg-emerald-50
                                    p-5
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-emerald-700
                                    "
                                >
                                    Đủ điều kiện
                                </p>

                                <p
                                    className="
                                        mt-2
                                        text-3xl
                                        font-bold
                                        text-emerald-700
                                    "
                                >
                                    {
                                        result.summary
                                            .eligible_count
                                    }
                                </p>

                                <p
                                    className="
                                        mt-1
                                        text-sm
                                        text-emerald-600
                                    "
                                >
                                    {
                                        result.summary
                                            .eligible_rate
                                    }
                                    %
                                </p>
                            </div>

                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-red-200
                                    bg-red-50
                                    p-5
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-red-700
                                    "
                                >
                                    Chưa đủ điều kiện
                                </p>

                                <p
                                    className="
                                        mt-2
                                        text-3xl
                                        font-bold
                                        text-red-700
                                    "
                                >
                                    {
                                        result.summary
                                            .not_eligible_count
                                    }
                                </p>

                                <p
                                    className="
                                        mt-1
                                        text-sm
                                        text-red-600
                                    "
                                >
                                    {
                                        result.summary
                                            .not_eligible_rate
                                    }
                                    %
                                </p>
                            </div>

                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-amber-200
                                    bg-amber-50
                                    p-5
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-amber-700
                                    "
                                >
                                    Thiếu dữ liệu
                                </p>

                                <p
                                    className="
                                        mt-2
                                        text-3xl
                                        font-bold
                                        text-amber-700
                                    "
                                >
                                    {
                                        result.summary
                                            .insufficient_data_count
                                    }
                                </p>

                                <p
                                    className="
                                        mt-1
                                        text-sm
                                        text-amber-600
                                    "
                                >
                                    {
                                        result.summary
                                            .insufficient_data_rate
                                    }
                                    %
                                </p>
                            </div>
                        </div>

                        <div className="mt-8">
                            <h3
                                className="
                                    text-lg
                                    font-bold
                                    text-slate-900
                                "
                            >
                                Các điều kiện không đạt
                                phổ biến
                            </h3>

                            {result.summary
                                .top_failed_conditions
                                .length === 0 ? (
                                <p
                                    className="
                                        mt-4
                                        text-sm
                                        text-slate-500
                                    "
                                >
                                    Không có điều kiện
                                    không đạt phổ biến.
                                </p>
                            ) : (
                                <div
                                    className="
                                        mt-4
                                        space-y-3
                                    "
                                >
                                    {result.summary
                                        .top_failed_conditions
                                        .map(
                                            (
                                                item,
                                                index,
                                            ) => (
                                                <div
                                                    key={
                                                        `${item.condition}-` +
                                                        index
                                                    }
                                                    className="
                                                        rounded-xl
                                                        border
                                                        border-slate-200
                                                        p-4
                                                    "
                                                >
                                                    <div
                                                        className="
                                                            flex
                                                            flex-col
                                                            gap-2
                                                            sm:flex-row
                                                            sm:items-center
                                                            sm:justify-between
                                                        "
                                                    >
                                                        <p
                                                            className="
                                                                text-sm
                                                                font-medium
                                                                text-slate-800
                                                            "
                                                        >
                                                            {
                                                                item.condition
                                                            }
                                                        </p>

                                                        <div
                                                            className="
                                                                flex
                                                                items-center
                                                                gap-3
                                                                text-sm
                                                            "
                                                        >
                                                            <span
                                                                className="
                                                                    font-semibold
                                                                    text-slate-900
                                                                "
                                                            >
                                                                {
                                                                    item.student_count
                                                                }{" "}
                                                                sinh viên
                                                            </span>

                                                            <span
                                                                className="
                                                                    rounded-full
                                                                    bg-slate-100
                                                                    px-3 py-1
                                                                    text-slate-600
                                                                "
                                                            >
                                                                {
                                                                    item.rate
                                                                }
                                                                %
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ),
                                        )}
                                </div>
                            )}
                        </div>

                        {result.warnings.length > 0 && (
                            <div
                                className="
                                    mt-8
                                    rounded-2xl
                                    border
                                    border-amber-200
                                    bg-amber-50
                                    p-5
                                "
                            >
                                <h3
                                    className="
                                        font-bold
                                        text-amber-800
                                    "
                                >
                                    Cảnh báo
                                </h3>

                                <div
                                    className="
                                        mt-3
                                        space-y-2
                                    "
                                >
                                    {result.warnings.map(
                                        (
                                            warning,
                                            index,
                                        ) => (
                                            <p
                                                key={
                                                    `${warning}-` +
                                                    index
                                                }
                                                className="
                                                    text-sm
                                                    text-amber-700
                                                "
                                            >
                                                • {warning}
                                            </p>
                                        ),
                                    )}
                                </div>
                            </div>
                        )}
                    </section>
                )}
            </div>
        </main>
    );
}