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

import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    ResponsiveContainer,
    Legend,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
} from "recharts";


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

    const [currentPage, setCurrentPage] =
    useState(1);

    const rowsPerPage = 20;


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
            setCurrentPage(1);
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

    const totalPages = result
    ? Math.ceil(
          result.students.length /
              rowsPerPage,
      )
    : 0;

    const paginatedStudents =
        result
            ? result.students.slice(
                (currentPage - 1) *
                    rowsPerPage,
                currentPage *
                    rowsPerPage,
            )
            : [];

    
    const pieData = result
    ? [
          {
              name: "Đủ điều kiện",
              value:
                  result.summary
                      .eligible_count,
          },
          {
              name: "Chưa đủ",
              value:
                  result.summary
                      .not_eligible_count,
          },
          {
              name: "Thiếu dữ liệu",
              value:
                  result.summary
                      .insufficient_data_count,
          },
      ]
    : [];

    const shortenCondition = (
    value: string,
): string => {
    const maxLength = 34;

    if (value.length <= maxLength) {
        return value;
    }

    return (
        value.slice(0, maxLength).trim() +
        "..."
    );
};

    const failedConditionData = result
        ? result.summary.top_failed_conditions.map(
            (item) => ({
                condition: shortenCondition(
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


    const COLORS = [
        "#2854f3",
        "#e444ef",
        "#0b97f5",
    ];

    function FailedConditionTooltip({
    active,
    payload,
        }: {
            active?: boolean;
            payload?: Array<{
                payload: {
                    fullCondition: string;
                    count: number;
                    rate: number;
                };
            }>;
        }) {
            if (
                !active ||
                !payload ||
                payload.length === 0
            ) {
                return null;
            }

            const item = payload[0].payload;

            return (
                <div className="max-w-sm rounded-xl border border-slate-700 bg-slate-950 p-4 shadow-2xl">
                    <p className="text-sm font-semibold leading-5 text-white">
                        {item.fullCondition}
                    </p>

                    <p className="mt-2 text-sm text-slate-300">
                        {item.count} sinh viên
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                        Tỷ lệ: {item.rate}%
                    </p>
                </div>
            );
        }




    return (
        <main className="min-h-screen bg-slate-50 px-6 py-10">
            <div className="mx-auto max-w-6xl">
                <section className="rounded-3xl bg-white p-8 shadow-sm">
                    <div>
                        <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                            InsightFlowAI
                        </p>

                        <h1 className="mt-2 text-3xl font-bold text-slate-900">
                            Đánh giá điều kiện tốt nghiệp
                        </h1>

                        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
                            Hệ thống sử dụng dataset đã được tải lên,
                            đối chiếu dữ liệu với bộ luật được trích xuất
                            từ kho tri thức PDF và trả về kết quả đánh giá.
                        </p>
                    </div>

                    <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-6">
                        <p className="text-sm font-semibold text-slate-800">
                            Dataset đang được đánh giá
                        </p>

                        <p className="mt-2 break-all text-sm text-blue-700">
                            {uploadedFilename ||
                                "Chưa có file nào được tải lên"}
                        </p>

                        {!uploadedFilename && (
                            <p className="mt-3 text-sm text-amber-600">
                                Vui lòng quay lại trang Upload và tải
                                dataset trước khi đánh giá.
                            </p>
                        )}

                        <button
                            type="button"
                            onClick={handleEvaluate}
                            disabled={
                                loading ||
                                !uploadedFilename
                            }
                            className="mt-5 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                        >
                            {loading
                                ? "Đang đánh giá..."
                                : "Bắt đầu đánh giá"}
                        </button>
                    </div>

                    {error && (
                        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                            <p className="text-sm font-semibold text-red-700">
                                Không thể xử lý yêu cầu
                            </p>

                            <p className="mt-1 text-sm text-red-600">
                                {error}
                            </p>
                        </div>
                    )}
                </section>

                {result && (
                    <section className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
                        <div>
                            <p className="text-sm font-semibold text-emerald-600">
                                Đánh giá thành công
                            </p>

                            <h2 className="mt-2 text-2xl font-bold text-slate-900">
                                {result.rule_set_name}
                            </h2>

                            <p className="mt-2 text-sm text-slate-500">
                                Dataset:{" "}
                                {result.dataset_name}
                            </p>
                        </div>

                        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <div className="rounded-2xl border border-slate-200 p-5">
                                <p className="text-sm text-slate-500">
                                    Tổng sinh viên
                                </p>

                                <p className="mt-2 text-3xl font-bold text-slate-900">
                                    {
                                        result.summary
                                            .total_students
                                    }
                                </p>
                            </div>

                            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                                <p className="text-sm text-emerald-700">
                                    Đủ điều kiện
                                </p>

                                <p className="mt-2 text-3xl font-bold text-emerald-700">
                                    {
                                        result.summary
                                            .eligible_count
                                    }
                                </p>

                                <p className="mt-1 text-sm text-emerald-600">
                                    {
                                        result.summary
                                            .eligible_rate
                                    }
                                    %
                                </p>
                            </div>

                            <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
                                <p className="text-sm text-red-700">
                                    Chưa đủ điều kiện
                                </p>

                                <p className="mt-2 text-3xl font-bold text-red-700">
                                    {
                                        result.summary
                                            .not_eligible_count
                                    }
                                </p>

                                <p className="mt-1 text-sm text-red-600">
                                    {
                                        result.summary
                                            .not_eligible_rate
                                    }
                                    %
                                </p>
                            </div>

                            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                                <p className="text-sm text-amber-700">
                                    Thiếu dữ liệu
                                </p>

                                <p className="mt-2 text-3xl font-bold text-amber-700">
                                    {
                                        result.summary
                                            .insufficient_data_count
                                    }
                                </p>

                                <p className="mt-1 text-sm text-amber-600">
                                    {
                                        result.summary
                                            .insufficient_data_rate
                                    }
                                    %
                                </p>
                            </div>
                        </div>

                            {/* Pie chart */}
                            <div className="mt-10 rounded-2xl border border-slate-200 p-6">

                                <h3 className="text-lg font-bold">
                                    Phân bố kết quả đánh giá
                                </h3>

                                <div className="mt-6 h-[350px]">

                                    <ResponsiveContainer>

                                        <PieChart>

                                            <Pie
                                                data={pieData}
                                                dataKey="value"
                                                nameKey="name"
                                                outerRadius={120}
                                                label
                                            >

                                                {pieData.map(
                                                    (_, index) => (
                                                        <Cell
                                                            key={index}
                                                            fill={
                                                                COLORS[
                                                                    index %
                                                                        COLORS.length
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

                            {/* Bar chart */}
                            <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900">
                                    Top điều kiện không đạt
                                </h3>

                                <p className="mt-1 text-sm text-slate-500">
                                    Các nguyên nhân phổ biến khiến sinh viên
                                    chưa đủ điều kiện.
                                </p>
                            </div>

                            {failedConditionData.length > 0 ? (
                                <div
                                    className="mt-6"
                                    style={{
                                        height: Math.max(
                                            360,
                                            failedConditionData.length *
                                                64,
                                        ),
                                    }}
                                >
                                    <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                    >
                                        <BarChart
                                            data={failedConditionData}
                                            layout="vertical"
                                            margin={{
                                                top: 8,
                                                right: 30,
                                                bottom: 8,
                                                left: 20,
                                            }}
                                            barCategoryGap={18}
                                        >
                                            <CartesianGrid
                                                strokeDasharray="3 3"
                                                horizontal={false}
                                                stroke="#e2e8f0"
                                            />

                                            <XAxis
                                                type="number"
                                                allowDecimals={false}
                                                tick={{
                                                    fill: "#64748b",
                                                    fontSize: 12,
                                                }}
                                                axisLine={{
                                                    stroke: "#cbd5e1",
                                                }}
                                                tickLine={false}
                                            />

                                            <YAxis
                                                type="category"
                                                dataKey="condition"
                                                width={240}
                                                tick={{
                                                    fill: "#475569",
                                                    fontSize: 12,
                                                }}
                                                axisLine={false}
                                                tickLine={false}
                                                interval={0}
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
                                                radius={[0, 10, 10, 0]}
                                                maxBarSize={30}
                                            />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <p className="mt-6 text-sm text-slate-500">
                                    Không có điều kiện không đạt để hiển thị.
                                </p>
                            )}
                            </div>
                        
                            {/*  */}
                            <div className="mt-8">
                                <h3 className="text-lg font-bold text-slate-900">
                                    Các điều kiện không đạt phổ biến
                                </h3>

                                <div className="mt-4 space-y-3">
                                    {result.summary.top_failed_conditions.map(
                                        (
                                            item,
                                            index,
                                        ) => (
                                            <div
                                                key={`${item.condition}-${index}`}
                                                className="rounded-xl border border-slate-200 p-4"
                                            >
                                                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                                    <p className="text-sm font-medium text-slate-800">
                                                        {
                                                            item.condition
                                                        }
                                                    </p>

                                                    <div className="flex items-center gap-3 text-sm">
                                                        <span className="font-semibold text-slate-900">
                                                            {
                                                                item.student_count
                                                            }{" "}
                                                            sinh viên
                                                        </span>

                                                        <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-600">
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


                        <div className="mt-8">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-slate-900">
                                        Kết quả chi tiết từng sinh viên
                                    </h3>

                                    <p className="mt-1 text-sm text-slate-500">
                                        Hiển thị mã sinh viên, họ tên, trạng thái
                                        và khuyến nghị từ hệ thống.
                                    </p>
                                </div>

                                <p className="text-sm text-slate-500">
                                    Tổng cộng {result.students.length} sinh viên
                                </p>
                            </div>

                            <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-slate-200">
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                                                    MSSV
                                                </th>

                                                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                                                    Họ tên
                                                </th>

                                                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                                                    Trạng thái
                                                </th>

                                                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                                                    Khuyến nghị
                                                </th>
                                            </tr>
                                        </thead>

                                        <tbody className="divide-y divide-slate-100 bg-white">
                                            {paginatedStudents.map((student) => {
                                                    const statusLabel =
                                                        student.status === "eligible"
                                                            ? "Đủ điều kiện"
                                                            : student.status ===
                                                                "not_eligible"
                                                            ? "Chưa đủ điều kiện"
                                                            : "Thiếu dữ liệu";

                                                    const statusClassName =
                                                        student.status === "eligible"
                                                            ? "bg-emerald-50 text-emerald-700"
                                                            : student.status ===
                                                                "not_eligible"
                                                            ? "bg-red-50 text-red-700"
                                                            : "bg-amber-50 text-amber-700";

                                                    return (
                                                        <tr key={student.student_id}>
                                                            <td className="whitespace-nowrap px-5 py-4 text-sm font-medium text-slate-900">
                                                                {student.student_id}
                                                            </td>

                                                            <td className="px-5 py-4 text-sm text-slate-700">
                                                                {student.student_name}
                                                            </td>

                                                            <td className="px-5 py-4">
                                                                <span
                                                                    className={`
                                                                        inline-flex
                                                                        rounded-full
                                                                        px-3 py-1
                                                                        text-xs
                                                                        font-semibold
                                                                        ${statusClassName}
                                                                    `}
                                                                >
                                                                    {statusLabel}
                                                                </span>
                                                            </td>

                                                            <td className="max-w-md px-5 py-4 text-sm leading-6 text-slate-600">
                                                                {student.recommendation ||
                                                                    "Không có khuyến nghị bổ sung."}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                        </tbody>
                                    </table>

                                    <div className="mt-6 flex items-center justify-between">
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setCurrentPage((page) =>
                                                    Math.max(1, page - 1),
                                                )
                                            }
                                            disabled={currentPage === 1}
                                            className="rounded-lg border px-4 py-2 disabled:opacity-40"
                                        >
                                            ← Trước
                                        </button>

                                        <p className="text-sm text-slate-500">
                                            Trang {currentPage} / {totalPages}
                                        </p>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                setCurrentPage((page) =>
                                                    Math.min(
                                                        totalPages,
                                                        page + 1,
                                                    ),
                                                )
                                            }
                                            disabled={
                                                currentPage === totalPages
                                            }
                                            className="rounded-lg border px-4 py-2 disabled:opacity-40"
                                        >
                                            Sau →
                                        </button>
                                    </div>
                                </div>
                            </div>

                        
                        </div>
                        



                        {result.warnings.length > 0 && (
                            <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-5">
                                <h3 className="font-bold text-amber-800">
                                    Cảnh báo
                                </h3>

                                <div className="mt-3 space-y-2">
                                    {result.warnings.map(
                                        (
                                            warning,
                                            index,
                                        ) => (
                                            <p
                                                key={`${warning}-${index}`}
                                                className="text-sm text-amber-700"
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
