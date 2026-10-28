"""Bulgarian: schema_tips. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    "1..K.": "1..K.",
    "Cluster of the source tag.": "Клъстер на изходния таг.",
    "Cluster of the target tag.": "Клъстер на целевия таг.",
    "Current Cluster Centers (other than the tag) that are no longer centers.":
        "Текущи центрове на клъстери (освен самия таг), които вече не са центрове.",
    "First cluster (or one_tag_pool).": "Първи клъстер (или one_tag_pool).",
    "Member tag ids by medoid_score, then the center tie-break.":
        "Идентификатори на таговете членове по medoid_score, после по правилото при равенство за центъра.",
    "Member tag names, matching member_tag_ids.": "Имена на таговете членове, в реда на member_tag_ids.",
    "Name of source_tag_id.": "Име на source_tag_id.",
    "Name of target_tag_id.": "Име на target_tag_id.",
    "Replicate number, 1..R.": "Номер на повторението, 1..R.",
    "Second cluster (or one_tag_pool).": "Втори клъстер (или one_tag_pool).",
    "Steam tag id.": "Идентификатор на тага в Steam.",
    "Tag id of the member with the highest intra-cluster strength (active weight).":
        "Идентификатор на члена с най-голяма сила вътре в клъстера (по активното тегло).",
    "Tag name.": "Име на тага.",
    "The Cluster Center's tag id (clusters of 3+ tags).":
        "Идентификатор на тага, който е център на клъстера (клъстери с 3+ тага).",
    "The higher tag id of the pair.": "По-големият идентификатор на таг в двойката.",
    "The lower tag id of the pair.": "По-малкият идентификатор на таг в двойката.",
    "The noise seed.": "Началното число за шума.",
    "The removed tag.": "Премахнатият таг.",
    "The replicate's seed (shuffle and clustering).": "Началното число на повторението (разбъркване и клъстеризация).",
    "Whether both tags are in the same cluster.": "Дали двата тага са в един и същи клъстер.",
}
