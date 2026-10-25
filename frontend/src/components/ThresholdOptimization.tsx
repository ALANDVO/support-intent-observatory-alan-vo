import React, { useState, useEffect } from "react";
import { api } from "../api/client";

interface ThresholdCurvePoint {
  confidence_threshold: number;
  margin_threshold: number;
  auto_routed_rate: number;
  auto_routed_accuracy: number;
  review_queue_rate: number;
  score: number;
}

interface ThresholdOptimizationResponse {
  optimal_confidence_threshold: number;
  optimal_margin_threshold: number;
  expected_auto_routed_rate: number;
  expected_auto_routed_accuracy: number;
  expected_review_queue_rate: number;
  threshold_curve: ThresholdCurvePoint[];
}

interface ThresholdOptimizationRequest {
  min_confidence?: number;
  max_confidence?: number;
  min_margin?: number;
  max_margin?: number;
  step?: number;
  target_auto_routed_rate?: number | null;
}

const ThresholdOptimization: React.FC = () => {
  const [modelId, setModelId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ThresholdOptimizationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<ThresholdOptimizationRequest>({
    min_confidence: 0.5,
    max_confidence: 0.95,
    min_margin: 0.05,
    max_margin: 0.5,
    step: 0.025,
    target_auto_routed_rate: null,
  });

  useEffect(() => {
    const loadActiveModel = async () => {
      try {
        const models = await api.listModels();
        const active = models.find((m) => m.is_active) || models[0];
        if (active) {
          setModelId(active.id);
        }
      } catch {
        // Ignore
      }
    };
    loadActiveModel();
  }, []);

  const handleOptimize = async () => {
    if (!modelId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await api.optimizeThresholds(modelId, params);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to optimize thresholds");
    } finally {
      setIsLoading(false);
    }
  };

  const MetricCard: React.FC<{ label: string; value: string; color: "indigo" | "emerald" | "amber" | "blue" }> = ({ label, value, color }) => {
    const colorClasses = {
      indigo: "text-indigo-400 border-indigo-500/30 bg-indigo-950/30",
      emerald: "text-emerald-400 border-emerald-500/30 bg-emerald-950/30",
      amber: "text-amber-400 border-amber-500/30 bg-amber-950/30",
      blue: "text-blue-400 border-blue-500/30 bg-blue-950/30",
    };

    return (
      <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
        <div className="text-xs text-slate-400 mb-1">{label}</div>
        <div className="text-2xl font-bold">{value}</div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
        <h2 className="text-base font-bold text-slate-100 mb-3">Threshold Optimization</h2>
        <p className="text-xs text-slate-400 mb-4">
          Find optimal confidence and margin thresholds for triage routing. 
          The grid search evaluates threshold combinations on the model's test sample predictions 
          to balance auto-routing rate against routing accuracy.
        </p>

        {!modelId ? (
          <div className="text-center py-8 text-slate-400">
            No trained model found. Train a model first in the Datasets & Training tab.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 mb-4">
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Min Confidence</label>
                <input
                  type="number"
                  min="0.1"
                  max="0.99"
                  step="0.05"
                  value={params.min_confidence}
                  onChange={(e) => setParams({ ...params, min_confidence: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Max Confidence</label>
                <input
                  type="number"
                  min="0.1"
                  max="0.99"
                  step="0.05"
                  value={params.max_confidence}
                  onChange={(e) => setParams({ ...params, max_confidence: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Min Margin</label>
                <input
                  type="number"
                  min="0.0"
                  max="0.5"
                  step="0.05"
                  value={params.min_margin}
                  onChange={(e) => setParams({ ...params, min_margin: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Max Margin</label>
                <input
                  type="number"
                  min="0.0"
                  max="0.5"
                  step="0.05"
                  value={params.max_margin}
                  onChange={(e) => setParams({ ...params, max_margin: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Step Size</label>
                <input
                  type="number"
                  min="0.01"
                  max="0.1"
                  step="0.005"
                  value={params.step}
                  onChange={(e) => setParams({ ...params, step: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                <label className="text-xs text-slate-400 block mb-1">Target Auto-Route Rate</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={params.target_auto_routed_rate ?? ""}
                  onChange={(e) => setParams({ ...params, target_auto_routed_rate: e.target.value ? parseFloat(e.target.value) : null })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-100 focus:ring-1 focus:ring-indigo-500"
                  placeholder="Optional"
                />
              </div>
            </div>

            <button
              onClick={handleOptimize}
              disabled={isLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Optimizing..." : "Optimize Thresholds"}
            </button>

            {error && (
              <div className="mt-3 p-3 bg-red-950/50 border border-red-500/30 rounded text-red-400 text-sm">
                {error}
              </div>
            )}

            {result && (
              <div className="mt-6 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <MetricCard
                    label="Optimal Confidence Threshold"
                    value={result.optimal_confidence_threshold.toFixed(3)}
                    color="indigo"
                  />
                  <MetricCard
                    label="Optimal Margin Threshold"
                    value={result.optimal_margin_threshold.toFixed(3)}
                    color="indigo"
                  />
                  <MetricCard
                    label="Expected Auto-Route Rate"
                    value={`{(result.expected_auto_routed_rate * 100).toFixed(1)}%`}
                    color="emerald"
                  />
                  <MetricCard
                    label="Expected Auto-Route Accuracy"
                    value={`{(result.expected_auto_routed_accuracy * 100).toFixed(1)}%`}
                    color="emerald"
                  />
                  <MetricCard
                    label="Expected Review Queue Rate"
                    value={`{(result.expected_review_queue_rate * 100).toFixed(1)}%`}
                    color="amber"
                  />
                  <MetricCard
                    label="Threshold Combinations Evaluated"
                    value={result.threshold_curve.length.toString()}
                    color="blue"
                  />
                </div>

                <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg overflow-hidden">
                  <div className="p-3 border-b border-slate-700/50 font-medium text-slate-200">
                    Threshold Search Curve (Top 20 by Score)
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-slate-800/50 text-slate-400">
                          <th className="py-2 px-2 text-left">Confidence</th>
                          <th className="py-2 px-2 text-left">Margin</th>
                          <th className="py-2 px-2 text-left">Auto-Route Rate</th>
                          <th className="py-2 px-2 text-left">Auto-Route Accuracy</th>
                          <th className="py-2 px-2 text-left">Review Queue Rate</th>
                          <th className="py-2 px-2 text-left">Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.threshold_curve
                          .sort((a, b) => b.score - a.score)
                          .slice(0, 20)
                          .map((point, idx) => (
                            <tr
                              key={idx}
                              className={`border-t border-slate-700/30 ${idx === 0 ? "bg-indigo-950/30" : ""}`}
                            >
                              <td className="py-2 px-2 font-mono">{point.confidence_threshold.toFixed(3)}</td>
                              <td className="py-2 px-2 font-mono">{point.margin_threshold.toFixed(3)}</td>
                              <td className="py-2 px-2 text-slate-300">{(point.auto_routed_rate * 100).toFixed(1)}%</td>
                              <td className="py-2 px-2 text-emerald-400 font-medium">{(point.auto_routed_accuracy * 100).toFixed(1)}%</td>
                              <td className="py-2 px-2 text-slate-300">{(point.review_queue_rate * 100).toFixed(1)}%</td>
                              <td className="py-2 px-2 font-mono text-indigo-400">{point.score.toFixed(4)}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-slate-200 mb-2">Recommendation</h3>
                  <p className="text-xs text-slate-400">
                    Use <code className="px-1.5 py-0.5 bg-slate-800 rounded font-mono">{result.optimal_confidence_threshold.toFixed(3)}</code> 
                    as the confidence threshold and 
                    <code className="px-1.5 py-0.5 bg-slate-800 rounded font-mono">{result.optimal_margin_threshold.toFixed(3)}</code> 
                    as the margin threshold for production triage routing. 
                    This configuration is expected to auto-route 
                    <span className="font-medium text-emerald-400">{(result.expected_auto_routed_rate * 100).toFixed(1)}%</span> 
                    of tickets with 
                    <span className="font-medium text-emerald-400">{(result.expected_auto_routed_accuracy * 100).toFixed(1)}%</span> 
                    accuracy, sending the remaining 
                    <span className="font-medium text-amber-400">{(result.expected_review_queue_rate * 100).toFixed(1)}%</span> 
                    to human review.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ThresholdOptimization;
</arg_key>
<arg_key=i>
Create ThresholdOptimization component
