import React from "react";
import { useAuth } from "../context/AuthContext";
import { UserRole } from "../types/api";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  pendingCount,
}) => {
  const { user, role, setRole } = useAuth();

  const tabs = [
    { id: "overview", label: "Overview & Metrics" },
    { id: "evaluation", label: "Model Evaluation" },
    { id: "triage", label: "Triage Workbench" },
    {
      id: "review",
      label: "Review Queue",
      badge: pendingCount > 0 ? pendingCount : undefined,
    },
    { id: "datasets", label: "Datasets & Training" },
  ];

  return (
    <header className="border-b border-slate-700 bg-slate-900 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md">
              SI
            </div>
            <div>
              <div className="text-lg font-bold text-slate-100 leading-tight">
                Support Intent Observatory
              </div>
              <div className="text-xs text-slate-400">
                Alan Vo | NLP Intent Classification & Triage
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-md border border-slate-700">
              <span className="text-xs text-slate-300 font-medium">{user?.username || "Guest"}</span>
              <span className="text-xs text-slate-500 font-medium">({role})</span>
              {(["viewer", "operator", "admin"] as UserRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`text-xs px-2.5 py-0.5 rounded font-medium transition-colors ${
                    role === r
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="hidden sm:flex items-center space-x-2 text-xs bg-emerald-950/60 text-emerald-400 border border-emerald-800 px-2.5 py-1 rounded">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Demo Mode</span>
            </div>
          </div>
        </div>

        <nav className="flex space-x-1 -mb-px overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
              }`}
            >
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};
