/**
 * useAccountApi — makes authenticated, account-aware API calls
 * Automatically appends ?account_id=<selectedAccount.id> to every request
 *
 * Usage:
 *   const { get, loading } = useAccountApi();
 *   const data = await get("/resources/ec2");
 */

import { useCallback, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useAccount } from "../context/AccountContext";

export function useAccountApi() {
  const { authFetch }       = useAuth();
  const { selectedAccount } = useAccount();
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const get = useCallback(async (path, options = {}) => {
    if (!selectedAccount) {
      throw new Error("No AWS account selected");
    }

    setLoading(true);
    setError(null);

    const separator = path.includes("?") ? "&" : "?";
    const url       = `${path}${separator}account_id=${selectedAccount.id}`;

    try {
      const res  = await authFetch(url, { method: "GET", ...options });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "API error");
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authFetch, selectedAccount]);

  const post = useCallback(async (path, body, options = {}) => {
    if (!selectedAccount) throw new Error("No AWS account selected");
    setLoading(true);
    setError(null);
    const separator = path.includes("?") ? "&" : "?";
    const url = `${path}${separator}account_id=${selectedAccount.id}`;
    try {
      const res  = await authFetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        ...options,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "API error");
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authFetch, selectedAccount]);

  return { get, post, loading, error };
}
