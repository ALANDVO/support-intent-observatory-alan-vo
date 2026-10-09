import React, { createContext, useContext, useState, useEffect } from "react";
import { UserIdentity, UserRole } from "../types/api";
import { api } from "../api/client";

interface AuthContextType {
  user: UserIdentity | null;
  role: UserRole;
  isLoading: boolean;
  setRole: (role: UserRole) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserIdentity | null>(null);
  const [role, setLocalRole] = useState<UserRole>("operator");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial fetch of profile or demo login
    const initAuth = async () => {
      try {
        const u = await api.demoLogin("operator");
        setUser(u);
        setLocalRole(u.role);
      } catch {
        setUser({
          username: "demo-operator",
          email: "demo-operator@example.local",
          role: "operator",
          is_authenticated: true,
          auth_source: "demo",
        });
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const setRole = async (newRole: UserRole) => {
    setIsLoading(true);
    try {
      const u = await api.demoLogin(newRole);
      setUser(u);
      setLocalRole(newRole);
      api.setDemoRole(newRole);
    } catch {
      setLocalRole(newRole);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    api.setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, role, isLoading, setRole, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
