"""
Create iPad 4:3 tablet variants from existing story images.

Example:
    python -m scripts.outpaint_tablet_images --input-dir frontend/public/images/pages/level1/lesson01
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ai.image_generator import outpaint_existing_image_for_tablet
from shared.settings import TABLET_IMAGE_SUFFIX


SUPPORTED_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}


def tablet_path_for(image_path: Path, *, output_dir: Path | None, input_dir: Path) -> Path:
    target_name = f"{image_path.stem}{TABLET_IMAGE_SUFFIX}{image_path.suffix}"
    if output_dir is None:
        return image_path.with_name(target_name)
    return output_dir / image_path.relative_to(input_dir).with_name(target_name)


def collect_images(input_dir: Path, *, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    images = []
    for path in sorted(input_dir.glob(pattern)):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.stem.endswith(TABLET_IMAGE_SUFFIX):
            continue
        images.append(path)
    return images


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Outpaint existing story images into iPad 4:3 tablet variants."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Folder containing existing p01.webp-style story images.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output folder. Defaults to writing beside each source image.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only process images directly inside --input-dir.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate tablet files even if they already exist.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N images. Useful for a smoke test.",
    )
    parser.add_argument(
        "--prompt",
        help="Optional extra prompt for the outpainted background.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned outputs without calling ComfyUI.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input folder not found: {input_dir}")

    images = collect_images(input_dir, recursive=not args.no_recursive)
    if args.limit is not None:
        images = images[: max(0, args.limit)]

    if not images:
        print("No source images found.")
        return

    print(f"Found {len(images)} source image(s).")
    for index, image_path in enumerate(images, start=1):
        target_path = tablet_path_for(image_path, output_dir=output_dir, input_dir=input_dir)
        if target_path.exists() and not args.overwrite:
            print(f"[{index}/{len(images)}] skip existing: {target_path}")
            continue

        print(f"[{index}/{len(images)}] {image_path} -> {target_path}")
        if args.dry_run:
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        outpaint_existing_image_for_tablet(
            str(image_path),
            output_path=str(target_path),
            prompt=args.prompt,
        )

    print("Done.")


if __name__ == "__main__":
    main()
