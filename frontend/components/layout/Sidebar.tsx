export default function Sidebar() {

    return (

        <aside className="w-64 bg-slate-950 border-r border-slate-800 p-6">

            <h2 className="text-2xl font-bold text-white">
                InsightFlowAI
            </h2>

            <div className="mt-10 space-y-3">

                <button className="w-full text-left text-slate-300 hover:text-white">
                    Dashboard
                </button>

                <button className="w-full text-left text-slate-300 hover:text-white">
                    Upload
                </button>

                <button className="w-full text-left text-slate-300 hover:text-white">
                    Profile
                </button>

            </div>

        </aside>

    )

}