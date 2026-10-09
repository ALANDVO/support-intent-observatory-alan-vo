import React, { useState, useEffect } from "react";
import { AuthProvider } from "./context/AuthContext";
import { Navbar } from "./components/Navbar";
import { MetricsCards } from "./components/MetricsCards";
import { ConfusionMatrix } from "./components/ConfusionMatrix";
import { TriageWorkbench } from "./components/TriageWorkbench";
import { ReviewQueue } from "./components/ReviewQueue";
import { DatasetManager } from "./components/DatasetManager";
import { SystemStats, EvaluationData } from "./types/api";
import { api } from "./api/client";

const MainContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [isLoadingEval, setIsLoadingEval] = useState(false);

  const refreshData = async () => {
    try {
      const s = await api.getSystemStats();
      setStats(s);

      const models = await api.listModels();
      const active = models.find((m) => m.is_active) || models[0];
      if (active) {
        setIsLoadingEval(true);
        const ev = await api.getModelEvaluation(active.id);
        setEvaluation(ev);
      }
    } catch {
      // Graceful error handling
    } finally {
      setIsLoadingEval(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pendingCount={stats?.pending_review_count ?? 0}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <MetricsCards
          stats={stats}
          onNavigateToReview={() => setActiveTab("review")}
        />

        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
              <h2 className="text-base font-bold text-slate-100 mb-1">
                NLP Intent Classification Pipeline Architecture
              </h2>
              <p className="text-xs text-slate-400 mb-4">
                Deterministic TF-IDF multi-class classification engine with calibrated confidence scoring, uncertainty routing, and opt-in advisory assistance.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                  <div className="font-semibold text-indigo-400 mb-1">1. Labeled Support Corpus</div>
                  <div className="text-slate-400">
                    6 operational support intents with sublinear TF-IDF vectorization and unigram/bigram tokenization.
                  </div>
                </div>
                <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                  <div className="font-semibold text-indigo-400 mb-1">2. Calibrated Multiclass Model</div>
                  <div className="text-slate-400">
                    Logistic regression estimating posterior probabilities, decision margin delta, and token attributions.
                  </div>
                </div>
                <div className="bg-slate-900/70 p-3 rounded border border-slate-700/60">
                  <div className="font-semibold text-indigo-400 mb-1">3. Uncertainty & Review Routing</div>
                  <div className="text-slate-400">
                    Threshold-based uncertainty gating to route ambiguous tickets to human-in-the-loop review.
                  </div>
                </div>
              </div>
            </div>

            <ConfusionMatrix evaluation={evaluation} isLoading={isLoadingEval} />
          </div>
        )}

        {activeTab === "evaluation" && (
          <ConfusionMatrix evaluation={evaluation} isLoading={isLoadingEval} />
        )}

        {activeTab === "triage" && (
          <TriageWorkbench onTriageComplete={refreshData} />
        )}

        {activeTab === "review" && (
          <ReviewQueue onQueueUpdated={refreshData} />
        )}

        {activeTab === "datasets" && (
          <DatasetManager onModelTrained={refreshData} />
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-950 py-4 text-center text-xs text-slate-500">
        Support Intent Observatory &bull; Built by Alan Vo (&lt;alanvo@gmail.com&gt;) &bull; Public Repository
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
};

export default App;
