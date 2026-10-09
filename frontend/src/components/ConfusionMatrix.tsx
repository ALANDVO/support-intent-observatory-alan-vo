import React, { useState } from "react";
import { EvaluationData } from "../types/api";

interface ConfusionMatrixProps {
  evaluation: EvaluationData | null;
  isLoading: boolean;
}

export const ConfusionMatrix: React.FC<ConfusionMatrixProps> = ({ evaluation, isLoading }) => {
  const [selectedCell, setSelectedCell] = useState<{ actual: string; predicted: string; count: number; rate: number } | null>(null);

  if (isLoading) {
    return <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center text-slate-400 text-xs">Loading metrics...</div>;
  }
  if (!evaluation) {
    return <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center text-slate-400 text-xs">No evaluation data available. Train a model to inspect confusion.</div>;
  }

  const { confusion_matrix, per_class_metrics, discriminative_features, baseline_comparison } = evaluation;
  const labels = confusion_matrix.labels;

  return (
    <div className="space-y-6">
      <div className="bg-indigo-950/40 border border-indigo-800/60 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-xs uppercase font-semibold text-indigo-400 tracking-wider">Evaluation vs Baseline</span>
          <div className="text-sm text-slate-200 mt-0.5">{baseline_comparison.interpretation}</div>
        </div>
        <div className="flex items-center space-x-3 text-sm">
          <div className="text-slate-400">Baseline: <span className="font-mono text-slate-200">{(baseline_comparison.baseline_accuracy * 100).toFixed(1)}%</span></div>
          <div className="text-emerald-400 font-semibold">Lift: +{(baseline_comparison.accuracy_delta * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-slate-100">Multi-Class Confusion Matrix Heatmap</h3>
            <p className="text-xs text-slate-400">Rows: Actual Intent; Columns: Predicted Intent.</p>
          </div>
          {selectedCell && (
            <div className="mt-2 sm:mt-0 text-xs bg-slate-900 border border-slate-700 px-3 py-1.5 rounded">
              <span className="text-slate-400">Selected: </span>
              <span className="font-semibold text-slate-200">{selectedCell.actual}</span> &rarr;{" "}
              <span className="font-semibold text-indigo-300">{selectedCell.predicted}</span>:{" "}
              <span className="text-emerald-400 font-mono">{selectedCell.count}</span> ({(selectedCell.rate * 100).toFixed(1)}%)
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="p-2 text-left font-medium text-slate-400 border-b border-slate-700">Actual \ Predicted</th>
                {labels.map((lbl) => (
                  <th key={lbl} className="p-2 text-center font-medium text-slate-300 border-b border-slate-700 truncate" title={lbl}>
                    {lbl.replace("_", " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {labels.map((actualLbl, rowIdx) => (
                <tr key={actualLbl} className="border-b border-slate-700/50">
                  <td className="p-2 font-medium text-slate-300 truncate" title={actualLbl}>{actualLbl.replace("_", " ")}</td>
                  {labels.map((predLbl, colIdx) => {
                    const count = confusion_matrix.matrix[rowIdx][colIdx];
                    const rate = confusion_matrix.normalized_matrix[rowIdx][colIdx];
                    const isDiag = rowIdx === colIdx;
                    let bg = "bg-slate-900/40 text-slate-400 hover:bg-slate-700";
                    if (isDiag && count > 0) bg = "bg-emerald-900/60 text-emerald-200 font-semibold hover:bg-emerald-800";
                    else if (!isDiag && count > 0) bg = "bg-rose-950/60 text-rose-300 font-medium hover:bg-rose-900";

                    return (
                      <td
                        key={predLbl}
                        onClick={() => setSelectedCell({ actual: actualLbl, predicted: predLbl, count, rate })}
                        className={`p-2.5 text-center cursor-pointer border border-slate-700/40 ${bg}`}
                      >
                        <div className="font-mono text-sm leading-tight">{count}</div>
                        <div className="text-[10px] opacity-75">{(rate * 100).toFixed(0)}%</div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-100 mb-3">Per-Class Metrics</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="py-2">Intent Class</th>
                  <th className="py-2 text-right">Precision</th>
                  <th className="py-2 text-right">Recall</th>
                  <th className="py-2 text-right">F1-Score</th>
                  <th className="py-2 text-right">Samples</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {Object.entries(per_class_metrics).map(([intent, m]) => (
                  <tr key={intent}>
                    <td className="py-2 font-medium text-slate-300">{intent.replace("_", " ")}</td>
                    <td className="py-2 text-right font-mono text-slate-300">{(m.precision * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right font-mono text-slate-300">{(m.recall * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right font-mono text-indigo-400 font-semibold">{(m.f1_score * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right font-mono text-slate-400">{m.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-100 mb-3">Top Discriminative N-Gram Tokens</h3>
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {Object.entries(discriminative_features.per_intent_features).map(([intent, features]) => (
              <div key={intent} className="bg-slate-900/60 p-2.5 rounded border border-slate-700/60">
                <div className="text-xs font-semibold text-indigo-300 mb-1.5 capitalize">{intent.replace("_", " ")}</div>
                <div className="flex flex-wrap gap-1.5">
                  {features.map((f) => (
                    <span key={f.feature} className="inline-flex items-center text-[11px] bg-slate-800 border border-slate-700 px-2 py-0.5 rounded text-slate-200">
                      <span className="font-mono mr-1">{f.feature}</span>
                      <span className="text-emerald-400 font-mono text-[10px]">+{f.weight.toFixed(2)}</span>
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
