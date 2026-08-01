import ColumnCard from "./ColumnCard";


interface Props {
    columns: any[];
}


export default function ColumnList({
    columns,
}: Props) {

    console.log("COLUMN LIST:", columns);

    return (

        <div className=" grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6
        ">

            {
                columns.map((column)=>(
                    
                    <ColumnCard
                        key={column.name}
                        column={column}
                    />

                ))
            }

        </div>

    );
}

