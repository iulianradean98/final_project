from __future__ import annotations

import sys
from pathlib import Path


IMAGE_NAMES = {
    "iulian98/recipe-rescue-backend",
    "iulian98/recipe-rescue-frontend",
}


def remove_top_level_images_block(content: str) -> str:
    lines = content.splitlines()
    cleaned_lines: list[str] = []
    skipping_images = False

    for line in lines:
        is_top_level_key = line and not line.startswith((" ", "\t")) and line.rstrip().endswith(":")

        if line == "images:":
            skipping_images = True
            continue

        if skipping_images and is_top_level_key:
            skipping_images = False

        if not skipping_images:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).rstrip()


def render_images_block(tag: str) -> str:
    lines = ["images:"]
    for image_name in sorted(IMAGE_NAMES):
        lines.extend(
            [
                f"  - name: {image_name}",
                f"    newTag: {tag}",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/set_kustomize_images.py <kustomization.yaml> <image-tag>")
        return 2

    kustomization_path = Path(sys.argv[1])
    image_tag = sys.argv[2]
    original_content = kustomization_path.read_text(encoding="utf-8")
    updated_content = remove_top_level_images_block(original_content)
    updated_content = f"{updated_content}\n{render_images_block(image_tag)}\n"
    kustomization_path.write_text(updated_content, encoding="utf-8")

    print(f"Updated {kustomization_path} to image tag {image_tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
