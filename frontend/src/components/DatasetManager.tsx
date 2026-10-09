import React, { useState, useEffect } from "react";
import { Dataset, DatasetDetail } from "../types/api";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface DatasetManagerProps {
  onModelTrained?: () => void;
}

export const DatasetManager: React.FC<DatasetManagerProps> = ({ onModelTrained }) => {
  const { role } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<DatasetDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [modelName, setModelName] = useState("support_intent_tfidf_v2");
  const [ngramMax, setNgramMax] = useState(2);
  const [cReg, setCReg] = useState(1.0);
  const [testSplit, setTestSplit] = useState(0.25);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null);

  const fetchDatasets = async () => {
    setIsLoading(true);
    try {
      const list = await api.listDatasets();
      setDatasets(list);
      if (list.length > 0) {
        const detail = await api.getDatasetDetail(list[0].id);
        setActiveDataset(detail);
      }
    } catch {
      // Handled
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modelName.trim()) return;

    setIsTraining(true);
    setTrainingMessage(null);
    try {
      const res = await api.trainModel({
        name: modelName,
        dataset_id: activeDataset?.id,
        hyperparameters: {
          ngram_min: 1,
          ngram_max: ngramMax,
          c_regularization: cReg,
          test_size: testSplit,
        },
      });
      setTrainingMessage(`Complete in ${res.training_latency_ms}ms! Accuracy: ${((res.accuracy ?? 0) * 100).toFixed(1)}%. Model active.`);
      if (onModelTrained) onModelTrained();
    } catch (err: unknown) {
      setTrainingMessage(`Training failed: ${err instanceof Error ? err.message : "Error"}`);
    } finally {
      setIsTraining(false);
    }
  };

  if (isLoading) {
    return <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center text-slate-400 text-xs">Loading datasets...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-slate-800 border border-slate-700 rounded-lg p-5">
          <div className="flex justify-between items-start mb-3">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-semibold text-slate-100">{activeDataset?.name || "Benchmark Dataset"}</h3>
                {datasets.length > 1 && (
                  <select
                    className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded px-2 py-0.5"
                    value={activeDataset?.id}
                    onChange={async (e) => {
                      const sel = await api.getDatasetDetail(e.target.value);
                      setActiveDataset(sel);
                    }}
                  >
                    {datasets.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">{activeDataset?.description || "Supervised support inquiries."}</p>
            </div>
            <span className="text-xs font-mono bg-slate-900 border border-slate-700 text-indigo-300 px-2.5 py-1 rounded">
              {activeDataset?.sample_count ?? 0} Tickets
            </span>
          </div>

          <div className="mt-4">
            <span className="text-xs font-medium text-slate-300 mb-2 block">Class Distribution:</span>
            <div className="space-y-2">
              {activeDataset &&
                Object.entries(activeDataset.class_distribution).map(([intent, count]) => {
                  const pct = activeDataset.sample_count > 0 ? (count / activeDataset.sample_count) * 100 : 0;
                  return (
                    <div key={intent} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-0.5">
                        <span className="capitalize">{intent.replace("_", " ")}</span>
                        <span className="font-mono text-slate-400">{count} ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                        <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${pct}%` }}></div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-base font-semibold text-slate-100 mb-2">Train Local TF-IDF Model</h3>
          <p className="text-xs text-slate-400 mb-4">Fit vectorizer and calibrate Logistic Regression.</p>

          <form onSubmit={handleTrain} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Model Name</label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-100 font-mono"
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">N-Grams</label>
                <select value={ngramMax} onChange={(e) => setNgramMax(parseInt(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-slate-200">
                  <option value={1}>(1,1) Words</option>
                  <option value={2}>(1,2) Bigrams</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">C Reg.</label>
                <select value={cReg} onChange={(e) => setCReg(parseFloat(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-slate-200">
                  <option value={0.5}>0.5</option>
                  <option value={1.0}>1.0</option>
                  <option value={5.0}>5.0</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Test Split</label>
                <select value={testSplit} onChange={(e) => setTestSplit(parseFloat(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-slate-200">
                  <option value={0.2}>20%</option>
                  <option value={0.25}>25%</option>
                  <option value={0.3}>30%</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={isTraining || role === "viewer"}
              className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold py-2 rounded transition-colors"
            >
              {isTraining ? "Training..." : "Train Model"}
            </button>
          </form>

          {trainingMessage && (
            <div className="mt-3 p-2 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200">
              {trainingMessage}
            </div>
          )}
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-100 mb-3">Corpus Sample Tickets</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="py-2.5 px-3">Ref</th>
                <th className="py-2.5 px-3">Message Text</th>
                <th className="py-2.5 px-3">Actual Intent</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {activeDataset?.preview_tickets.map((t) => (
                <tr key={t.id} className="hover:bg-slate-700/30">
                  <td className="py-2 px-3 font-mono text-slate-400 whitespace-nowrap">{t.ref || "TKT"}</td>
                  <td className="py-2 px-3 text-slate-200">{t.text}</td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    <span className="capitalize px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-indigo-300 font-medium">
                      {t.actual_intent.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
