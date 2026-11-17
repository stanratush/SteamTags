"""The Cluster Comparison's fixed sentences (`network/comparison_text.py`) against the spec's own examples."""

from __future__ import annotations

from steamstudy.i18n import text
from steamstudy.network import comparison_text as CT

EN, BG = text("en"), text("bg")


def test_source_lines_name_the_threshold_pair_never_the_cell():
    assert CT.source_line("pick", g=9, s=7, algorithm="Leiden", tx=EN) == "★ Selected Partition at g 9 · s 7 (chosen pair)"
    assert CT.source_line("cell", g=10, s=6, algorithm="Leiden", tx=EN) == "Selected Partition at g 10 · s 6"
    assert CT.source_line("hand", g=9, s=7, algorithm="Leiden", tx=EN) == "Set by hand: one Leiden run, main seed"
    assert CT.source_line("no_run", g=8, s=8, algorithm="Leiden", tx=EN) == (
        "No Automatic Parameter Selection run: network defaults, one Leiden run, main seed")
    assert "is gone" in CT.source_line("no_run", g=8, s=8, algorithm="Leiden", fallback="run_gone", tx=EN)
    assert "No qualifying pair" in CT.source_line("no_run", g=8, s=8, algorithm="Leiden", fallback="no_pick", tx=EN)
    assert CT.source_line("pick", g=9, s=7, algorithm="Leiden", tx=BG) == "★ Избрано разбиване при g 9 · s 7 (избраната двойка)"
    assert CT.source_line("hand", g=9, s=7, algorithm="Leiden", tx=BG) == (
        "Зададено ръчно: едно изпълнение на Leiden, основно начално число")


def test_the_row_figures_in_both_languages():
    assert CT.figures_line(0.52, 0.81, EN) == "Seed-Noise Floor 0.52 · NA 0.81"
    assert CT.figures_line(0.52, 0.81, BG) == "Праг на шума 0,52 · NA 0,81"
    assert CT.figures_line(1.0, None, EN) == "Seed-Noise Floor 1.00 · NA —"


def test_flags_and_tag_groups_carry_the_other_datasets_name():
    assert CT.flag_label("outside_network", other="Overall", minimum=0.1, tx=EN) == "No match: outside Overall's network"
    assert CT.flag_label("only_one_tag_clusters", other="Overall", minimum=0.1, tx=EN) == (
        "No match: only One-Tag Clusters in Overall")
    assert CT.flag_label("below_minimum", other="Overall", minimum=0.1, tx=EN) == "No match above 0.10"
    assert CT.flag_label("below_minimum", other="Overall", minimum=0.1, tx=BG) == "Няма съвпадение над 0,10"
    assert CT.flag_label("outside_network", other="Overall", minimum=0.1, tx=BG) == "Няма съвпадение: извън мрежата на Overall"
    assert CT.flag_label("", other="Overall", minimum=0.1, tx=EN) == ""
    assert CT.one_tag_counts(3, 2, other="Overall", tx=EN) == "3 Tags in One-Tag Clusters of Overall, 2 not in its network"
    assert CT.one_tag_counts(1, 1, other="Overall", tx=BG) == "1 таг в еднотагови клъстери на Overall, 1 не е в мрежата му"
    assert CT.tag_group("other_cluster", other="Overall", cluster="C5", tx=EN) == "in Overall C5"
    assert CT.tag_group("other_cluster", other="Overall", cluster="C5", tx=BG) == "в Overall C5"
    assert CT.tag_group("one_tag", other="Overall", tx=EN) == "One-Tag Cluster in Overall"
    assert CT.tag_group("not_in_network", other="Overall", n_games=2, minimum=5, tx=EN) == (
        "not in Overall's network (2 games, minimum 5)")
    assert CT.tag_group("not_in_network", other="Overall", n_games=2, minimum=5, tx=BG) == (
        "не е в мрежата на Overall (2 игри, минимум 5)")
    assert CT.tag_group("hidden", other="Strategy", tx=EN) == "hidden in Strategy (its defining Tag)"
    assert CT.tag_group("hidden", other="Strategy", tx=BG) == "скрит в Strategy (определящият му таг)"


def test_the_overlap_sentence_and_the_games_lines():
    assert CT.overlap_sentence(3, 3 / 1.25, 1.25, 38, EN) == (
        "3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)")
    counts = {"in_common": 38, "both": 5, "only_a": 10, "only_b": 3, "neither": 20}
    line = CT.games_count_line(counts, "Overall", "RPG", EN)
    assert [t.strip() for t, style in line if style == "bold"] == ["38", "5", "10", "3", "20"]
    assert "".join(t for t, _ in line) == (
        "Of 38 games in both datasets: 5 in both Clusters, 10 only in Overall, 3 only in RPG, 20 in neither.")
    assert "".join(t for t, _ in CT.no_games_line(0, EN)) == (
        "These two datasets have no games in common, so no game can be in both Clusters.")
    assert "".join(t for t, _ in CT.no_games_line(38, EN)) == "None of the 38 games in both datasets is in both Clusters."
    assert CT.cluster_name("Overall", "C3") == "Overall C3"
