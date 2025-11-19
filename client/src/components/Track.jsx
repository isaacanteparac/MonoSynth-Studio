import React, { useState, useEffect, useRef } from 'react';
import { TrackAudio } from '../utils/synth';
import * as Tone from 'tone';

const notes = ['C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4', 'C4'];
const instruments = [
    { id: 'Synth', label: 'SYN' },
    { id: 'FMSynth', label: 'FM' },
    { id: 'AMSynth', label: 'AM' },
    { id: 'MembraneSynth', label: 'DRM' }
];
const steps = 16;

const Track = ({ id, isPlaying, bpm, onRemove }) => {
    const [instrumentType, setInstrumentType] = useState('Synth');
    const [grid, setGrid] = useState(notes.map(() => Array(steps).fill(false)));
    const [currentStep, setCurrentStep] = useState(0);
    const audioRef = useRef(null);
    const loopRef = useRef(null);

    useEffect(() => {
        audioRef.current = new TrackAudio(instrumentType);
        return () => audioRef.current.dispose();
    }, []);

    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.setInstrument(instrumentType);
        }
    }, [instrumentType]);

    useEffect(() => {
        if (loopRef.current) loopRef.current.dispose();

        loopRef.current = new Tone.Sequence(
            (time, step) => {
                Tone.Draw.schedule(() => {
                    setCurrentStep(step);
                }, time);

                grid.forEach((row, rowIndex) => {
                    if (row[step]) {
                        audioRef.current.playNote(notes[rowIndex], "8n", time);
                    }
                });
            },
            [...Array(steps).keys()],
            "8n"
        ).start(0);

        return () => loopRef.current.dispose();
    }, [grid]);

    const toggleCell = (row, col) => {
        const newGrid = [...grid];
        newGrid[row][col] = !newGrid[row][col];
        setGrid(newGrid);
    };

    return (
        <div className="track">
            <div className="track-sidebar">
                <div className="instrument-selector">
                    {instruments.map(inst => (
                        <button
                            key={inst.id}
                            className={`inst-btn ${instrumentType === inst.id ? 'active' : ''}`}
                            onClick={() => setInstrumentType(inst.id)}
                            title={inst.id}
                        >
                            {inst.label}
                        </button>
                    ))}
                </div>
                <button className="remove-btn" onClick={() => onRemove(id)}>REMOVE</button>
            </div>

            <div className="sequencer-container">
                <div className="note-labels">
                    {notes.map(note => (
                        <div key={note} className="note-label">{note}</div>
                    ))}
                </div>
                <div className="sequencer">
                    <div className="grid">
                        {grid.map((row, rowIndex) => (
                            <div key={rowIndex} className="row">
                                {row.map((isActive, colIndex) => (
                                    <div
                                        key={colIndex}
                                        className={`cell ${isActive ? 'active' : ''} ${currentStep === colIndex ? 'current' : ''}`}
                                        onClick={() => toggleCell(rowIndex, colIndex)}
                                    />
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default React.memo(Track);
