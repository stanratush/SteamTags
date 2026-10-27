"""Every fixed sentence of Automatic Parameter Selection, in one place.

The app, `selection_report.md` and the guide test all read these. Text is structured: a list of paragraphs, each a
list of (text, style) spans with style None, "bold" or "italic", so Dash and Markdown render the same words.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

Span = tuple[str, str | None]
Paragraph = list[Span]

NA_CAVEAT = ("Neighbour Agreement measures how little the clustering changes when g or s moves by one. "
             "It does not show that the Clusters are real.")
HIGH_G_CAVEAT = ("Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, "
                 "particularly s, generally produces a smaller change in the graph. This can increase agreement "
                 "independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs "
                 "partially counterbalances this tendency.")
DESCRIPTIVE_CAPTION = "Descriptive: not comparable across pairs"
DESCRIPTIVE_HELP = ("Describes this pair's Selected Partition on its own network. Pairs differ in tags and edges, so a "
                    "higher value at one pair does not make it a better choice.")
DATASET_STRIP_SENTENCE = ("Each dataset is selected on its own, from its own games and tags. Different pairs in "
                          "different datasets are expected and are not a disagreement: the same pair builds networks "
                          "of different sizes in different datasets.")
LEIDEN_ONLY = "Leiden only: the scan and Apply's reproduction search are built on it"
NO_SELECTION_YET = "No selection yet. {done} of {total} pairs are computed; the selection needs the whole grid."
NOTHING_RUN = "No results for these settings yet. Run computes them."

# The Pair Constraints' wording in the explanation, in the constraint table's order.
CONSTRAINT_NAMES = {
    "min_retention": "retention", "max_isolated_share": "isolated-share", "min_lcc_share": "LCC",
    "min_comparable_neighbours": "neighbour", "max_multi_tag_clusters": "Multi-Tag Cluster",
}


def _n(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _pct(value: float) -> str:
    return f"{value * 100:g}%"


def constraint_phrases(c: Any) -> list[str]:
    """The active Pair Constraints as words, in the table's order."""
    out = [f"Information Retention ≥ {c.min_retention:.2f}", f"isolated tags ≤ {_pct(c.max_isolated_share)}",
           f"largest component ≥ {_pct(c.min_lcc_share)} of the tags with an edge",
           f"≥ {c.min_comparable_neighbours} neighbours with a different graph"]
    if c.max_multi_tag_clusters is not None:
        out.append(f"at most {c.max_multi_tag_clusters} Multi-Tag Clusters")
    return out


def _and_list(items: Sequence[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + ", and " + items[-1]


def _under(constraints_label: str) -> str:
    return "the default constraints" if constraints_label == "Default constraints" else "the custom constraints"


def caveats() -> list[Paragraph]:
    return [[(NA_CAVEAT, "italic")], [(HIGH_G_CAVEAT, "italic")]]


def explanation(choice: Any, pair: Any, na: Any, settings_label: str, constraints_label: str,
                minimum_k: int) -> list[Paragraph]:
    """"Why this pair": the template, built only from NA, the constraints and counts (never Q, Coverage or
    Silhouette). `pair` is the chosen pair's GraphResult and `na` its NeighbourAgreement."""
    g, s = choice.chosen
    wb = pair.workbench
    if wb["flag"] == "not_representable":
        where = "(cannot be entered as a two-decimal value)"
    else:
        where = f"(Workbench {wb['gamma']:.2f})"
    first: Paragraph = [(f"Selected: g = {g}, s = {s}", "bold"), (f", resolution {pair.selected_resolution:.3f} "
                                                                  f"{where}.", None)]
    if wb["flag"] == "not_reproduced":
        first.append((f" Workbench {wb['gamma']:.2f} with the main seed shows a different partition.", None))
    c = choice.constraints
    unexcluding = [CONSTRAINT_NAMES[x] for x in choice.excluded_none]
    qualify = (f"{choice.n_selected} of {choice.n_pairs} pairs have a Selected Partition. "
               f"{len(choice.qualifying)} qualify under {_under(constraints_label)}: "
               f"{_and_list(constraint_phrases(c))}.")
    if unexcluding:
        names = unexcluding[0] if len(unexcluding) == 1 else ", ".join(unexcluding[:-1]) + " and " + unexcluding[-1]
        qualify += f" The {names} constraint{'' if len(unexcluding) == 1 else 's'} excluded no pair."
    bg, bs = choice.best
    near = len(choice.near_best)
    pick = (f"The highest Neighbour Agreement among them is {choice.max_na:.2f} (g = {bg}, s = {bs}). "
            f"{_n(near, 'pair is', 'pairs are')} within {c.tolerance:.2f} of it, and of these the one with the "
            f"smallest g, then the smallest s, is selected.")
    own = f"Its Neighbour Agreement is {na.value:.2f} over {_n(na.n_different, 'neighbour', 'neighbours')} with a different graph."
    if na.n_identical:
        own += (f" {na.n_identical} more {'neighbour has' if na.n_identical == 1 else 'neighbours have'} an identical "
                f"graph and {'is' if na.n_identical == 1 else 'are'} not counted.")
    out: list[Paragraph] = [first, [(f"{constraints_label} · {settings_label}.", None)], [(qualify, None)],
                            [(pick, None)], [(own, None)]]
    if pair.n_multi == minimum_k:
        out.append([(f"Its Selected Partition has the minimum {minimum_k} Multi-Tag Clusters; a coarser split was "
                     "not allowed.", None)])
    floor = pair.seed_noise["floor"]
    if floor < 0.5:
        out.append([(f"The Seed-Noise Floor at this resolution is {floor:.2f}: the clustering also depends "
                     "noticeably on the seed.", None)])
    return out + caveats()


def no_qualifying_message(choice: Any, constraints_label: str) -> list[Paragraph]:
    excluded = ", ".join(f"{phrase}: {e.alone} ({e.cumulative})"
                         for phrase, e in zip(constraint_phrases(choice.constraints), choice.exclusion))
    return [[("No pair qualifies", "bold"),
             (f" under {_under(constraints_label)}. {choice.n_selected} of {choice.n_pairs} pairs have a Selected "
              f"Partition. Excluded by each constraint, alone (cumulative): {excluded}. Loosen a constraint, or "
              "inspect any pair in the grid and apply it by hand.", None)]]


def to_markdown(paragraphs: Sequence[Paragraph]) -> str:
    marks = {"bold": "**", "italic": "*", None: ""}
    return "\n\n".join("".join(f"{marks[style]}{text}{marks[style]}" for text, style in p) for p in paragraphs)


def to_text(paragraphs: Sequence[Paragraph]) -> str:
    return "\n\n".join("".join(text for text, _ in p) for p in paragraphs)


# ----------------------------------------------------------------------------- validation


NULL_CAVEAT = "This shows only that the network is not random, not that its Clusters are real."
SUBSAMPLE_CAVEAT = ("This measures how much the clustering depends on which games are in the dataset. It does not "
                    "show that the Clusters are real either.")
DEGENERATE_WORDS = {"no_edges": "had no edges", "no_stable_partition": "had no Selected Partition",
                    "too_few_multi_tag_clusters": "had no Selected Partition"}


def _range(spread: Any, digits: int = 3) -> str:
    return f"{spread['min']:.{digits}f} to {spread['max']:.{digits}f}".replace("-", "−")


def _signed(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def _degenerate_words(reasons: dict[str, int]) -> str:
    words: dict[str, int] = {}
    for reason, count in reasons.items():
        text = DEGENERATE_WORDS.get(reason, reason)
        words[text] = words.get(text, 0) + count
    return "; ".join(f"{count} {text}" for text, count in words.items())


def cluster_name(cluster: dict[str, Any], names: Any) -> str:
    """"C2 (Strategy, Tactical, …)": the label and up to three member tags."""
    members = [names.get(t, str(t)) for t in cluster["members"]]
    shown = ", ".join(members[:3]) + (", …" if len(members) > 3 else "")
    return f"{cluster['label']} ({shown})"


def null_sentences(summary: Any) -> list[Paragraph]:
    n = summary["null"]
    r, q = n["replicates"], n["q"]
    reach = q["reach"]
    head = f"Q at resolution {summary['resolution']:.3f} is {_signed(q['observed'])}; "
    if reach:
        head += f"{reach} of {r} shuffled networks reach it: Q not above the null."
    else:
        head += f"no shuffled network reaches it ({_range(q)})."
    k, w = n["selected"], n["width"]
    if k:
        side = "narrower" if w["median"] < w["observed"] else "wider"
        rank = "all" if w["narrower"] == k else f"{w['narrower']} of"
        head += (f" {k} of {r} also have a Selected Partition, with {side} domains (median {w['median']:.3g} against "
                 f"{w['observed']:.3g}; wider than {rank} {k}).")
    else:
        head += f" None of the {r} has a Selected Partition."
    return [[("Null Comparison", "bold"), (f" ({r} shuffled networks, same g and s). " + head, None)],
            [(NULL_CAVEAT, "italic")]]


def subsample_sentences(summary: Any, names: Any) -> list[Paragraph]:
    sub = summary["subsample"]
    total = sub["subsamples"]
    re_, at = sub["reselected"], sub["at_resolution"]
    text = f" ({total} random 80% subsets of the games, g′ = {sub['g']}, s′ = {sub['s']}). "
    if re_["ari"]["median"] is None:
        text += f"Re-selected: no subsample has a Selected Partition ({_degenerate_words(re_['reasons'])})."
    else:
        text += (f"Re-selected: median ARI {re_['ari']['median']:.2f} ({re_['ari']['p10']:.2f}–{re_['ari']['p90']:.2f})"
                 f" over {total - re_['degenerate']} of {total} subsamples")
        text += f"; {_degenerate_words(re_['reasons'])}." if re_["degenerate"] else "."
    gamma = f"{summary['resolution']:.3f}"
    if at["ari"]["median"] is not None:
        text += (f" At resolution {gamma}: median ARI {at['ari']['median']:.2f} "
                 f"({at['ari']['p10']:.2f}–{at['ari']['p90']:.2f})")
        text += f"; {_degenerate_words(at['reasons'])}." if at["degenerate"] else "."
    n_clusters = len(re_["clusters"])
    spans: Paragraph = [("Subsample Stability", "bold"), (text, None)]
    any_dissolved = False
    for arm, where in (("reselected", "when re-selected"), ("at_resolution", f"at resolution {gamma}")):
        gone = [c for c in sub[arm]["clusters"] if c["dissolved"]]
        if gone:
            any_dissolved = True
            verb = "is" if len(gone) == 1 else "are"
            spans.append((f" {len(gone)} of {n_clusters} Multi-Tag Clusters {verb} dissolved {where} (mean Jaccard "
                          "≤ 0.5): ", None))
            for i, c in enumerate(gone):
                spans.append((cluster_name(c, names), "italic"))
                spans.append((", " if i < len(gone) - 1 else ".", None))
    if not any_dissolved:
        spans.append((" No Multi-Tag Cluster is dissolved (mean Jaccard ≤ 0.5) in either arm.", None))
    return [spans, [(SUBSAMPLE_CAVEAT, "italic")]]


def validation_title(pair: tuple[int, int]) -> str:
    return f"Validation of g = {pair[0]}, s = {pair[1]}"


def validation_block(summary: Any, pair: tuple[int, int], chosen_pair: tuple[int, int] | None, ran_for_default: bool,
                     names: Any = None) -> list[Paragraph]:
    """The validation card. `summary` None: "Not validated". `ran_for_default` False when custom constraints chose
    `chosen_pair` and the shown validation is the default-constraint pair's."""
    names = names or {}
    out: list[Paragraph] = [[(validation_title(pair), "bold")]]
    if not ran_for_default and chosen_pair is not None and chosen_pair != pair:
        out.append([(f"Validation ran for g = {pair[0]}, s = {pair[1]}, the pair chosen under the default "
                     "constraints.", None)])
    if summary is None:
        return out + [[("Not validated.", None)]]
    return out + null_sentences(summary) + subsample_sentences(summary, names)


# ----------------------------------------------------------------------------- the methods paragraph


# One template for `selection_report.md` and the User Guide (ch. 5, shown with placeholders; a test keeps them equal).
METHODS_TEMPLATE = (
    "For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, "
    "{g_range} games per tag and {s_range} shared games with s ≤ g ({n_pairs} pairs), with {weight} as the "
    "Clustering Weight, a Minimum Months Filter of {min_months} and {hidden} hidden. On each distinct graph we ran "
    "Leiden (RBConfiguration, at most 1,000 passes) with {scan_seeds} seeds at every γ from 0 to Gibson and Mucha's "
    "γ_max(K), K being the number of tags with an edge, in steps of {gamma_step} (Gibson & Mucha 2022, SI §J); the "
    "derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound also holds for "
    "Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to the upper envelope "
    "of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality Domains (CHAMP; Weir et al. "
    "2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution γ̂ = (ω_in − ω_out)/(ln ω_in − "
    "ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable when γ̂ lies in its own domain "
    "(Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions with at least {min_multi} Multi-Tag "
    "Clusters, the Selected Partition has the widest domain in plain γ units, and the Selected Resolution is the "
    "domain's midpoint; the sources give no rule for choosing among Stable Partitions, and we did not rescale the "
    "width to log γ or to Gibson and Mucha's γ-scaled area (SI §A.7), whose usefulness the authors leave open. "
    "Neighbour Agreement is the mean adjusted Rand index between a pair's Selected Partition and those of its grid "
    "neighbours (g ± 1, s ± 1) with a different graph, on the shared tags with an edge in either graph. The chosen "
    "pair is the one with the smallest g, then the smallest s, among the pairs whose Neighbour Agreement is within "
    "{tolerance} of the highest, among pairs with {constraints}. We compared the chosen pair with {replicates} "
    "networks whose game–tag table was shuffled by curveball trades (every tag and game keeps its count), each "
    "analysed by the identical procedure (Karrer, Levina & Newman 2008, abstract, §III and §VI), and with "
    "{subsamples} random subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, "
    "s′ = max(2, ⌊s·m/n⌋)). For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on "
    "the tags present in both networks, over the B* subsamples in which the Cluster has a tag, and call it "
    "dissolved at a mean of 0.5 or less; the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and "
    "are not applied."
)
METHODS_FIELDS = ("g_range", "s_range", "n_pairs", "weight", "min_months", "hidden", "scan_seeds", "gamma_step",
                  "min_multi", "tolerance", "constraints", "replicates", "subsamples")


def methods_paragraph(values: dict[str, Any] | None = None) -> str:
    """The template filled with a run's values, or with ‹placeholders› (as in the User Guide)."""
    values = values or {name: f"‹{name}›" for name in METHODS_FIELDS}
    return METHODS_TEMPLATE.format(**values)


def methods_values(settings: Any, constraints: Any) -> dict[str, Any]:
    weight = {"lift": "Lift", "shared_games": "shared games"}[settings.clustering_weight]
    n_hidden = len(settings.genre_hidden)
    hidden = f"{n_hidden} Genre Tags" + (" and each dataset's defining tag" if settings.hide_defining_tag else "")
    return {"g_range": f"{settings.g_range[0]}–{settings.g_range[1]}",
            "s_range": f"{settings.s_range[0]}–{settings.s_range[1]}", "n_pairs": len(settings.pairs()),
            "weight": weight, "min_months": settings.min_months, "hidden": hidden, "scan_seeds": settings.scan_seeds,
            "gamma_step": f"{settings.gamma_step:g}", "min_multi": settings.min_multi_tag_clusters,
            "tolerance": f"{constraints.tolerance:.2f}", "constraints": _and_list(constraint_phrases(constraints)),
            "replicates": settings.replicates, "subsamples": settings.subsamples}
