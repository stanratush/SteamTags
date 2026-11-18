"""Bulgarian: cc_view (the Cluster Comparison mode). Keyed by the English text (see `steamstudy.i18n`)."""

MESSAGES: dict[str, str | dict[str, str]] = {
    "Cluster Comparison": "Сравнение на клъстери",
    "Shared settings": "Общи настройки",
    "Dataset pairs": "Двойки набори",
    "Comparing Clusters…": "Сравняване на клъстерите…",
    "{n} Comparable Tag: {share_a} of {a}'s, {share_b} of {b}'s": {
        "one": "{n} сравним таг: {share_a} от тези на {a}, {share_b} от тези на {b}",
        "other": "{n} сравними тага: {share_a} от тези на {a}, {share_b} от тези на {b}"},
    "{n} game in common": {"one": "{n} обща игра", "other": "{n} общи игри"},
    # the link diagram (issue 19)
    "Minimum Jaccard": "Минимален Jaccard",
    "show weaker": "покажи по-слабите",
    "hide weaker": "скрий по-слабите",
    "Line width = Match Jaccard. Click a curve for its match, a Cluster to show only its curves.":
        "Дебелина на линията = индекс на Jaccard на съвпадението. Щракнете върху крива за съвпадението ѝ, върху "
        "клъстер — за да видите само неговите криви.",
    "{n} Tag": {"one": "{n} таг", "other": "{n} тага"},
    "{n} Multi-Tag Cluster": {"one": "{n} многотагов клъстер", "other": "{n} многотагови клъстера"},
    "{a} ~ {b}: Match Jaccard {j}, {n} shared Tag": {
        "one": "{a} ~ {b}: индекс на Jaccard на съвпадението {j}, {n} общ таг",
        "other": "{a} ~ {b}: индекс на Jaccard на съвпадението {j}, {n} общи тага"},
    # the match detail (issue 20)
    "Match Jaccard": "Индекс на Jaccard на съвпадението",
    "Shared, % of {cluster}": "Общ дял от {cluster}",
    "comparable: {share}": "сравними: {share}",
    "Jaccard (comparable)": "Jaccard (сравними)",
    "Comparable Tags: {n_a} in {a}, {n_b} in {b}": "Сравними тагове: {n_a} в {a}, {n_b} в {b}",
    "Shared": "Общи",
    "Only in": "Само в",
    "Games in both Clusters": "Игри в двата клъстера",
    "Rank in {dataset}": "Място в {dataset}",
    "Matched in {dataset}": "Съвпадащи в {dataset}",
}
