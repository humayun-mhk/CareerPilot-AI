import { useEffect, useState } from 'react';
import { getEvidenceGraph } from '../api/client.js';

export default function EvidenceGraph() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    getEvidenceGraph()
      .then(setGraph)
      .catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load evidence graph.'));
  }, []);

  return (
    <div>
      <div className="pageHeader">
        <h1>Evidence Graph</h1>
        <p>Applications linked to verified skills and confidence scores.</p>
      </div>
      {error && <div className="panel error">{error}</div>}
      <section className="panel graphList">
        <h2>Nodes</h2>
        {graph.nodes.map((node) => (
          <div key={node.id} className={`node ${node.type}`}>{node.label}</div>
        ))}
      </section>
      <section className="panel graphList">
        <h2>Edges</h2>
        {graph.edges.map((edge, index) => (
          <div key={`${edge.source}-${edge.target}-${index}`} className="edge">
            {edge.source} -&gt; {edge.target} | {edge.status} | {Math.round(edge.confidence * 100)}%
          </div>
        ))}
      </section>
    </div>
  );
}
