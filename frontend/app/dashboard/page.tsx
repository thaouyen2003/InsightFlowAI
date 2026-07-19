"use client";

import { useEffect, useState } from "react";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import KPICard from "@/components/dashboard/KPICard";
import ChartRenderer from "@/components/charts/ChartRenderer";


export default function DashboardPage() {

    const [dashboard, setDashboard] = useState<any>(null);
    // const [uploadedFile, setUploadedFile] = useState("");
    const [datasetName, setDatasetName] = useState("");

    useEffect(() => {
    // const file = localStorage.getItem("uploadedFile");

    // if (!file) {
    //     console.log("Không tìm thấy uploadedFile trong localStorage");
    //     return;
    // }


    const file = localStorage.getItem("uploadedFile");

    if (!file) {
        return;
    }

    setDatasetName(file);


    console.log("Uploaded file:", file);

    fetch("http://127.0.0.1:8000/dashboard", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            filename: file,
        }),
    })
        .then((res) => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
        })
        .then((data) => {
            console.log("DASHBOARD API:", data);
            setDashboard(data);
        })
        .catch((err) => {
            console.error("Dashboard fetch error:", err);
        });
}, []);






    // useEffect(() => {

    //     const file = localStorage.getItem("uploadedFile");

    //     if (!file) {
    //         console.log("Không tìm thấy uploadedFile trong localStorage");
    //         return;
    //     }

    //     setUploadedFile(file);
    //     console.log("Uploaded file:", uploadedFile);

    //     fetch("http://127.0.0.1:8000/dashboard", {
    //         method: "POST",
    //         headers: {
    //             "Content-Type": "application/json",
    //         },
    //         body: JSON.stringify({
    //             filename: uploadedFile,
    //         }),
    //     })
    //         .then((res) => res.json())
    //         .then(data=>{
    //             console.log("DASHBOARD API:", data)
    //             setDashboard(data)
    //         })
    //         .catch((err) => {
    //             console.error(err);
    //         });

    // }, [uploadedFile]);

    return (

        <div className="flex min-h-screen bg-slate-950">

            <Sidebar />

            <main className="flex-1 p-10">

            


                <Header />

                <p className="mt-6 text-sm text-gray-500">
                    Dataset:
                    <span className="ml-2 text-blue-400">
                        {datasetName || "No dataset"}
                    </span>
                </p>

                <div className="grid grid-cols-3 gap-6 mt-8">
                    {dashboard?.kpis?.map((kpi: any, index: number) => (
                        <KPICard
                            key={index}
                            title={kpi.title}
                            value={kpi.value}
                        />
                    ))}
                </div>

                <div className="mt-10 grid grid-cols-2 gap-6">
                    {dashboard?.charts?.map((chart: any, index: number) => (
                        <div
                            key={index}
                            className={
                                chart.type === "line"
                                    ? "col-span-2 rounded-xl bg-white p-5 shadow-lg"
                                    : "rounded-xl bg-white p-5 shadow-lg"
                            }
                        >
                            <ChartRenderer chart={chart} />
                        </div>
                    ))}
                </div>

            </main>

        </div>

    );


    // return (
       
    //     <div className="min-h-screen bg-slate-900 p-10">
            

    //         <h1 className="text-4xl font-bold text-white">
    //             InsightFlowAI Dashboard
    //         </h1>

    //         <p className="mt-2 text-gray-400">
    //             AI-powered Data Visualization & Decision Support
    //         </p>

    //         <p className="mt-6 text-sm text-gray-500">
    //             Dataset:
    //             <span className="ml-2 text-blue-400">
    //                 {uploadedFile || "No dataset"}
    //             </span>
    //         </p>

    //         <div className="grid grid-cols-3 gap-6 mt-8">
    //             {dashboard?.kpis?.map((kpi: any, index: number) => (
    //                 <KPICard
    //                     key={index}
    //                     title={kpi.title}
    //                     value={kpi.value}
    //                 />
    //             ))}
    //         </div>

    //         <div className="mt-10 grid grid-cols-2 gap-6">
    //             {dashboard?.charts?.map((chart: any, index: number) => (
    //                 <div
    //                     key={index}
    //                     className={
    //                         chart.type === "line"
    //                             ? "col-span-2 rounded-xl bg-white p-5 shadow-lg"
    //                             : "rounded-xl bg-white p-5 shadow-lg"
    //                     }
    //                 >
    //                     <ChartRenderer chart={chart} />
    //                 </div>
    //             ))}
    //         </div>

    //     </div>
    // );
}