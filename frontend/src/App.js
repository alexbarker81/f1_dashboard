import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [laps, setLaps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get API base URL from environment variable (Docker)
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';

  // Fetch sessions on component mount
  useEffect(() => {
    setLoading(true);
    setError(null); // Clear previous errors
    fetch(`${API_BASE_URL}/sessions`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setSessions(data);
        setLoading(false);
      })
      .catch(error => {
        setError(error);
        setLoading(false);
      });
  }, [API_BASE_URL]);

  // Fetch laps when a session is selected
  useEffect(() => {
    if (selectedSessionId) {
      setLoading(true);
      setError(null); // Clear previous errors
      fetch(`${API_BASE_URL}/laps/${selectedSessionId}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          setLaps(data);
          setLoading(false);
        })
        .catch(error => {
          setError(error);
          setLoading(false);
        });
    } else {
      setLaps([]); // Clear laps if no session is selected
    }
  }, [selectedSessionId, API_BASE_URL]);

  const handleSessionChange = (event) => {
    setSelectedSessionId(event.target.value);
  };

  const formatMilliseconds = (ms) => {
    if (ms === null || ms === undefined) return '-';
    const totalSeconds = ms / 1000;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    const millis = Math.round((totalSeconds - Math.floor(totalSeconds)) * 1000);
    return `${minutes}:${String(seconds).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>F1 Data Dashboard</h1>
      </header>
      <main>
        {loading && <p>Loading data...</p>}
        {error && <p>Error: {error.message}</p>}

        <section className="session-selector">
          <h2>Select Session</h2>
          <select onChange={handleSessionChange} value={selectedSessionId || ''}>
            <option value="">-- Please choose a session --</option>
            {sessions.map(session => (
              <option key={session.session_id} value={session.session_id}>
                {session.year} {session.gp_name} - {session.session_type} ({session.date})
              </option>
            ))}
          </select>
        </section>

        {selectedSessionId && (
          <section className="lap-data">
            <h2>Lap Data</h2>
            {laps.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Driver</th>
                    <th>Lap No.</th>
                    <th>Lap Time</th>
                    <th>Sector 1</th>
                    <th>Sector 2</th>
                    <th>Sector 3</th>
                    <th>Speed Trap (km/h)</th>
                    <th>Tyre Compound</th>
                  </tr>
                </thead>
                <tbody>
                  {laps.map(lap => (
                    <tr key={lap.lap_id}>
                      <td>{lap.driver}</td>
                      <td>{lap.lap_number}</td>
                      <td>{formatMilliseconds(lap.lap_time_ms)}</td>
                      <td>{formatMilliseconds(lap.sector1_time_ms)}</td>
                      <td>{formatMilliseconds(lap.sector2_time_ms)}</td>
                      <td>{formatMilliseconds(lap.sector3_time_ms)}</td>
                      <td>{lap.speed_trap_kmh || '-'}</td>
                      <td>{lap.tyre_compound || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No lap data available for this session.</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
