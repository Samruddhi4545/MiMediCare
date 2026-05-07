import React, { useState } from 'react';
import axios from 'axios';

const styles = {
  container: { display: 'flex', height: '100vh', fontFamily: 'Segoe UI' },
  sidebar: { width: '250px', backgroundColor: '#f8f9fa', padding: '25px' },
  main: { flex: 1 },
  header: { padding: '20px', textAlign: 'center', fontSize: '28px', fontWeight: 'bold' },
  content: { padding: '30px' },
  navBtn: { display: 'block', width: '100%', padding: '12px', marginBottom: '10px', cursor: 'pointer' },
  activeBtn: { backgroundColor: '#3498db', color: 'white' },
  card: { padding: '20px', border: '1px solid #ddd', borderRadius: '10px' },
  actionBtn: { padding: '10px 20px', backgroundColor: '#3498db', color: 'white', border: 'none', cursor: 'pointer' },
  resultBox: { marginTop: '20px', padding: '15px', backgroundColor: '#f4f4f4' }
};

function App() {
  const cardStyle = {
      background: '#fff',
      padding: '25px',
      borderRadius: '15px',
      boxShadow: '0 6px 15px rgba(0,0,0,0.1)',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      fontSize: '18px',
      textAlign: 'center'
    };

  const [activeTab, setActiveTab] = useState('home');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [symptoms, setSymptoms] = useState("");

  const [pillResult, setPillResult] = useState(null);
  const [xrayResult, setXrayResult] = useState(null);
  const [symptomPrediction, setSymptomPrediction] = useState(null);
  const [nearestFacilities, setNearestFacilities] = useState(null);

  // ✅ MAIN HANDLER
  const handleAction = async (type, additionalData = null) => {

    if ((type === 'pill' || type === 'xray') && !file) {
      return alert("Please select an image first");
    }

    setLoading(true);

    try {

      // ---------------- PILL ----------------
      if (type === 'pill') {

        const formData = new FormData();
        formData.append("file", file);

        const res = await axios.post("http://127.0.0.1:8001/identify-pill", formData);
        setPillResult(res.data);
      }

      // ---------------- XRAY (REAL LOCATION) ----------------
      else if (type === 'xray') {

        navigator.geolocation.getCurrentPosition(
          async (pos) => {

            const formData = new FormData();
            formData.append("file", file);
            formData.append("user_lat", pos.coords.latitude);
            formData.append("user_lon", pos.coords.longitude);

            const res = await axios.post(
              "http://127.0.0.1:8001/analyze-xray",
              formData
            );

            setXrayResult(res.data);
            setLoading(false);
          },
          (err) => {
            alert("Location permission denied");
            setLoading(false);
          }
        );

        return; // IMPORTANT
      }

      // ---------------- SYMPTOMS ----------------
      else if (type === 'symptoms') {

        const res = await axios.post(
          "http://127.0.0.1:8001/predict-symptoms",
          { text: symptoms }
        );

        setSymptomPrediction(res.data);
      }

      // ---------------- DOCTORS ----------------
      else if (type === 'doctors') {

        navigator.geolocation.getCurrentPosition(
          async (pos) => {

            const res = await axios.post(
              "http://127.0.0.1:8001/find-nearby-doctors",
              {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude
              }
            );

            setNearestFacilities(res.data);
            setLoading(false);
          },
          () => {
            alert("Location required");
            setLoading(false);
          }
        );

        return;
      }

    } catch (err) {
      console.error(err);
      alert("Backend connection error");
    }

    setLoading(false);
  };

  return (
    <div style={styles.container}>

      {/* SIDEBAR */}
      <div style={styles.sidebar}>
        <button onClick={() => setActiveTab('home')} style={styles.navBtn}>Home</button>
        <button onClick={() => setActiveTab('medicine')} style={styles.navBtn}>Medicine</button>
        <button onClick={() => setActiveTab('xray')} style={styles.navBtn}>X-Ray</button>
        <button onClick={() => setActiveTab('symptoms')} style={styles.navBtn}>Symptoms</button>
        <button onClick={() => setActiveTab('doctors')} style={styles.navBtn}>Doctors</button>
      </div>

      {/* MAIN */}
      <div style={styles.main}>
        <div style={styles.header}>MiMediCare</div>

        <div style={styles.content}>

          {/* HOME */}
          {activeTab === 'home' && (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              background: 'linear-gradient(135deg, #e3f2fd, #ffffff)',
              borderRadius: '20px'
            }}>
    
            <h1 style={{
              fontSize: '40px',
              color: '#2c3e50',
              marginBottom: '10px'
            }}>
            🏥 Welcome to MiMediCare
            </h1>

              <p style={{
                fontSize: '18px',
                color: '#555',
                marginBottom: '30px'
              }}>
              AI-powered smart healthcare assistant for faster diagnosis & better care
              </p>

              {/* FEATURE CARDS */}
              <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '20px'
              }}>

                  {/* CARD 1 */}
                  <div style={cardStyle} onClick={()=>setActiveTab('medicine')}>
                    💊
                    <h3>Medicine Scanner</h3>
                    <p>Identify pills instantly using AI + OCR</p>
                  </div>

                  {/* CARD 2 */}
                  <div style={cardStyle} onClick={()=>setActiveTab('xray')}>
                    🩻
                    <h3>X-Ray Analysis</h3>
                    <p>Detect abnormalities with AI assistance</p>
                  </div>

                  {/* CARD 3 */}
                  <div style={cardStyle} onClick={()=>setActiveTab('symptoms')}>
                    🩺
                    <h3>Symptom Checker</h3>
                    <p>Predict possible diseases from symptoms</p>
                  </div>

                  {/* CARD 4 */}
                  <div style={cardStyle} onClick={()=>setActiveTab('doctors')}>
                    📍
                    <h3>Find Doctors</h3>
                    <p>Locate nearby specialists instantly</p>
                  </div>

                </div>

                {/* FOOTER */}
                <p style={{
                  marginTop: '40px',
                  fontSize: '14px',
                  color: '#888'
                }}>
                  ⚠️ This system provides AI-assisted insights, not a medical diagnosis.
                </p>
              </div>
            )}

          {/* MEDICINE */}
          {activeTab === 'medicine' && (
            <div style={styles.card}>
              <input type="file" onChange={(e) => setFile(e.target.files[0])} />
              <button style={styles.actionBtn} onClick={() => handleAction('pill')}>
                {loading ? "Processing..." : "Identify"}
              </button>

              {pillResult && (
                <div style={styles.resultBox}>
                  <h3>{pillResult.details.title}</h3>
                  <p>{pillResult.details.usage_intro}</p>
                </div>
              )}
            </div>
          )}

          {/* XRAY */}
          {activeTab === 'xray' && (
            <div style={styles.card}>
              <input type="file" onChange={(e) => setFile(e.target.files[0])} />
              <button style={styles.actionBtn} onClick={() => handleAction('xray')}>
                {loading ? "Analyzing..." : "Analyze X-ray"}
              </button>

              {xrayResult && (
                <div style={styles.resultBox}>
                  <h3>Detected Part: {xrayResult.detected_part}</h3>
                  <h2>{xrayResult.condition}</h2>
                  <p>{xrayResult.explanation}</p>
                </div>
              )}
            </div>
          )}

          {/* SYMPTOMS */}
          {activeTab === 'symptoms' && (
            <div style={styles.card}>
              <textarea value={symptoms} onChange={(e) => setSymptoms(e.target.value)} />
              <button onClick={() => handleAction('symptoms')} style={styles.actionBtn}>
                Predict
              </button>

              {symptomPrediction && (
                <div style={styles.resultBox}>
                  {Array.isArray(symptomPrediction.prediction) ? (
                    symptomPrediction.prediction.map((item, i) => (
                    <p key={i}>
                      <b>{item.disease}</b> — Confidence: {item.confidence}
                    </p>
              ))
              ) : (
              <p>{symptomPrediction.prediction}</p>
              )}
              </div>
              )}
            </div>
          )}

          {/* DOCTORS */}
          {activeTab === 'doctors' && (
            <div style={styles.card}>
              <button onClick={() => handleAction('doctors')} style={styles.actionBtn}>
                Find Doctors
              </button>

              {nearestFacilities && (
                <div style={styles.resultBox}>
                  {nearestFacilities.nearby_facilities.map((d, i) => (
                    <p key={i}>{d.name} - {d.distance} km</p>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;