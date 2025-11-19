import React, { useState, useEffect } from 'react';
import { playNote } from '../utils/synth';
import * as Tone from 'tone';

const notes = ['C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4', 'C4'];
const steps = 16;

const Sequencer = ({ isPlaying, setIsPlaying }) => {
    const [grid, setGrid] = useState(
        notes.map(() => Array(steps).fill(false))
    );
    const [currentStep, setCurrentStep] = useState(0);

    useEffect(() => {
        const loop = new Tone.Sequence(
            (time, step) => {
                setCurrentStep(step);
                grid.forEach((row, rowIndex) => {
                    if (row[step]) {
                        playNote(notes[rowIndex], "8n");
                    }
                });
            },
            [...Array(steps).keys()],
            "8n"
        );

        if (isPlaying) {
            loop.start(0);
            Tone.Transport.start();
        } else {
            loop.stop();
            Tone.Transport.stop();
        }

        return () => {
            loop.dispose();
        };
    }, [isPlaying, grid]);

    const toggleCell = (row, col) => {
        const newGrid = [...grid];
        newGrid[row][col] = !newGrid[row][col];
        setGrid(newGrid);
    };

    return (
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
    );
};

export default Sequencer;
