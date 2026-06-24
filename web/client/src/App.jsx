import React, { useState, useEffect } from 'react';
import Track from './components/Track';
import TopBar from './components/TopBar';
import { startAudioContext, setBpm } from './utils/synth';
import * as Tone from 'tone';
import './App.css';

function App() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isStarted, setIsStarted] = useState(false);
  const [bpm, setBpmState] = useState(120);
  const [tracks, setTracks] = useState([{ id: 1 }]);

  const handleStart = async () => {
    await startAudioContext();
    setIsStarted(true);
    Tone.Transport.start();
    setIsPlaying(true);
  };

  const togglePlay = () => {
    if (isPlaying) {
      Tone.Transport.pause();
    } else {
      Tone.Transport.start();
    }
    setIsPlaying(!isPlaying);
  };

  const handleBpmChange = (e) => {
    const newBpm = parseInt(e.target.value);
    setBpmState(newBpm);
    setBpm(newBpm);
  };

  const addTrack = () => {
    const newId = tracks.length > 0 ? Math.max(...tracks.map(t => t.id)) + 1 : 1;
    setTracks([...tracks, { id: newId }]);
  };

  const removeTrack = (id) => {
    setTracks(tracks.filter(t => t.id !== id));
  };

  const handleSelectSuggestion = (suggestion) => {
    setBpmState(suggestion.bpm);
    setBpm(suggestion.bpm);
    // In a real app, this would load the pattern. For now, just set BPM.
    alert(`Loaded suggestion: ${suggestion.title}`);
  };

  return (
    <div className="app">
      <header>
        <h1>MonoSynth Studio</h1>
      </header>

      <main>
        {!isStarted ? (
          <div className="start-screen">
            <button className="start-btn" onClick={handleStart}>
              Enter Studio
            </button>
          </div>
        ) : (
          <>
            <TopBar onSelectSuggestion={handleSelectSuggestion} />

            <div className="global-controls">
              <button onClick={togglePlay}>
                {isPlaying ? 'PAUSE' : 'PLAY'}
              </button>
              <div className="bpm-control">
                <label>BPM: {bpm}</label>
                <input
                  type="range"
                  min="60"
                  max="200"
                  value={bpm}
                  onChange={handleBpmChange}
                />
              </div>
              <button onClick={addTrack}>+ ADD TRACK</button>
            </div>

            <div className="tracks-container">
              {tracks.map(track => (
                <Track
                  key={track.id}
                  id={track.id}
                  isPlaying={isPlaying}
                  bpm={bpm}
                  onRemove={removeTrack}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
