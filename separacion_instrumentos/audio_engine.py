import os
import time
import wave
import io
import pygame

class AudioEngine:
    def __init__(self):
        # Initialize Pygame Mixer with standard 44100Hz, 16bit stereo
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        
        # Increase available channels (default is 8, 16 is safe for multi-stem)
        pygame.mixer.set_num_channels(16)

        self.mode = None  # "single" or "stems"
        self.is_playing = False
        self.is_paused = False

        # Single song properties
        self.single_path = None
        self.single_duration = 0.0

        # Stems song properties
        self.stem_paths = {}  # e.g. {"VOCALS": path, "DRUMS": path, ...}
        self.stem_volumes = {} # e.g. {"VOCALS": 1.0, ...}
        self.stem_mutes = {}   # e.g. {"VOCALS": False, ...}
        self.stem_solos = {}   # e.g. {"VOCALS": False, ...}
        self.stem_sounds = {}
        self.stem_channels = {}
        self.stems_duration = 0.0

        # Playback timing variables
        self.start_wall_time = 0.0
        self.seek_offset = 0.0
        self.duration = 0.0
        self.master_volume = 1.0

        self.on_finish_callback = None

    def load_single(self, file_path):
        self.stop()
        self.mode = "single"
        self.single_path = file_path
        self.seek_offset = 0.0

        # Estimate duration
        try:
            if file_path.lower().endswith(".wav"):
                with wave.open(file_path, "rb") as wf:
                    self.duration = wf.getnframes() / float(wf.getframerate())
            else:
                snd = pygame.mixer.Sound(file_path)
                self.duration = snd.get_length()
        except Exception as e:
            print(f"Error calculando duracion: {e}")
            self.duration = 180.0  # Fallback duration if unknown

        pygame.mixer.music.load(file_path)

    def load_stems(self, folder_path, stem_names):
        self.stop()
        self.mode = "stems"
        self.stem_paths = {}
        self.stem_volumes = {}
        self.stem_mutes = {}
        self.stem_solos = {}
        self.seek_offset = 0.0

        # Look for stem files inside folder_path
        self.stems_duration = 0.0
        for name in stem_names:
            filename = f"{name.lower()}.wav"
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                self.stem_paths[name] = file_path
                self.stem_volumes[name] = 0.8
                self.stem_mutes[name] = False
                self.stem_solos[name] = False

                if self.stems_duration == 0.0:
                    try:
                        with wave.open(file_path, "rb") as wf:
                            self.stems_duration = wf.getnframes() / float(wf.getframerate())
                    except Exception as e:
                        print(f"Error en wave header de stem: {e}")

        self.duration = self.stems_duration if self.stems_duration > 0 else 180.0

    def play(self, start_time=None):
        if start_time is not None:
            self.seek_offset = max(0.0, min(start_time, self.duration))

        if self.mode == "single":
            pygame.mixer.music.play(start=self.seek_offset)
            pygame.mixer.music.set_volume(self.master_volume)
            self.start_wall_time = time.time() - self.seek_offset
            self.is_playing = True
            self.is_paused = False

        elif self.mode == "stems":
            self._start_stems_playback(self.seek_offset)
            self.start_wall_time = time.time() - self.seek_offset
            self.is_playing = True
            self.is_paused = False

    def _start_stems_playback(self, start_sec):
        # Stop existing stem channels
        for ch in self.stem_channels.values():
            ch.stop()

        self.stem_sounds = {}
        self.stem_channels = {}

        has_any_solo = any(self.stem_solos.values())

        channel_idx = 0
        for name, path in self.stem_paths.items():
            try:
                # Use in-memory wave segment for accurate seeking
                with wave.open(path, "rb") as wf:
                    nchannels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    framerate = wf.getframerate()
                    nframes = wf.getnframes()
                    start_frame = int(start_sec * framerate)
                    start_frame = max(0, min(start_frame, nframes))
                    wf.setpos(start_frame)
                    frames = wf.readframes(nframes - start_frame)

                    out_buf = io.BytesIO()
                    out_wf = wave.open(out_buf, "wb")
                    out_wf.setnchannels(nchannels)
                    out_wf.setsampwidth(sampwidth)
                    out_wf.setframerate(framerate)
                    out_wf.writeframes(frames)
                    out_wf.close()
                    out_buf.seek(0)

                    sound = pygame.mixer.Sound(out_buf)
            except Exception as e:
                print(f"Fallback a carga directa para stem {name}: {e}")
                sound = pygame.mixer.Sound(path)

            ch = pygame.mixer.Channel(channel_idx)
            ch.play(sound)

            # Volume calculation considering mute & solo
            vol = self.stem_volumes.get(name, 0.8)
            if self.stem_mutes.get(name, False):
                vol = 0.0
            elif has_any_solo and not self.stem_solos.get(name, False):
                vol = 0.0
            
            ch.set_volume(vol * self.master_volume)

            self.stem_sounds[name] = sound
            self.stem_channels[name] = ch
            channel_idx += 1

    def pause(self):
        if not self.is_playing:
            return
        if not self.is_paused:
            if self.mode == "single":
                pygame.mixer.music.pause()
            elif self.mode == "stems":
                for ch in self.stem_channels.values():
                    ch.pause()
            self.is_paused = True
        else:
            if self.mode == "single":
                pygame.mixer.music.unpause()
            elif self.mode == "stems":
                for ch in self.stem_channels.values():
                    ch.unpause()
            self.is_paused = False

    def stop(self):
        if self.mode == "single":
            pygame.mixer.music.stop()
        elif self.mode == "stems":
            for ch in self.stem_channels.values():
                ch.stop()
        self.is_playing = False
        self.is_paused = False
        self.seek_offset = 0.0

    def seek(self, target_sec):
        target_sec = max(0.0, min(target_sec, self.duration))
        self.seek_offset = target_sec
        if self.is_playing:
            self.play(start_time=target_sec)

    def set_stem_volume(self, name, volume):
        self.stem_volumes[name] = float(volume)
        self.update_volumes()

    def set_stem_mute(self, name, muted):
        self.stem_mutes[name] = muted
        self.update_volumes()

    def set_stem_solo(self, name, soloed):
        self.stem_solos[name] = soloed
        self.update_volumes()

    def set_master_volume(self, volume):
        self.master_volume = float(volume)
        if self.mode == "single":
            pygame.mixer.music.set_volume(self.master_volume)
        else:
            self.update_volumes()

    def update_volumes(self):
        if self.mode == "stems":
            has_any_solo = any(self.stem_solos.values())
            for name, ch in self.stem_channels.items():
                vol = self.stem_volumes.get(name, 0.8)
                if self.stem_mutes.get(name, False):
                    vol = 0.0
                elif has_any_solo and not self.stem_solos.get(name, False):
                    vol = 0.0
                ch.set_volume(vol * self.master_volume)

    def get_current_position(self):
        if not self.is_playing:
            return self.seek_offset
        if self.is_paused:
            return self.seek_offset
        
        pos = time.time() - self.start_wall_time
        if pos >= self.duration:
            self.stop()
            if self.on_finish_callback:
                self.on_finish_callback()
            return self.duration
        return pos
