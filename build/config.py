from pathlib import Path
import base64

SITE_NAME = "Skinkpedia"
SITE_URL = "https://skinkpedia.online"
AUTHOR_NAME = "Farrukh Abdullah"
AUTHOR_URL = "/authors/farrukh-abdullah/"
DEFAULT_OG_IMAGE = "/assets/images/heroes/core-001-skink-overview-hero.webp"


def _materialize_encoded_heroes():
    """Restore staged binary hero assets from text-safe base64 fragments before the build copies public/ to dist/."""
    root = Path(__file__).resolve().parents[1]
    encoded = root / "data" / "media-encoded"
    output = root / "public" / "assets" / "images" / "heroes"
    if not encoded.exists():
        return
    output.mkdir(parents=True, exist_ok=True)
    for name in (
        "out-020-dibamus-irregularis-hero.webp",
        "out-021-scincella-verecunda-hero.webp",
    ):
        parts = sorted(encoded.glob(f"{name}.b64.*"))
        if not parts:
            continue
        payload = "".join(part.read_text(encoding="utf-8").strip() for part in parts)
        (output / name).write_bytes(base64.b64decode(payload, validate=True))


_materialize_encoded_heroes()
