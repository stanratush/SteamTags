# Prototype 04: measures on Build `20261008T221504Z-7a23ae9f`

Each dataset is on its pick (default Pair Constraints) and shows the stored Selected Partition. Lift, Leiden, no Minimum Months Filter, Genre Tags and the defining Tag hidden.

## 1. The datasets

| Dataset | g | s | γ | Tags in network | Multi-Tag Clusters (sizes) | One-Tag | Seed-Noise Floor | Workbench flag |
|---|---|---|---|---|---|---|---|---|
| overall | 17 | 2 | 1.15 | 29 | 4 (9, 9, 7, 4) | 0 | 1.00 | reproduced |
| puzzle | 14 | 2 | 1.09 | 31 | 4 (11, 8, 8, 4) | 0 | 0.52 | reproduced |
| rpg | 7 | 5 | 2.01 | 71 | 15 (8, 7, 7, 7, 6, 5, 4, 4, 4, 3, 3, 3, 3, 2, 2) | 3 | 0.80 | reproduced |
| strategy | 14 | 2 | 1.01 | 39 | 3 (16, 12, 11) | 0 | 1.00 | reproduced |
| simulation | 14 | 5 | 0.86 | 38 | 3 (18, 13, 7) | 0 | 1.00 | reproduced |

Defining Tag of each dataset, and where it sits in the others:

| Dataset | Defining Tag | Hidden here | in overall | in puzzle | in rpg | in strategy | in simulation |
|---|---|---|---|---|---|---|---|
| puzzle | Puzzle | yes | hidden (1 games) | hidden (100 games) | hidden (1 games) | hidden (2 games) | hidden (2 games) |
| rpg | RPG | yes | hidden (38 games) | hidden (15 games) | hidden (100 games) | hidden (32 games) | hidden (15 games) |
| strategy | Strategy | yes | hidden (24 games) | hidden (28 games) | hidden (21 games) | hidden (100 games) | hidden (48 games) |
| simulation | Simulation | yes | hidden (28 games) | hidden (30 games) | hidden (15 games) | hidden (55 games) | hidden (100 games) |

## 2. Pair overview

ARI and AMI on the `selection.link` set (Common Tags with an edge in at least one network). "Mean best J" is the Tag-weighted mean, over a dataset's Multi-Tag Clusters, of each Cluster's best whole-Cluster Jaccard.

| A | B | Tags A | Tags B | Common | % of A | % of B | Compared | Clusters A/B | Matches | ARI | AMI | Mean best J (A) | Mean best J (B) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| overall | puzzle | 29 | 31 | 16 | 55% | 52% | 16 | 4/4 | 8 | 0.23 | 0.19 | 0.25 | 0.21 |
| overall | rpg | 29 | 71 | 28 | 97% | 39% | 28 | 4/15 | 16 | 0.17 | 0.26 | 0.26 | 0.16 |
| overall | strategy | 29 | 39 | 24 | 83% | 62% | 24 | 4/3 | 7 | 0.32 | 0.39 | 0.33 | 0.37 |
| overall | simulation | 29 | 38 | 22 | 76% | 58% | 22 | 4/3 | 7 | 0.27 | 0.32 | 0.24 | 0.33 |
| puzzle | rpg | 31 | 71 | 23 | 74% | 32% | 23 | 4/15 | 15 | 0.07 | 0.12 | 0.18 | 0.09 |
| puzzle | strategy | 31 | 39 | 15 | 48% | 38% | 15 | 4/3 | 7 | 0.30 | 0.22 | 0.17 | 0.20 |
| puzzle | simulation | 31 | 38 | 16 | 52% | 42% | 16 | 4/3 | 5 | 0.07 | 0.15 | 0.17 | 0.19 |
| rpg | strategy | 71 | 39 | 31 | 44% | 79% | 31 | 15/3 | 18 | 0.10 | 0.14 | 0.12 | 0.21 |
| rpg | simulation | 71 | 38 | 27 | 38% | 71% | 27 | 15/3 | 14 | 0.11 | 0.18 | 0.10 | 0.21 |
| strategy | simulation | 39 | 38 | 32 | 82% | 84% | 32 | 3/3 | 6 | 0.53 | 0.54 | 0.50 | 0.53 |

Spearman across the 10 pairs: ARI vs AMI 0.90; ARI vs mean best J 0.84; ARI vs smaller Common-Tag share 0.65.

## 3. All matches: how the measures relate

103 Cluster Matches over 10 pairs of datasets. Jaccard: median 0.09, quartiles 0.06–0.16, max 0.58.

| Measure vs whole-Cluster Jaccard | Spearman ρ |
|---|---|
| cont_min | 0.96 |
| cont_max | 0.83 |
| lift | 0.38 |
| jaccard_common (80 judged) | 0.91 |

Common-Tag Jaccard − Jaccard: median 0.06, max 0.45; 27 of 80 matches gain 0.10 or more. 23 matches show "—" (a Cluster with fewer than two Common Tags).

One-shared-Tag matches: 58 of 103 (56%); their Jaccard max 0.17, their Lift median 1.8, max 11.5. Matches with n ≥ 2: Lift median 1.8.

Nested matches (one Cluster wholly inside the other, n ≥ 2): 1; of these 1 have Jaccard < 0.5 and 0 < 0.3.

### Matches surviving a minimum, by measure

| Minimum | Jaccard ≥ | of which n = 1 | Clusters with ≥ 2 surviving matches | Clusters flagged "no match above the minimum" | min containment ≥ | max containment ≥ |
|---|---|---|---|---|---|---|
| 0.05 | 95 | 50 | 52 of 116 | 1 of 116 | 103 | 103 |
| 0.10 | 48 | 7 | 23 of 116 | 30 of 116 | 69 | 99 |
| 0.15 | 30 | 1 | 6 of 116 | 44 of 116 | 42 | 79 |
| 0.20 | 19 | 0 | 1 of 116 | 61 of 116 | 29 | 76 |
| 0.25 | 16 | 0 | 0 of 116 | 66 of 116 | 23 | 71 |
| 0.30 | 13 | 0 | 0 of 116 | 72 of 116 | 17 | 45 |
| 0.40 | 5 | 0 | 0 of 116 | 88 of 116 | 9 | 33 |
| 0.50 | 2 | 0 | 0 of 116 | 94 of 116 | 6 | 28 |

### Where the measures disagree on rank (per Cluster, its matches ranked)

Clusters with two or more matches: 58. Top match differs from Jaccard's when ranked by: cont_min 0, cont_max 1, lift 13.

## 4. Flags per pair (minimum = Jaccard 0.20)

| A → B | Multi-Tag Clusters of A | not in B's network | no overlap | no match above 0.20 | matched |
|---|---|---|---|---|---|
| overall → puzzle | 4 | 0 | 0 | 2 | 2 |
| puzzle → overall | 4 | 1 | 0 | 1 | 2 |
| overall → rpg | 4 | 0 | 0 | 1 | 3 |
| rpg → overall | 15 | 3 | 0 | 9 | 3 |
| overall → strategy | 4 | 0 | 0 | 2 | 2 |
| strategy → overall | 3 | 0 | 0 | 1 | 2 |
| overall → simulation | 4 | 0 | 0 | 2 | 2 |
| simulation → overall | 3 | 0 | 0 | 0 | 3 |
| puzzle → rpg | 4 | 0 | 0 | 3 | 1 |
| rpg → puzzle | 15 | 4 | 0 | 10 | 1 |
| puzzle → strategy | 4 | 1 | 0 | 2 | 1 |
| strategy → puzzle | 3 | 0 | 0 | 2 | 1 |
| puzzle → simulation | 4 | 1 | 0 | 2 | 1 |
| simulation → puzzle | 3 | 1 | 0 | 1 | 1 |
| rpg → strategy | 15 | 3 | 0 | 10 | 2 |
| strategy → rpg | 3 | 0 | 0 | 1 | 2 |
| rpg → simulation | 15 | 4 | 0 | 10 | 1 |
| simulation → rpg | 3 | 0 | 0 | 2 | 1 |
| strategy → simulation | 3 | 0 | 0 | 0 | 3 |
| simulation → strategy | 3 | 0 | 0 | 0 | 3 |

## 5. Every match, pair by pair (ranked by Jaccard)

a, b = Cluster sizes; n = shared Tags; a′, b′ = Common Tags of each Cluster; E = expected overlap a′b′/N.

### overall × puzzle  (Common Tags 16, ARI 0.23)

| overall | puzzle | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C3 | 9 | 8 | 5 | 0.42 | 56% | 62% | 0.56 | 5 | 7 | 0.71 | 2.2 | 2.3 | Co-op, First-Person, Multiplayer, Online Co-Op, Realistic |
| C2 | C1 | 9 | 11 | 4 | 0.25 | 44% | 36% | 0.36 | 6 | 7 | 0.44 | 2.6 | 1.5 | Atmospheric, Great Soundtrack, Story Rich, Third Person |
| C3 | C1 | 7 | 11 | 2 | 0.12 | 29% | 18% | 0.18 | 4 | 7 | 0.22 | 1.8 | 1.1 | Exploration, Open World |
| C3 | C2 | 7 | 8 | 1 | 0.07 | 14% | 12% | 0.12 | 4 | 2 | 0.20 | 0.5 | 2.0 | Indie |
| C3 | C3 | 7 | 8 | 1 | 0.07 | 14% | 12% | 0.12 | 4 | 7 | 0.10 | 1.8 | 0.6 | Sandbox |
| C4 | C1 | 4 | 11 | 1 | 0.07 | 25% | 9% | 0.09 | 1 | 7 | — | 0.4 | 2.3 | Sci-fi |
| C2 | C2 | 9 | 8 | 1 | 0.06 | 11% | 12% | 0.11 | 6 | 2 | 0.14 | 0.8 | 1.3 | Singleplayer |
| C2 | C3 | 9 | 8 | 1 | 0.06 | 11% | 12% | 0.11 | 6 | 7 | 0.08 | 2.6 | 0.4 | 3D |

### overall × rpg  (Common Tags 28, ARI 0.17)

| overall | rpg | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C4 | C2 | 4 | 7 | 3 | 0.38 | 75% | 43% | 0.43 | 4 | 5 | 0.50 | 0.7 | 4.2 | Free to Play, Massively Multiplayer, PvE |
| C3 | C1 | 7 | 8 | 4 | 0.36 | 57% | 50% | 0.50 | 7 | 4 | 0.57 | 1.0 | 4.0 | Building, Crafting, Sandbox, Survival |
| C1 | C5 | 9 | 6 | 3 | 0.25 | 33% | 50% | 0.33 | 8 | 4 | 0.33 | 1.1 | 2.6 | FPS, First-Person, Shooter |
| C1 | C2 | 9 | 7 | 2 | 0.14 | 22% | 29% | 0.22 | 8 | 5 | 0.18 | 1.4 | 1.4 | Online Co-Op, PvP |
| C2 | C3 | 9 | 7 | 2 | 0.14 | 22% | 29% | 0.22 | 9 | 2 | 0.22 | 0.6 | 3.1 | 3D, Fantasy |
| C2 | C4 | 9 | 7 | 2 | 0.14 | 22% | 29% | 0.22 | 9 | 2 | 0.22 | 0.6 | 3.1 | Atmospheric, Great Soundtrack |
| C3 | C14 | 7 | 2 | 1 | 0.12 | 14% | 50% | 0.14 | 7 | 1 | — | 0.2 | 4.0 | Open World |
| C4 | C5 | 4 | 6 | 1 | 0.11 | 25% | 17% | 0.17 | 4 | 4 | 0.14 | 0.6 | 1.8 | Sci-fi |
| C2 | C15 | 9 | 2 | 1 | 0.10 | 11% | 50% | 0.11 | 9 | 1 | — | 0.3 | 3.1 | Action RPG |
| C3 | C9 | 7 | 4 | 1 | 0.10 | 14% | 25% | 0.14 | 7 | 2 | 0.12 | 0.5 | 2.0 | Exploration |
| C2 | C11 | 9 | 3 | 1 | 0.09 | 11% | 33% | 0.11 | 9 | 1 | — | 0.3 | 3.1 | Third Person |
| C2 | C13 | 9 | 3 | 1 | 0.09 | 11% | 33% | 0.11 | 9 | 1 | — | 0.3 | 3.1 | Character Customization |
| C3 | C6 | 7 | 5 | 1 | 0.09 | 14% | 20% | 0.14 | 7 | 2 | 0.12 | 0.5 | 2.0 | Indie |
| C1 | C9 | 9 | 4 | 1 | 0.08 | 11% | 25% | 0.11 | 8 | 2 | 0.11 | 0.6 | 1.8 | Realistic |
| C2 | C8 | 9 | 4 | 1 | 0.08 | 11% | 25% | 0.11 | 9 | 1 | — | 0.3 | 3.1 | Story Rich |
| C2 | C6 | 9 | 5 | 1 | 0.08 | 11% | 20% | 0.11 | 9 | 2 | 0.10 | 0.6 | 1.6 | Singleplayer |

### overall × strategy  (Common Tags 24, ARI 0.32)

| overall | strategy | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C1 | 9 | 16 | 8 | 0.47 | 89% | 50% | 0.50 | 9 | 14 | 0.53 | 5.2 | 1.5 | Co-op, FPS, First-Person, Multiplayer, Online Co-Op, PvP, Realistic, Shooter |
| C3 | C2 | 7 | 12 | 6 | 0.46 | 86% | 50% | 0.50 | 6 | 7 | 0.86 | 1.8 | 3.4 | Building, Exploration, Indie, Open World, Sandbox, Survival |
| C2 | C1 | 9 | 16 | 4 | 0.19 | 44% | 25% | 0.25 | 7 | 14 | 0.24 | 4.1 | 1.0 | 3D, Character Customization, Fantasy, Third Person |
| C2 | C3 | 9 | 11 | 2 | 0.11 | 22% | 18% | 0.18 | 7 | 3 | 0.25 | 0.9 | 2.3 | Great Soundtrack, Singleplayer |
| C4 | C1 | 4 | 16 | 2 | 0.11 | 50% | 12% | 0.12 | 2 | 14 | 0.14 | 1.2 | 1.7 | Free to Play, Massively Multiplayer |
| C1 | C3 | 9 | 11 | 1 | 0.05 | 11% | 9% | 0.09 | 9 | 3 | 0.09 | 1.1 | 0.9 | Tactical |
| C2 | C2 | 9 | 12 | 1 | 0.05 | 11% | 8% | 0.08 | 7 | 7 | 0.08 | 2.0 | 0.5 | Atmospheric |

### overall × simulation  (Common Tags 22, ARI 0.27)

| overall | simulation | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C3 | C1 | 7 | 18 | 7 | 0.39 | 100% | 39% | 0.39 | 7 | 10 | 0.70 | 3.2 | 2.2 | Building, Crafting, Exploration, Indie, Open World, Sandbox, Survival |
| C1 | C2 | 9 | 13 | 5 | 0.29 | 56% | 38% | 0.38 | 9 | 9 | 0.38 | 3.7 | 1.4 | Co-op, Multiplayer, Online Co-Op, PvP, Realistic |
| C1 | C3 | 9 | 7 | 3 | 0.23 | 33% | 43% | 0.33 | 9 | 3 | 0.33 | 1.2 | 2.4 | FPS, Shooter, Tactical |
| C2 | C2 | 9 | 13 | 3 | 0.16 | 33% | 23% | 0.23 | 5 | 9 | 0.27 | 2.0 | 1.5 | 3D, Character Customization, Third Person |
| C2 | C1 | 9 | 18 | 2 | 0.08 | 22% | 11% | 0.11 | 5 | 10 | 0.15 | 2.3 | 0.9 | Atmospheric, Singleplayer |
| C4 | C2 | 4 | 13 | 1 | 0.06 | 25% | 8% | 0.08 | 1 | 9 | — | 0.4 | 2.4 | Free to Play |
| C1 | C1 | 9 | 18 | 1 | 0.04 | 11% | 6% | 0.06 | 9 | 10 | 0.06 | 4.1 | 0.2 | First-Person |

### puzzle × rpg  (Common Tags 23, ARI 0.07)

| puzzle | rpg | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C2 | C6 | 8 | 5 | 3 | 0.30 | 38% | 60% | 0.38 | 4 | 3 | 0.75 | 0.5 | 5.8 | 2D, Indie, Singleplayer |
| C1 | C11 | 11 | 3 | 2 | 0.17 | 18% | 67% | 0.18 | 9 | 2 | 0.22 | 0.8 | 2.6 | Female Protagonist, Third Person |
| C4 | C10 | 4 | 3 | 1 | 0.17 | 25% | 33% | 0.25 | 2 | 1 | — | 0.1 | 11.5 | Horror |
| C1 | C9 | 11 | 4 | 2 | 0.15 | 18% | 50% | 0.18 | 9 | 3 | 0.20 | 1.2 | 1.7 | Action-Adventure, Exploration |
| C1 | C4 | 11 | 7 | 2 | 0.12 | 18% | 29% | 0.18 | 9 | 3 | 0.20 | 1.2 | 1.7 | Atmospheric, Great Soundtrack |
| C4 | C4 | 4 | 7 | 1 | 0.10 | 25% | 14% | 0.14 | 2 | 3 | 0.25 | 0.3 | 3.8 | Dark |
| C3 | C9 | 8 | 4 | 1 | 0.09 | 12% | 25% | 0.12 | 8 | 3 | 0.10 | 1.0 | 1.0 | Realistic |
| C1 | C14 | 11 | 2 | 1 | 0.08 | 9% | 50% | 0.09 | 9 | 1 | — | 0.4 | 2.6 | Open World |
| C3 | C5 | 8 | 6 | 1 | 0.08 | 12% | 17% | 0.12 | 8 | 2 | 0.11 | 0.7 | 1.4 | First-Person |
| C1 | C8 | 11 | 4 | 1 | 0.07 | 9% | 25% | 0.09 | 9 | 1 | — | 0.4 | 2.6 | Story Rich |
| C2 | C2 | 8 | 7 | 1 | 0.07 | 12% | 14% | 0.12 | 4 | 2 | 0.20 | 0.3 | 2.9 | Cute |
| C3 | C2 | 8 | 7 | 1 | 0.07 | 12% | 14% | 0.12 | 8 | 2 | 0.11 | 0.7 | 1.4 | Online Co-Op |
| C3 | C3 | 8 | 7 | 1 | 0.07 | 12% | 14% | 0.12 | 8 | 1 | — | 0.3 | 2.9 | 3D |
| C3 | C1 | 8 | 8 | 1 | 0.07 | 12% | 12% | 0.12 | 8 | 1 | — | 0.3 | 2.9 | Sandbox |
| C1 | C5 | 11 | 6 | 1 | 0.06 | 9% | 17% | 0.09 | 9 | 2 | 0.10 | 0.8 | 1.3 | Sci-fi |

### puzzle × strategy  (Common Tags 15, ARI 0.30)

| puzzle | strategy | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C3 | C1 | 8 | 16 | 6 | 0.33 | 75% | 38% | 0.38 | 7 | 7 | 0.75 | 3.3 | 1.8 | 3D, Co-op, First-Person, Multiplayer, Online Co-Op, Realistic |
| C1 | C2 | 11 | 12 | 3 | 0.15 | 27% | 25% | 0.25 | 5 | 6 | 0.38 | 2.0 | 1.5 | Atmospheric, Exploration, Open World |
| C2 | C2 | 8 | 12 | 2 | 0.11 | 25% | 17% | 0.17 | 3 | 6 | 0.29 | 1.2 | 1.7 | 2D, Indie |
| C2 | C3 | 8 | 11 | 1 | 0.06 | 12% | 9% | 0.09 | 3 | 2 | 0.25 | 0.4 | 2.5 | Singleplayer |
| C3 | C2 | 8 | 12 | 1 | 0.05 | 12% | 8% | 0.08 | 7 | 6 | 0.08 | 2.8 | 0.4 | Sandbox |
| C1 | C3 | 11 | 11 | 1 | 0.05 | 9% | 9% | 0.09 | 5 | 2 | 0.17 | 0.7 | 1.5 | Great Soundtrack |
| C1 | C1 | 11 | 16 | 1 | 0.04 | 9% | 6% | 0.06 | 5 | 7 | 0.09 | 2.3 | 0.4 | Third Person |

### puzzle × simulation  (Common Tags 16, ARI 0.07)

| puzzle | simulation | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C3 | C2 | 8 | 13 | 5 | 0.31 | 62% | 38% | 0.38 | 8 | 6 | 0.56 | 3.0 | 1.7 | 3D, Co-op, Multiplayer, Online Co-Op, Realistic |
| C2 | C1 | 8 | 18 | 4 | 0.18 | 50% | 22% | 0.22 | 4 | 10 | 0.40 | 2.5 | 1.6 | 2D, Indie, Relaxing, Singleplayer |
| C3 | C1 | 8 | 18 | 3 | 0.13 | 38% | 17% | 0.17 | 8 | 10 | 0.20 | 5.0 | 0.6 | First-Person, Funny, Sandbox |
| C1 | C1 | 11 | 18 | 3 | 0.12 | 27% | 17% | 0.17 | 4 | 10 | 0.27 | 2.5 | 1.2 | Atmospheric, Exploration, Open World |
| C1 | C2 | 11 | 13 | 1 | 0.04 | 9% | 8% | 0.08 | 4 | 6 | 0.11 | 1.5 | 0.7 | Third Person |

### rpg × strategy  (Common Tags 31, ARI 0.10)

| rpg | strategy | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C2 | 8 | 12 | 5 | 0.33 | 62% | 42% | 0.42 | 6 | 10 | 0.45 | 1.9 | 2.6 | Base Building, Building, Early Access, Sandbox, Survival |
| C2 | C1 | 7 | 16 | 4 | 0.21 | 57% | 25% | 0.25 | 4 | 15 | 0.27 | 1.9 | 2.1 | Free to Play, Massively Multiplayer, Online Co-Op, PvP |
| C5 | C1 | 6 | 16 | 3 | 0.16 | 50% | 19% | 0.19 | 4 | 15 | 0.19 | 1.9 | 1.6 | FPS, First-Person, Shooter |
| C6 | C2 | 5 | 12 | 2 | 0.13 | 40% | 17% | 0.17 | 3 | 10 | 0.18 | 1.0 | 2.1 | 2D, Indie |
| C3 | C1 | 7 | 16 | 2 | 0.10 | 29% | 12% | 0.12 | 2 | 15 | 0.13 | 1.0 | 2.1 | 3D, Fantasy |
| C12 | C3 | 3 | 11 | 1 | 0.08 | 33% | 9% | 0.09 | 1 | 6 | — | 0.2 | 5.2 | Turn-Based Strategy |
| C14 | C2 | 2 | 12 | 1 | 0.08 | 50% | 8% | 0.08 | 1 | 10 | — | 0.3 | 3.1 | Open World |
| C8 | C3 | 4 | 11 | 1 | 0.07 | 25% | 9% | 0.09 | 1 | 6 | — | 0.2 | 5.2 | Historical |
| C6 | C3 | 5 | 11 | 1 | 0.07 | 20% | 9% | 0.09 | 3 | 6 | 0.12 | 0.6 | 1.7 | Singleplayer |
| C9 | C2 | 4 | 12 | 1 | 0.07 | 25% | 8% | 0.08 | 2 | 10 | 0.09 | 0.6 | 1.6 | Exploration |
| C5 | C3 | 6 | 11 | 1 | 0.06 | 17% | 9% | 0.09 | 4 | 6 | 0.11 | 0.8 | 1.3 | Moddable |
| C4 | C3 | 7 | 11 | 1 | 0.06 | 14% | 9% | 0.09 | 3 | 6 | 0.12 | 0.6 | 1.7 | Great Soundtrack |
| C1 | C3 | 8 | 11 | 1 | 0.06 | 12% | 9% | 0.09 | 6 | 6 | 0.09 | 1.2 | 0.9 | War |
| C4 | C2 | 7 | 12 | 1 | 0.06 | 14% | 8% | 0.08 | 3 | 10 | 0.08 | 1.0 | 1.0 | Atmospheric |
| C11 | C1 | 3 | 16 | 1 | 0.06 | 33% | 6% | 0.06 | 1 | 15 | — | 0.5 | 2.1 | Third Person |
| C13 | C1 | 3 | 16 | 1 | 0.06 | 33% | 6% | 0.06 | 1 | 15 | — | 0.5 | 2.1 | Character Customization |
| C9 | C1 | 4 | 16 | 1 | 0.05 | 25% | 6% | 0.06 | 2 | 15 | 0.06 | 1.0 | 1.0 | Realistic |
| C4 | C1 | 7 | 16 | 1 | 0.05 | 14% | 6% | 0.06 | 3 | 15 | 0.06 | 1.5 | 0.7 | Difficult |

### rpg × simulation  (Common Tags 27, ARI 0.11)

| rpg | simulation | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C1 | 8 | 18 | 5 | 0.24 | 62% | 28% | 0.28 | 6 | 14 | 0.33 | 3.1 | 1.6 | Building, Crafting, Early Access, Sandbox, Survival |
| C5 | C3 | 6 | 7 | 2 | 0.18 | 33% | 29% | 0.29 | 4 | 4 | 0.33 | 0.6 | 3.4 | FPS, Shooter |
| C2 | C2 | 7 | 13 | 3 | 0.18 | 43% | 23% | 0.23 | 3 | 9 | 0.33 | 1.0 | 3.0 | Free to Play, Online Co-Op, PvP |
| C6 | C1 | 5 | 18 | 3 | 0.15 | 60% | 17% | 0.17 | 3 | 14 | 0.21 | 1.6 | 1.9 | 2D, Indie, Singleplayer |
| C8 | C3 | 4 | 7 | 1 | 0.10 | 25% | 14% | 0.14 | 1 | 4 | — | 0.1 | 6.8 | Historical |
| C5 | C1 | 6 | 18 | 2 | 0.09 | 33% | 11% | 0.11 | 4 | 14 | 0.12 | 2.1 | 1.0 | First-Person, Moddable |
| C1 | C3 | 8 | 7 | 1 | 0.07 | 12% | 14% | 0.12 | 6 | 4 | 0.11 | 0.9 | 1.1 | War |
| C11 | C2 | 3 | 13 | 1 | 0.07 | 33% | 8% | 0.08 | 1 | 9 | — | 0.3 | 3.0 | Third Person |
| C13 | C2 | 3 | 13 | 1 | 0.07 | 33% | 8% | 0.08 | 1 | 9 | — | 0.3 | 3.0 | Character Customization |
| C9 | C2 | 4 | 13 | 1 | 0.06 | 25% | 8% | 0.08 | 2 | 9 | 0.10 | 0.7 | 1.5 | Realistic |
| C3 | C2 | 7 | 13 | 1 | 0.05 | 14% | 8% | 0.08 | 1 | 9 | — | 0.3 | 3.0 | 3D |
| C14 | C1 | 2 | 18 | 1 | 0.05 | 50% | 6% | 0.06 | 1 | 14 | — | 0.5 | 1.9 | Open World |
| C9 | C1 | 4 | 18 | 1 | 0.05 | 25% | 6% | 0.06 | 2 | 14 | 0.07 | 1.0 | 1.0 | Exploration |
| C4 | C1 | 7 | 18 | 1 | 0.04 | 14% | 6% | 0.06 | 1 | 14 | — | 0.5 | 1.9 | Atmospheric |

### strategy × simulation  (Common Tags 32, ARI 0.53)

| strategy | simulation | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C2 | C1 | 12 | 18 | 11 | 0.58 | 92% | 61% | 0.61 | 11 | 15 | 0.73 | 5.2 | 2.1 | 2D, Atmospheric, Building, Early Access, Exploration, Indie, Management, Open World, Resource Management, Sandbox, Survival |
| C1 | C2 | 16 | 13 | 10 | 0.53 | 62% | 77% | 0.62 | 13 | 10 | 0.77 | 4.1 | 2.5 | 3D, Character Customization, Co-op, Free to Play, Multiplayer, Online Co-Op, PvP, Realistic, Team-Based, Third Person |
| C3 | C3 | 11 | 7 | 5 | 0.38 | 45% | 71% | 0.45 | 8 | 7 | 0.50 | 1.8 | 2.9 | Grand Strategy, Historical, Military, Tactical, War |
| C3 | C1 | 11 | 18 | 3 | 0.12 | 27% | 17% | 0.17 | 8 | 15 | 0.15 | 3.8 | 0.8 | Economy, Moddable, Singleplayer |
| C1 | C3 | 16 | 7 | 2 | 0.10 | 12% | 29% | 0.12 | 13 | 7 | 0.11 | 2.8 | 0.7 | FPS, Shooter |
| C1 | C1 | 16 | 18 | 1 | 0.03 | 6% | 6% | 0.06 | 13 | 15 | 0.04 | 6.1 | 0.2 | First-Person |
