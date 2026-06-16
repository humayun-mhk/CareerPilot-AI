import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import Analyze from './pages/Analyze.jsx';
import Approval from './pages/Approval.jsx';
import Tracker from './pages/Tracker.jsx';
import Analytics from './pages/Analytics.jsx';
import EvidenceGraph from './pages/EvidenceGraph.jsx';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/analyze" replace />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/approval/:analysisId" element={<Approval />} />
        <Route path="/tracker" element={<Tracker />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/evidence" element={<EvidenceGraph />} />
        <Route path="*" element={<Navigate to="/analyze" replace />} />
      </Routes>
    </Layout>
  );
}
