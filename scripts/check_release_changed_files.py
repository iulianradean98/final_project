from __future__ import annotations

import subprocess
from pathlib import Path


ALLOWED_FILES = {
    Path("k8s/overlays/dev/kustomization.yaml"),
    Path("k8s/overlays/production-blue/kustomization.yaml"),
    Path("k8s/overlays/production-green/kustomization.yaml"),
}


def changed_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/release...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [Path(path) for path in result.stdout.splitlines()]


def main() -> int:
    paths = changed_files()
    errors = []

    if not paths:
        errors.append("Release PR must contain a deployment promotion change.")

    unexpected_files = sorted(path for path in paths if path not in ALLOWED_FILES)
    for path in unexpected_files:
        errors.append(f"{path} is not allowed in a release promotion PR.")

    promoted_files = sorted(path for path in paths if path in ALLOWED_FILES)
    if len(promoted_files) != 1:
        errors.append(
            "Release PR must change exactly one overlay kustomization.yaml file."
        )

    if errors:
        print("Release changed-files check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Release changed-files check passed: {promoted_files[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
