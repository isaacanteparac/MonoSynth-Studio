import os
import sys
import shutil
import threading
import subprocess
import queue

class DemucsSeparator:
    def __init__(self, config_manager):
        self.config = config_manager
        self.task_queue = queue.Queue()
        self.pending_list = []
        self.is_running = False
        self.current_item = None

        # Callbacks
        self.on_item_start = None
        self.on_item_finish = None
        self.on_queue_finish = None
        self.on_error = None

    def add_to_queue(self, file_paths):
        added_count = 0
        for path in file_paths:
            if os.path.isfile(path) and path not in self.pending_list:
                self.pending_list.append(path)
                self.task_queue.put(path)
                added_count += 1
        return added_count

    def start_processing(self):
        if not self.is_running and not self.task_queue.empty():
            self.is_running = True
            threading.Thread(target=self._process_queue, daemon=True).start()
            return True
        return False

    def get_queue_size(self):
        return self.task_queue.qsize()

    def _process_queue(self):
        total_items = self.task_queue.qsize()
        processed_count = 0

        while not self.task_queue.empty():
            song_path = self.task_queue.get()
            if song_path in self.pending_list:
                self.pending_list.remove(song_path)

            song_name = os.path.splitext(os.path.basename(song_path))[0]
            self.current_item = song_name
            processed_count += 1

            if self.on_item_start:
                self.on_item_start(song_name, processed_count, total_items)

            try:
                output_folder = self._run_demucs(song_path, song_name)
                if self.on_item_finish:
                    self.on_item_finish(song_name, output_folder)
            except Exception as e:
                print(f"Error procesando {song_name}: {e}")
                if self.on_error:
                    self.on_error(song_name, str(e))
            finally:
                self.task_queue.task_done()

        self.is_running = False
        self.current_item = None
        if self.on_queue_finish:
            self.on_queue_finish()

    def _run_demucs(self, file_path, song_name):
        ffmpeg_dir = self.config.get("ffmpeg_path", "")
        model = self.config.get("model", "htdemucs")
        device = self.config.get("device", "cpu")
        base_output = self.config.get("output_dir", os.path.abspath("monosync"))

        # Pre-check CUDA support in PyTorch
        if device == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    device = "cpu"
            except Exception:
                device = "cpu"

        env = os.environ.copy()
        if ffmpeg_dir:
            env["PATH"] = ffmpeg_dir + os.pathsep + env["PATH"]

        temp_out = os.path.join(base_output, "_temp_demucs")
        os.makedirs(temp_out, exist_ok=True)

        cmd = [
            sys.executable, "-m", "demucs.separate",
            "-n", model,
            "-d", device,
            file_path,
            "-o", temp_out
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        # Fallback to CPU if CUDA fails at runtime
        if result.returncode != 0 and ("CUDA" in result.stderr or "cuda" in result.stderr or "AssertionError" in result.stderr) and device == "cuda":
            print("⚠️ CUDA no habilitado en PyTorch. Cambiando automáticamente a CPU...")
            cmd[cmd.index("cuda")] = "cpu"
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            err_msg = result.stderr if result.stderr else result.stdout
            raise RuntimeError(f"Error en Demucs: {err_msg}")

        demucs_generated_dir = os.path.join(temp_out, model, song_name)
        final_song_dir = os.path.join(base_output, song_name)
        os.makedirs(final_song_dir, exist_ok=True)

        if os.path.exists(demucs_generated_dir):
            for file in os.listdir(demucs_generated_dir):
                src_file = os.path.join(demucs_generated_dir, file)
                dst_file = os.path.join(final_song_dir, file)
                shutil.copy2(src_file, dst_file)

        try:
            shutil.rmtree(temp_out, ignore_errors=True)
        except Exception:
            pass

        return final_song_dir
