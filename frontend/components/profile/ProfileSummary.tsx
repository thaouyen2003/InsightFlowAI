interface ProfileSummaryProps {
    summary: {
        rows: number;
        columns: number;
        numeric_columns: number;
        categorical_columns: number;
        datetime_columns: number;
        boolean_columns: number;
        duplicates: number;
        missing_cells: number;
    };
}

export default function ProfileSummary({
    summary,
}: ProfileSummaryProps) {
    const cards = [
        {
            title: "Rows",
            value: summary.rows,
        },
        {
            title: "Columns",
            value: summary.columns,
        },
        {
            title: "Numeric",
            value: summary.numeric_columns,
        },
        {
            title: "Categorical",
            value: summary.categorical_columns,
        },
        {
            title: "Datetime",
            value: summary.datetime_columns,
        },
        {
            title: "Boolean",
            value: summary.boolean_columns,
        },
        {
            title: "Duplicates",
            value: summary.duplicates,
        },
        {
            title: "Missing Cells",
            value: summary.missing_cells,
        },
    ];

    return (
        <section className="mt-16">
            <h2 className="mb-6 text-2xl font-bold text-white">
                Dataset Profile
            </h2>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {cards.map((card) => (
                    <div
                        key={card.title}
                        className="rounded-xl border border-gray-700 bg-gray-900 p-5 shadow"
                    >
                        <p className="text-sm text-gray-400">
                            {card.title}
                        </p>

                        <p className="mt-2 text-3xl font-bold text-cyan-400">
                            {card.value}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
}