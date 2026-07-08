import React, { useState, useEffect } from 'react';
import './theme.css';

function App() {
  const [theme, setTheme] = useState('dark');
  const [url, setUrl] = useState('');
  const [layer, setLayer] = useState('surface');
  const [format, setFormat] = useState('json');
  const [targetQuery, setTargetQuery] = useState('');
  const [logs, setLogs] = useState(['[SYSTEM] AWAITING COMMAND_']);
  const [vaultFiles, setVaultFiles] = useState([]);

  // Fetch data logs from backend vault storage
  const refreshVault = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/exports');
      const data = await response.json();
      setVaultFiles(data.files || []);
    } catch (err) {
      setLogs((prev) => [...prev, '[ERROR] Failed to establish link with secure data vault.']);
    }
  };

  // Run vault synchronization on interface mount
  useEffect(() => {
    refreshVault();
    // Auto sync vault records every 5 seconds
    const interval = setInterval(refreshVault, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleCrawl = async () => {
    if (!url) {
      setLogs((prev) => [...prev, '[ERROR] Cannot target an empty string destination values.']);
      return;
    }

    setLogs((prev) => [...prev, `[INFO] Initializing ${layer.toUpperCase()} scan on target string: ${url}`]);

    const payload = {
      url: url,
      layer: layer,
      export_format: format,
      extraction_query: targetQuery
    };

    try {
      const res = await fetch('http://localhost:8000/api/v1/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setLogs((prev) => [...prev, `[SUCCESS] Broker response received: ${data.message}`]);

      // Force pipeline vault check update delay
      setTimeout(refreshVault, 3000);
    } catch (err) {
      setLogs((prev) => [...prev, '[CRITICAL] Transmission route failed to sync with orchestrator.']);
    }
  };

  const handleDownload = (filename) => {
    window.open(`http://localhost:8000/api/v1/exports/download/${filename}`, '_blank');
    setLogs((prev) => [...prev, `[SYSTEM] Stream link established for object: ${filename}`]);
  };

  return (
    <div className="terminal-wrapper">
      <div className="header">
        <h1>[TRI-LAYER-INTELLIGENCE_NODE]</h1>
        <button className="theme-toggle" onClick={toggleTheme}>
          SWITCH_UI_MODE
        </button>
      </div>

      <div className="control-panel">
        <div className="input-group">
          <label>TARGET_URL&gt; </label>
          <input
            type="text"
            onChange={(e) => setUrl(e.target.value)}
            placeholder="e.g., http://target.onion or https://example.com"
          />
        </div>

        <div className="input-group multi-select">
          <div>
            <label>ROUTING_LAYER&gt; </label>
            <select onChange={(e) => setLayer(e.target.value)} value={layer}>
              <option value="surface">Surface Web (Scrapy)</option>
              <option value="deep">Deep Web (Playwright)</option>
              <option value="dark">Dark Web (Tor/I2P)</option>
            </select>
          </div>

          <div>
            <label>EXPORT_FORMAT&gt; </label>
            <select onChange={(e) => setFormat(e.target.value)} value={format}>
              <option value="json">.JSON (Structured)</option>
              <option value="csv">.CSV (Tabular)</option>
              <option value="txt">.TXT (Raw Text)</option>
            </select>
          </div>
        </div>

        <div className="input-group">
          <label>EXTRACTION_PARAMETERS (What to look for)&gt; </label>
          <textarea
            onChange={(e) => setTargetQuery(e.target.value)}
            placeholder="e.g., Extract all structural content matching target terms..."
            rows="2"
          />
        </div>

        <button className="execute-btn" onClick={handleCrawl}>
          [ EXECUTE_DIRECTIVE ]
        </button>
      </div>

      {/* SECURE DATA VAULT VIEWPORTS */}
      <div className="output-stream" style={{ marginBottom: '20px', height: '180px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px dashed var(--border-color)', paddingBottom: '5px' }}>
          <h3>// DATA_VAULT_DECRYPTED</h3>
          <button onClick={refreshVault} style={{ background: 'transparent', color: 'var(--text-color)', border: '1px solid var(--border-color)', cursor: 'pointer', fontSize: '0.8em' }}>
            REFRESH_VAULT
          </button>
        </div>
        <div className="logs" style={{ marginTop: '10px' }}>
          {vaultFiles.length === 0 ? (
            <p style={{ color: '#666' }}>[EMPTY] No target structural nodes harvested yet inside local cluster volumes.</p>
          ) : (
            vaultFiles.map((file, index) => (
              <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '6px 0', background: 'rgba(0,255,65,0.03)', padding: '6px', borderLeft: '3px solid var(--border-color)' }}>
                <span>📁 {file}</span>
                <button onClick={() => handleDownload(file)} style={{ background: 'var(--text-color)', color: 'var(--bg-color)', border: 'none', padding: '3px 12px', cursor: 'pointer', fontWeight: 'bold', fontFamily: 'var(--font-family)' }}>
                  DOWNLOAD
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="output-stream">
        <h3>// INTERFACE_LOG_STREAM</h3>
        <div className="logs">
          {logs.map((log, index) => (
            <p key={index} className={index === logs.length - 1 ? 'blink-cursor' : ''}>
              {log}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
