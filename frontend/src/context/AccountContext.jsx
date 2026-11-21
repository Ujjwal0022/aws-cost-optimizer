import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useAuth } from "./AuthContext";

export const AccountContext = createContext(null);

export function AccountProvider({ children }) {
  const { isAuthenticated, authFetch, getToken } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch("/accounts/");
      const data = await res.json();
      const list = data.accounts || [];
      setAccounts(list);
      const stored = localStorage.getItem("finops_selected_account");
      const found = stored ? list.find((a) => a.id === stored) : null;
      if (found) {
        setSelectedAccount(found);
      } else if (list.length > 0) {
        setSelectedAccount(list[0]);
        localStorage.setItem("finops_selected_account", list[0].id);
      } else {
        setSelectedAccount(null);
      }
    } catch (e) {
      console.error("Failed to fetch accounts:", e);
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    if (isAuthenticated) fetchAccounts();
    else { setAccounts([]); setSelectedAccount(null); }
  }, [isAuthenticated, fetchAccounts]);

  const selectAccount = useCallback((account) => {
    setSelectedAccount(account);
    localStorage.setItem("finops_selected_account", account.id);
  }, []);

  const getAuthHeader = useCallback(async () => {
    const token = await getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [getToken]);

  const connectAccount = useCallback(async (payload) => {
    const res = await authFetch("/accounts/", { method: "POST", body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to connect account");
    await fetchAccounts();
    return data;
  }, [authFetch, fetchAccounts]);

  const disconnectAccount = useCallback(async (accountId) => {
    const res = await authFetch(`/accounts/${accountId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to disconnect account");
    if (selectedAccount?.id === accountId) {
      setSelectedAccount(null);
      localStorage.removeItem("finops_selected_account");
    }
    await fetchAccounts();
  }, [authFetch, fetchAccounts, selectedAccount]);

  const testConnection = useCallback(async (accountId) => {
    const res = await authFetch(`/accounts/${accountId}/test`, { method: "POST" });
    const data = await res.json();
    await fetchAccounts();
    return data;
  }, [authFetch, fetchAccounts]);

  const generateExternalId = useCallback(async () => {
    const res = await authFetch("/accounts/generate-external-id");
    return await res.json();
  }, [authFetch]);

  return (
    <AccountContext.Provider value={{
      accounts,
      selectedAccount,
      activeAccount: selectedAccount,
      loading,
      fetchAccounts,
      selectAccount,
      getAuthHeader,
      connectAccount,
      disconnectAccount,
      testConnection,
      generateExternalId,
      hasAccounts: accounts.length > 0,
    }}>
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount() {
  const ctx = useContext(AccountContext);
  if (!ctx) throw new Error("useAccount must be used within AccountProvider");
  return ctx;
}