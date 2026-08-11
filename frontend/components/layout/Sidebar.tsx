"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
    {
        label: "Upload dữ liệu",
        href: "/upload",
        icon: "↑",
    },
    {
        label: "Dashboard",
        href: "/dashboard",
        icon: "▦",
    },
    {
        label: "Kho tri thức",
        href: "/knowledge",
        icon: "✦",
    },

];

export default function AppSidebar() {
    const pathname = usePathname();

    return (
        <aside className="fixed left-0 top-0 flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-950 px-4 py-6 text-white">
            <div className="px-3">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">
                    InsightFlowAI
                </p>

                <h1 className="mt-2 text-xl font-bold">
                    Knowledge Analytics
                </h1>
            </div>

            <nav className="mt-10 space-y-2">
                {navItems.map((item) => {
                    const isActive =
                        pathname === item.href ||
                        pathname.startsWith(
                            `${item.href}/`,
                        );

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={[
                                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition",
                                isActive
                                    ? "bg-cyan-500 text-slate-950"
                                    : "text-slate-300 hover:bg-slate-900 hover:text-white",
                            ].join(" ")}
                        >
                            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/10 text-base">
                                {item.icon}
                            </span>

                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto rounded-xl border border-slate-800 bg-slate-900 p-4">
                <p className="text-sm font-semibold">
                    InsightFlowAI
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                    Dữ liệu → Dashboard → Tri thức → Khuyến nghị
                </p>
            </div>
        </aside>
    );
}