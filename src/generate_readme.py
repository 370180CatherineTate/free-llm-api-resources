#!/usr/bin/env python3
"""
Generate README.md from template and data.

This script reads the data from data.py and the README template,
then generates the final README.md with up-to-date provider information.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the src directory to the path so we can import data
sys.path.insert(0, str(Path(__file__).parent))

from data import (
    Provider,
    PROVIDERS,
    NOTES,
)


TEMPLATE_PATH = Path(__file__).parent / "README_template.md"
OUTPUT_PATH = Path(__file__).parent.parent / "README.md"


def format_rate_limit(provider: Provider) -> str:
    """Format rate limit information for a provider."""
    parts = []
    if provider.requests_per_minute:
        parts.append(f"{provider.requests_per_minute} req/min")
    if provider.requests_per_day:
        parts.append(f"{provider.requests_per_day} req/day")
    if provider.tokens_per_minute:
        parts.append(f"{provider.tokens_per_minute} tokens/min")
    if provider.tokens_per_day:
        parts.append(f"{provider.tokens_per_day} tokens/day")
    return ", ".join(parts) if parts else "Unknown"


def format_models(provider: Provider) -> str:
    """Format the list of available models for a provider."""
    if not provider.models:
        return "Various"
    return ", ".join(f"`{model}`" for model in provider.models)


def format_notes(provider: Provider) -> str:
    """Format notes for a provider, resolving note references."""
    if not provider.notes:
        return ""
    resolved = []
    for note in provider.notes:
        if note in NOTES:
            resolved.append(NOTES[note])
        else:
            resolved.append(note)
    return " ".join(resolved)


def build_provider_table(providers: list[Provider]) -> str:
    """Build a markdown table for a list of providers."""
    lines = [
        "| Provider | Models | Free Tier Limits | Requires Credit Card | Notes |",
        "|----------|--------|-----------------|---------------------|-------|",
    ]
    for provider in sorted(providers, key=lambda p: p.name.lower()):
        name_cell = f"[{provider.name}]({provider.url})"
        models_cell = format_models(provider)
        limits_cell = format_rate_limit(provider)
        cc_cell = "Yes" if provider.requires_credit_card else "No"
        notes_cell = format_notes(provider)
        lines.append(
            f"| {name_cell} | {models_cell} | {limits_cell} | {cc_cell} | {notes_cell} |"
        )
    return "\n".join(lines)


def generate_readme() -> str:
    """Generate the full README content from template and provider data."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Separate providers by category
    chat_providers = [p for p in PROVIDERS if "chat" in p.categories]
    image_providers = [p for p in PROVIDERS if "image" in p.categories]
    audio_providers = [p for p in PROVIDERS if "audio" in p.categories]
    embedding_providers = [p for p in PROVIDERS if "embedding" in p.categories]

    chat_table = build_provider_table(chat_providers)
    image_table = build_provider_table(image_providers)
    audio_table = build_provider_table(audio_providers)
    embedding_table = build_provider_table(embedding_providers)

    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    readme = template.replace("{{CHAT_PROVIDERS}}", chat_table)
    readme = readme.replace("{{IMAGE_PROVIDERS}}", image_table)
    readme = readme.replace("{{AUDIO_PROVIDERS}}", audio_table)
    readme = readme.replace("{{EMBEDDING_PROVIDERS}}", embedding_table)
    readme = readme.replace("{{LAST_UPDATED}}", last_updated)
    readme = readme.replace("{{PROVIDER_COUNT}}", str(len(PROVIDERS)))

    return readme


def main() -> int:
    """Main entry point for README generation."""
    print(f"Reading template from: {TEMPLATE_PATH}")
    print(f"Writing output to: {OUTPUT_PATH}")

    if not TEMPLATE_PATH.exists():
        print(f"ERROR: Template file not found: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    readme_content = generate_readme()
    OUTPUT_PATH.write_text(readme_content, encoding="utf-8")

    print(f"Successfully generated README.md with {len(PROVIDERS)} providers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
