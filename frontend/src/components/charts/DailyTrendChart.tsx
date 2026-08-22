import React from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { DailyCost } from "../../types";

export const DailyTrendChart: React.FC<{ data: DailyCost[] }> = ({ data }) => {
  const formatted = data.map(d => ({ date: d.date.slice(5), amount: d.amount }));
  return (
    <div className="chart-card">
      <p className="chart-title">Daily Cost Trend (Last 30 Days)</p>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={formatted}>
          <defs>
            <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2B6CB0" stopOpacity={0.25}/>
              <stop offset="95%" stopColor="#2B6CB0" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8"/>
          <XAxis dataKey="date" tick={{fontSize:11}} tickLine={false} axisLine={false}/>
          <YAxis tick={{fontSize:11}} tickLine={false} axisLine={false} tickFormatter={v=>`$${v}`}/>
          <Tooltip formatter={(v:number)=>[`$${v.toFixed(2)}`,"Cost"]}/>
          <Area type="monotone" dataKey="amount" stroke="#2B6CB0" strokeWidth={2} fill="url(#cg)"/>
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
