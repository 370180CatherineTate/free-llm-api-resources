#!/usr/bin/env python3
"""Validation script for data.py entries.

Checks that all provider entries in data.py conform to the expected schema
and contain valid values before the README is generated or a PR is merged.
"""

import sys
from typing import Any

# Import the providers list from data.py
from data import providers

# Required top-level keys for every provider entry
REQUIRED_PROVIDER_KEYS = {"name", "url", "models"}

# Optional but validated keys
OPTIONAL_PROVIDER_KEYS = {
    "notes",
    "requires_account",
    "rate_limits",
    "openai_compatible",
    "free_tier",
}

# Required keys for each model entry
REQUIRED_MODEL_KEYS = {"name"}

# Optional model-level keys
OPTIONAL_MODEL_KEYS = {
    "notes",
    "rate_limits",
    "context_window",
    "modalities",
}

ALL_VALID_PROVIDER_KEYS = REQUIRED_PROVIDER_KEYS | OPTIONAL_PROVIDER_KEYS
ALL_VALID_MODEL_KEYS = REQUIRED_MODEL_KEYS | OPTIONAL_MODEL_KEYS


def validate_url(url: str) -> bool:
    """Return True if the url looks like a valid http/https URL."""
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def validate_rate_limit(rate_limit: Any, context: str) -> list[str]:
    """Validate a rate_limits value and return a list of error messages."""
    errors: list[str] = []
    if not isinstance(rate_limit, (str, dict, list)):
        errors.append(
            f"{context}: 'rate_limits' must be a string, dict, or list, "
            f"got {type(rate_limit).__name__}"
        )
    return errors


def validate_model(model: Any, provider_name: str, index: int) -> list[str]:
    """Validate a single model entry and return a list of error messages."""
    errors: list[str] = []
    ctx = f"Provider '{provider_name}' model[{index}]"

    if not isinstance(model, dict):
        errors.append(f"{ctx}: expected a dict, got {type(model).__name__}")
        return errors

    # Check for required keys
    for key in REQUIRED_MODEL_KEYS:
        if key not in model:
            errors.append(f"{ctx}: missing required key '{key}'")

    # Check for unexpected keys
    unknown = set(model.keys()) - ALL_VALID_MODEL_KEYS
    if unknown:
        errors.append(f"{ctx}: unknown keys {sorted(unknown)}")

    # Validate name
    if "name" in model and not isinstance(model["name"], str):
        errors.append(f"{ctx}: 'name' must be a string")

    # Validate rate_limits if present
    if "rate_limits" in model:
        errors.extend(validate_rate_limit(model["rate_limits"], ctx))

    # Validate context_window if present
    if "context_window" in model:
        if not isinstance(model["context_window"], int) or model["context_window"] <= 0:
            errors.append(f"{ctx}: 'context_window' must be a positive integer")

    return errors


def validate_provider(provider: Any, index: int) -> list[str]:
    """Validate a single provider entry and return a list of error messages."""
    errors: list[str] = []
    ctx = f"Provider[{index}]"

    if not isinstance(provider, dict):
        errors.append(f"{ctx}: expected a dict, got {type(provider).__name__}")
        return errors

    name = provider.get("name", f"<unnamed provider at index {index}>")
    ctx = f"Provider '{name}'"

    # Check for required keys
    for key in REQUIRED_PROVIDER_KEYS:
        if key not in provider:
            errors.append(f"{ctx}: missing required key '{key}'")

    # Check for unexpected keys
    unknown = set(provider.keys()) - ALL_VALID_PROVIDER_KEYS
    if unknown:
        errors.append(f"{ctx}: unknown keys {sorted(unknown)}")

    # Validate URL
    if "url" in provider and not validate_url(provider["url"]):
        errors.append(f"{ctx}: 'url' must be a valid http/https URL, got '{provider['url']}'")

    # Validate models list
    if "models" in provider:
        if not isinstance(provider["models"], list):
            errors.append(f"{ctx}: 'models' must be a list")
        elif len(provider["models"]) == 0:
            errors.append(f"{ctx}: 'models' list must not be empty")
        else:
            for i, model in enumerate(provider["models"]):
                errors.extend(validate_model(model, name, i))

    # Validate boolean fields
    for bool_key in ("requires_account", "openai_compatible", "free_tier"):
        if bool_key in provider and not isinstance(provider[bool_key], bool):
            errors.append(f"{ctx}: '{bool_key}' must be a boolean")

    return errors


def validate_all(provider_list: list) -> list[str]:
    """Validate every provider in the list and return all errors found."""
    all_errors: list[str] = []

    if not isinstance(provider_list, list):
        return [f"Top-level 'providers' must be a list, got {type(provider_list).__name__}"]

    # Check for duplicate provider names
    names = [p.get("name") for p in provider_list if isinstance(p, dict)]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            all_errors.append(f"Duplicate provider name: '{name}'")
        seen.add(name)

    for i, provider in enumerate(provider_list):
        all_errors.extend(validate_provider(provider, i))

    return all_errors


def main() -> int:
    """Run validation and print results. Returns exit code."""
    print(f"Validating {len(providers)} provider entries...")
    errors = validate_all(providers)

    if errors:
        print(f"\n❌ Found {len(errors)} validation error(s):\n")
        for error in errors:
            print(f"  • {error}")
        return 1

    print(f"✅ All {len(providers)} providers passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
