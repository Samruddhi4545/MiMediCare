import React, { useState } from 'react';
import './App.css';

function App() {
  // --- State Management ---
  const [activeTab, setActiveTab] = useState('Home');
  const [file, setFile] = useState(null);
  const [symptoms, setSymptoms] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // --- API Functions ---

  // 1. Medicine Scanner & X-Ray Analysis
  const handleFileUpload = async (endpoint) => {
    if (!file) return alert("Please select an image first!");
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    
    // Coordinates updated to Mangaluru to match your database script
    formData.append("user_lat", 12.8706); 
    formData.append("user_lon", 74.8427);

    try {
      // Ensure port matches your Uvicorn port (usually 8000)
      const response = await fetch(`http://127.0.0.1:8001/${endpoint}`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      alert("Backend server is not running!");
    }
    setLoading(false);
  };

  // 2. Symptom Checker
  const handleSymptomCheck = async () => {
    if (!symptoms) return alert("Please describe your symptoms!");
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8001/predict-symptoms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: symptoms }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
    }
    setLoading(false);
  };

  // 3. New Feature: Fetch Nearby Doctors for the Doctor Panel
  const fetchNearbyDoctors = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8001/find-nearby-doctors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          lat: 12.8706, // Mangaluru Latitude
          lon: 74.8427  // Mangaluru Longitude
        }),
      });

      if (!response.ok) throw new Error("No doctors found");

      const data = await response.json();
      
      // We structure this to be rendered by the renderOutputWindow
      setResult({
        nearby_doctors: data.nearby_facilities,
        recommended_specialist: "Available Specialists"
      });
    } catch (error) {
      console.error("Error:", error);
      setResult({ nearby_doctors: [], message: "No doctors found in Mangaluru area." });
    }
    setLoading(false);
  };

  // --- UI Components ---

  const renderOutputWindow = () => {
    if (!result) return null;
    return (
      <div className="output-window">
        <h3>Diagnostic Report</h3>
        <hr />
        {activeTab === 'X-Ray' && (
          <div>
            <p><strong>Detected Part:</strong> {result.detected_part}</p>
            <p className="explanation"><strong>AI Explanation:</strong> {result.explanation}</p>
            <p><strong>Suggested Specialist:</strong> {result.recommended_specialist}</p>
          </div>
        )}
        {activeTab === 'Symptoms' && (
          <div>
            <p><strong>Condition:</strong> {result.prediction}</p>
            <p className="explanation"><strong>Analysis:</strong> {result.explanation}</p>
          </div>
        )}
        {activeTab === 'Medicine' && (
          <div>
            <p><strong>Detected Pill:</strong> {Array.isArray(result.ai_prediction) ? result.ai_prediction.join(', ') : result.ai_prediction}</p>
            <p><strong>OCR Text:</strong> {result.detected_text || "No text found"}</p>
          </div>
        )}
        
        {/* Logic to show Doctor Cards in both X-Ray and Doctor Panel */}
        {result.nearby_doctors && result.nearby_doctors.length > 0 && (
          <div className="doctors-list">
            <h4>Nearby {result.recommended_specialist || "Doctors"}:</h4>
            <div className="doctor-grid">
              {result.nearby_doctors.map((doc, i) => (
                <div key={i} className="doctor-card">
                  <p><strong>{doc.name}</strong></p>
                  <p>{doc.specialty}</p>
                  <p>{doc.address}</p>
                  <span>{doc.distance} km away</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <h2>MiMediCare</h2>
        {['Home', 'Medicine', 'X-Ray', 'Symptoms', 'Doctors'].map(tab => (
          <button 
            key={tab} 
            className={activeTab === tab ? 'active' : ''} 
            onClick={() => { 
              setActiveTab(tab); 
              setResult(null);
              // Auto-fetch if the user clicks the Doctors tab
              if (tab === 'Doctors') fetchNearbyDoctors();
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        <h1>{activeTab} Panel</h1>
        
        {activeTab === 'Home' && (
          <div className="welcome-hero">
            <h2>Welcome to MiMediCare, Samruddhi</h2>
            <p>AI-powered smart healthcare assistant for faster diagnosis.</p>
          </div>
        )}

        {activeTab === 'X-Ray' && (
          <div className="card">
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            <button onClick={() => handleFileUpload('analyze-xray')}>Run X-Ray Analysis</button>
          </div>
        )}

        {activeTab === 'Symptoms' && (
          <div className="card">
            <textarea 
              placeholder="Describe how you feel (e.g., I have a dry cough and fever)..."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
            />
            <button onClick={handleSymptomCheck}>Check Symptoms</button>
          </div>
        )}

        {activeTab === 'Medicine' && (
          <div className="card">
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            <button onClick={() => handleFileUpload('identify-pill')}>Scan Medicine</button>
          </div>
        )}

        {activeTab === 'Doctors' && !result && !loading && (
          <div className="card">
            <p>Click "Doctors" in the sidebar to refresh local listings.</p>
          </div>
        )}

        {loading && <div className="loader">Analyzing Data...</div>}
        {renderOutputWindow()}
      </div>
    </div>
  );
}

export default App;