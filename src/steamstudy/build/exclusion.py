"""Exclusion rules, Exclusion Overrides, manual exclusions and Content Flags.

Rules are evaluated in order and every match is recorded; `primary_reason` is the first match.
`store_data_unavailable` and `app_type` short-circuit. Tags are matched on tag id (names are labels),
except the configured name-only entries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from steamstudy.build.games import Game
from steamstudy.build.parse import StoreTag
from steamstudy.config import ExclusionConfig, TagList

RULES = ("store_data_unavailable", "app_type", "no_tags", "adult_content", "software_tag", "dating_sim_tag", "manual")
OVERRIDABLE = ("app_type", "no_tags", "adult_content", "software_tag", "dating_sim_tag")


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
    return {e["appid"]: e for e in _validate_list(entries, "manual_exclusions.toml", needs_rule=False)}


def validate_overrides(entries: tuple[dict[str, Any], ...]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(e["appid"], e["rule"]): e for e in _validate_list(entries, "exclusion_overrides.toml", needs_rule=True)}


def _validate_list(entries: tuple[dict[str, Any], ...], where: str, *, needs_rule: bool) -> list[dict[str, Any]]:
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
        if needs_rule and e.get("rule") not in OVERRIDABLE:
            raise ExclusionListError(f"{w} (appid {e['appid']}): rule must be one of {OVERRIDABLE}")
        out.append(e)
    return out


def configured_tag_ids(cfg: ExclusionConfig) -> list[tuple[str, int, str]]:
    """(where, tag id, name) for every tag id the exclusion config names, for the vocabulary check."""
    out: list[tuple[str, int, str]] = []
    for where, tag_list in (("adult_content", cfg.adult_tags), ("software_tag", cfg.software_tags),
                            ("dating_sim_tag", cfg.dating_sim_tags),
                            *((f"content_flags.{k}", v) for k, v in cfg.content_flags.items())):
        out.extend((where, t.id, t.name) for t in tag_list.tags)
    return out


def _limit(cfg: ExclusionConfig, tag_id: int) -> int:
    return cfg.per_tag_rank_limit.get(tag_id, cfg.global_rank_limit)


def _tags_in(game: Game, tag_list: TagList) -> list[StoreTag]:
    ids = {t.id for t in tag_list.tags}
    names = set(tag_list.name_only)
    return [t for t in game.tags if t.tag_id in ids or t.name in names]


def _tag_rule(rule: str, game: Game, tag_list: TagList, cfg: ExclusionConfig) -> tuple[Match | None, list[NearMiss]]:
    within: list[tuple[StoreTag, int]] = []
    beyond: list[tuple[StoreTag, int]] = []
    for tag in _tags_in(game, tag_list):
        limit = _limit(cfg, tag.tag_id)
        (within if tag.position <= limit else beyond).append((tag, limit))
    near = [NearMiss(rule, tag, limit) for tag, limit in beyond]
    if not within:
        return None, near
    detail = "; ".join(f"{t.name} ({t.tag_id}) at position {t.position}" for t, _ in within)
    return Match(rule, detail, tuple((t.name, t.tag_id) for t, _ in within)), near


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

    hentai, hentai_near = _tag_rule("adult_content", game, cfg.adult_tags, cfg)
    near_misses += hentai_near
    adult_signals = {
        "adult_only_notice": game.adult_only,
        "content_descriptor_3": any(i in game.descriptor_ids for i in cfg.adult_descriptor_ids),
        "hentai_tag": hentai is not None,
    }
    fired: list[tuple[str, int | None]] = []
    if adult_signals["adult_only_notice"]:
        fired.append(("adult_only_notice", None))
    if adult_signals["content_descriptor_3"]:
        ids = [i for i in game.descriptor_ids if i in cfg.adult_descriptor_ids]
        fired.extend((f"content_descriptor_{i}", None) for i in ids)
    if hentai is not None:
        fired.extend(hentai.signals)
    if fired:
        parts = [label if tag_id is None else f"tag {label} ({tag_id})" for label, tag_id in fired]
        add(Match("adult_content", "signals: " + "; ".join(parts), tuple(fired)))

    for rule, tag_list in (("software_tag", cfg.software_tags), ("dating_sim_tag", cfg.dating_sim_tags)):
        match, near = _tag_rule(rule, game, tag_list, cfg)
        near_misses += near
        add(match)

    if game.appid in manual:
        add(Match("manual", str(manual[game.appid]["reason"]), (("manual", None),)))
    return Evaluation(tuple(matches), tuple(overridden), tuple(near_misses), adult_signals)


def content_flags(game: Game, cfg: ExclusionConfig) -> list[str]:
    """Content Flag codes, matched anywhere in the displayed tags; they never filter."""
    return [code for code, tag_list in cfg.content_flags.items() if _tags_in(game, tag_list)]
