"use client";

import {
    useEffect,
    useState,
} from "react";

import {
    evaluateStoredGraduation,
} from "@/services/graduationApi";

import {
    evaluateStoredScholarship,
} from "@/services/scholarshipApi";

import type {
    GraduationEvaluationResponse,
} from "@/types/graduation";

import type {
    ScholarshipEvaluationResponse,
} from "@/types/scholarship";

import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";


type EvaluationType =
    | "graduation"
    | "scholarship"
    | "admission";


interface EvaluationTab {
    id: EvaluationType;
    label: string;
    title: string;
    description: string;
}


interface FailedConditionTooltipProps {
    active?: boolean;

    payload?: Array<{
        payload: {
            fullCondition: string;
            count: number;
            rate: number;
        };
    }>;
}


const EVALUATION_TABS: EvaluationTab[] = [
    {
        id: "graduation",
        label: "Tốt nghiệp",
        title:
            "Đánh giá điều kiện tốt nghiệp",
        description:
            "Đối chiếu dữ liệu sinh viên với bộ luật xét và công nhận tốt nghiệp.",
    },
    {
        id: "scholarship",
        label: "Học bổng",
        title:
            "Đánh giá điều kiện học bổng",
        description:
            "Đối chiếu dữ liệu sinh viên với bộ luật xét và cấp học bổng.",
    },
    {
        id: "admission",
        label: "Tuyển sinh",
        title:
            "Đánh giá điều kiện tuyển sinh",
        description:
            "Đối chiếu hồ sơ với các điều kiện xét tuyển đầu vào.",
    },
];


const CHART_COLORS = [
    "#2563eb",
    "#e11d48",
    "#f59e0b",
];


function resolveEvaluationType(
    category: string,
    filename: string,
): EvaluationType | null {
    const normalizedCategory =
        category
            .trim()
            .toLowerCase();

    if (
        normalizedCategory ===
            "tot_nghiep" ||
        normalizedCategory ===
            "graduation"
    ) {
        return "graduation";
    }

    if (
        normalizedCategory ===
            "hoc_bong" ||
        normalizedCategory ===
            "scholarship"
    ) {
        return "scholarship";
    }

    if (
        normalizedCategory ===
            "tuyen_sinh" ||
        normalizedCategory ===
            "admission"
    ) {
        return "admission";
    }

    const normalizedFilename =
        filename.toLowerCase();

    if (
        normalizedFilename.includes(
            "tot_nghiep",
        ) ||
        normalizedFilename.includes(
            "tot-nghiep",
        ) ||
        normalizedFilename.includes(
            "graduation",
        )
    ) {
        return "graduation";
    }

    if (
        normalizedFilename.includes(
            "hoc_bong",
        ) ||
        normalizedFilename.includes(
            "hoc-bong",
        ) ||
        normalizedFilename.includes(
            "scholarship",
        )
    ) {
        return "scholarship";
    }

    if (
        normalizedFilename.includes(
            "tuyen_sinh",
        ) ||
        normalizedFilename.includes(
            "tuyen-sinh",
        ) ||
        normalizedFilename.includes(
            "admission",
        )
    ) {
        return "admission";
    }

    return null;
}


function shortenCondition(
    value: string,
): string {
    const maxLength = 34;

    if (value.length <= maxLength) {
        return value;
    }

    return (
        value
            .slice(
                0,
                maxLength,
            )
            .trim() + "..."
    );
}


function FailedConditionTooltip({
    active,
    payload,
}: FailedConditionTooltipProps) {
    if (
        !active ||
        !payload ||
        payload.length === 0
    ) {
        return null;
    }

    const item =
        payload[0].payload;

    return (
        <div
            className="
                max-w-sm
                rounded-xl
                border
                border-slate-700
                bg-slate-950
                p-4
                shadow-2xl
            "
        >
            <p
                className="
                    text-sm
                    font-semibold
                    leading-5
                    text-white
                "
            >
                {item.fullCondition}
            </p>

            <p
                className="
                    mt-2
                    text-sm
                    text-slate-300
                "
            >
                {item.count} sinh viên
            </p>

            <p
                className="
                    mt-1
                    text-xs
                    text-slate-400
                "
            >
                Tỷ lệ: {item.rate}%
            </p>
        </div>
    );
}


export default function EvaluationPage() {
    const [
        uploadedFilename,
        setUploadedFilename,
    ] = useState("");

    const [
        evaluationType,
        setEvaluationType,
    ] = useState<EvaluationType>(
        "graduation",
    );

    const [
        detectedEvaluationType,
        setDetectedEvaluationType,
    ] = useState<
        EvaluationType | null
    >(null);

    const [
        graduationResult,
        setGraduationResult,
    ] = useState<
        GraduationEvaluationResponse | null
    >(null);

    const [
        scholarshipResult,
        setScholarshipResult,
    ] = useState<
        ScholarshipEvaluationResponse | null
    >(null);

    const [
        loading,
        setLoading,
    ] = useState(false);

    const [
        error,
        setError,
    ] = useState("");

    const [
        currentPage,
        setCurrentPage,
    ] = useState(1);

    const rowsPerPage = 20;

    const activeTab =
        EVALUATION_TABS.find(
            (tab) =>
                tab.id ===
                evaluationType,
        );

    const detectedTab =
        EVALUATION_TABS.find(
            (tab) =>
                tab.id ===
                detectedEvaluationType,
        );

    const activeResult =
        evaluationType ===
        "graduation"
            ? graduationResult
            : evaluationType ===
              "scholarship"
            ? scholarshipResult
            : null;

    const isEvaluationCompatible =
        detectedEvaluationType === null ||
        detectedEvaluationType ===
            evaluationType;


    useEffect(() => {
        const storedFilename =
            localStorage.getItem(
                "uploadedFile",
            ) ?? "";

        const storedCategory =
            localStorage.getItem(
                "datasetCategory",
            ) ?? "";

        setUploadedFilename(
            storedFilename,
        );

        const detectedType =
            resolveEvaluationType(
                storedCategory,
                storedFilename,
            );

        setDetectedEvaluationType(
            detectedType,
        );

        if (detectedType) {
            setEvaluationType(
                detectedType,
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

        if (!isEvaluationCompatible) {
            setError(
                "Dataset hiện tại được nhận diện " +
                `thuộc lĩnh vực ${
                    detectedTab?.label ??
                    "khác"
                }. ` +
                "Vui lòng chọn đúng tab để xem phân tích.",
            );

            return;
        }

        if (
            evaluationType ===
            "admission"
        ) {
            setError(
                "Chức năng đánh giá tuyển sinh " +
                "sẽ được bổ sung trong Sprint tiếp theo.",
            );

            return;
        }

        try {
            setLoading(true);
            setError("");

            if (
                evaluationType ===
                "graduation"
            ) {
                const response =
                    await evaluateStoredGraduation(
                        uploadedFilename,
                    );

                setGraduationResult(
                    response,
                );
            }

            if (
                evaluationType ===
                "scholarship"
            ) {
                const response =
                    await evaluateStoredScholarship(
                        uploadedFilename,
                    );

                setScholarshipResult(
                    response,
                );
            }

            setCurrentPage(1);
        } catch (requestError: unknown) {
            const message =
                requestError instanceof Error
                    ? requestError.message
                    : (
                        "Không thể đánh giá " +
                        "dữ liệu."
                    );

            setError(message);
        } finally {
            setLoading(false);
        }
    }


    const totalPages =
        activeResult
            ? Math.max(
                  1,
                  Math.ceil(
                      activeResult
                          .students
                          .length /
                          rowsPerPage,
                  ),
              )
            : 0;


    const paginatedStudents =
        activeResult
            ? activeResult
                  .students
                  .slice(
                      (
                          currentPage -
                          1
                      ) *
                          rowsPerPage,
                      currentPage *
                          rowsPerPage,
                  )
            : [];


    const pieData =
        activeResult
            ? [
                  {
                      name:
                          "Đủ điều kiện",
                      value:
                          activeResult
                              .summary
                              .eligible_count,
                  },
                  {
                      name:
                          "Chưa đủ điều kiện",
                      value:
                          activeResult
                              .summary
                              .not_eligible_count,
                  },
                  {
                      name:
                          "Thiếu dữ liệu",
                      value:
                          activeResult
                              .summary
                              .insufficient_data_count,
                  },
              ]
            : [];


    const failedConditionData =
        activeResult
            ? activeResult
                  .summary
                  .top_failed_conditions
                  .map(
                      (item) => ({
                          condition:
                              shortenCondition(
                                  item.condition,
                              ),

                          fullCondition:
                              item.condition,

                          count:
                              item.student_count,

                          rate:
                              item.rate,
                      }),
                  )
            : [];


    const evaluateButtonLabel =
        evaluationType ===
        "graduation"
            ? "Phân tích tốt nghiệp"
            : evaluationType ===
              "scholarship"
            ? "Phân tích học bổng"
            : "Tuyển sinh sẽ được bổ sung";


    return (
        <main
            className="
                min-h-screen
                bg-slate-50
                px-6
                py-10
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
                            {activeTab?.title}
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
                            {activeTab?.description}
                        </p>
                    </div>


                    <div className="mt-8">
                        <div
                            className="
                                grid
                                grid-cols-1
                                gap-3
                                rounded-2xl
                                bg-slate-100
                                p-2
                                sm:grid-cols-3
                            "
                        >
                            {EVALUATION_TABS.map(
                                (tab) => {
                                    const isActive =
                                        evaluationType ===
                                        tab.id;

                                    const isDetected =
                                        detectedEvaluationType ===
                                        tab.id;

                                    return (
                                        <button
                                            key={
                                                tab.id
                                            }
                                            type="button"
                                            onClick={() => {
                                                setEvaluationType(
                                                    tab.id,
                                                );

                                                setError(
                                                    "",
                                                );

                                                setCurrentPage(
                                                    1,
                                                );
                                            }}
                                            className={`
                                                relative
                                                rounded-xl
                                                px-5
                                                py-4
                                                text-left
                                                transition
                                                ${
                                                    isActive
                                                        ? "bg-white shadow-sm ring-2 ring-blue-500"
                                                        : "hover:bg-white/70"
                                                }
                                            `}
                                        >
                                            <div
                                                className="
                                                    flex
                                                    items-center
                                                    justify-between
                                                    gap-3
                                                "
                                            >
                                                <span
                                                    className={`
                                                        font-semibold
                                                        ${
                                                            isActive
                                                                ? "text-blue-700"
                                                                : "text-slate-700"
                                                        }
                                                    `}
                                                >
                                                    {
                                                        tab.label
                                                    }
                                                </span>

                                                {isDetected && (
                                                    <span
                                                        className="
                                                            rounded-full
                                                            bg-emerald-100
                                                            px-2.5
                                                            py-1
                                                            text-[11px]
                                                            font-semibold
                                                            text-emerald-700
                                                        "
                                                    >
                                                        Phù hợp dữ liệu
                                                    </span>
                                                )}
                                            </div>

                                            <p
                                                className="
                                                    mt-2
                                                    text-xs
                                                    leading-5
                                                    text-slate-500
                                                "
                                            >
                                                {
                                                    tab.description
                                                }
                                            </p>
                                        </button>
                                    );
                                },
                            )}
                        </div>
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
                                    "Chưa có file " +
                                    "nào được tải lên"
                                )}
                        </p>


                        {detectedTab && (
                            <p
                                className="
                                    mt-3
                                    text-sm
                                    text-emerald-700
                                "
                            >
                                Hệ thống nhận diện
                                dataset thuộc lĩnh vực{" "}
                                <strong>
                                    {
                                        detectedTab
                                            .label
                                    }
                                </strong>
                                .
                            </p>
                        )}


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


                        {!isEvaluationCompatible && (
                            <div
                                className="
                                    mt-4
                                    rounded-xl
                                    border
                                    border-amber-200
                                    bg-amber-50
                                    p-4
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-amber-700
                                    "
                                >
                                    Tab{" "}
                                    <strong>
                                        {
                                            activeTab
                                                ?.label
                                        }
                                    </strong>{" "}
                                    không phù hợp với
                                    dataset hiện tại.
                                    Hãy chọn tab{" "}
                                    <strong>
                                        {
                                            detectedTab
                                                ?.label
                                        }
                                    </strong>{" "}
                                    được đánh dấu
                                    “Phù hợp dữ liệu”.
                                </p>
                            </div>
                        )}


                        {evaluationType ===
                            "admission" && (
                            <div
                                className="
                                    mt-4
                                    rounded-xl
                                    border
                                    border-blue-200
                                    bg-blue-50
                                    p-4
                                "
                            >
                                <p
                                    className="
                                        text-sm
                                        text-blue-700
                                    "
                                >
                                    Module tuyển sinh
                                    đang được chuẩn bị
                                    cho Sprint tiếp theo.
                                </p>
                            </div>
                        )}


                        <button
                            type="button"
                            onClick={
                                handleEvaluate
                            }
                            disabled={
                                loading ||
                                !uploadedFilename ||
                                !isEvaluationCompatible ||
                                evaluationType ===
                                    "admission"
                            }
                            className="
                                mt-5
                                rounded-xl
                                bg-blue-600
                                px-6
                                py-3
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
                                : evaluateButtonLabel}
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


                {activeResult && (
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
                                {evaluationType ===
                                "graduation"
                                    ? (
                                        "Phân tích " +
                                        "tốt nghiệp " +
                                        "thành công"
                                    )
                                    : (
                                        "Phân tích " +
                                        "học bổng " +
                                        "thành công"
                                    )}
                            </p>

                            <h2
                                className="
                                    mt-2
                                    text-2xl
                                    font-bold
                                    text-slate-900
                                "
                            >
                                {
                                    activeResult
                                        .rule_set_name
                                }
                            </h2>

                            <p
                                className="
                                    mt-2
                                    text-sm
                                    text-slate-500
                                "
                            >
                                Dataset:{" "}
                                {
                                    activeResult
                                        .dataset_name
                                }
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
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
                                        activeResult
                                            .summary
                                            .insufficient_data_rate
                                    }
                                    %
                                </p>
                            </div>
                        </div>


                        <div
                            className="
                                mt-10
                                grid
                                grid-cols-1
                                gap-6
                                xl:grid-cols-2
                            "
                        >
                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-slate-200
                                    p-6
                                "
                            >
                                <h3
                                    className="
                                        text-lg
                                        font-bold
                                        text-slate-900
                                    "
                                >
                                    Phân bố kết quả
                                </h3>

                                <p
                                    className="
                                        mt-1
                                        text-sm
                                        text-slate-500
                                    "
                                >
                                    Tỷ lệ sinh viên theo
                                    trạng thái đánh giá.
                                </p>

                                <div
                                    className="
                                        mt-6
                                        h-[360px]
                                    "
                                >
                                    <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                    >
                                        <PieChart>
                                            <Pie
                                                data={
                                                    pieData
                                                }
                                                dataKey="value"
                                                nameKey="name"
                                                outerRadius={
                                                    115
                                                }
                                                label
                                            >
                                                {pieData.map(
                                                    (
                                                        _,
                                                        index,
                                                    ) => (
                                                        <Cell
                                                            key={
                                                                index
                                                            }
                                                            fill={
                                                                CHART_COLORS[
                                                                    index %
                                                                        CHART_COLORS.length
                                                                ]
                                                            }
                                                        />
                                                    ),
                                                )}
                                            </Pie>

                                            <Tooltip />

                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>


                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-slate-200
                                    p-6
                                "
                            >
                                <h3
                                    className="
                                        text-lg
                                        font-bold
                                        text-slate-900
                                    "
                                >
                                    Top điều kiện không đạt
                                </h3>

                                <p
                                    className="
                                        mt-1
                                        text-sm
                                        text-slate-500
                                    "
                                >
                                    Các nguyên nhân phổ
                                    biến khiến sinh viên
                                    chưa đủ điều kiện.
                                </p>

                                {failedConditionData
                                    .length >
                                0 ? (
                                    <div
                                        className="mt-6"
                                        style={{
                                            height:
                                                Math.max(
                                                    360,
                                                    failedConditionData
                                                        .length *
                                                        64,
                                                ),
                                        }}
                                    >
                                        <ResponsiveContainer
                                            width="100%"
                                            height="100%"
                                        >
                                            <BarChart
                                                data={
                                                    failedConditionData
                                                }
                                                layout="vertical"
                                                margin={{
                                                    top: 8,
                                                    right: 30,
                                                    bottom: 8,
                                                    left: 20,
                                                }}
                                                barCategoryGap={
                                                    18
                                                }
                                            >
                                                <CartesianGrid
                                                    strokeDasharray="3 3"
                                                    horizontal={
                                                        false
                                                    }
                                                    stroke="#e2e8f0"
                                                />

                                                <XAxis
                                                    type="number"
                                                    allowDecimals={
                                                        false
                                                    }
                                                    tick={{
                                                        fill: "#64748b",
                                                        fontSize: 12,
                                                    }}
                                                    axisLine={{
                                                        stroke: "#cbd5e1",
                                                    }}
                                                    tickLine={
                                                        false
                                                    }
                                                />

                                                <YAxis
                                                    type="category"
                                                    dataKey="condition"
                                                    width={
                                                        210
                                                    }
                                                    tick={{
                                                        fill: "#475569",
                                                        fontSize: 12,
                                                    }}
                                                    axisLine={
                                                        false
                                                    }
                                                    tickLine={
                                                        false
                                                    }
                                                    interval={
                                                        0
                                                    }
                                                />

                                                <Tooltip
                                                    content={
                                                        <FailedConditionTooltip />
                                                    }
                                                    cursor={{
                                                        fill: "#f8fafc",
                                                    }}
                                                />

                                                <Bar
                                                    dataKey="count"
                                                    name="Số sinh viên"
                                                    fill="#6366f1"
                                                    radius={[
                                                        0,
                                                        10,
                                                        10,
                                                        0,
                                                    ]}
                                                    maxBarSize={
                                                        30
                                                    }
                                                />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    <div
                                        className="
                                            mt-6
                                            flex
                                            h-[360px]
                                            items-center
                                            justify-center
                                            rounded-xl
                                            bg-slate-50
                                        "
                                    >
                                        <p
                                            className="
                                                text-sm
                                                text-slate-500
                                            "
                                        >
                                            Không có điều
                                            kiện không đạt
                                            để hiển thị.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>


                        {activeResult
                            .summary
                            .top_failed_conditions
                            .length >
                            0 && (
                            <div className="mt-8">
                                <h3
                                    className="
                                        text-lg
                                        font-bold
                                        text-slate-900
                                    "
                                >
                                    Các điều kiện không
                                    đạt phổ biến
                                </h3>

                                <div
                                    className="
                                        mt-4
                                        space-y-3
                                    "
                                >
                                    {activeResult
                                        .summary
                                        .top_failed_conditions
                                        .map(
                                            (
                                                item,
                                                index,
                                            ) => (
                                                <div
                                                    key={`${item.condition}-${index}`}
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
                                                                    px-3
                                                                    py-1
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
                            </div>
                        )}


                        <div className="mt-8">
                            <div
                                className="
                                    flex
                                    flex-col
                                    gap-3
                                    sm:flex-row
                                    sm:items-center
                                    sm:justify-between
                                "
                            >
                                <div>
                                    <h3
                                        className="
                                            text-lg
                                            font-bold
                                            text-slate-900
                                        "
                                    >
                                        Kết quả chi tiết
                                        từng sinh viên
                                    </h3>

                                    <p
                                        className="
                                            mt-1
                                            text-sm
                                            text-slate-500
                                        "
                                    >
                                        Hiển thị mã sinh
                                        viên, họ tên,
                                        trạng thái và
                                        khuyến nghị.
                                    </p>
                                </div>

                                <p
                                    className="
                                        text-sm
                                        text-slate-500
                                    "
                                >
                                    Tổng cộng{" "}
                                    {
                                        activeResult
                                            .students
                                            .length
                                    }{" "}
                                    sinh viên
                                </p>
                            </div>


                            <div
                                className="
                                    mt-4
                                    overflow-hidden
                                    rounded-2xl
                                    border
                                    border-slate-200
                                "
                            >
                                <div className="overflow-x-auto">
                                    <table
                                        className="
                                            min-w-full
                                            divide-y
                                            divide-slate-200
                                        "
                                    >
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th
                                                    className="
                                                        px-5
                                                        py-4
                                                        text-left
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-wider
                                                        text-slate-500
                                                    "
                                                >
                                                    MSSV
                                                </th>

                                                <th
                                                    className="
                                                        px-5
                                                        py-4
                                                        text-left
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-wider
                                                        text-slate-500
                                                    "
                                                >
                                                    Họ tên
                                                </th>

                                                <th
                                                    className="
                                                        px-5
                                                        py-4
                                                        text-left
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-wider
                                                        text-slate-500
                                                    "
                                                >
                                                    Trạng thái
                                                </th>

                                                <th
                                                    className="
                                                        px-5
                                                        py-4
                                                        text-left
                                                        text-xs
                                                        font-semibold
                                                        uppercase
                                                        tracking-wider
                                                        text-slate-500
                                                    "
                                                >
                                                    Khuyến nghị
                                                </th>
                                            </tr>
                                        </thead>

                                        <tbody
                                            className="
                                                divide-y
                                                divide-slate-100
                                                bg-white
                                            "
                                        >
                                            {paginatedStudents.map(
                                                (
                                                    student,
                                                ) => {
                                                    const statusLabel =
                                                        student.status ===
                                                        "eligible"
                                                            ? "Đủ điều kiện"
                                                            : student.status ===
                                                              "not_eligible"
                                                            ? "Chưa đủ điều kiện"
                                                            : "Thiếu dữ liệu";

                                                    const statusClassName =
                                                        student.status ===
                                                        "eligible"
                                                            ? "bg-emerald-50 text-emerald-700"
                                                            : student.status ===
                                                              "not_eligible"
                                                            ? "bg-red-50 text-red-700"
                                                            : "bg-amber-50 text-amber-700";

                                                    return (
                                                        <tr
                                                            key={
                                                                student.student_id
                                                            }
                                                        >
                                                            <td
                                                                className="
                                                                    whitespace-nowrap
                                                                    px-5
                                                                    py-4
                                                                    text-sm
                                                                    font-medium
                                                                    text-slate-900
                                                                "
                                                            >
                                                                {
                                                                    student.student_id
                                                                }
                                                            </td>

                                                            <td
                                                                className="
                                                                    px-5
                                                                    py-4
                                                                    text-sm
                                                                    text-slate-700
                                                                "
                                                            >
                                                                {
                                                                    student.student_name
                                                                }
                                                            </td>

                                                            <td
                                                                className="
                                                                    px-5
                                                                    py-4
                                                                "
                                                            >
                                                                <span
                                                                    className={`
                                                                        inline-flex
                                                                        rounded-full
                                                                        px-3
                                                                        py-1
                                                                        text-xs
                                                                        font-semibold
                                                                        ${statusClassName}
                                                                    `}
                                                                >
                                                                    {
                                                                        statusLabel
                                                                    }
                                                                </span>
                                                            </td>

                                                            <td
                                                                className="
                                                                    max-w-md
                                                                    px-5
                                                                    py-4
                                                                    text-sm
                                                                    leading-6
                                                                    text-slate-600
                                                                "
                                                            >
                                                                {student.recommendation ||
                                                                    "Không có khuyến nghị bổ sung."}
                                                            </td>
                                                        </tr>
                                                    );
                                                },
                                            )}
                                        </tbody>
                                    </table>
                                </div>


                                {activeResult
                                    .students
                                    .length >
                                    rowsPerPage && (
                                    <div
                                        className="
                                            flex
                                            items-center
                                            justify-between
                                            border-t
                                            border-slate-200
                                            bg-slate-50
                                            px-5
                                            py-4
                                        "
                                    >
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setCurrentPage(
                                                    (
                                                        page,
                                                    ) =>
                                                        Math.max(
                                                            1,
                                                            page -
                                                                1,
                                                        ),
                                                )
                                            }
                                            disabled={
                                                currentPage ===
                                                1
                                            }
                                            className="
                                                rounded-lg
                                                border
                                                border-slate-300
                                                bg-white
                                                px-4
                                                py-2
                                                text-sm
                                                font-medium
                                                text-slate-700
                                                transition
                                                hover:bg-slate-100
                                                disabled:cursor-not-allowed
                                                disabled:opacity-40
                                            "
                                        >
                                            ← Trước
                                        </button>

                                        <p
                                            className="
                                                text-sm
                                                text-slate-500
                                            "
                                        >
                                            Trang{" "}
                                            {
                                                currentPage
                                            }{" "}
                                            /{" "}
                                            {
                                                totalPages
                                            }
                                        </p>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                setCurrentPage(
                                                    (
                                                        page,
                                                    ) =>
                                                        Math.min(
                                                            totalPages,
                                                            page +
                                                                1,
                                                        ),
                                                )
                                            }
                                            disabled={
                                                currentPage ===
                                                totalPages
                                            }
                                            className="
                                                rounded-lg
                                                border
                                                border-slate-300
                                                bg-white
                                                px-4
                                                py-2
                                                text-sm
                                                font-medium
                                                text-slate-700
                                                transition
                                                hover:bg-slate-100
                                                disabled:cursor-not-allowed
                                                disabled:opacity-40
                                            "
                                        >
                                            Sau →
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>


                        {activeResult
                            .warnings
                            .length >
                            0 && (
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
                                    {activeResult
                                        .warnings
                                        .map(
                                            (
                                                warning,
                                                index,
                                            ) => (
                                                <p
                                                    key={`${warning}-${index}`}
                                                    className="
                                                        text-sm
                                                        text-amber-700
                                                    "
                                                >
                                                    •{" "}
                                                    {
                                                        warning
                                                    }
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