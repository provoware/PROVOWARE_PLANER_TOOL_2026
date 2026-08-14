from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "TRANSPORT_PROFILE_CONTRACT.json"
MANIFEST_PATH = ROOT / "REPOSITORY_MANIFEST.json"


class TransportProfileError(RuntimeError):
    pass


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "contracts" / "TRANSPORT_PROFILE_CONTRACT.json").read_text(encoding="utf-8"))


def repository_paths(root: Path = ROOT) -> tuple[str, ...]:
    data = json.loads((root / "REPOSITORY_MANIFEST.json").read_text(encoding="utf-8"))
    paths = data.get("expected_paths") or data.get("files") or []
    return tuple(sorted(str(item) for item in paths))


def _rule_matches(path: str, rule: dict[str, Any]) -> bool:
    if path in set(rule.get("exclude_exact", [])):
        return False
    if path in set(rule.get("exact", [])):
        return True
    if any(path.startswith(prefix) for prefix in rule.get("prefixes", [])):
        return True
    if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule.get("globs", [])):
        return True
    return False


def matching_classes(path: str, contract: dict[str, Any]) -> tuple[str, ...]:
    found = {
        str(rule["class"])
        for rule in contract.get("classification_rules", [])
        if _rule_matches(path, rule)
    }
    return tuple(sorted(found))


def classify_path(path: str, contract: dict[str, Any]) -> str:
    classes = matching_classes(path, contract)
    if len(classes) != 1:
        if not classes:
            raise TransportProfileError(f"TRANSPORT-KLASSE-FEHLT: {path}")
        raise TransportProfileError(f"TRANSPORT-KLASSE-MEHRDEUTIG: {path}: {', '.join(classes)}")
    return classes[0]


def never_transport(path: str, contract: dict[str, Any]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in contract.get("never_transport_globs", []))


def validate_contract(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    contract = load_contract(root)
    declared_classes = set(contract.get("classes", []))
    profiles = contract.get("profiles", {})

    if contract.get("default_profile") not in profiles:
        errors.append("TRANSPORT-DEFAULT-PROFIL-FEHLT")

    for name, profile in profiles.items():
        unknown = set(profile.get("classes", [])) - declared_classes
        if unknown:
            errors.append(f"TRANSPORT-PROFIL-KLASSE-UNBEKANNT: {name}: {sorted(unknown)}")

    classified: dict[str, str] = {}
    for path in repository_paths(root):
        if never_transport(path, contract):
            errors.append(f"TRANSPORT-REPOSITORY-PFAD-VERBOTEN: {path}")
            continue
        try:
            classified[path] = classify_path(path, contract)
        except TransportProfileError as exc:
            errors.append(str(exc))

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_paths": len(repository_paths(root)),
        "classified_paths": len(classified),
        "class_counts": {
            name: sum(value == name for value in classified.values())
            for name in sorted(declared_classes)
        },
    }


def select_profile(profile_name: str, root: Path = ROOT) -> tuple[str, ...]:
    contract = load_contract(root)
    profiles = contract.get("profiles", {})
    if profile_name not in profiles:
        raise TransportProfileError(f"TRANSPORT-PROFIL-UNBEKANNT: {profile_name}")

    profile = profiles[profile_name]
    classes = set(profile.get("classes", []))
    include_exact = set(profile.get("include_exact", []))
    selected: list[str] = []

    for path in repository_paths(root):
        if never_transport(path, contract):
            continue
        path_class = classify_path(path, contract)
        if path_class in classes or path in include_exact:
            selected.append(path)

    return tuple(sorted(selected))


def profile_report(root: Path = ROOT) -> dict[str, Any]:
    contract = load_contract(root)
    result = validate_contract(root)
    profile_counts: dict[str, int] = {}
    if result["status"] == "PASS":
        for name in contract.get("profiles", {}):
            profile_counts[name] = len(select_profile(name, root))
    result["default_profile"] = contract.get("default_profile")
    result["profile_counts"] = profile_counts
    return result
