"""Exclusion rules, Exclusion Overrides, manual exclusions and Content Flags.

Rules are evaluated in order and every match is recorded; `primary_reason` is the first match.
The fixed rules run first (`store_data_unavailable`, `app_type`, `no_tags`), then the named rules of
`exclusions.toml` in file order, then `manual`. `store_data_unavailable` and `app_type` short-circuit.
Tags are matched on tag id (names are labels), except the configured name-only entries. Rules and Content
Flags read the full displayed tag list, and rank limits count positions in it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from steamstudy.build.games import Game
from steamstudy.build.parse import StoreTag
from steamstudy.config import ExclusionConfig, ExclusionRule

ADULT_RULE = "adult_content"  # the rule `impact_adult_signals.csv` reports on


def rule_codes(cfg: ExclusionConfig) -> tuple[str, ...]:
    """Every rule code in evaluation order: fixed rules, the named rules, then manual."""
    return ("store_data_unavailable", "app_type", "no_tags", *(r.name for r in cfg.rules), "manual")


def overridable(cfg: ExclusionConfig) -> tuple[str, ...]:
    return ("app_type", "no_tags", *(r.name for r in cfg.rules))


class ExclusionListError(ValueError):
    """An entry of manual_exclusions.toml or exclusion_overrides.toml is invalid."""


@dataclass(frozen=True)
class Match:
    rule: str
    detail: str
    signals: tuple[tuple[str, int | None], ...]  # (signal label, tag id or None), for the impact report


@dataclass(frozen=True)
class NearMiss:
    rule: str
    tag: StoreTag
    rank_limit: int


@dataclass(frozen=True)
class Evaluation:
    matches: tuple[Match, ...]
    overridden: tuple[str, ...]
    near_misses: tuple[NearMiss, ...]
    adult_signals: dict[str, bool]

    @property
    def excluded(self) -> bool:
        return bool(self.matches)

    @property
    def primary_reason(self) -> str | None:
        return self.matches[0].rule if self.matches else None


def validate_manual_exclusions(entries: tuple[dict[str, Any], ...]) -> dict[int, dict[str, Any]]:
    return {e["appid"]: e for e in _validate_list(entries, "manual_exclusions.toml")}


def validate_overrides(
    entries: tuple[dict[str, Any], ...], cfg: ExclusionConfig
) -> dict[tuple[int, str], dict[str, Any]]:
    return {(e["appid"], e["rule"]): e
            for e in _validate_list(entries, "exclusion_overrides.toml", rules=overridable(cfg))}


def _validate_list(
    entries: tuple[dict[str, Any], ...], where: str, *, rules: tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
    out = []
    for i, e in enumerate(entries):
        w = f"{where} entry {i + 1}"
        if not isinstance(e.get("appid"), int) or isinstance(e.get("appid"), bool):
            raise ExclusionListError(f"{w}: appid must be an integer")
        for key in ("name", "reason", "added"):
            if not str(e.get(key, "")).strip():
                raise ExclusionListError(f"{w} (appid {e['appid']}): missing {key}")
        evidence = e.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ExclusionListError(f"{w} (appid {e['appid']}): at least one evidence entry is required")
        for ev in evidence:
            if not isinstance(ev, dict) or not str(ev.get("url", "")).strip() or not str(ev.get("retrieved", "")).strip():
                raise ExclusionListError(f"{w} (appid {e['appid']}): every evidence entry needs a url and a retrieved date")
        if rules is not None and e.get("rule") not in rules:
            rule = e.get("rule")
            why = ("cannot be overridden (use a Manual Metadata Entry)" if rule == "store_data_unavailable" else
                   "cannot be overridden (remove the manual exclusion instead)" if rule == "manual" else
                   "is not a rule of exclusions.toml")
            raise ExclusionListError(
                f"{w} (appid {e['appid']}): rule {rule!r} {why}; it must be one of {rules}")
        out.append(e)
    return out


def configured_tag_ids(cfg: ExclusionConfig) -> list[tuple[str, int, str]]:
    """(where, tag id, name) for every tag id the exclusion config names, for the vocabulary check."""
    out: list[tuple[str, int, str]] = []
    for rule in cfg.rules:
        out.extend((rule.name, t.id, t.name) for t in rule.tags)
    for flag in cfg.content_flags:
        out.extend((f"content_flags.{flag.name}", t.id, t.name) for t in flag.tags)
    return out


def _tags_in(game: Game, tags: Any, name_only: tuple[str, ...]) -> list[StoreTag]:
    ids = {t.id for t in tags}
    return [t for t in game.tags if t.tag_id in ids or t.name in name_only]


def _tag_signal(rule: ExclusionRule, game: Game, cfg: ExclusionConfig) -> tuple[Match | None, list[NearMiss]]:
    limits = {t.id: t.rank_limit for t in rule.tags if t.rank_limit is not None}
    within: list[tuple[StoreTag, int]] = []
    beyond: list[tuple[StoreTag, int]] = []
    for tag in _tags_in(game, rule.tags, rule.name_only):
        limit = limits.get(tag.tag_id, cfg.global_rank_limit)
        (within if tag.position <= limit else beyond).append((tag, limit))
    near = [NearMiss(rule.name, tag, limit) for tag, limit in beyond]
    if not within:
        return None, near
    detail = "; ".join(f"{t.name} ({t.tag_id}) at position {t.position}" for t, _ in within)
    return Match(rule.name, detail, tuple((t.name, t.tag_id) for t, _ in within)), near


def evaluate(
    game: Game,
    cfg: ExclusionConfig,
    manual: dict[int, dict[str, Any]],
    overrides: dict[tuple[int, str], dict[str, Any]],
) -> Evaluation:
    matches: list[Match] = []
    overridden: list[str] = []
    near_misses: list[NearMiss] = []

    def add(match: Match | None) -> bool:
        if match is None:
            return False
        if (game.appid, match.rule) in overrides:
            overridden.append(match.rule)
            return False
        matches.append(match)
        return True

    if not game.has_data:
        add(Match("store_data_unavailable", game.store_detail(), (("store_data_unavailable", None),)))
        return Evaluation(tuple(matches), (), (), {})
    if game.app_type not in cfg.allowed_app_types:
        if add(Match("app_type", game.app_type, ((f"app_type={game.app_type}", None),))):
            return Evaluation(tuple(matches), tuple(overridden), (), {})
    if not game.tags:
        add(Match("no_tags", "the store page displays no tags", (("no_tags", None),)))

    adult_signals: dict[str, bool] = {}
    for rule in cfg.rules:
        tag_match, near = _tag_signal(rule, game, cfg)
        near_misses += near
        if not (rule.content_descriptor_ids or rule.adult_only_notice):
            add(tag_match)
            continue
        descriptors = [i for i in game.descriptor_ids if i in rule.content_descriptor_ids]
        if rule.name == ADULT_RULE:
            adult_signals = {"adult_only_notice": game.adult_only, "content_descriptor_3": bool(descriptors),
                             "hentai_tag": tag_match is not None}
        fired: list[tuple[str, int | None]] = []
        if rule.adult_only_notice and game.adult_only:
            fired.append(("adult_only_notice", None))
        fired.extend((f"content_descriptor_{i}", None) for i in descriptors)
        if tag_match is not None:
            fired.extend(tag_match.signals)
        if fired:
            parts = [label if tag_id is None else f"tag {label} ({tag_id})" for label, tag_id in fired]
            add(Match(rule.name, "signals: " + "; ".join(parts), tuple(fired)))

    if game.appid in manual:
        add(Match("manual", str(manual[game.appid]["reason"]), (("manual", None),)))
    return Evaluation(tuple(matches), tuple(overridden), tuple(near_misses), adult_signals)


def content_flags(game: Game, cfg: ExclusionConfig) -> list[str]:
    """Content Flag codes, matched anywhere in the displayed tags; they never filter."""
    return [f.name for f in cfg.content_flags if _tags_in(game, f.tags, f.name_only)]
