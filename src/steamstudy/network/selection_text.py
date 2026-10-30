"""Every fixed sentence of Automatic Parameter Selection, in one place.

The app, `selection_report.md` and the guide test all read these. Text is structured: a list of paragraphs, each a
list of (text, style) spans with style None, "bold" or "italic", so Dash and Markdown render the same words.

Every function takes the Interface Language's translator `tx` (`steamstudy.i18n`): the app passes the page's, and
`selection_report.md`, the CLI and the guide test pass `text("en")`, so the report stays English.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from steamstudy.i18n import Text

Span = tuple[str, str | None]
Paragraph = list[Span]

# The English sentences other modules and tests quote; shown through `tx` (a declared parity source).
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
NULL_CAVEAT = "This shows only that the network is not random, not that its Clusters are real."
SUBSAMPLE_CAVEAT = ("This measures how much the clustering depends on which games are in the dataset. It does not "
                    "show that the Clusters are real either.")
SENTENCES = (NA_CAVEAT, HIGH_G_CAVEAT, DESCRIPTIVE_CAPTION, DESCRIPTIVE_HELP, DATASET_STRIP_SENTENCE, LEIDEN_ONLY,
             NO_SELECTION_YET, NOTHING_RUN, NULL_CAVEAT, SUBSAMPLE_CAVEAT)


def constraint_names(tx: Text) -> dict[str, str]:
    """The Pair Constraints' wording in the explanation, in the constraint table's order."""
    return {"min_retention": tx("retention"), "max_isolated_share": tx("isolated-share"), "min_lcc_share": tx("LCC"),
            "min_comparable_neighbours": tx("neighbour"), "max_multi_tag_clusters": tx("Multi-Tag Cluster")}


def _pct(value: float, tx: Text) -> str:
    return tx.pct(value)


def constraint_phrases(c: Any, tx: Text) -> list[str]:
    """The active Pair Constraints as words, in the table's order."""
    out = [tx("Information Retention ≥ {value}", value=tx.fixed(c.min_retention, ".2f")),
           tx("isolated tags ≤ {value}", value=_pct(c.max_isolated_share, tx)),
           tx("largest component ≥ {value} of the tags with an edge", value=_pct(c.min_lcc_share, tx)),
           tx("≥ {n} neighbours with a different graph", n=c.min_comparable_neighbours)]
    if c.max_multi_tag_clusters is not None:
        out.append(tx("at most {n} Multi-Tag Clusters", n=c.max_multi_tag_clusters))
    return out


def _under(constraints_label: str, tx: Text) -> str:
    return tx("the default constraints") if constraints_label == tx("Default constraints") else tx("the custom constraints")


def caveats(tx: Text) -> list[Paragraph]:
    return [[(tx(NA_CAVEAT), "italic")], [(tx(HIGH_G_CAVEAT), "italic")]]


def explanation(choice: Any, pair: Any, na: Any, settings_label: str, constraints_label: str,
                minimum_k: int, *, tx: Text) -> list[Paragraph]:
    """"Why this pair": the template, built only from NA, the constraints and counts (never Q, Coverage or
    Silhouette). `pair` is the chosen pair's GraphResult and `na` its NeighbourAgreement."""
    g, s = choice.chosen
    first: Paragraph = [(tx("Selected: g = {g}, s = {s}", g=g, s=s), "bold"), *_resolution(pair, tx)]
    c = choice.constraints
    names_of = constraint_names(tx)
    unexcluding = [names_of[x] for x in choice.excluded_none]
    qualify = (tx("{selected} of {pairs} pairs have a Selected Partition.", selected=choice.n_selected,
                  pairs=choice.n_pairs) + " " +
               tx("{n} qualify under {under}: {constraints}.", n=len(choice.qualifying),
                  under=_under(constraints_label, tx), constraints=tx.join(constraint_phrases(c, tx), serial=True)))
    if unexcluding:
        qualify += " " + tx.n(len(unexcluding), one="The {names} constraint excluded no pair.",
                              other="The {names} constraints excluded no pair.", names=tx.join(unexcluding))
    bg, bs = choice.best
    near = len(choice.near_best)
    pick = (tx("The highest Neighbour Agreement among them is {na} (g = {g}, s = {s}).",
               na=tx.fixed(choice.max_na, ".2f"), g=bg, s=bs) + " " +
            tx.n(near, one="{n} pair is within {tolerance} of it, and of these the one with the smallest g, then the "
                           "smallest s, is selected.",
                 other="{n} pairs are within {tolerance} of it, and of these the one with the smallest g, then the "
                       "smallest s, is selected.", tolerance=tx.fixed(c.tolerance, ".2f")))
    out: list[Paragraph] = [first, [(f"{constraints_label} · {settings_label}.", None)], [(qualify, None)],
                            [(pick, None)], [(_own_agreement(na, tx), None)]]
    return out + _partition_notes(pair, minimum_k, tx) + caveats(tx)


def pair_explanation(choice: Any, at: tuple[int, int], pair: Any, na: Any, settings_label: str,
                     constraints_label: str, minimum_k: int, reason_words: Mapping[str, str], *,
                     tx: Text) -> list[Paragraph]:
    """"Why this pair" for an inspected pair other than the selected one: whether it qualifies and, if it does, why
    another pair was selected. The same facts as `explanation` (NA, the constraints and counts). `pair` is the
    inspected pair's GraphResult, `na` its NeighbourAgreement and `reason_words` the words of each exclusion reason."""
    g, s = at
    first: Paragraph = [(tx("Inspected: g = {g}, s = {s}", g=g, s=s), "bold")]
    first += _resolution(pair, tx) if pair.selected_resolution is not None else [(".", None)]
    c = choice.constraints
    reasons = choice.reasons[at]
    if reasons:
        verdict = tx("It does not qualify: {reasons}.", reasons=tx.join([reason_words[r] for r in reasons]))
    else:
        bg, bs = choice.best
        values = {"tolerance": tx.fixed(c.tolerance, ".2f"), "na": tx.fixed(choice.max_na, ".2f"), "g": bg, "s": bs}
        verdict = (tx("It qualifies and is within {tolerance} of the highest Neighbour Agreement among the qualifying "
                      "pairs, {na} (g = {g}, s = {s}); of these near-best pairs the one with the smallest g, then the "
                      "smallest s, is selected.", **values) if at in choice.near_best else
                   tx("It qualifies, but its Neighbour Agreement is more than {tolerance} below the highest among the "
                      "qualifying pairs, {na} (g = {g}, s = {s}).", **values))
    if choice.chosen is not None:
        verdict += " " + tx("The selected pair is g = {g}, s = {s}.", g=choice.chosen[0], s=choice.chosen[1])
    else:
        verdict += " " + tx("No pair qualifies under {under}.", under=_under(constraints_label, tx))
    out: list[Paragraph] = [first, [(f"{constraints_label} · {settings_label}.", None)], [(verdict, None)]]
    if na.value is not None:
        out.append([(_own_agreement(na, tx), None)])
    if pair.selected is not None:
        out += _partition_notes(pair, minimum_k, tx)
    return out + caveats(tx)


def _resolution(pair: Any, tx: Text) -> Paragraph:
    """A pair's Selected Resolution and its Workbench value, after its "g = …, s = …"."""
    wb = pair.workbench
    if wb["flag"] == "not_representable":
        where = tx("(cannot be entered as a two-decimal value)")
    else:
        where = tx("(Workbench {gamma})", gamma=tx.fixed(wb["gamma"], ".2f"))
    out: Paragraph = [(tx(", resolution {resolution} {where}.", resolution=tx.fixed(pair.selected_resolution, ".3f"),
                          where=where), None)]
    if wb["flag"] == "not_reproduced":
        out.append((" " + tx("Workbench {gamma} with the main seed shows a different partition.",
                             gamma=tx.fixed(wb["gamma"], ".2f")), None))
    return out


def _own_agreement(na: Any, tx: Text) -> str:
    own = tx.n(na.n_different, one="Its Neighbour Agreement is {na} over {n} neighbour with a different graph.",
               other="Its Neighbour Agreement is {na} over {n} neighbours with a different graph.",
               na=tx.fixed(na.value, ".2f"))
    if na.n_identical:
        own += " " + tx.n(na.n_identical, one="{n} more neighbour has an identical graph and is not counted.",
                          other="{n} more neighbours have an identical graph and are not counted.")
    return own


def _partition_notes(pair: Any, minimum_k: int, tx: Text) -> list[Paragraph]:
    """The Selected Partition's notes: the minimum Multi-Tag Clusters, a low Seed-Noise Floor."""
    out: list[Paragraph] = []
    if pair.n_multi == minimum_k:
        out.append([(tx("Its Selected Partition has the minimum {k} Multi-Tag Clusters; a coarser split was not "
                        "allowed.", k=minimum_k), None)])
    floor = pair.seed_noise["floor"]
    if floor < 0.5:
        out.append([(tx("The Seed-Noise Floor at this resolution is {floor}: the clustering also depends noticeably on "
                        "the seed.", floor=tx.fixed(floor, ".2f")), None)])
    return out


def no_qualifying_message(choice: Any, constraints_label: str, *, tx: Text) -> list[Paragraph]:
    excluded = ", ".join(tx("{phrase}: {alone} ({cumulative})", phrase=phrase, alone=e.alone, cumulative=e.cumulative)
                         for phrase, e in zip(constraint_phrases(choice.constraints, tx), choice.exclusion))
    return [[(tx("No pair qualifies"), "bold"),
             (" " + tx("under {under}. {selected} of {pairs} pairs have a Selected Partition. Excluded by each "
                       "constraint, alone (cumulative): {excluded}. Loosen a constraint, or inspect any pair in the "
                       "grid and apply it by hand.", under=_under(constraints_label, tx), selected=choice.n_selected,
                       pairs=choice.n_pairs, excluded=excluded), None)]]


def to_markdown(paragraphs: Sequence[Paragraph]) -> str:
    marks = {"bold": "**", "italic": "*", None: ""}
    return "\n\n".join("".join(f"{marks[style]}{text}{marks[style]}" for text, style in p) for p in paragraphs)


def to_text(paragraphs: Sequence[Paragraph]) -> str:
    return "\n\n".join("".join(text for text, _ in p) for p in paragraphs)


# ----------------------------------------------------------------------------- validation


def _degenerate(reason: str, count: int, tx: Text) -> str:
    if reason == "no_edges":
        return tx.n(count, one="{n} had no edges", other="{n} had no edges")
    if reason in ("no_stable_partition", "too_few_multi_tag_clusters"):
        return tx.n(count, one="{n} had no Selected Partition", other="{n} had no Selected Partition")
    return f"{count} {reason}"


def _range(spread: Any, tx: Text, digits: int = 3) -> str:
    return tx("{lo} to {hi}", lo=_signed(spread["min"], tx, digits), hi=_signed(spread["max"], tx, digits))


def _signed(value: float, tx: Text, digits: int = 3) -> str:
    return tx.fixed(value, f".{digits}f").replace("-", "−")


def _degenerate_words(reasons: dict[str, int], tx: Text) -> str:
    groups: dict[str, int] = {}
    for reason, count in reasons.items():
        key = "no_stable_partition" if reason == "too_few_multi_tag_clusters" else reason
        groups[key] = groups.get(key, 0) + count
    return "; ".join(_degenerate(reason, count, tx) for reason, count in groups.items())


def cluster_name(cluster: dict[str, Any], names: Any) -> str:
    """"C2 (Strategy, Tactical, …)": the label and up to three member tags."""
    members = [names.get(t, str(t)) for t in cluster["members"]]
    shown = ", ".join(members[:3]) + (", …" if len(members) > 3 else "")
    return f"{cluster['label']} ({shown})"


def null_sentences(summary: Any, *, tx: Text) -> list[Paragraph]:
    n = summary["null"]
    r, q = n["replicates"], n["q"]
    reach = q["reach"]
    head = tx("Q at resolution {resolution} is {q};", resolution=tx.fixed(summary["resolution"], ".3f"),
              q=_signed(q["observed"], tx)) + " "
    if reach:
        head += tx("{reach} of {r} shuffled networks reach it: Q not above the null.", reach=reach, r=r)
    else:
        head += tx("no shuffled network reaches it ({range}).", range=_range(q, tx))
    k, w = n["selected"], n["width"]
    if k:
        side = tx("narrower") if w["median"] < w["observed"] else tx("wider")
        values = {"k": k, "r": r, "side": side, "median": tx.fixed(w["median"], ".3g"),
                  "observed": tx.fixed(w["observed"], ".3g")}
        # two literal keys, not one chosen beforehand: the catalogue's parity scan reads only literals
        head += " " + (tx("{k} of {r} also have a Selected Partition, with {side} domains (median {median} against "
                          "{observed}; wider than all {k}).", **values) if w["narrower"] == k else
                       tx("{k} of {r} also have a Selected Partition, with {side} domains (median {median} against "
                          "{observed}; wider than {narrower} of {k}).", narrower=w["narrower"], **values))
    else:
        head += " " + tx("None of the {r} has a Selected Partition.", r=r)
    return [[(tx("Null Comparison"), "bold"), (" " + tx("({r} shuffled networks, same g and s).", r=r) + " " + head,
                                               None)],
            [(tx(NULL_CAVEAT), "italic")]]


def _ari_spread(ari: dict[str, Any], tx: Text) -> str:
    return tx("median ARI {median} ({p10}–{p90})", median=tx.fixed(ari["median"], ".2f"),
              p10=tx.fixed(ari["p10"], ".2f"), p90=tx.fixed(ari["p90"], ".2f"))


def subsample_sentences(summary: Any, names: Any, *, tx: Text) -> list[Paragraph]:
    sub = summary["subsample"]
    total = sub["subsamples"]
    re_, at = sub["reselected"], sub["at_resolution"]
    text = " " + tx("({total} random 80% subsets of the games, g′ = {g}, s′ = {s}).", total=total, g=sub["g"],
                    s=sub["s"]) + " "
    if re_["ari"]["median"] is None:
        text += tx("Re-selected: no subsample has a Selected Partition ({reasons}).",
                   reasons=_degenerate_words(re_["reasons"], tx))
    else:
        text += tx("Re-selected: {ari} over {n} of {total} subsamples", ari=_ari_spread(re_["ari"], tx),
                   n=total - re_["degenerate"], total=total)
        text += f"; {_degenerate_words(re_['reasons'], tx)}." if re_["degenerate"] else "."
    gamma = tx.fixed(summary["resolution"], ".3f")
    if at["ari"]["median"] is not None:
        text += " " + tx("At resolution {gamma}: {ari}", gamma=gamma, ari=_ari_spread(at["ari"], tx))
        text += f"; {_degenerate_words(at['reasons'], tx)}." if at["degenerate"] else "."
    n_clusters = len(re_["clusters"])
    spans: Paragraph = [(tx("Subsample Stability"), "bold"), (text, None)]
    any_dissolved = False
    for arm in ("reselected", "at_resolution"):
        gone = [c for c in sub[arm]["clusters"] if c["dissolved"]]
        if gone:
            any_dissolved = True
            if arm == "reselected":
                lead = tx.n(len(gone), one="{n} of {total} Multi-Tag Clusters is dissolved when re-selected (mean "
                                           "Jaccard ≤ 0.5):",
                            other="{n} of {total} Multi-Tag Clusters are dissolved when re-selected (mean Jaccard "
                                  "≤ 0.5):", total=n_clusters)
            else:
                lead = tx.n(len(gone), one="{n} of {total} Multi-Tag Clusters is dissolved at resolution {gamma} "
                                           "(mean Jaccard ≤ 0.5):",
                            other="{n} of {total} Multi-Tag Clusters are dissolved at resolution {gamma} (mean "
                                  "Jaccard ≤ 0.5):", total=n_clusters, gamma=gamma)
            spans.append((f" {lead} ", None))
            for i, c in enumerate(gone):
                spans.append((cluster_name(c, names), "italic"))
                spans.append((", " if i < len(gone) - 1 else ".", None))
    if not any_dissolved:
        spans.append((" " + tx("No Multi-Tag Cluster is dissolved (mean Jaccard ≤ 0.5) in either arm."), None))
    return [spans, [(tx(SUBSAMPLE_CAVEAT), "italic")]]


def validation_title(pair: tuple[int, int], *, tx: Text) -> str:
    return tx("Validation of g = {g}, s = {s}", g=pair[0], s=pair[1])


def validation_block(summary: Any, pair: tuple[int, int], chosen_pair: tuple[int, int] | None, ran_for_default: bool,
                     names: Any = None, *, tx: Text) -> list[Paragraph]:
    """The validation card. `summary` None: "Not validated". `ran_for_default` False when custom constraints chose
    `chosen_pair` and the shown validation is the default-constraint pair's."""
    names = names or {}
    out: list[Paragraph] = [[(validation_title(pair, tx=tx), "bold")]]
    if not ran_for_default and chosen_pair is not None and chosen_pair != pair:
        out.append([(tx("Validation ran for g = {g}, s = {s}, the pair chosen under the default constraints.",
                        g=pair[0], s=pair[1]), None)])
    if summary is None:
        return out + [[(tx("Not validated."), None)]]
    return out + null_sentences(summary, tx=tx) + subsample_sentences(summary, names, tx=tx)


# ----------------------------------------------------------------------------- the methods paragraph


METHODS_FIELDS = ("g_range", "s_range", "n_pairs", "weight", "min_months", "hidden", "scan_seeds", "gamma_step",
                  "min_multi", "tolerance", "constraints", "replicates", "subsamples")


def methods_paragraph(tx: Text, values: dict[str, Any] | None = None) -> str:
    """One template for `selection_report.md` and the User Guide (ch. 5, shown with placeholders; a test keeps them
    equal), filled with a run's values, or with ‹placeholders›."""
    values = values or {name: f"‹{name}›" for name in METHODS_FIELDS}
    return tx(
        "For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, "
        "{g_range} games per tag and {s_range} shared games with s ≤ g ({n_pairs} pairs), with {weight} as the "
        "Clustering Weight, a Minimum Months Filter of {min_months} and {hidden} hidden. On each distinct graph we ran "
        "Leiden (RBConfiguration, at most 1,000 passes) with {scan_seeds} seeds at every γ from 0 to Gibson and "
        "Mucha's γ_max(K), K being the number of tags with an edge, in steps of {gamma_step} (Gibson & Mucha 2022, "
        "SI §J); the derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound "
        "also holds for Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to "
        "the upper envelope of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality "
        "Domains (CHAMP; Weir et al. 2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution "
        "γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable "
        "when γ̂ lies in its own domain (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions "
        "with at least {min_multi} Multi-Tag Clusters, the Selected Partition has the widest domain in plain γ "
        "units, and the Selected Resolution is the domain's midpoint; the sources give no rule for choosing among "
        "Stable Partitions, and we did not rescale the width to log γ or to Gibson and Mucha's γ-scaled area "
        "(SI §A.7), whose usefulness the authors leave open. Neighbour Agreement is the mean adjusted Rand index "
        "between a pair's Selected Partition and those of its grid neighbours (g ± 1, s ± 1) with a different graph, "
        "on the shared tags with an edge in either graph. The chosen pair is the one with the smallest g, then the "
        "smallest s, among the pairs whose Neighbour Agreement is within {tolerance} of the highest, among pairs with "
        "{constraints}. We compared the chosen pair with {replicates} networks whose game–tag table was shuffled by "
        "curveball trades (every tag and game keeps its count), each analysed by the identical procedure (Karrer, "
        "Levina & Newman 2008, abstract, §III and §VI), and with {subsamples} random subsets of m = ⌊0.8·n⌋ of the n "
        "games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)). For each Multi-Tag Cluster "
        "we report Hennig's (2007, §2) mean best-match Jaccard on the tags present in both networks, over the B* "
        "subsamples in which the Cluster has a tag, and call it dissolved at a mean of 0.5 or less; the 0.6, 0.75 "
        "and 0.85 bands of the fpc package refer to the bootstrap and are not applied.", **values)


def methods_values(settings: Any, constraints: Any, *, tx: Text) -> dict[str, Any]:
    weight = tx("Lift") if settings.clustering_weight == "lift" else tx("shared games")
    n_hidden = len(settings.genre_hidden)
    hidden = (tx("{n} Genre Tags and each dataset's defining tag", n=n_hidden) if settings.hide_defining_tag
              else tx("{n} Genre Tags", n=n_hidden))
    return {"g_range": f"{settings.g_range[0]}–{settings.g_range[1]}",
            "s_range": f"{settings.s_range[0]}–{settings.s_range[1]}", "n_pairs": len(settings.pairs()),
            "weight": weight, "min_months": settings.min_months, "hidden": hidden, "scan_seeds": settings.scan_seeds,
            "gamma_step": tx.fixed(settings.gamma_step, "g"), "min_multi": settings.min_multi_tag_clusters,
            "tolerance": tx.fixed(constraints.tolerance, ".2f"),
            "constraints": tx.join(constraint_phrases(constraints, tx), serial=True),
            "replicates": settings.replicates, "subsamples": settings.subsamples}
