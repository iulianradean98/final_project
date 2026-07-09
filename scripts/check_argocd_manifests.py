from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


REPO_URL = "https://github.com/iulianradean98/final_project.git"
VALID_APPLICATION_TARGETS = {
    "argocd/applications": "main",
    "k8s/overlays/dev": "release/dev",
    "k8s/overlays/production-blue": "release/production-blue",
    "k8s/overlays/production-green": "release/production-green",
}


def expand_manifest_paths(raw_paths: list[str]) -> list[Path]:
    paths: list[Path] = []

    for raw_path in raw_paths:
        if any(pattern in raw_path for pattern in ("*", "?", "[")):
            matches = sorted(Path().glob(raw_path))
            if not matches:
                print(f"No ArgoCD manifest files matched pattern: {raw_path}")
                raise SystemExit(2)
            paths.extend(matches)
        else:
            paths.append(Path(raw_path))

    return paths


def load_documents(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as manifest_file:
        return [
            document
            for document in yaml.safe_load_all(manifest_file)
            if isinstance(document, dict)
        ]


def resource_name(resource: dict[str, Any]) -> str:
    return str((resource.get("metadata") or {}).get("name", "<unnamed>"))


def validate_application(path: Path, resource: dict[str, Any]) -> list[str]:
    errors = []
    name = resource_name(resource)
    spec = resource.get("spec") or {}
    source = spec.get("source") or {}
    destination = spec.get("destination") or {}

    if source.get("repoURL") != REPO_URL:
        errors.append(f"{path}: Application/{name} must use repoURL {REPO_URL}.")

    source_path = source.get("path")
    expected_target_revision = VALID_APPLICATION_TARGETS.get(source_path)
    if expected_target_revision is None:
        errors.append(f"{path}: Application/{name} uses unexpected source path {source_path}.")
    elif not Path(source_path).exists():
        errors.append(f"{path}: Application/{name} source path does not exist: {source_path}.")
    elif source.get("targetRevision") != expected_target_revision:
        errors.append(
            f"{path}: Application/{name} must target {expected_target_revision} "
            f"for source path {source_path}."
        )

    if destination.get("server") != "https://kubernetes.default.svc":
        errors.append(f"{path}: Application/{name} must target the in-cluster Kubernetes API.")

    if not destination.get("namespace"):
        errors.append(f"{path}: Application/{name} must define a destination namespace.")

    return errors


def validate_project(path: Path, resource: dict[str, Any]) -> list[str]:
    errors = []
    name = resource_name(resource)
    spec = resource.get("spec") or {}

    if REPO_URL not in (spec.get("sourceRepos") or []):
        errors.append(f"{path}: AppProject/{name} must allow source repo {REPO_URL}.")

    allowed_namespaces = {
        destination.get("namespace")
        for destination in spec.get("destinations", [])
        if isinstance(destination, dict)
    }
    required_namespaces = {
        "argocd",
        "recipe-rescue-dev",
        "recipe-rescue-blue",
        "recipe-rescue-green",
    }
    missing_namespaces = sorted(required_namespaces - allowed_namespaces)
    if missing_namespaces:
        errors.append(
            f"{path}: AppProject/{name} is missing destinations: {', '.join(missing_namespaces)}."
        )

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_argocd_manifests.py <manifest.yaml> [...]")
        return 2

    errors = []
    for manifest_path in expand_manifest_paths(sys.argv[1:]):
        for resource in load_documents(manifest_path):
            api_version = resource.get("apiVersion")
            kind = resource.get("kind")

            if api_version != "argoproj.io/v1alpha1":
                errors.append(f"{manifest_path}: {kind} must use apiVersion argoproj.io/v1alpha1.")
                continue

            if kind == "Application":
                errors.extend(validate_application(manifest_path, resource))
            elif kind == "AppProject":
                errors.extend(validate_project(manifest_path, resource))
            else:
                errors.append(f"{manifest_path}: unsupported ArgoCD kind {kind}.")

    if errors:
        print("ArgoCD manifest checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ArgoCD manifest checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
