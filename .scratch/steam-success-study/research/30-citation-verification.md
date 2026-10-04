# Research 30: Citation verification for the User Guide

Ticket: [Citation verification for the User Guide](../issues/30-citation-verification.md)
Date: 2026-10-04

**Question:** For every source the User Guide may cite that was still unverified after [User Guide metric reference](../issues/26-user-guide-metric-reference.md), does the primary text (page, section or equation) back the claim the research notes attribute to it? Each source gets one verdict: confirmed (with locator), needs correcting (with the corrected statement) or drop (with a verified replacement where one exists).

## How to read this file

- Scope: [KR90], [M07], [ST04], [COH92], [LZ20], every source that [the metric reference findings](26-user-guide-metric-reference.md) lists at bibliographic or abstract level, and the graph-methods references in [the clustering findings](05-graph-clustering-methods.md) that were cited from memory. Sources already read in full text for research 26 ([NG04], [CNM04], [FB07], [BDG08], [BMS97], [T19], [H07], [SHR97], library docs) were not re-audited. [GSA04] and [GA05] were spot-checked because research 05 cited them from memory.
- Keys are those of research 26 and 05. Terms follow [CONTEXT.md](../../../CONTEXT.md).
- **Locators.** Where I read an author preprint or an arXiv version instead of the published article, page numbers are the preprint's. The guide should then cite section, equation, table or proposition numbers, which carry over, not those pages. Each such case is marked "preprint" in the table.
- **Unverified** means I could not reach the primary text. Paywalled or bot-blocked: APA PsycNet, Springer, Taylor & Francis, JSTOR, ScienceDirect (even its open archive), and the archive.org lending copy of the Kaufman & Rousseeuw book. It does not mean the claim is wrong. It means the guide cannot cite the source under the page-level rule in [User Guide scope and home](../issues/29-user-guide-scope-and-home.md) until someone with library access checks it.
- Quotes are kept to short phrases.

## Verdicts

| Key | Claim in research 26 / 05 | Verdict | Locator and note |
|---|---|---|---|
| [KR90] Kaufman & Rousseeuw 1990 | Silhouette bands (0.71–1.00 strong … ≤ 0.25 none), "often cited to p. 88"; via 05: PAM / medoid | **Drop** (unverified) | The book is not freely readable (archive.org lending copy only). **Replacement for the bands:** [SHR97] p. 10, Table 2, which presents them on its own authority ("Experience has led to the subjective interpretation…") and does **not** cite KR90 for them. **Replacement for PAM / medoid:** [SHR97] §2.1, eq. (2.1), p. 6 (medoids minimise total dissimilarity to their nearest medoid). |
| [SHR97] (as cited for the bands) | "Table 2 … citing [KR90]" | **Needs correcting** | Table 2 (p. 10) has no citation. Corrected statement: *bands from Struyf, Hubert & Rousseeuw (1997), p. 10, Table 2, offered by the authors as a "subjective interpretation" of the silhouette coefficient (the highest average silhouette width over several k) for partitioning methods.* |
| [ST04] Steinley 2004 | ARI ≥ .90 excellent, .80–.90 good, .65–.80 moderate, < .65 poor | **Drop** (unverified) | APA paywall; PubMed and PsycNet abstracts do not give the values. All other sightings are secondary. No verified replacement for the band. Bibliographic record confirmed: *Psychol. Methods* 9(3), 386–396. |
| [COH92] Cohen 1992 | w = .10 / .30 / .50 small / medium / large; w = \|phi\| for a 2 × 2 table | **Confirmed, with one correction** | Table 1, p. 157, row 6 (chi-square, w): .10 / .30 / .50. Row 2 (product-moment r) has the same values. Correction: Cohen does **not** state w = \|phi\|. For a 2 × 2 table it follows from w² = χ²/N = phi² (derivation). Alternatively, cite row 2, since phi is the product-moment r of two binary variables. |
| [LZ20] Li & Zhang 2020 | Steam tag co-occurrence network, Louvain; values unknown | **Confirmed; title needs correcting** | Full text (ACM DL, free access). Full title: *A preliminary network analysis on Steam game tags: another way of understanding game genres*, pp. 65–73. Louvain via Gephi: §3, §3.3, pp. 67–68. Network from all 378 Steam "Popular Tags", edge weight = number of games with both tags (as here), edges limited to the top connections in Steam's "Narrow by Tag" lists, 326 tags / 3,035 edges: §4, p. 68. **Values:** after removing the five highest-degree tags (Indie, Action, Adventure, Singleplayer, Casual) and 15 tags linked only to them (306 tags, 1,813 edges), the best of more than 100 runs gave Q = 0.414 with four communities. With the five tags kept, Q was 0.150: §5.2, p. 70. No silhouette, ARI or stability values. The authors note that Louvain "falls short" on small communities (p. 72). |
| [M07] Meilă 2007 | VI is a true metric (05) | **Confirmed** (preprint) | Author's revised preprint (2006): §4.1, Property 1 (VI satisfies the metric axioms). Bibliographic: *J. Multivariate Anal.* 98(5), 873–895, doi:10.1016/j.jmva.2006.11.013. Journal page not checked (ScienceDirect blocked). |
| [HA85] Hubert & Arabie 1985 | ARI corrects for chance agreement | **Drop as a cited locator** (unverified); claim confirmed elsewhere | Springer paywall. **Replacement:** [M07] §2.1, eq. (6) gives AR = (R − E[R]) / (1 − E[R]), attributes it to Hubert & Arabie, and says the expected value is 0, the maximum (identical partitions) is 1, and negative values can occur. [SK-ARI] (already full text) as a second source. |
| [R87] Rousseeuw 1987 | s(i) definition and −1…1 range; (05, via Wikipedia) s(i) = 0 for one-member clusters | **Drop** (unverified) | ScienceDirect open archive not reachable from here. **Replacements:** definition and range: [SHR97] pp. 9–10, eqs. (2.2)–(2.3) and the s(i) formula (same author). One-member-cluster convention: the scikit-learn source [SK-SRC] (sets them to 0; checked in research 05). Do not attribute the convention to R87 on Wikipedia's word. |
| [SH88] Shiffler 1988 | Max z in n values: √(n−1) (population SD), (n−1)/√n (sample SD) | **Drop** (unverified) | T&F / JSTOR paywall. The bound was checked numerically in research 26. **Replacement:** state it in the guide as a derivation (all but one value equal), with no citation. |
| [KVV04] Kannan, Vempala & Vetta 2004 | Conductance (cut / min volume) as "how much of a cluster's weight leaks to the rest" is their cluster-quality criterion | **Needs correcting** | §2, pp. 501–502 (author PDF of the J. ACM article). They define the conductance of a cut (S, S̄) as cut / min(a(S), a(S̄)), matching our formula. But their cluster-quality criterion is the **minimum conductance of cuts inside a cluster** (α), paired with ε, **the fraction of total edge weight between clusters** (Def. 2.1, p. 502). Corrected statement: *our conductance of cluster C is the cut conductance φ(C) = cut(C, V∖C) / min(vol C, vol V∖C) [F10 eq. 20; KVV04 §2]; KVV04's ε is our inter-cluster weight share.* |
| [F10] Fortunato 2010 | Coverage, performance, intra-cluster density; (05) intra/inter density "basic definitions" | **Confirmed, with a note** | arXiv 0906.0612. Intra- / inter-cluster density: §III.B.1, eqs. (1)–(2), p. 10. Performance eq. (12) and coverage: §III.C.2, p. 15. Conductance with total degrees: §IV.A, eq. (20), p. 18, adding that it is undefined when the denominator vanishes. Note: F10 defines these with **edge counts**. Our weighted coverage and weighted density are analogues, which the guide should say. |
| [B08] Blondel et al. 2008 | Louvain alternates local moves and aggregation; node order changes the result | **Confirmed** | arXiv 0803.0476v2, §2 (two phases repeated in passes). The output "depends on the order in which the nodes are considered": §2, arXiv p. 4. |
| [GMC10] Good, de Montjoye & Clauset 2010 | Degeneracy: many near-optimal, mutually inconsistent partitions; interpret cautiously; combine solutions | **Confirmed** | arXiv 0910.0165: abstract; §III ("Extreme degeneracy"); §VII Discussion, point 2 (exponential number of near-optimal partitions) and the closing paragraphs (combining many high-modularity partitions). The abstract also says Q_max depends on network size and module count. |
| [N04] Newman 2004 | Weighted network → multigraph; modularity with weights; strength = sum of edge weights | **Confirmed** | arXiv cond-mat/0407503. Weighted degree k_i = Σ_j A_ij: §II.A, eq. (5). Weighted modularity is the same formula, eq. (9), with weights: §II.C. Also on p. 7 there: "values around 0.3 or more usually indicate good divisions", **a further published Q rule of thumb**, notably from a word co-occurrence example (Fig. 3). |
| [RB06] Reichardt & Bornholdt 2006 | γ is their resolution parameter | **Confirmed** | arXiv cond-mat/0603718. Hamiltonian H = −Σ (A_ij − γ p_ij) δ(σ_i, σ_j): eq. (2), p. 3. With γ = 1 and p_ij = k_i k_j / 2M it reduces to modularity: p. 4. |
| [GSA04] Guimerà, Sales-Pardo & Amaral 2004 | Random graphs reach high Q; Q falls with density | **Confirmed** | arXiv cond-mat/0403660v2. Abstract (random and scale-free graphs "have modularity"). Fig. 1 and eq. (17): for large ER graphs Q ∼ (pS)^(−2/3), i.e. it falls as mean degree rises. |
| [GA05] Guimerà & Amaral 2005 | within-module z (eq. 3), participation P, role regions "heuristic" | **Confirmed, with a note** | arXiv q-bio/0502035. z: Methods, eq. (3); P: eq. (4), p. 9. Roles "defined heuristically", z ≥ 2.5 hubs, R1–R7 bounds: pp. 3–4. Note: GA05 uses **link counts** κ, not strengths, and does not fix the SD convention. Our weighted versions (and the population SD chosen in [Metric definition gaps](../issues/28-metric-definition-gaps.md)) are adaptations. |
| [KLN08] Karrer, Levina & Newman 2008 | Robustness under random perturbation, compared with random graphs | **Confirmed** | arXiv 0709.2108: abstract; §III (perturbation and VI, configuration-model random graph). Also useful for the guide: §I, eq. (1), p. 2 defines the modularity z-score against a random-graph ensemble. It says this "has a number of problems" (false positives and negatives), which supports showing `q_excess` and never `modularity_z` alone ([ticket 27](../issues/27-user-guide-wording-bands.md)). |
| [LF12] Lancichinetti & Fortunato 2012 | Consensus clustering improves stability and accuracy | **Confirmed** | arXiv 1203.6093, abstract. It also notes that results "depend on the specific random seeds". |
| [O10] Opsahl, Agneessens & Skvoretz 2010 | Invert weights for shortest paths; d = min Σ (1/w)^α | **Confirmed** (preprint) | Author preprint: §3, eq. (7) (inverted-weight Dijkstra distance) and the α-generalised distance after it, pp. 13–14. Journal pages (245–251) not checked. |
| [VEW09] van Eck & Waltman 2009 | Association strength (∝ lift) recommended; Jaccard set-theoretic, does not correct for tag frequency | **Confirmed** (preprint; upgraded from abstract) | ERIM report ERS-2009-001-LIS. Association strength c_ij / (s_i s_j): eq. (5), proportional to observed / expected co-occurrences under independence. Set-theoretic measures (incl. Jaccard): §3. Probabilistic measures correct for the "size effect": §4, Property 4.2. Recommendation: §6 (set-theoretic measures "should not be used to normalize co-occurrence data"; they score frequent objects higher). |
| [W08] Warrens 2008 | phi / phi_max = Loevinger's H; phi-max formula was "my own derivation" | **Confirmed; upgrades the formula** | Open access. phi_max = min(p1 q2, p2 q1) / √(p1 p2 q1 q2): §3.2, eq. (7), p. 784. Dividing phi by its maximum gives Loevinger's H: Proposition 2, p. 784. For p_a ≤ p_b this equals research 26's √(p_a(1−p_b) / (p_b(1−p_a))), so 2.10 can cite W08 instead of a private derivation. |
| [AIS93] Agrawal, Imieliński & Swami 1993 | "Confidence" is the standard association-rule term | **Confirmed** | §2 "Formal Model", p. 208. A rule X ⇒ I_j holds with "confidence factor" c if at least c% of transactions with X also contain I_j. Support is defined on the same page, and the paper stresses that the two are not to be confused. |
| [BH95] Benjamini & Hochberg 1995 | BH procedure; q ≤ 0.05 ⇒ expected share of false findings ≤ 5% | **Confirmed** | §3.1, procedure (1) and Theorem 1, p. 293 (FDR ≤ q* for independent tests). FDR as the expected proportion of false rejections: §2. Note: the paper defines the procedure, not "adjusted q-values". The q column is the standard step-up adjustment of procedure (1), as computed by SciPy `false_discovery_control` and statsmodels `multipletests` [SM-MT]. |
| [BY01] Benjamini & Yekutieli 2001 | Version for arbitrary dependence | **Confirmed** | Theorem 1.3, p. 1169 (q / Σ 1/i). Also Theorem 1.2, p. 1168: BH itself controls FDR under positive regression dependency (PRDS). That is the primary source for the "robust under positive correlation" remark currently cited to [SM-MT]. PRDS is narrower than "positive correlation", and tag-pair tests are not shown to satisfy it. |
| [J1912] Jaccard 1912 | Jaccard index = overlap of two sets | **Confirmed** | Scan of *New Phytologist* 11 (archive.org, Digital Library of India copy), §I, p. 39 and its footnote. "Coefficient of community" = species common to two districts / total species in the two districts together × 100, i.e. \|A ∩ B\| / \|A ∪ B\| as a percentage. |
| [STR14] Strona et al. 2014 | Curveball randomisation with fixed row and column totals | **Confirmed** | Open access. Abstract, p. 1. "Description of the algorithm", p. 3, Fig. 1. |

### Other observations from the primary texts

- **A comparable published Q now exists.** [LZ20] is the only published Steam tag network found. Its 0.414 comes from a network **pruned** of the five most common tags and capped to Steam's top related-tag links. Its 0.150 with those tags kept shows how much a few near-universal tags lower Q. Our Exclusions, Minimum Months Filter and Clustering Weight differ, so the numbers are context, not a benchmark.
- **A fourth modularity rule of thumb** (Q ≈ 0.3 or more, [N04] §II.C) belongs in the guide's Appendix A next to [NG04], [CNM04] and [FB07] if that appendix aims to list what readers will meet.
- **KVV04's ε** is exactly our inter-cluster weight share (1 − weighted coverage). It is a verified primary source for that column if one is wanted.

## Changes needed in earlier findings and tickets

Not edited here; listed for whoever revises them.

**[Research 26](26-user-guide-metric-reference.md)**
1. *Bands table, Mean silhouette row*: source = [SHR97] p. 10, Table 2. Remove "citing [KR90] (page not checked)". Remove [KR90] from Sources, or mark it "not used".
2. *Bands table, ARI row*: [ST04] stays unverified. Mark the row "not citable", or have someone verify it through APA PsycArticles. Until then the guide's Appendix A must leave it out.
3. *Bands table, phi row*: [COH92] Table 1, p. 157 (verified). Replace "w (= |phi| for a 2 × 2 table)" by the r row (.10 / .30 / .50), or keep w with the identity marked as a derivation.
4. *Bands table, Modularity*: optionally add [N04] §II.C ("around 0.3 or more").
5. *"Typical values in comparable work"* paragraph: replace with the verified [LZ20] facts above (Q 0.414 / 0.150, pruning, weighting, pp. 68–70). Fix the [LZ20] title (add the subtitle) and its status (full text).
6. *4.10 Conductance, Measures* and the [KVV04] row: apply the KVV04 correction. Cite [F10] eq. (20) and [KVV04] §2 for the formula. Optionally cite KVV04 Def. 2.1 for the inter-cluster weight share in 4.6.
7. *4.6 Coverage, 4.9 Densities*: cite [F10] §III.B.1 eq. (1) and §III.C.2, and say F10 counts edges while ours are weighted analogues.
8. *3.10 within_z, 3.11 participation*: cite [GA05] eqs. (3)–(4) as the unweighted originals. Our strength-based versions are adaptations.
9. *3.10 Range* and the Bands-table caveat that cite [SH88]: present the √(n−1) and (n−1)/√n caps as a derivation, without a citation.
10. *2.10 phi*: cite [W08] §3.2 eq. (7) for phi_max and Proposition 2 for Loevinger's H. Drop "my own derivation".
11. *2.12 Jaccard, 2.11 pair lift*: [VEW09] upgraded to full text (preprint): eq. (5), §3, §4 (Property 4.2), §6. [J1912] p. 39.
12. *3.6 Per-tag silhouette*: cite [SHR97] pp. 9–10 for the definition. [R87] stays unverified.
13. *5.1 ARI, Measures*: cite [M07] §2.1 eq. (6) (and [SK-ARI]) for the chance correction. [HA85] stays unverified.
14. *2.14 BH q, Limitations*: add [BY01] Theorem 1.2 as the primary source for BH under positive dependence (PRDS).
15. *Sources table*: update the status column per the Verdicts table (AIS93, B08, BH95, BY01, COH92, F10, GMC10, J1912, LZ20, N04, STR14, VEW09, W08 → full text with locators; HA85, KR90, R87, SH88, ST04 → unverified).

**[Research 05](05-graph-clustering-methods.md)**
16. §4 *Medoid*: replace [KR90] with [SHR97] §2.1 eq. (2.1).
17. §2 *Silhouette*: the s(i) = 0 convention for one-member clusters rests on [SK-SRC], not on [R87] via [WP-SIL].
18. §3 *Conductance*: apply the [KVV04] correction.
19. Citation caveat line: [RB06], [GSA04], [GA05], [KVV04], [M07], [KLN08], [VEW09] are now checked (locators above). [HA85] and [KR90] remain unverified. Add [M07]'s issue number and DOI.

**Tickets**
20. [User Guide metric reference](../issues/26-user-guide-metric-reference.md), Answer: "silhouette (Struyf, Hubert & Rousseeuw 1997, after Kaufman & Rousseeuw 1990)" → "(Struyf, Hubert & Rousseeuw 1997, Table 2)". "ARI (Steinley 2004)" → "unverified". "Li & Zhang 2020 record only" → full text, Q 0.414 / 0.150 reported.
21. [User Guide metric wording and interpretation bands](../issues/27-user-guide-wording-bands.md): Appendix A lists only bands with a confirmed locator. Silhouette ([SHR97] Table 2), modularity ([NG04], [CNM04], [FB07], optionally [N04]), cluster-wise Jaccard ([H07], [FPC]), roles ([GA05]), phi ([COH92] Table 1). **The Steinley ARI band is omitted** (or added later once verified). The `modularity_z` caveat can cite [KLN08] §I.
22. [User Guide scope and home](../issues/29-user-guide-scope-and-home.md), Appendix C: the citable set is the "Confirmed" rows above plus the full-text sources of research 26. Sources marked unverified (KR90, ST04, R87, HA85, SH88) do not appear. Preprint-located sources are cited by section, equation or table.

## Sources

Verification levels:
- **Full text**: I read the cited passage in the published version.
- **Full text (preprint)**: I read the passage in an author preprint or arXiv version; section, equation and table numbers are given, pages are the preprint's.
- **Full text (scan)**: I read a scan of the original printing.
- **Bibliographic**: record confirmed (Crossref, PubMed, publisher landing page), content not read.
- **Unverified**: primary text not reached.

| Key | Reference | Accessed copy | Level |
|---|---|---|---|
| [AIS93] | Agrawal, R., Imieliński, T., Swami, A. (1993). Mining association rules between sets of items in large databases. *Proc. ACM SIGMOD 1993*, 207–216. doi:10.1145/170035.170072 | https://www.math.unipd.it/~dulli/corso04/sigmod93.pdf | Full text |
| [B08] | Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. *J. Stat. Mech.* P10008. doi:10.1088/1742-5468/2008/10/P10008 | arXiv:0803.0476v2 | Full text (preprint) |
| [BH95] | Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. *J. R. Stat. Soc. B* 57(1), 289–300. doi:10.1111/j.2517-6161.1995.tb02031.x | https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_hochberg1995.pdf (scan of the journal pages) | Full text |
| [BY01] | Benjamini, Y., Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under dependency. *Ann. Stat.* 29(4), 1165–1188. doi:10.1214/aos/1013699998 | https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_yekutieli_ANNSTAT2001.pdf | Full text |
| [COH92] | Cohen, J. (1992). A power primer. *Psychol. Bull.* 112(1), 155–159. doi:10.1037/0033-2909.112.1.155 | https://www2.psych.ubc.ca/~schaller/528Readings/Cohen1992.pdf (scan of the journal pages) | Full text |
| [F10] | Fortunato, S. (2010). Community detection in graphs. *Phys. Rep.* 486(3–5), 75–174. doi:10.1016/j.physrep.2009.11.002 | arXiv:0906.0612 | Full text (preprint) |
| [GA05] | Guimerà, R., Nunes Amaral, L. A. (2005). Functional cartography of complex metabolic networks. *Nature* 433, 895–900. doi:10.1038/nature03288 | arXiv:q-bio/0502035 | Full text (preprint) |
| [GMC10] | Good, B. H., de Montjoye, Y.-A., Clauset, A. (2010). Performance of modularity maximization in practical contexts. *Phys. Rev. E* 81, 046106. doi:10.1103/PhysRevE.81.046106 | arXiv:0910.0165 | Full text (preprint) |
| [GSA04] | Guimerà, R., Sales-Pardo, M., Amaral, L. A. N. (2004). Modularity from fluctuations in random graphs and complex networks. *Phys. Rev. E* 70, 025101(R). doi:10.1103/PhysRevE.70.025101 | arXiv:cond-mat/0403660v2 | Full text (preprint) |
| [HA85] | Hubert, L., Arabie, P. (1985). Comparing partitions. *J. Classification* 2(1), 193–218. doi:10.1007/BF01908075 | none (Springer paywall) | Unverified; claim confirmed via [M07] §2.1 |
| [J1912] | Jaccard, P. (1912). The distribution of the flora in the alpine zone. *New Phytologist* 11(2), 37–50. doi:10.1111/j.1469-8137.1912.tb05611.x | https://archive.org/details/in.ernet.dli.2015.271400 (OCR of the bound volume) | Full text (scan) |
| [KLN08] | Karrer, B., Levina, E., Newman, M. E. J. (2008). Robustness of community structure in networks. *Phys. Rev. E* 77, 046119. doi:10.1103/PhysRevE.77.046119 | arXiv:0709.2108v1 | Full text (preprint) |
| [KR90] | Kaufman, L., Rousseeuw, P. J. (1990). *Finding Groups in Data*. Wiley. | none (archive.org lending copy, restricted) | Unverified |
| [KVV04] | Kannan, R., Vempala, S., Vetta, A. (2004). On clusterings: good, bad and spectral. *J. ACM* 51(3), 497–515. doi:10.1145/990308.990313 | https://www.cc.gatech.edu/~vempala/papers/jacm-spectral.pdf (journal pagination) | Full text |
| [LF12] | Lancichinetti, A., Fortunato, S. (2012). Consensus clustering in complex networks. *Sci. Rep.* 2, 336. doi:10.1038/srep00336 | arXiv:1203.6093 | Full text (preprint), abstract passage |
| [LZ20] | Li, X., Zhang, B. (2020). A preliminary network analysis on Steam game tags: another way of understanding game genres. *Proc. 23rd Int. Academic Mindtrek Conf.*, 65–73. doi:10.1145/3377290.3377300 | ACM DL PDF (free access) | Full text |
| [M07] | Meilă, M. (2007). Comparing clusterings: an information based distance. *J. Multivariate Anal.* 98(5), 873–895. doi:10.1016/j.jmva.2006.11.013 | https://sites.stat.washington.edu/mmp/Papers/compare-jmva-revised.ps (revised preprint, 2006) | Full text (preprint) |
| [N04] | Newman, M. E. J. (2004). Analysis of weighted networks. *Phys. Rev. E* 70, 056131. doi:10.1103/PhysRevE.70.056131 | arXiv:cond-mat/0407503 | Full text (preprint) |
| [O10] | Opsahl, T., Agneessens, F., Skvoretz, J. (2010). Node centrality in weighted networks: generalizing degree and shortest paths. *Social Networks* 32(3), 245–251. doi:10.1016/j.socnet.2010.03.006 | https://toreopsahl.com/wp-content/uploads/2010/04/node_centrality_in_weighted_networks1.pdf | Full text (preprint) |
| [R87] | Rousseeuw, P. J. (1987). Silhouettes. *J. Comput. Appl. Math.* 20, 53–65. doi:10.1016/0377-0427(87)90125-7 | none (ScienceDirect open archive not reachable from this environment) | Unverified |
| [RB06] | Reichardt, J., Bornholdt, S. (2006). Statistical mechanics of community detection. *Phys. Rev. E* 74, 016110. doi:10.1103/PhysRevE.74.016110 | arXiv:cond-mat/0603718v1 | Full text (preprint) |
| [SH88] | Shiffler, R. E. (1988). Maximum Z scores and outliers. *Am. Stat.* 42(1), 79–80. doi:10.1080/00031305.1988.10475530 | none (paywall) | Unverified |
| [SHR97] | Struyf, A., Hubert, M., Rousseeuw, P. J. (1997). Clustering in an object-oriented environment. *J. Stat. Softw.* 1(4), 1–30. doi:10.18637/jss.v001.i04 | https://www.jstatsoft.org/article/view/v001i04 | Full text |
| [ST04] | Steinley, D. (2004). Properties of the Hubert–Arabie adjusted Rand index. *Psychol. Methods* 9(3), 386–396. doi:10.1037/1082-989X.9.3.386 | PubMed 15355155 and PsycNet abstract only | Unverified (band values) |
| [STR14] | Strona, G., et al. (2014). A fast and unbiased procedure to randomize ecological binary matrices with fixed row and column totals. *Nat. Commun.* 5, 4114. doi:10.1038/ncomms5114 | https://www.nature.com/articles/ncomms5114.pdf | Full text |
| [VEW09] | van Eck, N. J., Waltman, L. (2009). How to normalize cooccurrence data? *JASIST* 60(8), 1635–1651. doi:10.1002/asi.21075 | https://repub.eur.nl/pub/14528/ERS-2009-001-LIS.pdf (ERIM report) | Full text (preprint) |
| [W08] | Warrens, M. J. (2008). On association coefficients for 2 × 2 tables and properties that do not depend on the marginal distributions. *Psychometrika* 73(4), 777–789. doi:10.1007/s11336-008-9070-3 | https://link.springer.com/content/pdf/10.1007/s11336-008-9070-3.pdf (open access) | Full text |

Library and other keys ([SK-ARI], [SK-SRC], [SM-MT], [SP-FE], [FPC], [NX-*]) are as in research 26 and 05.
