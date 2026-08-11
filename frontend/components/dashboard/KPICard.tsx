"use client"


interface KPICardProps {

    title: string;

    value: string | number;

}



export default function KPICard(
    {
        title,
        value
    }: KPICardProps
) {


    return (

        // <div className=" rounded-xl bg-gradient-to-r from-slate-800 to-slate-950 p-6 shadow-xl " >
        //     <p className="text-sm text-blue-100">
        //         {title}
        //     </p>
        //     <h2 className="mt-4 text-4xl font-bold text-white" >
        //         {value}
        //     </h2>
        // </div>
        <div className="relative rounded-xl bg-gradient-to-br from-indigo-700 to-sky-400 p-6 shadow-xl border-l-4 border-sky-300">
            <p className="text-sm font-medium text-white">
                {title}
            </p>
            <h2 className="mt-3 text-4xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                {value}
            </h2>
        </div>
      

    )

}