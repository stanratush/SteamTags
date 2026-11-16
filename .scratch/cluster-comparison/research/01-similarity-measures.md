# Research 01: Measures for the similarity of two Clusters from different datasets

Ticket: [01 Similarity measures](../issues/01-similarity-measures.md), for [04 Measures on real Builds](../issues/04-measures-on-real-builds.md)
Date: 2026-11-16

**Question:** A Cluster is a set of Tags. Two Top-N Datasets of one Build give two partitions of two overlapping but different Tag sets. Jaccard on the two Tag sets is the baseline. Which other measures are worth trying, and what does each answer that Jaccard does not?

**How to read this file.** **Established** statements report what a cited primary source says, with its section, equation or table. **Inference** marks my own derivations (mostly short algebra on the definitions), which no source states in this form. A source I could not read is marked **unverified**, with what the claim rests on instead. The source list at the end gives the access level of every reference. Terms follow [CONTEXT.md](../../../CONTEXT.md); "community" appears only when citing literature.

**Notation.** A is a Cluster of dataset 1, B a Cluster of dataset 2. a = |A|, b = |B|, n = |A ∩ B|. U₁ and U₂ are the Tag sets of the two networks, U = U₁ ∩ U₂ the common Tags, N = |U|. A′ = A ∩ U and B′ = B ∩ U are the Clusters restricted to the common Tags (a′, b′ their sizes; n is unchanged, because every shared Tag is common). The two containments are c_A = n/a (the share of A's Tags that are shared) and c_B = n/b.

---

## Summary

1. **Every symmetric set-overlap measure is a function of the two containments the view already shows.** Jaccard, Dice, cosine, the overlap coefficient and Hopcroft's match value are different means of c_A and c_B (Section B.2, inference). None of them adds information to the two percentages; they differ only in how they collapse two numbers into one. The choice that matters is whether to collapse at all.
2. **Jaccard cannot tell nesting from partial overlap, and its usual thresholds hide splits.** A Cluster nested in one twice its size has J = 0.5, the same as two equal Clusters sharing two thirds of their Tags. An even split into k parts gives J = 1/k for each part, so Hennig's 0.5 cut removes every split, and Greene et al.'s 0.3 removes splits into four or more. The containments separate these cases: nesting is c_A = 1 with c_B small.
3. **Chance correction is usable as a description, not as a test.** Under the permutation model the overlap of two Clusters is hypergeometric with mean a′b′/N [VEB10 §4.1 eq. 2; GA17 §4.1], so observed ÷ expected is the same construction as the repository's **Lift**. A p-value is not sound here: the cells of one partition are dependent, the Cluster sizes are outcomes and not fixed margins, the null (Tags shuffled at random between Clusters) is not a plausible alternative, and the Clusters are small. Gates & Ahn show that conclusions change with the random model and ask for the model to be justified [GA17 §1 and Discussion].
4. **The two partitions cover different Tag sets, and the literature's answer is to restrict to the common elements and report how many there are.** Hennig does this for cluster-wise Jaccard [H07 §2], Strehl & Ghosh for NMI with missing labels [SG02 §2.2, eq. 6], and the repository does it for **Neighbour Agreement** and **Subsample Stability**. I found no primary source that recommends treating missing elements as an extra class. The repository's own pair of **Hennig's Jaccard** and **Whole-Cluster Jaccard** is the cluster-level version of this choice and carries over directly.
5. **For the pair overview, ARI on the common Tags is already in the code and is the right default; plain NMI is not.** With tens of Tags and several Clusters, N/K is far below the level at which unadjusted NMI has a near-zero baseline [VEB10 §4, Fig. 1; §4.2]. If an information measure is wanted, it should be AMI, or the two conditional entropies, which say which partition is the finer one.
6. **The community-tracking literature matches one-to-many by thresholding a pairwise measure, and defines a split or merge by the count of matches.** Jaccard with θ between 0.1 and 0.5 [GDC10]; the minimum of the two containments with p = 0.5 to 0.7 [HKKS04]; two directional inclusions with α, β between 50% and 100% [BSK13]. The methods that name splits and merges explicitly use directional measures or a relaxed Jaccard threshold. This supports the map's design (ranked Cluster Matches, a user-set minimum) and argues for a low default minimum.
7. **Shortlist to run beside Jaccard** (Section G): the two containments (with their minimum as a strict summary), Jaccard on the common Tags, the overlap Lift on the common Tags, and ARI on the common Tags for the pair overview.

---

## A. What the repository already has

Not new, so not proposed below as new:

- **Jaccard on Tag sets, best match, with and without lost Tags.** `validation.compare` computes **Hennig's Jaccard** |C′ ∩ D′| / |C′ ∪ D′| on the surviving Tags and the **Whole-Cluster Jaccard** |C ∩ D′| / |C ∪ D′|, each as the maximum over the other partition's Clusters, plus the surviving-Tag count and share (`src/steamstudy/network/validation.py`, `compare`). The 0.5 dissolution cut is Hennig's [H07 §2].
- **ARI between two partitions with different Tag sets.** `selection.link` computes ARI on the Tags present in both networks that have an edge in at least one, and reports `n_shared`, `n_compared` and the Jaccard of the two node sets (`shared_jaccard`) and edge sets (**Edge Overlap**) beside it (`src/steamstudy/network/selection.py`, `link`). `validation.compare` uses the same comparison set. Both call `sklearn.metrics.adjusted_rand_score`.
- **Jaccard distance between game sets** for the silhouette and the **Cluster Center** (`metrics.jaccard_distances`). This is a Tag-to-Tag measure on games, not a Cluster-to-Cluster measure.
- **Lift** (observed ÷ expected co-occurrence) for Tag pairs, after van Eck & Waltman's association strength [VEW09 eq. 5].
- **NMI is not in the code.** The ticket says the repository uses ARI and NMI; a search of `src/` finds ARI only. NMI, AMI and VI would be new.

---

## B. Set-overlap measures for one pair of Clusters

### B.1 The candidates

None of these needs a common Tag universe: each uses only a, b and n. All are 0 exactly when the Clusters share no Tag. "Nested" means A ⊂ B, so n = a ≤ b.

| Measure | Formula | Range | Source | Size imbalance (a ≪ b) | Nested (A ⊂ B) |
|---|---|---|---|---|---|
| Jaccard | n / (a + b − n) | [0, 1]; 1 iff A = B | [J1912] p. 39; [VEW09] eq. 8 | Capped at a/b. Two Clusters of very different size can never score high. | a/b. Falls with the size ratio; indistinguishable from partial overlap. |
| Dice / Sørensen | 2n / (a + b) | [0, 1]; 1 iff A = B | Dice 1945, Sørensen 1948 (**unverified**); the form 2f(A∩B)/(f(A)+f(B)) is in [T77] p. 333 | Capped at 2a/(a+b). Monotone in Jaccard: D = 2J/(1+J) ([VEW09] §2 cites Anderberg 1973 for the monotone relation; the formula is algebra). Ranks every pair as Jaccard does. | 2a/(a+b). |
| Cosine / Ochiai | n / √(ab) | [0, 1]; 1 iff A = B | [O57] abstract (credited there to Otsuka); [VEW09] eq. 6 | Capped at √(a/b). Penalises imbalance less than Jaccard: SJ ≤ SC [VEW09 eq. 9]. | √(a/b). |
| Overlap coefficient (Szymkiewicz–Simpson; "inclusion index") | n / min(a, b) | [0, 1]; 1 iff one contains the other | [VEW09] eq. 7 and §2 (names: inclusion index, overlap measure, Simpson coefficient). Szymkiewicz 1934 and Simpson 1943 **unverified** | Ignores the larger Cluster's size. SC ≤ SI [VEW09 eq. 9]. | 1, whatever b is. A two-Tag Cluster inside a 30-Tag Cluster scores 1. |
| Containment of A in B | c_A = n / a | [0, 1]; 1 iff A ⊂ B | [B97] §2 (containment of A in B = \|S(A) ∩ S(B)\| / \|S(A)\|) | Asymmetric by design: reported per direction. | c_A = 1, c_B = a/b. |
| Match value (minimum containment) | min(n/a, n/b) = n / max(a, b) | [0, 1]; 1 iff A = B | [HKKS04] eq. 3 | Capped at a/b, like Jaccard. | a/b. |
| Tversky ratio model | n / (n + α(a − n) + β(b − n)), α, β ≥ 0 | [0, 1] | [T77] p. 333 | Set by α, β. | α = 1, β = 0 gives c_A; α = β = 1 gives Jaccard; α = β = ½ gives Dice [T77 p. 333]. |

**Established.**
- van Eck & Waltman order the four symmetric measures: association strength ≤ Jaccard ≤ cosine ≤ inclusion index [VEW09 eq. 9].
- They define a "set-theoretic" similarity measure by three properties (minimum when disjoint; unchanged when all counts are multiplied by a constant; strictly decreasing when one set grows and the overlap stays) [VEW09 §3, Properties 3.1–3.3, Definition 3.1]. Jaccard and cosine qualify. The inclusion index does not: it only satisfies the weak form (non-increasing, Property 3.4) and is a "weak set-theoretic" measure [VEW09 Definition 3.2]. Weak measures need not reach their maximum only for identical sets [VEW09 Properties 3.6–3.7 and the remark after Proposition 3.1].
- Broder defines resemblance (= Jaccard) and containment side by side as the measures for "roughly the same" and "roughly contained", and notes that 1 − resemblance is a metric [B97 abstract, §1–2].
- Tversky's ratio model is asymmetric whenever α ≠ β and the two sets differ in measure [T77 p. 333].
- Hopcroft et al. say their minimum-of-containments match is high only "when two clusters have many papers in common and are roughly of the same size" [HKKS04, text after eq. 3].

### B.2 They are all means of the two containments

**Inference** (algebra on the definitions above).

- Overlap coefficient = max(c_A, c_B).
- Cosine = √(c_A · c_B), the geometric mean.
- Dice = 2 c_A c_B / (c_A + c_B), the harmonic mean.
- Jaccard = 1 / (1/c_A + 1/c_B − 1).
- Match value = min(c_A, c_B).
- Order: **Jaccard ≤ match ≤ Dice ≤ cosine ≤ overlap coefficient**. Jaccard ≤ match because a + b − n ≥ max(a, b), with equality exactly when the smaller Cluster is nested in the larger.

So once the view shows c_A and c_B (decided on the map), a symmetric score is a display choice about how to rank and filter, not extra evidence. Two consequences:

1. **Dice is redundant beside Jaccard** (same ranking, same information). Cosine differs in ranking only for unequal sizes, and less than the minimum/maximum do.
2. **The informative pair is the minimum and the maximum.** The maximum (overlap coefficient) says "one of the two is mostly inside the other". The minimum says "each is mostly the other". Their gap is the nesting signal.

### B.3 Worked cases

**Inference.** Values for typical situations (J = Jaccard, cos = cosine, OC = overlap coefficient):

| Situation | a, b, n | c_A | c_B | J | cos | OC |
|---|---|---|---|---|---|---|
| Identical | 6, 6, 6 | 1 | 1 | 1 | 1 | 1 |
| Equal size, two thirds shared | 6, 6, 4 | 0.67 | 0.67 | 0.50 | 0.67 | 0.67 |
| A nested in B, half its size | 3, 6, 3 | 1 | 0.50 | 0.50 | 0.71 | 1 |
| B split evenly in three; A is one part | 4, 12, 4 | 1 | 0.33 | 0.33 | 0.58 | 1 |
| Two-Tag Cluster inside a large one | 2, 20, 2 | 1 | 0.10 | 0.10 | 0.32 | 1 |
| Two-Tag Cluster, one Tag shared with a large one | 2, 20, 1 | 0.50 | 0.05 | 0.05 | 0.16 | 0.50 |

Rows 2 and 3 have the same Jaccard and mean opposite things. Rows 5 and 6 show the overlap coefficient's weakness: with small Clusters it reaches 1 or 0.5 on one or two Tags. Any measure that ignores the larger set needs a floor on n or on the smaller Cluster's size, or it must be read beside the minimum.

---

## C. Chance correction

### C.1 What overlap the sizes alone would give

**Established.**
- The usual random model for two clusterings is the **permutation model**: the number and sizes of the clusters are fixed and the elements are shuffled between them [VEB10 §4.1, citing Lancaster 1969; GA17 §1]. Under it the contingency table follows the generalised hypergeometric distribution [GA17 §4.1], and each cell n_ij is hypergeometric with support max(a_i + b_j − N, 0) … min(a_i, b_j) [VEB10 eq. 2, the inner sum]. This is the model behind ARI (Hubert & Arabie 1985, per [VEB10 §4.1] and [M07 §2.1]) and AMI [VEB10 §4.1].
- Observed ÷ expected under independence is van Eck & Waltman's association strength, their one "probabilistic" measure [VEW09 eq. 5, §4]. The repository's **Lift** is this ratio for Tag pairs.
- Chung et al. give a different null for the Jaccard coefficient of two presence–absence vectors: independent Bernoulli occurrences with probabilities p_i, p_j, under which E[J] = p_i p_j / (p_i + p_j − p_i p_j); they define the centred Jaccard J − E[J] and an exact test over the multinomial table, and report that earlier hypergeometric and combinatorial p-values "may lead to inaccurate estimates" under their null [CMSG19, Methods, Proposition 1, eqs. 2–5; Introduction]. Real & Vargas (1996) is the older probability table for Jaccard (**unverified**: bibliographic record only).

**Inference: the three forms for one pair of Clusters**, all on the common Tags U (N = |U|, restricted sizes a′, b′):

| Form | Formula | Range | Reads as |
|---|---|---|---|
| Expected overlap | E = a′b′ / N | [0, min(a′, b′)] | Shared Tags the sizes alone would give. |
| Overlap Lift | n / E = nN / (a′b′) | [0, N / max(a′, b′)] | 1 = as the sizes predict. Unbounded scale; largest for small Clusters. |
| Standardised overlap | z = (n − E) / √V, V = a′b′(N − a′)(N − b′) / (N²(N − 1)) | unbounded | Overlap in standard deviations above the size-only expectation. |
| Tail probability | P(X ≥ n), X ~ Hypergeometric(N, a′, b′) | (0, 1] | Not recommended; see C.2. |

The hypergeometric mean and variance are the standard textbook results; I did not check them against a textbook (**unverified** locator), but the mean follows from [VEB10 eq. 2] and both are easy to confirm by simulation in ticket 04.

All three **need a common Tag universe** and depend on its size. A Tag that is in only one network cannot be shared, so it must not count towards N, a′ or b′. Choosing U (all common Tags, or only common Tags in Multi-Tag Clusters on both sides, or the repository's "edge in at least one network" set) changes every value; the choice must be fixed and stated.

### C.2 Is a chance-corrected value sound when the sets come from a clustering?

**Established.**
- Gates & Ahn: "the premises of the permutation model are frequently violated; in many clustering scenarios, either the number of clusters, the size distribution of those clusters, or both vary drastically" [GA17 §1]. They show that the adjusted value and even the ranking of results change with the random model (fixed sizes, fixed number of clusters, all clusterings; one-sided or two-sided) and conclude that the model must be chosen from what the clustering method fixes and justified [GA17 Discussion, guidelines 1–2].
- Vinh et al.: adjustment matters most "when the number of data items is relatively small compared to the number of clusters"; at about N/K ≥ 100 the expected mutual information is near zero [VEB10 §4.2, Theorem 7 and the example after it; §4.3].

**Inference: four reasons a p-value is not sound here, and what remains usable.**

1. **Dependent cells.** Within one partition the Clusters are disjoint and exhaustive on U, so the overlaps of A with all Clusters of the other dataset sum to a′. One large overlap forces the others down. The K₁ × K₂ pair tests are one table, not independent draws. The single-cell hypergeometric is the correct *marginal* under the permutation model, but a list of per-pair p-values has no valid joint reading without a correction, and there are few enough Tags that a correction leaves nothing.
2. **The margins are outcomes.** Community detection chooses the number and sizes of the Clusters from the data; nothing fixes them in advance. By Gates & Ahn's guideline the permutation model fits a method with a fixed size sequence, which modularity optimisation is not.
3. **The null is not a live alternative.** Both partitions come from co-occurrence networks of games of the same Build, on largely the same Tags. "Tags are assigned to Clusters at random" is false before any data are seen, so rejecting it is uninformative. The repository already takes this position for the **Null Comparison** ("shows only that the network is not random") and avoids the words "significant" and "p-value".
4. **Small counts.** With Clusters of 2 to 10 Tags and N in the tens, the hypergeometric distribution has a handful of support points, so tail probabilities jump in coarse steps and E is often below 1.

What remains sound is the **descriptive** use: the expected overlap E and the Lift n/E state how far an overlap exceeds what two Clusters of these sizes share by size alone. That corrects the one thing Jaccard and the containments cannot see: two large Clusters in a small Tag universe overlap heavily by necessity. It should be worded like **Lift** and **Connection Ratio** (1 = as predicted), never as evidence that a match is real. The Lift's own weakness is the mirror image of the overlap coefficient's: it is largest for small Clusters (one shared Tag between two two-Tag Clusters among 60 common Tags gives a Lift of 15), so it should be shown with n, not used alone to rank. van Eck & Waltman note the same property of the association strength as the price of its frequency correction [VEW09 §4, Property 4.2].

ARI is the whole-table version of the same correction and inherits reasons 2 and 3; it stays useful as a relative index across pairs of datasets, as the repository already uses it.

---

## D. Weighted variants

**Established.**
- **Weighted (generalised) Jaccard**, for two non-negative vectors S, T: J(S, T) = Σ_k min(S_k, T_k) / Σ_k max(S_k, T_k) [I10 eq. 1]. Range [0, 1]; it reduces to Jaccard for 0/1 vectors. It is commonly named after Ružička (1958) (**unverified**; the formula is verified from [I10]).
- **Tversky's models** are stated for a general feature measure f, not for counts: f(A ∩ B) / (f(A ∩ B) + α f(A − B) + β f(B − A)) [T77 p. 333]. Any additive Tag weight gives a weighted Jaccard, Dice or containment.
- **GED's inclusion** is a weighted containment used for tracking: I(G₁, G₂) = (|G₁ ∩ G₂| / |G₁|) · (Σ_{x ∈ G₁∩G₂} SP_{G₁}(x) / Σ_{x ∈ G₁} SP_{G₁}(x)), the share of members times the share of member importance (SP is a centrality within the group; "any other measure which indicates member position within the community can be used") [BSK13 §4, eq. 3].

**Inference: what weighting would mean here.**

- With one weight w_t per Tag that is the same in both datasets, weighted Jaccard is Σ_{t ∈ A∩B} w_t / Σ_{t ∈ A∪B} w_t. With a weight per Tag per dataset (games having the Tag in that dataset, or the Tag's strength in that network), it is Σ min(w₁, w₂) / Σ max(w₁, w₂) with weight 0 where the Tag is not a member. Range [0, 1]. No common universe is needed.
- **What it changes.** Frequent or strongly connected Tags decide the score; Tags near the minimum-games threshold barely count. Those threshold Tags are the ones most likely to be in one network and not the other, so weighting would mostly mute the coverage difference between the datasets. That is a different question from Jaccard's ("do the big Tags travel together?"), not a refinement of it.
- **Problems specific to this comparison.**
  - Per-dataset weights are not on one scale: List Sizes can differ, and in a Tag-Specific Dataset the defining Tag is in every game (the map's open point on the defining Tag). A weight would have to be a share (of the dataset's games, or of the Cluster's total weight) before min and max mean anything.
  - With per-dataset weights, two Clusters with identical Tags score below 1. The score then mixes Tag-set agreement with frequency agreement, and no longer matches the shared/unique Tag lists the view shows.
  - Game-count weights bring game frequencies into a similarity the map restricts to Tag sets. Tag weights are still Tag-level, so it does not break the decision outright, but it comes close to the excluded "similarity computed on games".
- **Membership Stability** is a dataset-internal Tag weight on a common [0, 1] scale and would avoid the scale problem; no source proposes it and it would need its own justification.
- **Verdict:** not on the shortlist. If ticket 04 shows Jaccard dominated by threshold Tags, the restricted Jaccard of Section E.1 addresses that directly and stays explainable.

---

## E. Different Tag sets

### E.1 One pair of Clusters

**Established.** Hennig computes the cluster-wise Jaccard only on the points present in both data sets: the original cluster and the new clustering are both restricted before the maximum Jaccard is taken [H07 §2, steps (1)–(4); verified in [research 02](../../auto-parameter-selection/research/02-validation-methods.md)].

**Inference.** The repository's two definitions carry over unchanged in form:

| Measure | Formula | Range | Needs common universe | Size imbalance, nesting |
|---|---|---|---|---|
| Jaccard on common Tags (the form of **Hennig's Jaccard**) | n / (a′ + b′ − n) | [0, 1]; undefined when a′ or b′ is 0 | Yes: U | As Jaccard, on the restricted sizes. Never below the plain Jaccard. |
| Plain Jaccard (the form of the **Whole-Cluster Jaccard**) | n / (a + b − n) | [0, 1] | No | Section B. |

The gap between them is the part of the dissimilarity due to Tags that are absent from the other network, as opposed to Tags that are present there but grouped elsewhere. In a comparison of two datasets this split is the main thing a reader needs: at the same g and s, a Tag-Specific Dataset and Overall keep different Tags, and a low plain Jaccard may say nothing about the grouping. The same split applies to the containments (n/a′ beside n/a). As in the repository, a restricted Cluster with fewer than two Tags cannot be judged [H07 §2: single points are "perfectly stable, though totally meaningless"].

Baselga's partition of Sørensen dissimilarity into a turnover part (Simpson dissimilarity, 1 − overlap coefficient) and a nestedness-resultant part addresses a related split: dissimilarity from replacement against dissimilarity from one set being a subset of the other. The betapart documentation confirms the decomposition and its two references [BP]; the formulas themselves are **unverified** (paywalled). It is the published precedent for reporting the overlap coefficient beside a Jaccard-family measure to isolate nesting.

### E.2 Whole partitions, for the pair overview

| Measure | Formula | Range | Source | Notes |
|---|---|---|---|---|
| ARI | (RI − E[RI]) / (1 − E[RI]) under the permutation model | ≤ 1; 0 expected for random labellings; can be negative | Hubert & Arabie 1985 (**unverified**), as given in [M07 §2.1 eq. 6] and [VEB10, paragraph on the adjusted Rand index] | In the repository. 1 − ARI is not a metric [VEB10, same paragraph]. |
| NMI | I(U, V) divided by one of: √(H(U)H(V)) [SG02 eq. 2]; (H(U) + H(V))/2 [DDDA05 eq. 2]; max(H(U), H(V)); min; H(U, V) [VEB10 Table 2] | [0, 1] | [SG02], [DDDA05], [VEB10 Table 2] | Not chance-corrected; the baseline rises as N/K falls [VEB10 §4, Fig. 1; §4.2]. The normalisation must be named. |
| AMI | (I − E[I]) / (normaliser − E[I]), E[I] under the permutation model | ≤ 1; 0 expected for random labellings | [VEB10 §4.1, eq. 2, Table 2] | Loses the metric property [VEB10 Theorem 6]. |
| Variation of information | VI = H(U \| V) + H(V \| U) = H(U) + H(V) − 2 I(U, V) | [0, log N]; 0 iff identical | [M07 §4.1, Property 1: a metric]; identity as in [MGH11 Fig. 1] | A distance, not normalised; Karrer et al. divide by log n (cited in research 02). Not chance-corrected. |
| NVI, NID | 1 − I/H(U, V); 1 − I/max(H(U), H(V)) | [0, 1] | [VEB10 Theorems 3–4: both are metrics] | Vinh et al. recommend NID as the general-purpose measure when N/K is large [VEB10 abstract and Conclusions]. |

**Established: handling different element sets.**
- **Restrict to the common elements.** Hennig [H07 §2]; Strehl & Ghosh compute NMI on the objects with known labels in each labelling, L⁽q⁾, and weight each term by the share of known labels [SG02 §2.2, eq. 6]. The repository does this for ARI and reports the size of the comparison set.
- **Allow uncovered elements.** The NMI for covers of Lancichinetti, Fortunato & Kertész compares two sets of clusters on one node set in which a node may belong to several clusters "or indeed to no clusters" [MGH11 §I; LFK09 via MGH11, **unverified** at source]. It scores each cluster against its best match in the other cover [MGH11 eqs. 3–4]. McDaid et al. show it overestimates when one cover has far fewer clusters (a single matching cluster gives at least 0.5) and replace the normalisation by max(H(X), H(Y)) [MGH11 §III–IV, eqs. 7, 10].
- **Treat missing elements as a class.** I found no primary source that defines or recommends this for ARI, NMI or VI. (Limited search; unverified absence.)

**Inference.**
- **Restrict, and report coverage beside the score.** A partition measure on U answers "do the common Tags group the same way?". The share of each network's Tags that are common (the repository's `shared_jaccard`) answers "do the networks hold the same Tags?". They are separate facts and should stay separate numbers. A missing-class variant folds the second into the first: two Tags absent from the same network would count as agreeing, so the score would rise and fall with the thresholds g and s.
- **The comparison set must be stated.** The repository's set (common Tags with an edge in at least one network) drops Tags isolated in both, which agree trivially. Since only Multi-Tag Clusters are matched, One-Tag Clusters on U still enter a partition measure as singletons; that is what `selection.link` does today.
- **Small N.** With N in the tens and K from 3 to 15 Clusters, N/K is far below 100. Unadjusted NMI and VI would mostly track the number of Clusters. ARI or AMI are the defensible choices; of the two, ARI is already implemented and documented.
- **Direction at the partition level.** H(U | V) = 0 exactly when every Cluster of V lies inside one Cluster of U, so the two conditional entropies say which dataset's partition is the finer one (dataset 2 splits dataset 1's Clusters, or merges them). That is the overview-level counterpart of the two containments. It follows from the definition of conditional entropy; I did not locate the statement in a source. van Dongen's split/join distance is the count-based analogue (**unverified**; not read).
- **The cover NMI is not needed.** Its one advantage, uncovered nodes, is also given by restriction plus a coverage figure, and its best-match construction is a less transparent version of what the Cluster Match table shows.

---

## F. One-to-many matching, splits and merges

### F.1 What the tracking literature does

**Established.**

| Source | Pairwise measure | A match is | Split / merge | Thresholds |
|---|---|---|---|---|
| Hennig 2007 [H07 §2] | Jaccard on common points | The best-matching cluster only (maximum) | Not defined. ≤ 0.5 is "dissolution". 0.5 is "the smallest value so that every cluster in a partition consisting of more than one cluster can be dissolved by a new partition" (quoted in research 02). | 0.5 dissolved; > 0.75 "good recoveries, say". |
| Hopcroft et al. 2004 [HKKS04 eq. 3, Definition 3.1] | min(n/a, n/b) | The best match in the other clustering | Not defined; clusters are tracked one-to-one. | A "natural community" has best match > p in a fraction f of runs: f = 0.6, p = 0.7 (smaller clusters) and 0.5 (larger). Average best match of an ordinary cluster: about 0.40 (Table 2). |
| Palla et al. 2007 [PBV07 Methods; eq. 1] | Relative overlap \|A ∩ B\| / \|A ∪ B\| (Jaccard) | Communities of t and t+1 that fall in the same community of the joint graph (union of the two link sets, clique percolation); within one, matched "in descending order of their relative node overlap" | Growth, contraction, merging, splitting, birth, death are named; a merge or split is several communities of one step in one joint community. | None stated in the main text. Details are in the Supplementary Information (**not read**). The construction relies on clique percolation and does not transfer to modularity Clusters. |
| Greene et al. 2010 [GDC10 §3.1.2, §3.2.2, §4.2–4.3] | Jaccard | Every pair with sim > θ. Many-to-many on purpose: optimal bipartite matching "will not readily support the identification of dynamic events such as community merging and splitting". | Merge: two dynamic communities match one step community. Split: one dynamic community matches two step communities. Expansion / contraction: size change, "e.g." > 10%. | θ ∈ [0.1, 0.5] tested. θ ≤ 0.3 "significantly better"; θ = 0.1 nearly no loss over time; θ ≥ 0.5 "not appropriate" on the overlapping benchmarks; for merge and split data "lower thresholds yielded the highest accuracies". |
| Bródka et al. 2013, GED [BSK13 §4] | Inclusion in both directions, I(G₁, G₂) and I(G₂, G₁) (weighted containment, Section D) | A pair with at least one inclusion above its threshold | Continuing: both ≥ thresholds, equal size. Splitting: the later group is included in the earlier (≥ β), not the reverse (< α), and the earlier group has more than one such match. Merging: the mirror case. Forming / dissolving: both inclusions < 10% for every counterpart. | α, β suggested in [50%, 100%]; 10% for forming and dissolving. |
| Asur et al. 2007/2009 | Overlap share against each cluster's size | — | Merge and split by an overlap threshold κ | "30 or 50%" as reported in [BSK13 §5.1.1]. **Unverified** at source. |
| Rosvall & Bergstrom 2010 [RB10 Methods 3–4] | None | Every transition is drawn: an alluvial diagram's stream fields carry the nodes moving from one cluster to another | Shown as merging and diverging streams; no measure or threshold. (The 95% rule in that paper is for bootstrap significance within one network.) | None. |

### F.2 What this means for Cluster Matches

**Inference.**

- **The map's definition is the superset of all of them.** A Cluster Match is any pair sharing a Tag, ranked, with a user-set minimum. Greene's rule is that with a Jaccard minimum; Rosvall & Bergstrom's diagram is that with no minimum.
- **A Jaccard minimum of 0.5 makes the comparison one-to-one.** Two disjoint Clusters cannot both have Jaccard > 0.5 with the same Cluster (each would need more than half of it). This is the content of Hennig's 0.5. So at a default minimum of 0.5 no split or merge can ever be displayed. Greene et al.'s results point the same way: relaxed thresholds were needed exactly on the merge and split data. A default near 0.3, or lower, keeps two- and three-way splits visible.
- **Directional definitions of split and merge need no extra measure.** In the terms of the view: Cluster A of dataset 1 **splits** in dataset 2 when two or more Clusters B_i each have high containment in A (c_{B_i} high) while A's containment in each is low; A is **merged** when A and at least one other Cluster of dataset 1 have high containment in the same B. "Continues" is both containments high. This is GED's scheme with plain containment in place of weighted inclusion, and GED's 50% is the natural cut: a Cluster can be more than half inside at most one Cluster of the other dataset, so "mostly inside" is unambiguous.
- **"Split" and "merge" are the same event read in two directions.** Between two datasets there is no time order, so the view should describe the relation (A contains B₁ and B₂) and not name an event, or name it relative to the dataset the user is reading from.
- **Size change needs no threshold of its own.** Greene's 10% expansion/contraction is an example value and concerns time steps; here the two sizes and the two containments already say it.

---

## G. Shortlist for ticket 04

Run these beside plain Jaccard on the real Builds.

1. **The two containments, c_A = n/a and c_B = n/b, with min(c_A, c_B) as the strict summary** ([B97]; [HKKS04] eq. 3; the maximum is the overlap coefficient). *Answers what Jaccard cannot: whether one Cluster sits inside the other, which is what separates a split or merge from a partial overlap.* To check in 04: how often max and min disagree strongly, and whether the overlap coefficient is dominated by two- and three-Tag Clusters.
2. **Jaccard on the common Tags, n / (a′ + b′ − n), beside the plain Jaccard** (the form of Hennig's Jaccard against the Whole-Cluster Jaccard; [H07 §2]). *Answers whether a low Jaccard comes from Tags grouped differently or from Tags that are simply absent from the other network.* To check in 04: the size of the gap between the two for datasets of different size or density (the map's open point on lopsided comparisons).
3. **Overlap Lift on the common Tags, nN / (a′b′), shown with the expected overlap** (hypergeometric expectation under the permutation model, [VEB10 eq. 2], [GA17 §4.1]; the construction of [VEW09 eq. 5]). *Answers whether two Clusters share more Tags than two Clusters of their sizes would share by size alone.* Descriptive only, no p-value. To check in 04: whether it re-ranks matches between large Clusters in a useful way or is swamped by small Clusters.
4. **ARI on the common Tags for the pair overview, with the share of common Tags beside it** (already implemented in `selection.link`). *Answers, in one number per pair of datasets, how alike the two groupings are overall, which no per-Cluster Jaccard does.* To check in 04: whether AMI [VEB10] or the two conditional entropies add anything ARI does not show at these sizes.

**Considered and left out.** Dice (same ranking as Jaccard). Cosine (a mean of the two containments between Jaccard and the overlap coefficient; no distinct question). Weighted Jaccard (weights not comparable across datasets; Section D). Hypergeometric p-values and z-scores (not sound as tests; Section C.2). Unadjusted NMI and VI (biased at this N/K). Cover NMI (LFK defect; restriction plus coverage does the same job). A missing-Tags class in partition measures (no source; mixes coverage with grouping).

---

## Sources

Access levels: **Full text** = read for this note; **Repo** = verified earlier in this repository ([citation verification](../../steam-success-study/research/30-citation-verification.md), [research 02](../../auto-parameter-selection/research/02-validation-methods.md)), not re-read; **Unverified** = not read, with what the claim rests on. Volume, page and DOI details marked † were not on the copy I read and come from search listings or memory.

| Key | Reference | Access |
|---|---|---|
| [B97] | Broder, A. Z. (1997). On the resemblance and containment of documents. *Proc. Compression and Complexity of Sequences 1997*, 21–29†. doi:10.1109/SEQUEN.1997.666900†. https://www.cs.princeton.edu/courses/archive/spring13/cos598C/broder97resemblance.pdf | Full text (abstract, §1–2) |
| [BP] | betapart R package, `beta.pair` reference page. https://search.r-project.org/CRAN/refmans/betapart/html/beta.pair.html. Cites Baselga, A. (2010). Partitioning the turnover and nestedness components of beta diversity. *Global Ecol. Biogeogr.* 19, 134–143; Baselga, A. (2012). *Global Ecol. Biogeogr.* 21, 1223–1232. | Documentation page read. Baselga's papers and formulas **unverified**. |
| [BSK13] | Bródka, P., Saganowski, S., Kazienko, P. (2013). GED: the method for group evolution discovery in social networks. *Soc. Netw. Anal. Min.* 3(1), 1–14†. doi:10.1007/s13278-012-0058-8. https://arxiv.org/abs/1207.4297 | Full text (§3–5, eq. 3) |
| [CMSG19] | Chung, N. C., Miasojedow, B., Startek, M., Gambin, A. (2019). Jaccard/Tanimoto similarity test and estimation methods for biological presence-absence data. *BMC Bioinformatics* 20(Suppl 15), 644. doi:10.1186/s12859-019-3118-5. https://pmc.ncbi.nlm.nih.gov/articles/PMC6929325/ | Full text (via an automated reading of the PMC page; equations not checked by eye) |
| [DDDA05] | Danon, L., Díaz-Guilera, A., Duch, J., Arenas, A. (2005). Comparing community structure identification. *J. Stat. Mech.* P09008†. doi:10.1088/1742-5468/2005/09/P09008†. https://arxiv.org/abs/cond-mat/0505245 | Full text (arXiv v2, eq. 2) |
| [GA17] | Gates, A. J., Ahn, Y.-Y. (2017). The impact of random models on clustering similarity. *J. Mach. Learn. Res.* 18(87), 1–28. https://www.jmlr.org/papers/volume18/17-039/17-039.pdf | Full text (§1, §4.1, Discussion) |
| [GDC10] | Greene, D., Doyle, D., Cunningham, P. (2010). Tracking the evolution of communities in dynamic social networks. *Proc. ASONAM 2010*, 176–183†. doi:10.1109/ASONAM.2010.17†. Read in the extended version: Technical Report UCD-CSI-2011-06, University College Dublin (May 2011). https://researchrepository.ucd.ie/server/api/core/bitstreams/40b640fb-685f-4449-bd9a-3b179e829dc4/content | Full text (technical report §3–4). Section numbers are the report's; the conference paper was not compared. |
| [H07] | Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Comput. Stat. Data Anal.* 52(1), 258–271. doi:10.1016/j.csda.2006.11.025 | Repo (author preprint, §2) |
| [HKKS04] | Hopcroft, J., Khan, O., Kulis, B., Selman, B. (2004). Tracking evolving communities in large linked networks. *Proc. Natl. Acad. Sci. USA* 101(suppl. 1), 5249–5253. doi:10.1073/pnas.0307750100. https://people.bu.edu/bkulis/pubs/pnaspaper.pdf | Full text (eq. 3, Definition 3.1, Tables 2–3) |
| [I10] | Ioffe, S. (2010). Improved consistent sampling, weighted minhash and L1 sketching. *Proc. IEEE ICDM 2010*, 246–255†. doi:10.1109/ICDM.2010.80†. https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36928.pdf | Full text (§1, eq. 1) |
| [J1912] | Jaccard, P. (1912). The distribution of the flora in the alpine zone. *New Phytologist* 11(2), 37–50. doi:10.1111/j.1469-8137.1912.tb05611.x | Repo (scan, p. 39) |
| [M07] | Meilă, M. (2007). Comparing clusterings: an information based distance. *J. Multivariate Anal.* 98(5), 873–895. doi:10.1016/j.jmva.2006.11.013 | Repo (revised preprint: §2.1 eq. 6, §4.1 Property 1). Not re-read; the preprint is PostScript and I could not open it. |
| [MGH11] | McDaid, A. F., Greene, D., Hurley, N. (2011). Normalized mutual information to evaluate overlapping community finding algorithms. arXiv:1110.2515. https://arxiv.org/abs/1110.2515 | Full text (v2) |
| [O57] | Ochiai, A. (1957). Zoogeographical studies on the soleoid fishes found in Japan and its neighbouring regions-II. *Bull. Jpn. Soc. Sci. Fish.* 22(9), 526–530. doi:10.2331/suisan.22.526 | Abstract only (J-STAGE): C = 100c/√(S₁S₂), credited to Otsuka. Body (Japanese) not read. |
| [PBV07] | Palla, G., Barabási, A.-L., Vicsek, T. (2007). Quantifying social group evolution. *Nature* 446, 664–667†. doi:10.1038/nature05670†. https://arxiv.org/abs/0704.0744 | Full text (arXiv: main text, eq. 1–2, Methods). Supplementary Information **not read**. |
| [RB10] | Rosvall, M., Bergstrom, C. T. (2010). Mapping change in large networks. *PLoS ONE* 5(1), e8694. doi:10.1371/journal.pone.0008694 | Full text (via an automated reading of the journal page) |
| [SG02] | Strehl, A., Ghosh, J. (2002). Cluster ensembles: a knowledge reuse framework for combining multiple partitions. *J. Mach. Learn. Res.* 3, 583–617. https://www.jmlr.org/papers/volume3/strehl02a/strehl02a.pdf | Full text (§2.2, eqs. 2–3, 6) |
| [T77] | Tversky, A. (1977). Features of similarity. *Psychol. Rev.* 84(4), 327–352. doi:10.1037/0033-295X.84.4.327†. https://pages.ucsd.edu/~scoulson/203/tversky-features.pdf | Full text (scan with OCR, p. 333). The OCR garbles the Greek letters; the formula's structure is legible. |
| [VEB10] | Vinh, N. X., Epps, J., Bailey, J. (2010). Information theoretic measures for clusterings comparison: variants, properties, normalization and correction for chance. *J. Mach. Learn. Res.* 11, 2837–2854†. https://www.jmlr.org/papers/volume11/vinh10a/vinh10a.pdf | Full text (Table 2, Theorems 1–7, §4.1 eq. 2, §4.2, §4.3, Conclusions) |
| [VEW09] | van Eck, N. J., Waltman, L. (2009). How to normalize cooccurrence data? An analysis of some well-known similarity measures. *J. Am. Soc. Inf. Sci. Technol.* 60(8), 1635–1651. doi:10.1002/asi.21075. https://repub.eur.nl/pub/14528/ERS-2009-001-LIS.pdf | Full text (ERIM preprint: §2 eqs. 5–9, §3, §4). Equation numbers are the preprint's. |

**Unverified: cited by name only, not read.**

- Dice, L. R. (1945). Measures of the amount of ecologic association between species. *Ecology* 26(3), 297–302. doi:10.2307/1932409. (Paywalled. The formula rests on [T77] p. 333 and on [VEW09] §2, which names the Dice coefficient as monotonically related to Jaccard.)
- Sørensen, T. (1948). A method of establishing groups of equal amplitude in plant sociology based on similarity of species content. *K. Dan. Vidensk. Selsk. Biol. Skr.* 5(4), 1–34. (Citation from memory.)
- Szymkiewicz, D. (1934). Une contribution statistique à la géographie floristique. *Acta Soc. Bot. Pol.* 11(3), 249–265. Simpson, G. G. (1943). Mammals and the nature of continents. *Am. J. Sci.* 241(1), 1–31. (Citations from memory. The overlap coefficient's formula and its "Simpson coefficient" name rest on [VEW09] eq. 7 and §2.)
- Ružička, M. (1958). Anwendung mathematisch-statistischer Methoden in der Geobotanik. *Biologia (Bratislava)* 13, 647–661. (Citation from memory. The weighted Jaccard formula rests on [I10] eq. 1, which does not name Ružička.)
- Hubert, L., Arabie, P. (1985). Comparing partitions. *J. Classification* 2(1), 193–218. doi:10.1007/BF01908075. (Paywalled, as recorded in the citation verification. ARI's form and model rest on [M07] §2.1 and [VEB10] §4.1.)
- Real, R., Vargas, J. M. (1996). The probabilistic basis of Jaccard's index of similarity. *Syst. Biol.* 45(3), 380–385. doi:10.1093/sysbio/45.3.380. (Bibliographic record only.)
- Lancichinetti, A., Fortunato, S., Kertész, J. (2009). Detecting the overlapping and hierarchical community structure in complex networks. *New J. Phys.* 11, 033015. doi:10.1088/1367-2630/11/3/033015. (As described in [MGH11].)
- Asur, S., Parthasarathy, S., Ucar, D. (2009). An event-based framework for characterizing the evolutionary behavior of interaction graphs. *ACM Trans. Knowl. Discov. Data* 3(4), 16. (KDD 2007 version: doi:10.1145/1281192.1281290.) (Thresholds as reported in [BSK13] §5.1.1.)
- van Dongen, S. (2000). Performance criteria for graph clustering and Markov cluster experiments. CWI Technical Report INS-R0012. (Not read; mentioned only as the count-based analogue of the conditional entropies.)
- The hypergeometric variance in Section C.1 (standard result; no textbook locator checked).
- scikit-learn offers `adjusted_mutual_info_score` and `normalized_mutual_info_score` next to the `adjusted_rand_score` the repository uses; their defaults were not checked for this note.

**Not found.** A primary source that defines ARI, NMI or VI with missing elements treated as an extra class. A primary source that scores Clusters of two partitions with a Tag weight taken from a different table (games) than the one the similarity is defined on.
