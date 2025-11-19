import React, { useState, useEffect } from 'react';

const TopBar = ({ onSelectSuggestion }) => {
    const [suggestions, setSuggestions] = useState([]);

    useEffect(() => {
        fetch('http://localhost:3000/api/suggestions')
            .then(res => res.json())
            .then(data => setSuggestions(data))
            .catch(err => console.error('Failed to fetch suggestions:', err));
    }, []);

    return (
        <div className="top-bar">
            <div className="suggestions-label">SUGGESTIONS:</div>
            <div className="suggestions-list">
                {suggestions.map(s => (
                    <button key={s.id} className="suggestion-btn" onClick={() => onSelectSuggestion(s)}>
                        {s.title} ({s.bpm} BPM)
                    </button>
                ))}
            </div>
        </div>
    );
};

export default TopBar;
