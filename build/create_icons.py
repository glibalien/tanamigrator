#!/usr/bin/env python3
"""Generate application icons for all platforms."""

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image, ImageDraw, ImageFont


def create_icon_image(size: int) -> Image.Image:
    """Create the icon image at the specified size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    padding = size // 16
    radius = size // 5
    bg_color = (66, 133, 244)
    accent_color = (138, 43, 226)

    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=radius,
        fill=bg_color
    )

    center_y = size // 2
    font_size = size // 3

    try:
        for font_name in ['Arial Bold', 'Helvetica Bold', 'DejaVuSans-Bold']:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except (OSError, IOError):
                continue
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    t_x = size // 5
    draw.text((t_x, center_y - font_size // 2), "T", fill='white', font=font, anchor='lm')

    arrow_x = size // 2
    arrow_size = size // 8
    arrow_y = center_y

    draw.line(
        [(arrow_x - arrow_size, arrow_y), (arrow_x + arrow_size, arrow_y)],
        fill='white', width=max(2, size // 32)
    )
    draw.polygon([
        (arrow_x + arrow_size, arrow_y),
        (arrow_x + arrow_size // 2, arrow_y - arrow_size // 2),
        (arrow_x + arrow_size // 2, arrow_y + arrow_size // 2)
    ], fill='white')

    o_x = size - size // 5
    draw.text((o_x, center_y - font_size // 2), "O", fill=accent_color, font=font, anchor='rm')

    return img


def create_ico(png_path: Path, ico_path: Path):
    """Create Windows .ico file."""
    img = Image.open(png_path)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = [img.resize(size, Image.Resampling.LANCZOS) for size in sizes]
    images[0].save(ico_path, format='ICO', sizes=sizes, append_images=images[1:])
    print(f"Created: {ico_path}")


def create_icns(png_path: Path, icns_path: Path):
    """Create macOS .icns file."""
    iconset_dir = png_path.parent / "icon.iconset"
    iconset_dir.mkdir(exist_ok=True)
    img = Image.open(png_path)

    icon_sizes = [
        (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
    ]

    for size, filename in icon_sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / filename, 'PNG')

    try:
        subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)],
                      check=True, capture_output=True)
        print(f"Created: {icns_path}")
        for f in iconset_dir.iterdir():
            f.unlink()
        iconset_dir.rmdir()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Note: iconutil not available, iconset at: {iconset_dir}")


def main():
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets"
    assets_dir.mkdir(exist_ok=True)

    print("Generating icons...")
    png_path = assets_dir / "icon.png"
    icon_img = create_icon_image(1024)
    icon_img.save(png_path, 'PNG')
    print(f"Created: {png_path}")

    create_ico(png_path, assets_dir / "icon.ico")
    create_icns(png_path, assets_dir / "icon.icns")
    print("Done!")


if __name__ == "__main__":
    main()
