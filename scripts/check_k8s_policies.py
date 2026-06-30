from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


WORKLOAD_KINDS = {"Deployment", "StatefulSet"}


def load_documents(path: Path) -> list[dict[str, Any]]:
    raw_content = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            content = raw_content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError(
            "utf-8",
            raw_content,
            0,
            1,
            "manifest file must be UTF-8 or UTF-16 text",
        )

    return [
        document
        for document in yaml.safe_load_all(content)
        if isinstance(document, dict)
    ]


def metadata_name(resource: dict[str, Any]) -> str:
    metadata = resource.get("metadata") or {}
    return str(metadata.get("name", "<unnamed>"))


def pod_template(resource: dict[str, Any]) -> dict[str, Any]:
    return resource.get("spec", {}).get("template", {})


def containers(resource: dict[str, Any]) -> list[dict[str, Any]]:
    spec = pod_template(resource).get("spec") or {}
    return spec.get("containers") or []


def pod_labels(resource: dict[str, Any]) -> dict[str, str]:
    metadata = pod_template(resource).get("metadata") or {}
    return metadata.get("labels") or {}


def service_selector_matches(selector: dict[str, str], labels: dict[str, str]) -> bool:
    return all(labels.get(key) == value for key, value in selector.items())


def validate_no_rendered_secrets(resources: list[dict[str, Any]]) -> list[str]:
    errors = []

    for resource in resources:
        if resource.get("kind") == "Secret":
            errors.append(
                f"Secret/{metadata_name(resource)} must not be rendered from k8s/base. "
                "Commit only secret examples and create real secrets outside Git."
            )

    return errors


def validate_workload_containers(resources: list[dict[str, Any]]) -> list[str]:
    errors = []

    for resource in resources:
        kind = resource.get("kind")
        if kind not in WORKLOAD_KINDS:
            continue

        name = metadata_name(resource)
        for container in containers(resource):
            container_name = container.get("name", "<unnamed>")
            location = f"{kind}/{name} container/{container_name}"

            if "readinessProbe" not in container:
                errors.append(f"{location} must define a readinessProbe.")

            if "livenessProbe" not in container:
                errors.append(f"{location} must define a livenessProbe.")

            resources_config = container.get("resources") or {}
            requests = resources_config.get("requests") or {}
            limits = resources_config.get("limits") or {}

            for key in ("cpu", "memory"):
                if key not in requests:
                    errors.append(f"{location} must define resources.requests.{key}.")
                if key not in limits:
                    errors.append(f"{location} must define resources.limits.{key}.")

            security_context = container.get("securityContext") or {}
            if security_context.get("privileged") is True:
                errors.append(f"{location} must not run as privileged.")

            if security_context.get("allowPrivilegeEscalation") is True:
                errors.append(f"{location} must not allow privilege escalation.")

    return errors


def validate_service_selectors(resources: list[dict[str, Any]]) -> list[str]:
    errors = []
    workload_labels = [
        pod_labels(resource)
        for resource in resources
        if resource.get("kind") in WORKLOAD_KINDS
    ]

    for resource in resources:
        if resource.get("kind") != "Service":
            continue

        name = metadata_name(resource)
        selector = resource.get("spec", {}).get("selector") or {}
        if not selector:
            errors.append(f"Service/{name} must define a selector.")
            continue

        if not any(service_selector_matches(selector, labels) for labels in workload_labels):
            errors.append(f"Service/{name} selector does not match any workload pod labels.")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_k8s_policies.py <rendered-manifests.yaml>")
        return 2

    manifest_path = Path(sys.argv[1])
    resources = load_documents(manifest_path)
    errors = [
        *validate_no_rendered_secrets(resources),
        *validate_workload_containers(resources),
        *validate_service_selectors(resources),
    ]

    if errors:
        print("Kubernetes policy checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Kubernetes policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
