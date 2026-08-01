interface Props {
    summary: {
        rows: number;
        columns: number;
        numeric_columns: number;
        categorical_columns: number;
        datetime_columns: number;
        missing_cells: number;
    };
}

export default function SummaryCards({ summary }: Props) {

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
            title: "Category",
            value: summary.categorical_columns,
        },
        {
            title: "Datetime",
            value: summary.datetime_columns,
        },
        {
            title: "Missing",
            value: summary.missing_cells,
        },
    ];

    return (

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">

            {cards.map((card) => (

                <div
                    key={card.title}
                    className=" rounded-xl border border-zinc-800 bg-zinc-900/60 p-5
                        transition-all duration-300 hover:border-indigo-500 hover:-translate-y-1
                        hover:shadow-lg
                        "
                >

                    <p className="text-sm text-zinc-400">
                        {card.title}
                    </p>

                    <h2 className="mt-2 text-3xl font-bold text-white">
                        {card.value.toLocaleString()}
                        
                    </h2>

                </div>

            ))}

        </div>

    );

}