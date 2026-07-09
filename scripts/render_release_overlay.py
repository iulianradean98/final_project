from __future__ import annotations

import subprocess
from pathlib import Path


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


def main() -> int:
    paths = changed_kustomization_files()
    if len(paths) != 1:
        print("Release overlay render failed:")
        print("- Release PR must change exactly one overlay kustomization.yaml file.")
        return 1

    overlay_dir = paths[0].parent
    result = subprocess.run(
        ["kubectl", "kustomize", str(overlay_dir)],
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print("Release overlay render failed:")
        print(result.stderr)
        return result.returncode

    output_path = Path("rendered-release-overlay.yaml")
    output_path.write_text(result.stdout, encoding="utf-8")
    print(f"Rendered {overlay_dir} to {output_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
