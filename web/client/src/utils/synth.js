import * as Tone from 'tone';

export class TrackAudio {
    constructor(type = 'Synth') {
        this.instrument = this.createInstrument(type);
        this.instrument.toDestination();
    }

    createInstrument(type) {
        switch (type) {
            case 'FMSynth':
                return new Tone.PolySynth(Tone.FMSynth);
            case 'AMSynth':
                return new Tone.PolySynth(Tone.AMSynth);
            case 'MembraneSynth':
                return new Tone.PolySynth(Tone.MembraneSynth);
            case 'Synth':
            default:
                return new Tone.PolySynth(Tone.Synth, {
                    oscillator: { type: "triangle" },
                    envelope: { attack: 0.005, decay: 0.1, sustain: 0.3, release: 1 }
                });
        }
    }

    setInstrument(type) {
        if (this.instrument) {
            this.instrument.dispose();
        }
        this.instrument = this.createInstrument(type);
        this.instrument.toDestination();
    }

    playNote(note, duration = "8n", time) {
        if (this.instrument) {
            this.instrument.triggerAttackRelease(note, duration, time);
        }
    }

    dispose() {
        if (this.instrument) {
            this.instrument.dispose();
        }
    }
}

export const startAudioContext = async () => {
    await Tone.start();
    console.log('Audio is ready');
};

export const setBpm = (bpm) => {
    Tone.Transport.bpm.value = bpm;
};
