import { useEffect, useMemo, useState } from 'react';
import { getTraceRun, getTraces } from '../api/client.js';

function groupByRun(traces) {
  return traces.reduce((groups, trace) => {
    const runId = trace.graph_run_id || 'unknown';
    groups[runId] = groups[runId] || [];
    groups[runId].push(trace);
    return groups;
  }, {});
}

export default function AgentTracing() {
  const [traces, setTraces] = useState([]);
  const [selectedRun, setSelectedRun] = useState('');
  const [runDetail, setRunDetail] = useState([]);
  const [error, setError] = useState('');
  const grouped = useMemo(() => groupByRun(traces), [traces]);

  useEffect(() => {
    getTraces(1)
      .then(setTraces)
      .catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load traces.'));
  }, []);

  async function loadRun(graphRunId) {
    setSelectedRun(graphRunId);
    setRunDetail(await getTraceRun(graphRunId));
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Agent Tracing</h1>
        <p>Inspect graph runs, agent order, runtime, input/output JSON, tool calls, and failures.</p>
      </div>
      {error && <div className="panel error">{error}</div>}

      <section className="panel">
        <h2>Graph Runs</h2>
        {Object.keys(grouped).length === 0 ? <p>No traces yet. Run an analysis first.</p> : (
          <div className="graphList">
            {Object.entries(grouped).map(([runId, items]) => (
              <button className="traceButton" key={runId} onClick={() => loadRun(runId)}>
                {runId} | {items.length} steps | latest {items[0]?.started_at}
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedRun && (
        <section className="panel">
          <h2>Run Detail</h2>
          <div className="traceList">
            {runDetail.map((trace) => (
              <details className="traceItem" key={trace.id}>
                <summary>
                  <span>{trace.step_order}. {trace.agent_name}</span>
                  <span className={`badge ${trace.status}`}>{trace.status}</span>
                  <span>{trace.duration_ms || 0} ms</span>
                </summary>
                {trace.error_message && <p className="error">{trace.error_message}</p>}
                <h3>Input</h3>
                <pre>{JSON.stringify(trace.input, null, 2)}</pre>
                <h3>Output</h3>
                <pre>{JSON.stringify(trace.output, null, 2)}</pre>
                <h3>Tools</h3>
                <pre>{JSON.stringify(trace.tools_called, null, 2)}</pre>
              </details>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
