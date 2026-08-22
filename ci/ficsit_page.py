#!/usr/bin/env python3
"""Render and optionally deploy Faxit Reborn ficsit.app page metadata."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml


FICSIT_API_URL = "https://api.ficsit.app/v2/query"
FICSIT_ID = re.compile(r"^[A-Za-z0-9]{14}$")
PLACEHOLDER = re.compile(r"{{([A-Z0-9_]+)}}")
AI_DISCLOSURE_TYPES = {"ai_usage", "no_ai_usage", "runtime_ai_usage"}


def multiplayer_badge(label: str, color: str) -> str:
    encoded = urllib.parse.quote(label)
    return (
        f'<img src="https://img.shields.io/badge/Multiplayer-{encoded}-{color}'
        '?style=for-the-badge&logo=steam&logoColor=white" '
        f'alt="Multiplayer: {html.escape(label, quote=True)}" />'
    )


MULTIPLAYER_BADGES = {
    "yes": multiplayer_badge("Supported", "brightgreen"),
    "no": multiplayer_badge("Not Supported", "red"),
    "not-tested": multiplayer_badge("Not Tested", "lightgrey"),
    "wip": multiplayer_badge("WIP", "yellow"),
}

UPDATE_MOD_QUERY = """
mutation UpdateModDescription($modId: ModID!, $mod: UpdateMod!) {
  updateMod(modId: $modId, mod: $mod) {
    id
  }
}
""".strip()


class ConfigurationError(ValueError):
    """Raised when repository metadata cannot produce a safe page update."""


GraphqlRequester = Callable[[str, dict[str, object], str | None], dict[str, object]]


def load_yaml_mapping(path: Path, context: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ConfigurationError(f"cannot read {context} {path}: {error}") from error
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"{context} must be a YAML mapping: {path}")
    return loaded


def required_string(mapping: Mapping[str, object], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{context} requires non-empty {key}")
    return " ".join(value.split())


def load_page_config(path: Path) -> dict[str, Any]:
    config = load_yaml_mapping(path, "page config")
    mod_id = required_string(config, "modId", "page config")
    if not FICSIT_ID.fullmatch(mod_id):
        raise ConfigurationError("page config modId must be a 14-character ficsit.app ID")
    required_string(config, "modReference", "page config")
    required_string(config, "name", "page config")
    required_string(config, "shortDescription", "page config")
    if "hidden" not in config or not isinstance(config["hidden"], bool):
        raise ConfigurationError("page config hidden must be boolean")
    return config


def template_values(root: Path, config: Mapping[str, object]) -> dict[str, str]:
    del root
    template_config = config.get("template")
    if not isinstance(template_config, dict):
        raise ConfigurationError("page config requires template mapping")
    source_url_value = config.get("sourceUrl", template_config.get("sourceUrl"))
    values = {
        "MOD_NAME": required_string(config, "name", "page config"),
        "MOD_REFERENCE": required_string(config, "modReference", "page config"),
        "SOURCE_URL": required_string({"sourceUrl": source_url_value}, "sourceUrl", "page config"),
        "TARGET_PAGE_URL": f"https://ficsit.app/mod/{required_string(config, 'modId', 'page config')}",
    }
    optional_template_values = {
        "discordUrl": "DISCORD_URL",
        "patreonUrl": "PATREON_URL",
        "ficsitProfileUrl": "FICSIT_PROFILE_URL",
    }
    for source_key, target_key in optional_template_values.items():
        if source_key in template_config:
            values[target_key] = required_string(template_config, source_key, "template")
    if "multiplayer" in template_config:
        multiplayer = required_string(template_config, "multiplayer", "template")
        if multiplayer not in MULTIPLAYER_BADGES:
            raise ConfigurationError(f"template multiplayer must be one of {sorted(MULTIPLAYER_BADGES)}")
        values["MULTIPLAYER_BADGE"] = MULTIPLAYER_BADGES[multiplayer]
    return values


def render_description(root: Path, template: str, config: Mapping[str, object]) -> str:
    rendered = template
    for key, value in template_values(root, config).items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = sorted(set(PLACEHOLDER.findall(rendered)))
    if unresolved:
        raise ConfigurationError(f"unresolved template placeholder(s): {', '.join(unresolved)}")
    return rendered.strip() + "\n"


def build_update_input(config: Mapping[str, object], full_description: str) -> dict[str, object]:
    if not full_description.strip():
        raise ConfigurationError("rendered full description is empty")
    update: dict[str, object] = {
        "full_description": full_description,
        "short_description": required_string(config, "shortDescription", "page config"),
        "name": required_string(config, "name", "page config"),
        "hidden": config["hidden"],
    }
    optional_fields = {
        "sourceUrl": "source_url",
        "networkUseDisclosure": "network_use_disclosure",
    }
    for source_key, api_key in optional_fields.items():
        if source_key in config:
            update[api_key] = required_string(config, source_key, "page config")
    disclosure = config.get("aiUseDisclosure")
    if disclosure is not None:
        if not isinstance(disclosure, dict):
            raise ConfigurationError("aiUseDisclosure must be a mapping")
        disclosure_type = required_string(disclosure, "type", "aiUseDisclosure")
        if disclosure_type not in AI_DISCLOSURE_TYPES:
            raise ConfigurationError(f"aiUseDisclosure type must be one of {sorted(AI_DISCLOSURE_TYPES)}")
        api_disclosure: dict[str, object] = {"disclosure_type": disclosure_type}
        if "message" in disclosure:
            api_disclosure["message"] = required_string(disclosure, "message", "aiUseDisclosure")
        update["ai_use_disclosure"] = api_disclosure
    return update


def graphql_request(query: str, variables: dict[str, object], token: str | None = None) -> dict[str, object]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    request = urllib.request.Request(
        FICSIT_API_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as error:
        raise RuntimeError(f"ficsit.app request failed: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("ficsit.app returned a non-object response")
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        messages = [str(error.get("message", error)) if isinstance(error, dict) else str(error) for error in errors]
        raise RuntimeError(f"ficsit.app GraphQL error: {'; '.join(messages)}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("ficsit.app response did not contain data")
    return data


def deploy_ficsit_page(
    config: Mapping[str, object],
    full_description: str,
    token: str,
    *,
    requester: GraphqlRequester = graphql_request,
) -> str:
    if not token.strip():
        raise ConfigurationError("FICSIT_TOKEN is empty")
    mod_id = required_string(config, "modId", "page config")
    result = requester(
        UPDATE_MOD_QUERY,
        {"modId": mod_id, "mod": build_update_input(config, full_description)},
        token,
    )
    updated = result.get("updateMod")
    updated_id = updated.get("id") if isinstance(updated, dict) else None
    if not isinstance(updated_id, str) or not updated_id:
        raise RuntimeError("ficsit.app updateMod response did not contain an id")
    return updated_id


def resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else root / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path(".github/ficsit-page.yml"))
    parser.add_argument("--template", type=Path, default=Path(".github/ficsit-description.template.md"))
    parser.add_argument("--description", type=Path, help="Use an already-rendered description")
    parser.add_argument("--output", type=Path, help="Write rendered description")
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    try:
        config = load_page_config(resolve(root, args.config))
        if args.description:
            description = resolve(root, args.description).read_text(encoding="utf-8")
        else:
            template = resolve(root, args.template).read_text(encoding="utf-8")
            description = render_description(root, template, config)
        if args.output:
            output = resolve(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(description, encoding="utf-8", newline="\n")
            print(f"rendered ficsit.app description: {output}")
        if args.deploy:
            updated_id = deploy_ficsit_page(config, description, os.environ.get("FICSIT_TOKEN", ""))
            print(f"updated ficsit.app page: {updated_id}")
    except (OSError, ConfigurationError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
