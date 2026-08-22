import axios from "axios";
import { CostSummary, ResourceSummary, BudgetAlert } from "../types";

// Vite uses VITE_ prefix, fallback to localhost
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

export const getCostSummary = (): Promise<CostSummary> =>
  api.get("/api/costs/summary").then((r) => r.data);

export const getBudgetAlerts = (): Promise<BudgetAlert[]> =>
  api.get("/api/costs/budgets").then((r) => r.data);

export const getRecommendations = (): Promise<ResourceSummary> =>
  api.get("/api/resources/recommendations").then((r) => r.data);

export const downloadReport = (type: "csv" | "excel" | "pdf") => {
  window.open(`${BASE_URL}/api/reports/${type}`, "_blank");
};
