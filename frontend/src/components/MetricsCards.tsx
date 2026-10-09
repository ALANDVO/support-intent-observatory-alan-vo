import React from "react";
import { SystemStats } from "../types/api";

interface MetricsCardsProps {
  stats: SystemStats | null;
  onNavigateToReview: () => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  stats,
  onNavigateToReview,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 shadow-sm">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
          Active Intent Model
        </div>
        <div className="text-lg font-bold text-slate-100 truncate">
          {stats?.active_model_name || "Baseline TF-IDF Model"}
        </div>
        <div className="mt-2 flex items-center text-xs text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5"></span>
          Ready for live inference
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 shadow-sm">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
          Test Accuracy / F1
        </div>
        <div className="text-2xl font-bold text-indigo-400">
          {stats?.active_model_accuracy !== null && stats?.active_model_accuracy !== undefined
            ? `${(stats.active_model_accuracy * 100).toFixed(1)}%`
            : "—"}
        </div>
        <div className="mt-1 text-xs text-slate-400">
          Macro F1:{" "}
          <span className="font-semibold text-slate-200">
            {stats?.active_model_macro_f1 !== null && stats?.active_model_macro_f1 !== undefined
              ? (stats.active_model_macro_f1 * 100).toFixed(1) + "%"
              : "—"}
          </span>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 shadow-sm">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
          Support Corpus Tickets
        </div>
        <div className="text-2xl font-bold text-slate-100">
          {stats?.ticket_count ?? 0}
        </div>
        <div className="mt-1 text-xs text-slate-400">
          Across <span className="font-semibold text-slate-200">{stats?.dataset_count ?? 1}</span> benchmark dataset
        </div>
      </div>

      <div
        onClick={onNavigateToReview}
        className="bg-slate-800 border border-slate-700 hover:border-amber-500/50 rounded-lg p-5 shadow-sm cursor-pointer transition-colors"
      >
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
          Uncertain Review Queue
        </div>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold text-amber-400">
            {stats?.pending_review_count ?? 0}
          </div>
          <span className="text-xs text-indigo-400 hover:underline">
            Inspect queue &rarr;
          </span>
        </div>
        <div className="mt-1 text-xs text-slate-400">
          <span className="text-emerald-400 font-semibold">{stats?.resolved_review_count ?? 0}</span> resolved by human operators
        </div>
      </div>
    </div>
  );
};
