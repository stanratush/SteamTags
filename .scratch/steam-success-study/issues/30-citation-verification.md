# Citation verification for the User Guide
Type: research
Status: resolved
Blocked by: none

## Question

The User Guide cites only sources verified at page level ([User Guide scope and home](29-user-guide-scope-and-home.md)). For each source still unverified after [User Guide metric reference](26-user-guide-metric-reference.md), check the claim the research notes attribute to it against the primary text (page, section or equation), and say whether it is confirmed, needs correcting (give the corrected statement) or should be dropped (give a verified replacement where one exists):

- Kaufman & Rousseeuw 1990: the silhouette interpretation bands and their page;
- Meilă 2007;
- Steinley 2004: the ARI band values, so far seen only second-hand;
- Cohen 1992: the phi / effect-size band values, so far seen only second-hand;
- Li & Zhang 2020: full text;
- every source listed only bibliographically in [the metric reference findings](../research/26-user-guide-metric-reference.md) (and the graph-methods references in [the clustering findings](../research/05-graph-clustering-methods.md) cited from memory): check what the source actually says against each claim it backs.

Record each result with its exact locator, and list what in the findings and tickets would change.

## Answer

Resolved 2026-10-04 (research, AFK). Findings: [research/30-citation-verification.md](../research/30-citation-verification.md).

- **27 sources checked. Confirmed with locators:** Cohen 1992 (Table 1, p. 157: w and r both .10 / .30 / .50), Li & Zhang 2020 (full text), Meilă 2007 (§4.1, Property 1, preprint), Agrawal et al. 1993, Benjamini & Hochberg 1995, Benjamini & Yekutieli 2001, Blondel et al. 2008, Fortunato 2010, Good et al. 2010, Guimerà et al. 2004, Guimerà & Amaral 2005, Jaccard 1912, Karrer et al. 2008, Lancichinetti & Fortunato 2012, Newman 2004, Opsahl et al. 2010, Reichardt & Bornholdt 2006, Strona et al. 2014, van Eck & Waltman 2009, Warrens 2008. arXiv or author preprints are cited by section, equation or table number.
- **Needs correcting:** Struyf et al. 1997 do **not** cite Kaufman & Rousseeuw for the silhouette bands (Table 2, p. 10, "subjective interpretation"). Kannan et al. 2004 use *internal* conductance plus the inter-cluster weight fraction ε as their quality criterion, not our cut conductance. For that, cite Fortunato 2010 eq. (20). Cohen 1992 does not state w = |phi|. Fortunato 2010 and Guimerà & Amaral 2005 define their measures on edge or link counts; ours are weighted adaptations. The Li & Zhang title lacks its subtitle.
- **Drop (unverified, primary text not reachable):** Kaufman & Rousseeuw 1990 (→ Struyf et al. 1997 Table 2, and §2.1 for medoids), Steinley 2004 ARI bands (no verified replacement), Rousseeuw 1987 (→ Struyf et al. pp. 9–10; scikit-learn source for s = 0 in one-member clusters), Hubert & Arabie 1985 (→ Meilă 2007 §2.1 eq. 6, scikit-learn docs), Shiffler 1988 (→ state the z cap as a derivation).
- **New facts:** Li & Zhang report Q = 0.414 (four communities, best of more than 100 Gephi Louvain runs) on a Steam tag network pruned of its five most common tags and capped to Steam's top related-tag links. With those five tags kept, Q = 0.150 (§5.2, p. 70). Edge weight = shared games, as here. No silhouette, ARI or stability values. Newman 2004 gives another Q rule of thumb ("around 0.3 or more"). Warrens 2008 eq. (7) is a published source for the phi-maximum formula. Karrer et al. 2008 §I criticise the modularity z-score.

**What would change** (full list in the findings, "Changes needed"):
- [Research 26](../research/26-user-guide-metric-reference.md):
  - Bands table: silhouette row → SHR97 Table 2 only; ARI row → unverified, not citable; phi row → COH92 Table 1 p. 157, using the r row or marking w = |phi| as a derivation; optionally add N04 to the modularity rows.
  - "Typical values" paragraph → the verified Li & Zhang facts.
  - Conductance (4.10) and the KVV04 source note corrected.
  - F10 / GA05 entries noted as unweighted originals.
  - SH88 caps restated as a derivation; phi_max cited to W08.
  - Silhouette definition cited to SHR97; ARI chance correction cited to M07.
  - BY01 Theorem 1.2 added for BH under positive dependence.
  - Sources-table statuses updated.
- [Research 05](../research/05-graph-clustering-methods.md): medoid → SHR97 §2.1; singleton silhouette convention → scikit-learn source, not R87 via Wikipedia; conductance / KVV04 corrected; citation-caveat line updated (RB06, GSA04, GA05, KVV04, M07, KLN08, VEW09 now checked; HA85, KR90 still unverified).
- [User Guide metric reference](26-user-guide-metric-reference.md) Answer: the silhouette, ARI and Li & Zhang wording.
- [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md): Appendix A omits the Steinley ARI band until it is verified; the `modularity_z` caveat can cite KLN08.
- [User Guide scope and home](29-user-guide-scope-and-home.md): Appendix C is limited to the confirmed set; KR90, ST04, R87, HA85 and SH88 are not cited.
