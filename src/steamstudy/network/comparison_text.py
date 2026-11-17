"""Every fixed sentence of the Cluster Comparison, in one place.

The app, `comparison.json` and the guide test all read these. Each function takes the Interface Language's
translator `tx` (`steamstudy.i18n`): the app passes the page's, the export and the guide test pass `text("en")`.
Text that needs emphasis comes as a paragraph of (text, style) spans, style None or "bold", as in `selection_text`.
"""

from __future__ import annotations

from collections.abc import Mapping

from steamstudy.i18n import Text

Span = tuple[str, str | None]
Paragraph = list[Span]

# The caution: the guide's mode section and metric chapter, the in-app help and `comparison.json` quote it.
CAUTION = ("A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not "
           "evidence that the Clusters are real or that the datasets share a genre structure. A match can appear, "
           "vanish or change its Match Jaccard with the seed, with g and s, and with the resolution. Read it against "
           "each dataset's Seed-Noise Floor and Neighbour Agreement.")

# Each figure's reading: the In short line of its metric-reference entry, so also its tooltip (help.py reads the
# guide); kept here so the guide test can hold the two together.
READINGS = {
    "cluster_match": ("Two Multi-Tag Clusters, one from each dataset, that share at least one Tag; it says they share "
                      "Tags, not that they are the same group."),
    "match_jaccard": ("The shared Tags as a share of all Tags in either Cluster; 1 = the same Tags, 0 = none in "
                      "common; a Tag missing from the other network counts against it."),
    "comparable_jaccard": ("The same overlap on the Comparable Tags only; never lower than Match Jaccard, and the gap "
                           "shows how much of a low score comes from Tags missing from the other network; \"—\" when "
                           "either Cluster has fewer than two Comparable Tags."),
    "shared_share": ("The share of one Cluster's Tags that the other also has; they differ when the sizes differ; "
                     "100% on one side means that Cluster lies wholly inside the other."),
    "overlap_vs_expected": ("Shared Tags ÷ what two Clusters of these sizes would share if Tags were placed at random "
                            "among the Comparable Tags; 1× = the sizes alone; descriptive, no p-value, since Clusters "
                            "are not random draws."),
    "ari": ("How alike the two partitions are on the Comparable Tags with an edge in either network; 1 = identical, "
            "around 0 = no more than chance."),
    "comparable_tags": ("How many Tags are in both networks and what share of each network that is; a low share means "
                        "the pair is compared on only a small part of that network."),
    "games_in_common": "The games ranked in both Top-N Datasets; shown, never scored.",
}

SCAN_SEEDS_TIP = "found among the partitions of {n} scan seeds; no seed of its own"
FEWER_THAN_TWO = "Include at least two datasets to compare"
NO_MATCH = "These two datasets have no Cluster Match: no Multi-Tag Cluster of one shares a Tag with one of the other."
CHOOSE_A_MATCH = "Click a curve in the diagram to see that Cluster Match."
NO_GAMES_IN_COMMON = "These two datasets have no games in common, so no game can be in both Clusters."
SHARED_SETTINGS_CHANGED = ("The shared settings changed, so every dataset was resolved again on its pick (or with no "
                           "run); values set by hand were dropped.")
USE_DISABLED = "The Cluster Comparison uses other shared settings; this cell comes from a different run."
SENTENCES = (CAUTION, *READINGS.values(), SCAN_SEEDS_TIP, FEWER_THAN_TWO, NO_MATCH, CHOOSE_A_MATCH,
             NO_GAMES_IN_COMMON, SHARED_SETTINGS_CHANGED, USE_DISABLED)


def caution(tx: Text) -> str:
    return tx(CAUTION)


def reading(key: str, tx: Text) -> str:
    return tx(READINGS[key])


def cluster_name(dataset: str, label: str) -> str:
    """A Cluster standing alone is always written with its dataset: "Overall C3" (labels mean nothing across
    datasets). Dataset labels are names, never translated."""
    return f"{dataset} {label}"


# ----------------------------------------------------------------------------- the dataset row


def source_line(source: str, *, g: int, s: int, algorithm: str, fallback: str | None = None, tx: Text) -> str:
    """A dataset's source line, by Threshold Pair (never "cell"); `fallback` says why a dataset asked for on a cell
    has none (`cc_view.Resolved.fallback`)."""
    if source == "pick":
        return tx("★ Selected Partition at g {g} · s {s} (chosen pair)", g=g, s=s)
    if source == "cell":
        return tx("Selected Partition at g {g} · s {s}", g=g, s=s)
    if source == "hand":
        return tx("Set by hand: one {algorithm} run, main seed", algorithm=algorithm)
    if fallback == "run_gone":
        return tx("The selected cell's Automatic Parameter Selection run is gone: network defaults, one {algorithm} "
                  "run, main seed", algorithm=algorithm)
    if fallback == "no_pick":
        return tx("No qualifying pair in the Automatic Parameter Selection run: network defaults, one {algorithm} "
                  "run, main seed", algorithm=algorithm)
    return tx("No Automatic Parameter Selection run: network defaults, one {algorithm} run, main seed",
              algorithm=algorithm)


def scan_seeds_tip(n: int, tx: Text) -> str:
    return tx(SCAN_SEEDS_TIP, n=n)


def open_parameter_selection(tx: Text) -> str:
    return tx("Open Parameter Selection")


def figures_line(floor: float | None, na: float | None, tx: Text) -> str:
    """"Seed-Noise Floor 0.52 · NA 0.81": the run's floor and the cell's NA, or "—"."""
    return tx("Seed-Noise Floor {floor} · NA {na}", floor=_num(floor, tx), na=_num(na, tx))


def _num(value: float | None, tx: Text) -> str:
    return "—" if value is None else tx.num(value, 2)


# ----------------------------------------------------------------------------- flags and Tag groups


def flag_label(flag: str, *, other: str, minimum: float, tx: Text) -> str:
    """A Cluster's "No match" badge against the other dataset `other` ("" for a Cluster with a match above the
    minimum)."""
    if flag == "outside_network":
        return tx("No match: outside {dataset}'s network", dataset=other)
    if flag == "only_one_tag_clusters":
        return tx("No match: only One-Tag Clusters in {dataset}", dataset=other)
    if flag == "below_minimum":
        return tx("No match above {minimum}", minimum=tx.num(minimum, 2))
    return ""


def one_tag_counts(n_one_tag: int, n_not_in_network: int, *, other: str, tx: Text) -> str:
    """The "only One-Tag Clusters" badge's tooltip: "3 Tags in One-Tag Clusters of Overall, 2 not in its network"."""
    parts = [tx.n(n_one_tag, one="{n} Tag in One-Tag Clusters of {dataset}",
                  other="{n} Tags in One-Tag Clusters of {dataset}", dataset=other)]
    if n_not_in_network:
        parts.append(tx.n(n_not_in_network, one="{n} not in its network", other="{n} not in its network"))
    return ", ".join(parts)


def tag_group(group: str, *, other: str, cluster: str | None = None, n_games: int | None = None,
              minimum: int | None = None, tx: Text) -> str:
    """Where an unshared Tag sits in the other dataset `other` (`comparison.TagPlace`)."""
    if group == "other_cluster":
        return tx("in {cluster}", cluster=cluster_name(other, cluster or ""))
    if group == "one_tag":
        return tx("One-Tag Cluster in {dataset}", dataset=other)
    if group == "not_in_network":
        return tx.n(n_games or 0, one="not in {dataset}'s network ({n} game, minimum {minimum})",
                    other="not in {dataset}'s network ({n} games, minimum {minimum})", dataset=other, minimum=minimum)
    return tx("hidden in {dataset} (its defining Tag)", dataset=other)


def one_tag_line(a: str, n_a: int, b: str, n_b: int, tx: Text) -> str:
    """Under the diagram: the One-Tag Clusters of each side, which are never matched."""
    return tx("One-Tag Clusters are not matched: {a} has {n_a}, {b} has {n_b}.", a=a, n_a=n_a, b=b, n_b=n_b)


# ----------------------------------------------------------------------------- the match detail


def overlap_sentence(n_shared: int, ratio: float, expected: float, n_comparable: int, tx: Text) -> str:
    """"3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)"."""
    return tx.n(n_shared,
                one="{n} shared Tag: {ratio}× the {expected} expected from the Cluster sizes (N = {total} Comparable "
                    "Tags)",
                other="{n} shared Tags: {ratio}× the {expected} expected from the Cluster sizes (N = {total} "
                      "Comparable Tags)",
                ratio=tx.num(ratio, 1), expected=tx.num(expected, 2), total=n_comparable)


def games_count_line(counts: Mapping[str, int], a: str, b: str, tx: Text) -> Paragraph:
    """"Of **N** games in both datasets: **k** in both Clusters, **x** only in A, **y** only in B, **z** in
    neither."""
    return [(tx("Of"), None), (f" {counts['in_common']} ", "bold"), (tx("games in both datasets:"), None),
            (f" {counts['both']} ", "bold"), (tx("in both Clusters,"), None), (f" {counts['only_a']} ", "bold"),
            (tx("only in {a},", a=a), None), (f" {counts['only_b']} ", "bold"), (tx("only in {b},", b=b), None),
            (f" {counts['neither']} ", "bold"), (tx("in neither."), None)]


def no_games_line(n_in_common: int, tx: Text) -> Paragraph:
    """The empty games list: no games in common, or none of them in both Clusters."""
    if n_in_common == 0:
        return [(tx(NO_GAMES_IN_COMMON), None)]
    return [(tx("None of the"), None), (f" {n_in_common} ", "bold"),
            (tx("games in both datasets is in both Clusters."), None)]


def show_all(n: int, tx: Text) -> str:
    return tx("Show all {n}", n=n)
