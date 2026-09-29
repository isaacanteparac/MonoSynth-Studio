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

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]

def get_song_metadata(file_path):
    """
    Extracts artist, title, and cover image from audio file metadata or directory.
    Returns dict: {"artist": str, "title": str, "cover_image": PIL.Image or None}
    """
    filename = os.path.basename(file_path)
    base_title = os.path.splitext(filename)[0]
    artist = "Artista Desconocido"
    title = base_title
    cover_img = None

    if " - " in base_title:
        parts = base_title.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()

    if HAS_MUTAGEN and os.path.exists(file_path):
        try:
            meta = mutagen.File(file_path)
            if meta:
                if "TPE1" in meta:
                    artist = str(meta["TPE1"].text[0])
                elif "artist" in meta:
                    artist = str(meta["artist"][0])
                elif "©ART" in meta:
                    artist = str(meta["©ART"][0])

                if "TIT2" in meta:
                    title = str(meta["TIT2"].text[0])
                elif "title" in meta:
                    title = str(meta["title"][0])
                elif "©nam" in meta:
                    title = str(meta["©nam"][0])

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

                if cover_data and HAS_PIL:
                    try:
                        cover_img = Image.open(io.BytesIO(cover_data))
                    except Exception:
                        cover_img = None
        except Exception as e:
            print(f"Error leyendo metadatos de {filename}: {e}")

    if cover_img is None and HAS_PIL:
        song_dir = os.path.dirname(file_path)
        if os.path.exists(song_dir):
            for file in os.listdir(song_dir):
                name_lower = file.lower()
                ext = os.path.splitext(name_lower)[1]
                if ext in IMAGE_EXTENSIONS:
                    if any(k in name_lower for k in ["cover", "folder", "front", "art", "album"]) or len(os.listdir(song_dir)) < 10:
                        try:
                            img_path = os.path.join(song_dir, file)
                            cover_img = Image.open(img_path)
                            break
                        except Exception:
                            pass

    return {
        "artist": artist if artist else "Artista Desconocido",
        "title": title if title else base_title,
        "cover_image": cover_img
    }
