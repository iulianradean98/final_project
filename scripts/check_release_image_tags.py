from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


IMAGE_NAMES = {
    "iulian98/recipe-rescue-backend",
    "iulian98/recipe-rescue-frontend",
}
IMAGE_TAG_PATTERN = re.compile(r"^sha-[0-9a-f]{12}$")


def changed_kustomization_files() -> list[Path]:
    base_ref = "origin/release"
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", "k8s/overlays"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [
        Path(path)
        for path in result.stdout.splitlines()
        if path.endswith("kustomization.yaml")
    ]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        content = yaml.safe_load(file) or {}

    if not isinstance(content, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")

    return content


def validate_image_tags(path: Path) -> list[str]:
    errors = []
    content = load_yaml(path)
    images = content.get("images") or []
    image_tags = {
        image.get("name"): image.get("newTag")
        for image in images
        if isinstance(image, dict)
    }

    missing_images = sorted(IMAGE_NAMES - set(image_tags))
    for image_name in missing_images:
        errors.append(f"{path}: missing pinned image entry for {image_name}.")

    for image_name in sorted(IMAGE_NAMES):
        tag = image_tags.get(image_name)
        if tag is None:
            continue

        if tag == "latest":
            errors.append(f"{path}: {image_name} must not use latest in release.")
        elif not IMAGE_TAG_PATTERN.fullmatch(str(tag)):
            errors.append(
                f"{path}: {image_name} tag must match sha-<12 lowercase hex chars>, got {tag}."
            )

    promoted_tags = {image_tags.get(image_name) for image_name in IMAGE_NAMES}
    if None not in promoted_tags and len(promoted_tags) > 1:
        errors.append(f"{path}: backend and frontend must use the same release image tag.")

    return errors


def main() -> int:
    paths = changed_kustomization_files()
    if not paths:
        print("Release image tag checks failed:")
        print("- Release PRs must change at least one overlay kustomization.yaml file.")
        return 1

    errors = []
    for path in paths:
        errors.extend(validate_image_tags(path))

    if errors:
        print("Release image tag checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release image tag checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
