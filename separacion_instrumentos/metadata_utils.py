import os
import io

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

try:
    import mutagen
    from mutagen.id3 import ID3, APIC
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def get_song_metadata(file_path):
    """
    Extracts artist, title, and cover image from audio file metadata or directory.
    Optimized for fast folder indexing.
    """
    filename = os.path.basename(file_path)
    base_title = os.path.splitext(filename)[0]
    artist = "Artista Desconocido"
    title = base_title
    cover_img = None

    # 1. Fast parse from filename "Artist - Title"
    if " - " in base_title:
        parts = base_title.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        # Fallback to parent directory name if directory is "Artist Name"
        parent_dir = os.path.basename(os.path.dirname(file_path))
        if parent_dir and len(parent_dir) > 1 and parent_dir.lower() not in ["music", "musica", "audio", "downloads", "monosync"]:
            artist = parent_dir

    # 2. Fast tag extraction if mutagen is available
    if HAS_MUTAGEN and os.path.exists(file_path):
        try:
            meta = mutagen.File(file_path, easy=True)
            if meta:
                if "artist" in meta and meta["artist"]:
                    artist = str(meta["artist"][0])
                if "title" in meta and meta["title"]:
                    title = str(meta["title"][0])
        except Exception:
            pass

    return {
        "artist": artist if artist else "Artista Desconocido",
        "title": title if title else base_title,
        "cover_image": cover_img
    }

def get_cover_image(file_path):
    """Extracts cover image on-demand when selecting a song."""
    if not HAS_MUTAGEN or not HAS_PIL or not os.path.exists(file_path):
        return _find_folder_cover(file_path)

    try:
        meta = mutagen.File(file_path)
        if meta:
            cover_data = None
            if isinstance(meta, ID3) or hasattr(meta, "tags") and isinstance(meta.tags, ID3):
                for tag in meta.tags.values():
                    if isinstance(tag, APIC):
                        cover_data = tag.data
                        break
            elif isinstance(meta, FLAC) and meta.pictures:
                cover_data = meta.pictures[0].data
            elif isinstance(meta, MP4) and "covr" in meta:
                cover_data = bytes(meta["covr"][0])

            if cover_data:
                return Image.open(io.BytesIO(cover_data))
    except Exception:
        pass

    return _find_folder_cover(file_path)

def _find_folder_cover(file_path):
    if not HAS_PIL:
        return None
    song_dir = os.path.dirname(file_path)
    if os.path.exists(song_dir):
        try:
            files = os.listdir(song_dir)
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    if any(k in file.lower() for k in ["cover", "folder", "front", "art", "album"]) or len(files) < 10:
                        return Image.open(os.path.join(song_dir, file))
        except Exception:
            pass
    return None
