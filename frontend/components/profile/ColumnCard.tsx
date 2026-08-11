interface Props {
    column: any;
}


export default function ColumnCard({
    column
}: Props) {


    return (

        <div
            className="
            border
            rounded-xl
            p-5
            bg-white
            shadow-sm
            hover:shadow-md
            transition
            "
        >

            {/* Column name */}
            <h3 className="
                text-lg
                font-bold
                mb-4
            ">
                {column.name}
            </h3>



            {/* Basic information */}
            <div className="
                space-y-2
                text-sm
            ">


                <div className="flex justify-between">

                    <span className="text-gray-500">
                        Data Type
                    </span>

                    <span className="font-medium">
                        {column.dtype}
                    </span>

                </div>



                <div className="flex justify-between">

                    <span className="text-gray-500">
                        Semantic
                    </span>

                    <span className="font-medium">
                        {column.semantic_type}
                    </span>

                </div>



                <div className="flex justify-between">

                    <span className="text-gray-500">
                        Missing
                    </span>

                    <span className="font-medium">
                        {column.missing}
                    </span>

                </div>



                <div className="flex justify-between">

                    <span className="text-gray-500">
                        Unique
                    </span>

                    <span className="font-medium">
                        {column.unique}
                    </span>

                </div>


            </div>



            {/* Statistics */}
            {
                column.statistics && (

                    <div className="
                        mt-5
                        pt-4
                        border-t
                    ">


                        <h4 className="
                            font-semibold
                            mb-2
                        ">
                            Statistics
                        </h4>


                        {
                            Object.entries(
                                column.statistics
                            )
                                .map(
                                    ([key, value]) => (

                                        <div
                                            key={key}
                                            className="
                                        flex
                                        justify-between
                                        text-sm
                                        "
                                        >

                                            <span className="text-gray-500">
                                                {key}
                                            </span>


                                            <span>
                                                {
                                                    typeof value === "object"
                                                        ? JSON.stringify(value)
                                                        : String(value)
                                                }
                                            </span>


                                        </div>

                                    )
                                )
                        }


                    </div>

                )
            }


        </div>

    );
}