import React, { useState, useEffect } from "react";
import { ReviewQueueItem, ReviewStats } from "../types/api";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface ReviewQueueProps {
  onQueueUpdated?: () => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ onQueueUpdated }) => {
  const { role } = useAuth();
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [isLoading, setIsLoading] = useState(true);
  const [resolvingItem, setResolvingItem] = useState<ReviewQueueItem | null>(null);
  const [resolvedIntent, setResolvedIntent] = useState("");
  const [notes, setNotes] = useState("");
  const [addToDataset, setAddToDataset] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const candidateIntents = [
    "billing_inquiry",
    "account_access",
    "technical_issue",
    "feature_request",
    "cancellation",
    "refund_request",
  ];

  const fetchQueue = async () => {
    setIsLoading(true);
    try {
      const [queueData, statsData] = await Promise.all([
        api.listReviewQueue(statusFilter),
        api.getReviewStats(),
      ]);
      setItems(queueData);
      setStats(statsData);
    } catch {
      // Handled
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [statusFilter]);

  const handleOpenResolve = (item: ReviewQueueItem) => {
    setResolvingItem(item);
    setResolvedIntent(item.predicted_intent);
    setNotes("");
  };

  const handleConfirmResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingItem || !resolvedIntent) return;
    setIsSubmitting(true);
    try {
      await api.resolveReviewItem(resolvingItem.id, {
        resolved_intent: resolvedIntent,
        reviewer_notes: notes,
        add_to_training_dataset: addToDataset,
      });
      setResolvingItem(null);
      await fetchQueue();
      if (onQueueUpdated) onQueueUpdated();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Resolution failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Review Queue</h3>
          <p className="text-xs text-slate-400 mt-0.5">Tickets with ambiguous classifications or low decision margins.</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setStatusFilter("pending")}
            className={`text-xs px-3 py-1.5 rounded-md font-medium ${statusFilter === "pending" ? "bg-amber-600 text-white" : "bg-slate-900 text-slate-400"}`}
          >
            Pending ({stats?.pending_count ?? 0})
          </button>
          <button
            onClick={() => setStatusFilter("resolved")}
            className={`text-xs px-3 py-1.5 rounded-md font-medium ${statusFilter === "resolved" ? "bg-indigo-600 text-white" : "bg-slate-900 text-slate-400"}`}
          >
            Resolved ({stats?.resolved_count ?? 0})
          </button>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-400 text-xs">Loading queue items...</div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            {statusFilter === "pending" ? "All uncertain tickets reviewed! Queue clear." : "No resolved items."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Ticket</th>
                  <th className="py-3 px-4">Predicted</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4 text-center">Margin</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-700/30">
                    <td className="py-3 px-4 max-w-xs font-medium text-slate-200">
                      <div className="line-clamp-2">{item.ticket_text}</div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="capitalize px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-indigo-300">
                        {item.predicted_intent.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-300">{(item.confidence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-center font-mono text-amber-400">+{(item.margin * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-slate-400 text-[11px] max-w-[200px] truncate">{item.uncertainty_reason}</td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {item.status === "pending" ? (
                        <button
                          disabled={role === "viewer"}
                          onClick={() => handleOpenResolve(item)}
                          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-3 py-1 rounded text-xs"
                        >
                          Resolve
                        </button>
                      ) : (
                        <span className="text-emerald-400 font-medium">&check; {item.resolved_intent?.replace("_", " ")}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {resolvingItem && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-lg w-full p-6 shadow-xl space-y-4">
            <h4 className="text-base font-bold text-slate-100">Resolve Uncertain Ticket</h4>
            <div className="bg-slate-900 p-3 rounded text-xs text-slate-300 border border-slate-700">{resolvingItem.ticket_text}</div>

            <form onSubmit={handleConfirmResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Assign Intent:</label>
                <select
                  value={resolvedIntent}
                  onChange={(e) => setResolvedIntent(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                >
                  {candidateIntents.map((i) => (
                    <option key={i} value={i}>{i.replace("_", " ").toUpperCase()}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Notes:</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Rationale or notes..."
                  className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                />
              </div>

              <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={addToDataset}
                  onChange={(e) => setAddToDataset(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 bg-slate-900"
                />
                <span>Include in training corpus</span>
              </label>

              <div className="flex justify-end space-x-3 pt-2">
                <button type="button" onClick={() => setResolvingItem(null)} className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-1.5 rounded">
                  {isSubmitting ? "Saving..." : "Confirm & Resolve"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
