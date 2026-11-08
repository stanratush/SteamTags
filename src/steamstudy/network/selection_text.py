"""Every fixed sentence of Automatic Parameter Selection, in one place.

The app, `selection_report.md` and the guide test all read these. Text is structured: a list of paragraphs, each a
list of (text, style) spans with style None, "bold" or "italic", so Dash and Markdown render the same words.

Every function takes the Interface Language's translator `tx` (`steamstudy.i18n`): the app passes the page's, and
`selection_report.md`, the CLI and the guide test pass `text("en")`, so the report stays English.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
LIMITATION = ("The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no "
              "part in the choice, so the Null Comparison is barely affected.")
SENTENCES = (NA_CAVEAT, HIGH_G_CAVEAT, DESCRIPTIVE_CAPTION, DESCRIPTIVE_HELP, DATASET_STRIP_SENTENCE, LEIDEN_ONLY,
             NO_SELECTION_YET, NOTHING_RUN, NULL_CAVEAT, SUBSAMPLE_CAVEAT, LIMITATION)


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


@dataclass(frozen=True)
class Section:
    """One part of the validation card: its title (an H5 on the card, bold in the report), its help key, the muted
    header after the title, and its prose."""

    title: str
    help_key: str
    header: str
    paragraphs: list[Paragraph]


def _degenerate(reason: str, count: int, tx: Text) -> str:
    if reason == "no_edges":
        return tx.n(count, one="{n} had no edges", other="{n} had no edges")
    if reason == "beyond_scan":
        return tx.n(count, one="{n} lay beyond their γ scan", other="{n} lay beyond their γ scan")
    if reason in ("no_stable_partition", "too_few_multi_tag_clusters"):
        return tx.n(count, one="{n} had no Selected Partition", other="{n} had no Selected Partition")
    return f"{count} {reason}"


def _signed(value: float, tx: Text, digits: int = 3) -> str:
    return tx.fixed(value, f".{digits}f").replace("-", "−")


def _degenerate_words(reasons: Mapping[str, int], tx: Text) -> str:
    groups: dict[str, int] = {}
    for reason, count in reasons.items():
        key = "no_stable_partition" if reason == "too_few_multi_tag_clusters" else reason
        groups[key] = groups.get(key, 0) + count
    return "; ".join(_degenerate(reason, count, tx) for reason, count in groups.items())


def cluster_name(cluster: Mapping[str, Any], names: Any) -> str:
    """"C2 (Strategy, Tactical, …)": the label and up to three member tags."""
    members = [names.get(t, str(t)) for t in cluster["members"]]
    shown = ", ".join(members[:3]) + (", …" if len(members) > 3 else "")
    return f"{cluster['label']} ({shown})"


def _q_sentence(summary: Any, tx: Text) -> str:
    """"Q at resolution … is …;" and the Null Comparison's state over the D shuffled networks with a Q."""
    n = summary["null"]
    q, d, r = n["q"], n["q_defined"], n["replicates"]
    out = tx("Q at resolution {resolution} is {q};", resolution=tx.fixed(summary["resolution"], ".3f"),
             q=_signed(q["observed"], tx)) + " "
    reasons = n["q_undefined_reasons"]
    if not d:
        if set(reasons) == {"no_edges"}:
            return out + tx("no shuffled network has edges, so Q cannot be compared.")
        return out + tx("no shuffled network has a Q ({reasons}), so Q cannot be compared.",
                        reasons=_degenerate_words(reasons, tx))
    if q["reach"]:
        out += tx("{k} of {d} shuffled networks with a Q reach it: Q not above the null", k=q["reach"], d=d)
    else:
        out += tx("none of the {d} shuffled networks with a Q reaches it (range over {d} shuffled networks: {lo} to "
                  "{hi})", d=d, lo=_signed(q["min"], tx), hi=_signed(q["max"], tx))
    return out + (f"; {_degenerate_words(reasons, tx)}." if n["q_undefined"] else ".")


def null_section(summary: Any, pair: tuple[int, int], *, tx: Text) -> Section:
    n = summary["null"]
    q, r, k = n["q"], n["replicates"], n["selected"]
    first = _q_sentence(summary, tx)
    if q["observed_from_runs"]:
        first += " " + tx("The runs at γ_obs found a Q of {q} on the observed network, above its Selected Partition's "
                          "{q0}; the comparison uses {q}.", q=_signed(q["observed"], tx),
                          q0=_signed(q["observed_selected"], tx))
    paragraphs: list[Paragraph] = [[(first, None)]]
    if n["weak"]:
        paragraphs.append([("⚠ " + tx("Most shuffled networks have no Q ({u} of {r}), so this comparison is weak.",
                                      u=n["q_undefined"], r=r), None)])
    if k:
        m, w = n["n_multi"], n["width"]
        values = {"n": w["wider"], "k": k, "median": tx.fixed(w["median"], ".3f"),
                  "observed": tx.fixed(w["observed"], ".3f")}
        width = (tx("Median domain width {median} vs observed {observed}; observed wider than {n}, equal to {t}, of "
                    "{k}.", t=w["equal"], **values) if w["equal"] else
                 tx("Median domain width {median} vs observed {observed}; observed wider than {n} of {k}.", **values))
        paragraphs.append([(" ".join([
            tx("Multi-Tag Clusters: observed {observed}, median {median} (range over {k} shuffled networks with a "
               "Selected Partition: {lo} to {hi}).", observed=m["observed"], median=tx.fixed(m["median"], "g"), k=k,
               lo=m["min"], hi=m["max"]),
            width, tx("Widths are upper bounds, conditional on the partitions the γ scan finds.")]), None)])
    else:
        paragraphs.append([(tx("None of the {r} shuffled networks has a Selected Partition.", r=r), None)])
    paragraphs.append([(tx(NULL_CAVEAT), "italic")])
    header = tx("({r} shuffled networks, per-pair procedure at g = {g}, s = {s})", r=r, g=pair[0], s=pair[1])
    return Section(tx("Null Comparison"), "selection.null", header, paragraphs)


def _ari(ari: Mapping[str, Any], tx: Text) -> dict[str, str]:
    """ARI can be negative: its ranges are always "from … to", never a compact dash."""
    return {"median": _signed(ari["median"], tx, 2), "p10": _signed(ari["p10"], tx, 2),
            "p90": _signed(ari["p90"], tx, 2)}


def _arm_groups(sub: Mapping[str, Any], key: str, value: bool, names: Any, tx: Text) -> list[tuple[str | None, list]]:
    """The Clusters with `key` == `value` in both arms, re-selected only and at resolution only, in Cluster order;
    empty groups left out. Each group: its words (None for "both arms") and its Clusters."""
    re_ = [c for c in sub["reselected"]["clusters"] if c[key] is value]
    at = {c["label"] for c in sub["at_resolution"]["clusters"] if c[key] is value}
    re_labels = {c["label"] for c in re_}
    at_clusters = [c for c in sub["at_resolution"]["clusters"] if c["label"] in at]
    groups = [(None, [c for c in re_ if c["label"] in at]),
              (tx("re-selected only"), [c for c in re_ if c["label"] not in at]),
              (tx("at resolution only"), [c for c in at_clusters if c["label"] not in re_labels])]
    return [(words, clusters) for words, clusters in groups if clusters]


def _lead(lead: str) -> list[Span]:
    """A list's lead: bold up to its first " (", the parenthesis plain."""
    cut = lead.find(" (")
    return [(lead, "bold")] if cut < 0 else [(lead[:cut], "bold"), (lead[cut:], None)]


def _grouped(lead: str, groups: list[tuple[str | None, list]], both: str, names: Any) -> Paragraph:
    spans: Paragraph = _lead(lead)
    for i, (words, clusters) in enumerate(groups):
        spans.append((("; " if i else " ") + (both if words is None else words) + ": ", None))
        for j, c in enumerate(clusters):
            spans.append((cluster_name(c, names), "italic"))
            if j < len(clusters) - 1:
                spans.append((", ", None))
    spans.append((".", None))
    return spans


def subsample_section(summary: Any, names: Any, *, tx: Text) -> Section:
    sub = summary["subsample"]
    total = sub["subsamples"]
    re_, at = sub["reselected"], sub["at_resolution"]
    if re_["ari"]["median"] is None:
        text = tx("Re-selected: no subsample has a Selected Partition ({reasons}).",
                  reasons=_degenerate_words(re_["reasons"], tx))
    else:
        share = re_["edged_share_mean"]
        text = tx("Re-selected: median ARI {median} (10th–90th percentile: {p10} to {p90}) over {n} of {total} "
                  "subsamples, on {share} of the tags", n=total - re_["degenerate"], total=total,
                  share=tx.num(None) if share is None else tx.pct(share, 0), **_ari(re_["ari"], tx))
        text += f"; {_degenerate_words(re_['reasons'], tx)}." if re_["degenerate"] else "."
    resolution = tx.fixed(summary["resolution"], ".3f")
    if at["ari"]["median"] is not None:
        text += " " + tx("At resolution {resolution}: median ARI {median} (10th–90th percentile: {p10} to {p90})",
                         resolution=resolution, **_ari(at["ari"], tx))
        text += f"; {_degenerate_words(at['reasons'], tx)}." if at["degenerate"] else "."
    elif at["degenerate"]:
        text += " " + tx("At resolution {resolution}: no subsample can be compared ({reasons}).",
                         resolution=resolution, reasons=_degenerate_words(at["reasons"], tx))
    paragraphs: list[Paragraph] = [[(text, None)]]
    n_clusters = len(re_["clusters"])
    both = tx("in both arms")
    dissolved = _arm_groups(sub, "dissolved_in_most", True, names, tx)
    if dissolved:
        words, first = dissolved[0]
        if words is None:  # "k of N Multi-Tag Clusters in both arms"
            dissolved[0] = (tx.n(n_clusters, one="{k} of {n} Multi-Tag Cluster in both arms",
                                 other="{k} of {n} Multi-Tag Clusters in both arms", k=len(first)), first)
        paragraphs.append(_grouped(tx("Dissolved in most subsamples (Hennig's Jaccard ≤ 0.5 in more than half; the "
                                      "majority is this study's rule):"), dissolved, both, names))
    borderline = _arm_groups(sub, "borderline", True, names, tx)
    if borderline:
        paragraphs.append(_grouped(tx("Borderline (the 95% Wilson interval contains ½):"), borderline, both, names))
    unassessable = _arm_groups(sub, "assessable", False, names, tx)
    if unassessable:
        paragraphs.append(_grouped(tx("Not assessable (fewer than 2 of its tags survive in every subsample):"),
                                   unassessable, both, names))
    if not dissolved and not unassessable:
        paragraphs.append([(tx("No Multi-Tag Cluster is dissolved in most subsamples in either arm."), None)])
    header = tx("({total} random 80% subsets of the games, g′ = {g}, s′ = {s}).", total=total, g=sub["g"], s=sub["s"])
    return Section(tx("Subsample Stability"), "selection.subsample", header, paragraphs)


def closing(*, tx: Text) -> list[Paragraph]:
    """The card's last lines: what Subsample Stability does not show, and the selection effect."""
    return [[(tx(SUBSAMPLE_CAVEAT), "italic")], [(tx(LIMITATION), "italic")]]


def section_paragraphs(section: Section) -> list[Paragraph]:
    """A section as report paragraphs: its title in bold before its header, then its prose."""
    return [[(section.title, "bold"), (" " + section.header, None)], *section.paragraphs]


def validation_title(pair: tuple[int, int], *, tx: Text) -> str:
    return tx("Validation of g = {g}, s = {s}", g=pair[0], s=pair[1])


def constraints_note(pair: tuple[int, int], chosen_pair: tuple[int, int] | None, ran_for_default: bool, *,
                     tx: Text) -> tuple[str, bool] | None:
    """The note under the title when custom constraints are in force: (text, is a warning), or None. `chosen_pair`
    None means no pair qualifies under the custom constraints."""
    if ran_for_default:
        return None
    if chosen_pair is None:
        return (tx("No pair qualifies under your constraints, so this is the validation of g = {g}, s = {s}, the pair "
                   "chosen under the default constraints.", g=pair[0], s=pair[1]), True)
    if chosen_pair != pair:
        return (tx("Validation ran for g = {g}, s = {s}, the pair chosen under the default constraints.", g=pair[0],
                   s=pair[1]), False)
    return None


def validation_block(summary: Any, pair: tuple[int, int], chosen_pair: tuple[int, int] | None, ran_for_default: bool,
                     names: Any = None, *, tx: Text) -> list[Paragraph]:
    """The validation card as report paragraphs. `summary` None: "Not validated". `ran_for_default` False when
    custom constraints are in force; then `chosen_pair` is their pair (None: none qualifies) and the shown
    validation is the default-constraint pair's."""
    names = names or {}
    out: list[Paragraph] = [[(validation_title(pair, tx=tx), "bold")]]
    note = constraints_note(pair, chosen_pair, ran_for_default, tx=tx)
    if note is not None:
        out.append([(("⚠ " if note[1] else "") + note[0], None)])
    if summary is None:
        return out + [[(tx("Not validated."), None)]]
    return (out + section_paragraphs(null_section(summary, pair, tx=tx))
            + section_paragraphs(subsample_section(summary, names, tx=tx)) + closing(tx=tx))


# ----------------------------------------------------------------------------- the methods paragraph


METHODS_FIELDS = ("top_n", "g_range", "s_range", "n_pairs", "weight", "min_months", "hidden", "scan_seeds", "gamma_step",
                  "min_multi", "tolerance", "constraints", "replicates", "subsamples")


def methods_paragraph(tx: Text, values: dict[str, Any] | None = None) -> str:
    """One template for `selection_report.md` and the User Guide (ch. 5, shown with placeholders; a test keeps them
    equal), filled with a run's values, or with ‹placeholders›."""
    values = values or {name: f"‹{name}›" for name in METHODS_FIELDS}
    return tx(
        "For each {top_n} Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, "
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
        "{constraints}. We compared each validated Threshold Pair with {replicates} networks whose game–tag table was "
        "shuffled by curveball trades (every tag and game keeps its count; Strona et al. 2014), each analysed by the "
        "identical procedure: the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the "
        "Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, "
        "abstract, §III and §VI). Q at the observed Selected Resolution was taken as the best of each network's scan "
        "envelope and {scan_seeds} Leiden runs at exactly that γ, on the observed network and every replicate "
        "alike; we report "
        "how many of the D shuffled networks with a defined Q reach the observed Q, and give no p-value, because the "
        "resolution and the pair were chosen on the observed data. We also compared the pair with {subsamples} random "
        "subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, "
        "⌊s·m/n⌋)), once re-selecting by the same per-pair procedure and once reading the partition at the observed "
        "resolution. For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on its tags "
        "present in both networks, over the B* subsamples in which at least two of them survive, with its Monte Carlo "
        "standard error and the frequencies of values ≤ 0.5 and > 0.75 with 95% Wilson intervals (Wilson 1927), and a "
        "Whole-Cluster Jaccard that counts lost tags as not recovered. We call a Cluster dissolved in most subsamples "
        "when its Jaccard is 0.5 or less in more than half of the B* subsamples (the per-subsample cut is Hennig's, "
        "the majority our rule); the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and are not "
        "applied. The pair was chosen on the same data, so Subsample Stability may be slightly optimistic.", **values)


def methods_values(settings: Any, constraints: Any, *, tx: Text, top_n: str = "Top-100") -> dict[str, Any]:
    """`top_n` is the Build-output wording: "Top-100" when every List Size is 100, else "Top-N"."""
    weight = tx("Lift") if settings.clustering_weight == "lift" else tx("shared games")
    n_hidden = len(settings.genre_hidden)
    hidden = (tx("{n} Genre Tags and each dataset's defining tag", n=n_hidden) if settings.hide_defining_tag
              else tx("{n} Genre Tags", n=n_hidden))
    return {"top_n": top_n, "g_range": f"{settings.g_range[0]}–{settings.g_range[1]}",
            "s_range": f"{settings.s_range[0]}–{settings.s_range[1]}", "n_pairs": len(settings.pairs()),
            "weight": weight, "min_months": settings.min_months, "hidden": hidden, "scan_seeds": settings.scan_seeds,
            "gamma_step": tx.fixed(settings.gamma_step, "g"), "min_multi": settings.min_multi_tag_clusters,
            "tolerance": tx.fixed(constraints.tolerance, ".2f"),
            "constraints": tx.join(constraint_phrases(constraints, tx), serial=True),
            "replicates": settings.replicates, "subsamples": settings.subsamples}
