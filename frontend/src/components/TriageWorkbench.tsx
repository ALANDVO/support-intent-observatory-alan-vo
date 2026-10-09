import React, { useState } from "react";
import { TriageResult } from "../types/api";
import { api } from "../api/client";

interface TriageWorkbenchProps {
  onTriageComplete?: () => void;
}

export const TriageWorkbench: React.FC<TriageWorkbenchProps> = ({ onTriageComplete }) => {
  const [text, setText] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [marginThreshold, setMarginThreshold] = useState(0.2);
  const [includeAdvisory, setIncludeAdvisory] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const presets = [
    { label: "Billing Issue", text: "Our card was charged twice on invoice INV-9021. Please issue a refund." },
    { label: "2FA Lockout", text: "I lost my phone and cannot receive the 2FA SMS code to sign in." },
    { label: "API 500 Error", text: "Requests to /api/v2/ingest fail with 500 Internal Server Error." },
    { label: "Feature Request", text: "Do you support dark mode or exporting analytics charts to PDF?" },
    { label: "Ambiguous", text: "Your platform is broken, give me back my subscription or cancel." },
  ];

  const handleTriage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.triageTicket({
        text,
        confidence_threshold: confidenceThreshold,
        margin_threshold: marginThreshold,
        include_advisory: includeAdvisory,
      });
      setResult(res);
      if (onTriageComplete) onTriageComplete();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Triage operation failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-6 space-y-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-base font-semibold text-slate-100 mb-2">Ticket Triage Simulator</h3>
          <p className="text-xs text-slate-400 mb-4">Evaluate customer support text using the active TF-IDF classifier.</p>

          <div className="mb-4">
            <span className="text-xs font-medium text-slate-400 mb-2 block">Quick Presets:</span>
            <div className="flex flex-wrap gap-1.5">
              {presets.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => setText(p.text)}
                  className="text-xs bg-slate-900 hover:bg-slate-700 text-slate-300 border border-slate-700 px-2.5 py-1 rounded"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleTriage} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Ticket Message</label>
              <textarea
                rows={4}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste customer support inquiry or message..."
                className="w-full bg-slate-900 border border-slate-700 rounded-md p-3 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Confidence Threshold</span>
                  <span className="font-mono text-indigo-400">{(confidenceThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.4"
                  max="0.95"
                  step="0.05"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Margin Threshold</span>
                  <span className="font-mono text-indigo-400">{(marginThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.5"
                  step="0.05"
                  value={marginThreshold}
                  onChange={(e) => setMarginThreshold(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAdvisory}
                  onChange={(e) => setIncludeAdvisory(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 bg-slate-900"
                />
                <span>Include advisory analysis</span>
              </label>

              <button
                type="submit"
                disabled={isLoading || !text.trim()}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-md"
              >
                {isLoading ? "Triaging..." : "Triage Ticket"}
              </button>
            </div>
          </form>

          {error && <div className="mt-4 p-3 bg-rose-950/60 border border-rose-800 text-rose-300 text-xs rounded">{error}</div>}
        </div>
      </div>

      <div className="lg:col-span-6 space-y-4">
        {result ? (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-700">
              <div>
                <span className="text-xs text-slate-400">Predicted Intent:</span>
                <div className="text-base font-bold text-slate-100 capitalize">{result.predicted_intent.replace("_", " ")}</div>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400">Confidence:</span>
                <div className="text-base font-mono font-bold text-indigo-400">{(result.confidence * 100).toFixed(1)}%</div>
              </div>
            </div>

            {result.is_uncertain ? (
              <div className="bg-amber-950/60 border border-amber-800/80 rounded p-3 text-xs text-amber-200">
                <div className="font-semibold flex items-center">
                  <span className="w-2 h-2 rounded-full bg-amber-400 mr-2"></span>
                  Flagged for Human Review Queue
                </div>
                <div className="mt-1 text-slate-300 text-[11px]">
                  Reason: {result.uncertainty_reason} (Margin: {(result.margin * 100).toFixed(1)}%)
                </div>
              </div>
            ) : (
              <div className="bg-emerald-950/60 border border-emerald-800/80 rounded p-3 text-xs text-emerald-200">
                <div className="font-semibold flex items-center">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2"></span>
                  Confident Prediction &mdash; Auto-Routed
                </div>
                <div className="mt-1 text-slate-300 text-[11px]">
                  Decision margin: +{(result.margin * 100).toFixed(1)}% over secondary candidate.
                </div>
              </div>
            )}

            {result.token_highlights && result.token_highlights.length > 0 && (
              <div>
                <span className="text-xs font-medium text-slate-400 mb-1.5 block">Influential Tokens:</span>
                <div className="flex flex-wrap gap-1.5">
                  {result.token_highlights.map((th) => (
                    <span key={th.token} className="text-[11px] bg-slate-900 border border-slate-700 px-2 py-0.5 rounded text-slate-300">
                      <span className="font-mono text-indigo-300">{th.token}</span>
                      <span className="text-emerald-400 font-mono text-[10px] ml-1">(+{th.contribution.toFixed(2)})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <span className="text-xs font-medium text-slate-400 mb-2 block">Top Candidates:</span>
              <div className="space-y-1.5">
                {result.candidates.slice(0, 4).map((c) => (
                  <div key={c.intent} className="text-xs">
                    <div className="flex justify-between text-slate-300 mb-0.5">
                      <span className="capitalize">{c.intent.replace("_", " ")}</span>
                      <span className="font-mono text-slate-400">{(c.probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${c.intent === result.predicted_intent ? "bg-indigo-500" : "bg-slate-600"}`}
                        style={{ width: `${Math.min(100, c.probability * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {result.advisory && (
              <div className="mt-4 pt-3 border-t border-slate-700 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">Grounded Advisory</span>
                  <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono">{result.advisory.provider}</span>
                </div>
                <p className="text-xs text-slate-300 bg-slate-900/80 p-2.5 rounded border border-slate-700/60">{result.advisory.suggested_action}</p>
                <div>
                  <span className="text-[11px] text-slate-400 font-medium">Draft Response:</span>
                  <pre className="text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded border border-slate-700/40 whitespace-pre-wrap font-sans mt-1">
                    {result.advisory.draft_response}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center text-slate-400">
            Submit a support inquiry or click a quick preset to run classification.
          </div>
        )}
      </div>
    </div>
  );
};
