"""
Generate all Tauri icon sizes from a programmatically drawn compass icon.
Dark background (#1a1a2e), white/gold needle, gold ring.
"""
import math
import struct
import zlib
from pathlib import Path
from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).parent.parent / "src-tauri" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# ── Colours ────────────────────────────────────────────────────────────────────
BG       = (18,  18,  30, 255)   # near-black navy
RING     = (212, 175,  55, 255)  # gold
NEEDLE_N = (255, 255, 255, 255)  # white  (north)
NEEDLE_S = (160,  60,  60, 255)  # muted red (south)
CARDINAL = (212, 175,  55, 200)  # gold, semi-transparent


def draw_compass(size: int) -> Image.Image:
    scale = 4                        # supersample factor
    S = size * scale
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = S / 2, S / 2
    r = S / 2

    # ── Background circle ──────────────────────────────────────────────────────
    margin = S * 0.04
    d.ellipse([margin, margin, S - margin, S - margin], fill=BG)

    # ── Outer gold ring ────────────────────────────────────────────────────────
    ring_w = max(2, S * 0.030)
    ro = r - margin
    ri = ro - ring_w
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], outline=RING, width=int(ring_w))

    # ── Inner thin guide circle ────────────────────────────────────────────────
    inner_r = S * 0.30
    guide_w = max(1, S * 0.008)
    d.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        outline=(*RING[:3], 80), width=int(guide_w),
    )

    # ── Cardinal tick marks ────────────────────────────────────────────────────
    tick_outer = ro - ring_w * 0.5
    tick_inner_major = tick_outer - S * 0.08
    tick_inner_minor = tick_outer - S * 0.04
    tick_w_major = max(1, int(S * 0.018))
    tick_w_minor = max(1, int(S * 0.010))

    for i in range(16):
        angle = math.radians(i * 22.5 - 90)
        is_cardinal = (i % 4 == 0)
        is_ordinal  = (i % 2 == 0)
        t_inner = tick_inner_major if is_cardinal else (
                  tick_inner_minor if is_ordinal  else tick_outer - S * 0.025)
        w = tick_w_major if is_cardinal else tick_w_minor
        x1 = cx + tick_outer * math.cos(angle)
        y1 = cy + tick_outer * math.sin(angle)
        x2 = cx + t_inner   * math.cos(angle)
        y2 = cy + t_inner   * math.sin(angle)
        d.line([x1, y1, x2, y2], fill=CARDINAL, width=w)

    # ── Compass needle (diamond shape) ─────────────────────────────────────────
    needle_len  = S * 0.34   # tip distance from centre
    needle_back = S * 0.22   # back spur distance
    needle_w    = S * 0.060  # half-width at widest

    def needle_poly(tip_angle):
        """Return a diamond needle polygon pointing at tip_angle (radians)."""
        perp = tip_angle + math.pi / 2
        tip  = (cx + needle_len  * math.cos(tip_angle),
                cy + needle_len  * math.sin(tip_angle))
        back = (cx + needle_back * math.cos(tip_angle + math.pi),
                cy + needle_back * math.sin(tip_angle + math.pi))
        left  = (cx + needle_w * math.cos(perp), cy + needle_w * math.sin(perp))
        right = (cx - needle_w * math.cos(perp), cy - needle_w * math.sin(perp))
        return [tip, left, back, right]

    north_angle = math.radians(-90)   # up
    south_angle = north_angle + math.pi

    d.polygon(needle_poly(north_angle), fill=NEEDLE_N)
    d.polygon(needle_poly(south_angle), fill=NEEDLE_S)

    # Thin dark divider line between the two halves
    divider_w = max(1, int(S * 0.012))
    perp = north_angle + math.pi / 2
    d.line(
        [cx + needle_w * math.cos(perp),  cy + needle_w * math.sin(perp),
         cx - needle_w * math.cos(perp),  cy - needle_w * math.sin(perp)],
        fill=(0, 0, 0, 180), width=divider_w,
    )

    # ── Centre dot ─────────────────────────────────────────────────────────────
    dot_r = S * 0.045
    d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=RING)
    inner_dot = dot_r * 0.45
    d.ellipse(
        [cx - inner_dot, cy - inner_dot, cx + inner_dot, cy + inner_dot],
        fill=BG,
    )

    # ── Downsample ─────────────────────────────────────────────────────────────
    return img.resize((size, size), Image.LANCZOS)


# ── PNG helper ─────────────────────────────────────────────────────────────────

def save_png(img: Image.Image, path: Path):
    img.save(str(path), "PNG")
    print(f"  wrote {path.name}  ({img.size[0]}x{img.size[1]})")


# ── ICO builder (multi-size) ───────────────────────────────────────────────────

def build_ico(images: dict[int, Image.Image], path: Path):
    """Write a proper .ico with multiple embedded PNG frames."""
    import io
    sizes = sorted(images.keys())
    frames = []
    for s in sizes:
        buf = io.BytesIO()
        images[s].save(buf, "PNG")
        frames.append(buf.getvalue())

    # ICO header
    n = len(sizes)
    header = struct.pack("<HHH", 0, 1, n)   # reserved, type=1 (ICO), count
    dir_offset = 6 + n * 16
    directory = b""
    data_offset = dir_offset
    for i, s in enumerate(sizes):
        data = frames[i]
        w = s if s < 256 else 0
        h = s if s < 256 else 0
        directory += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), data_offset)
        data_offset += len(data)

    with open(path, "wb") as f:
        f.write(header + directory + b"".join(frames))
    print(f"  wrote {path.name}")


# ── ICNS builder ───────────────────────────────────────────────────────────────

ICNS_TYPES = {
    16:   b"icp4",
    32:   b"icp5",
    64:   b"icp6",
    128:  b"ic07",
    256:  b"ic08",
    512:  b"ic09",
    1024: b"ic10",
}

def build_icns(images: dict[int, Image.Image], path: Path):
    import io
    chunks = b""
    for size, tag in ICNS_TYPES.items():
        if size not in images:
            continue
        buf = io.BytesIO()
        images[size].save(buf, "PNG")
        data = buf.getvalue()
        chunk_len = 8 + len(data)
        chunks += tag + struct.pack(">I", chunk_len) + data

    total = 8 + len(chunks)
    with open(path, "wb") as f:
        f.write(b"icns" + struct.pack(">I", total) + chunks)
    print(f"  wrote {path.name}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Generating compass icons…")

    # All sizes needed
    png_sizes = {
        32, 128, 256,        # standard Tauri PNGs
        107, 142, 150, 284,  # Windows Square logos
        30, 310, 44, 71, 89, # more Windows logos
        16, 48, 64, 512, 1024,  # for ICO / ICNS
    }

    cache: dict[int, Image.Image] = {}
    for s in sorted(png_sizes):
        cache[s] = draw_compass(s)

    # ── Named PNGs Tauri expects ───────────────────────────────────────────────
    save_png(cache[32],   ICONS_DIR / "32x32.png")
    save_png(cache[128],  ICONS_DIR / "128x128.png")

    # 128x128@2x.png = 256px content
    save_png(cache[256],  ICONS_DIR / "128x128@2x.png")

    # icon.png — high-res master (512px)
    save_png(cache[512],  ICONS_DIR / "icon.png")

    # Windows Square logos
    for s, name in [
        (30,  "Square30x30Logo.png"),
        (44,  "Square44x44Logo.png"),
        (71,  "Square71x71Logo.png"),
        (89,  "Square89x89Logo.png"),
        (107, "Square107x107Logo.png"),
        (142, "Square142x142Logo.png"),
        (150, "Square150x150Logo.png"),
        (284, "Square284x284Logo.png"),
        (310, "Square310x310Logo.png"),
        (50,  "StoreLogo.png"),
    ]:
        img = cache.get(s) or draw_compass(s)
        save_png(img, ICONS_DIR / name)

    # ── ICO (16, 32, 48, 64, 128, 256) ────────────────────────────────────────
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_images = {s: cache.get(s) or draw_compass(s) for s in ico_sizes}
    build_ico(ico_images, ICONS_DIR / "icon.ico")

    # ── ICNS ──────────────────────────────────────────────────────────────────
    icns_images = {s: cache.get(s) or draw_compass(s) for s in ICNS_TYPES}
    build_icns(icns_images, ICONS_DIR / "icon.icns")

    print("Done.")


if __name__ == "__main__":
    main()
