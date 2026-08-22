import React, { useState } from "react";
import { downloadReport } from "../lib/api";
import { Topbar } from "../components/ui/Topbar";
import { FileText, FileSpreadsheet, File, Download } from "lucide-react";

const REPORTS = [
  { type: "pdf"   as const, icon: FileText,        cls: "report-pdf",   title: "PDF Report",   desc: "Full cost summary + recommendations. Best for sharing with managers." },
  { type: "excel" as const, icon: FileSpreadsheet,  cls: "report-excel", title: "Excel Report", desc: "4 sheets: Cost Summary, Top Services, Daily Trend, Recommendations." },
  { type: "csv"   as const, icon: File,             cls: "report-csv",   title: "CSV Export",   desc: "Raw recommendations data. Best for importing into Jira, Notion, etc." },
];

export const Reports: React.FC = () => {
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = (type: "pdf" | "excel" | "csv") => {
    setDownloading(type);
    downloadReport(type);
    setTimeout(() => setDownloading(null), 2000);
  };

  return (
    <div>
      <Topbar title="Reports" subtitle="Download cost and waste reports in multiple formats" />
      <div className="report-grid">
        {REPORTS.map(({ type, icon: Icon, cls, title, desc }) => (
          <div key={type} className={`report-card ${cls}`}>
            <div className="report-icon-wrap"><Icon size={24} /></div>
            <div>
              <p className="report-title">{title}</p>
              <p className="report-desc">{desc}</p>
            </div>
            <button onClick={() => handleDownload(type)} disabled={downloading === type} className="download-btn">
              <Download size={15} />
              {downloading === type ? "Downloading..." : `Download ${type.toUpperCase()}`}
            </button>
          </div>
        ))}
      </div>
      <div className="report-includes">
        <h3>What's included in each report</h3>
        <p>✅ <span>Cost Summary</span> — MTD spend, last month, forecast</p>
        <p>✅ <span>Top Services</span> — Top 10 services by cost</p>
        <p>✅ <span>Daily Trend</span> — Last 30 days daily cost</p>
        <p>✅ <span>Waste Recommendations</span> — All detected idle/unused resources with savings estimate</p>
      </div>
    </div>
  );
};
