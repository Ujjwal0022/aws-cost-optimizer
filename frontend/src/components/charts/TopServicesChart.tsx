import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { CostByService } from "../../types";

const COLORS = ["#2B6CB0","#3182CE","#4299E1","#63B3ED","#90CDF4","#BEE3F8","#93C5FD"];

export const TopServicesChart: React.FC<{ data: CostByService[] }> = ({ data }) => {
  const formatted = data.slice(0,7).map(d => ({
    name: d.service.replace("Amazon ","").replace("AWS ","").slice(0,18),
    amount: d.amount
  }));
  return (
    <div className="chart-card">
      <p className="chart-title">Top Services by Cost (MTD)</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={formatted} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" horizontal={false}/>
          <XAxis type="number" tick={{fontSize:11}} tickLine={false} axisLine={false} tickFormatter={v=>`$${v}`}/>
          <YAxis type="category" dataKey="name" tick={{fontSize:11}} width={100} tickLine={false} axisLine={false}/>
          <Tooltip formatter={(v:number)=>[`$${v.toFixed(4)}`,"Cost"]}/>
          <Bar dataKey="amount" radius={[0,4,4,0]}>
            {formatted.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
