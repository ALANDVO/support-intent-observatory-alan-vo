# Changelog

## 1.6.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.5.0 — work-in-progress checkpoint

### Improved
- Added "Clear" button for the optional Target Auto-Route Rate field in Threshold Optimization UI, allowing users to easily reset the target rate parameter.

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Fixed
- Fixed corrupted XML tags in `frontend/src/api/client.ts`, `frontend/src/components/ThresholdOptimization.tsx`, `frontend/src/App.tsx`, and `frontend/src/components/Navbar.tsx` that caused build/test failures.
- Fixed TypeScript errors in `frontend/src/api/client.ts` (added `vite-env.d.ts` for `import.meta.env` type), `frontend/src/App.tsx` (corrected default import for `ThresholdOptimization`), and `frontend/src/components/TriageWorkbench.tsx` (removed unused `confidence_threshold` and `margin_threshold` parameters not accepted by backend).
- Added frontend test coverage for ThresholdOptimization component (`frontend/src/test/ThresholdOptimization.test.tsx`).

### Testing
- All 24 backend tests pass.
- All 7 frontend tests pass (4 test files).
- Frontend production build succeeds.

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
