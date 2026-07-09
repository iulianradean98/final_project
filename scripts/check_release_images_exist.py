from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml


IMAGE_NAMES = {
    "iulian98/recipe-rescue-backend",
    "iulian98/recipe-rescue-frontend",
}


def changed_kustomization_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/release...HEAD", "--", "k8s/overlays"],
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


def image_tags(path: Path) -> dict[str, str]:
    images = load_yaml(path).get("images") or []
    return {
        str(image.get("name")): str(image.get("newTag"))
        for image in images
        if isinstance(image, dict) and image.get("name") and image.get("newTag")
    }


def docker_image_exists(image: str, tag: str) -> bool:
    result = subprocess.run(
        ["docker", "manifest", "inspect", f"{image}:{tag}"],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def main() -> int:
    paths = changed_kustomization_files()
    errors = []

    for path in paths:
        tags = image_tags(path)
        for image in sorted(IMAGE_NAMES):
            tag = tags.get(image)
            if not tag:
                errors.append(f"{path}: missing tag for {image}.")
                continue

            if not docker_image_exists(image, tag):
                errors.append(f"Docker image does not exist or is not public: {image}:{tag}.")

    if errors:
        print("Release Docker image existence check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release Docker image existence check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
