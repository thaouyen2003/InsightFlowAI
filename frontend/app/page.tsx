"use client";

import { useEffect, useState } from "react";

type DashboardData = {
  kpi: {
    revenue: number;
    orders: number;
    customers: number;
    avg_order: number;
  };
};

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dashboard")
      .then((res) => res.json())
      .then((json) => setData(json));
  }, []);

  if (!data) return <h1>Loading...</h1>;

  return (
    <div style={{ padding: 40 }}>
      <h1>Insight Flow AI</h1>

      <hr />

      <h2>Revenue : {data.kpi.revenue.toLocaleString()}</h2>

      <h2>Orders : {data.kpi.orders}</h2>

      <h2>Customers : {data.kpi.customers}</h2>

      <h2>Average Order : {data.kpi.avg_order}</h2>
    </div>
  );
}