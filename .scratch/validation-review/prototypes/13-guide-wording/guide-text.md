# PROTOTYPE: User Guide and glossary wording for the validation review (ticket 13)

Throwaway draft for [What do the User Guide's validation passages and CONTEXT.md entries say, in English and Bulgarian?](../../issues/13-guide-and-context-wording.md).
It is a wording prototype, so it is a rough take to react to, not code. Once agreed, the spec quotes each passage verbatim.

**How to read it.** Each passage starts with a change list against the current guide:
- **K**: kept as is.
- **R**: replaced.
- **X**: removed.
- **+**: added.

The ticket that fixed a sentence is in brackets: [04] means [What does the Null Comparison state, and by which rule?](../../issues/04-null-comparison-rule-and-wording.md), and so on. Sentences with no bracket are new connective text from this ticket. The English comes first, then the Bulgarian. The Bulgarian follows [bg-terms.md](../../../../docs/i18n/bg-terms.md) and [ticket 11's term table](../11-bg-wording/bg-strings.md).

Example figures are real. They come from the stored `ps-validation-1` run at Overall g = 17, s = 2 on Build `20261008T221504Z-7a23ae9f`, read from [10-scan-step](../10-scan-step/results.json) and [09-clamp-bracket](../09-clamp-bracket/results.md). The current guide's example ("−0.021 to −0.012", "79 of 100") does not match that stored run (−0.022 to −0.009, 70 of 100).

---

## Points settled (all nine accepted by the researcher, 2026-11-05)

1. **"outwidths" in ticket 12's fixed clause.** The clause reads "so the count of shuffled networks the observed outwidths tends to understate…". "Outwidths" is not a word. The draft uses **"so the count of shuffled networks narrower than the observed tends to understate, not overstate, how distinctive its width is"**, which means the same thing.
2. **A gap from tickets 03→04: the note shown when the observed network's runs at γ_obs beat its Selected Partition's Q.** Ticket 03 says such a Q serves only the comparison, "with a note". Ticket 04 took over that note but fixed no wording, and ticket 11 has no bg for it. Proposed card note: "The runs at γ_obs found a Q of {q} on the observed network, above its Selected Partition's {q0}; the comparison uses {q}." In bg: "Изпълненията при γ_obs намериха Q {q} за наблюдаваната мрежа, над {q0} на избраното ѝ разбиване; сравнението използва {q}." The guide mentions it in one sentence, marked ⟨gap⟩ below.
3. **Appendix A misattributes Hennig.** The current bullet says that a cluster-wise *mean* Jaccard ≤ 0.5 is "dissolved" (Hennig 2007). Hennig's 0.5 applies per resample ([Verified review](../../research/01-verified-review.md), item 13; [Research 02](../../../auto-parameter-selection/research/02-validation-methods.md) §A). The draft corrects the bullet as well as the "Why not here" paragraph.
4. **Bulgarian for Perturbation Share.** Proposed: **дял на смущението**, since bg-terms already renders "perturbation" as *смущение* (row "neighbour link … perturbation"). The alternative is the more literal *дял на преместените назначения*.
5. **"Monte Carlo" in Bulgarian.** Neither language of the guide uses the phrase yet. The draft keeps it in Latin script (*по Monte Carlo*), following the proper-names policy (Leiden, Jaccard). The alternative is the common Cyrillic *Монте Карло*.
6. **"The chosen pair" in the methods paragraph.** Ticket 04 drops "chosen pair" because Validate runs on any inspected pair. The draft uses **"each validated Threshold Pair"**.
7. **Wilson (1927) is not in Appendix C.** The draft adds it.
8. **Export columns (ticket 07) leave out two of ticket 02's figures:** the 10th–90th percentile spread of either Jaccard, and the Whole-Cluster Jaccard's s.e. The draft's column lists follow ticket 07, so those figures stay card-only. The per-replicate Jaccards they come from stay in the cache JSON.
9. **CONTEXT.md needs no change.** Commit 9f3b2ec already added Hennig's Jaccard, Whole-Cluster Jaccard, Dissolved in most subsamples, Q not above the null and Perturbation Share, and it fixed the scope phrase in Null Comparison and Subsample Stability. All of these were re-read against tickets 01–05. CONTEXT.md is English-only, so its Bulgarian lives in the bg-terms rows in §7.

---

## 1. Chapter 3: Null Comparison (`03-metric-reference.md#null-comparison`)

**Changes**
- In short: **R** "The chosen pair's procedure" becomes "The per-pair procedure at the validated Threshold Pair" [04: "chosen pair" is not used]. Here and Caution: **K**.
- Columns: **R**, with the new replicate columns and `validation_pairs.csv` [07].
- Paragraph 1:
  - "Each of R = 100 replicates shuffles…": **K**.
  - "The whole per-pair procedure then runs at the same (g, s)…": **R** by the scope phrase [04].
  - "A second arm reads Q … from each replicate's own envelope, with no extra Leiden runs": **R** by the runs at γ_obs and the residual [03].
  - **+** These runs never change a Selected Partition, and there is no extrapolation (`beyond_scan`) [03].
  - **+** The note when the observed side's runs beat the Selected Partition ⟨gap⟩.
- Verdict sentences ("The verdict 'Q not above the null' appears when … above all replicates"): **R** by the three states over D and the D < R/2 flag [04].
- "No z-score or p-value is given.": **K**, **+** its two reasons [04].
- **+** A width and Multi-Tag Cluster paragraph [04], with the scan sentence [05], its direction clause [12] and the scan-step quote [10].
- **+** A Perturbation Share paragraph [05], with the mixing quote [08].
- Why it matters:
  - Sentence 1: **K**.
  - "the observed Clusters are no more than what the counts produce": **R** by ticket 04's text.
- Example: **R** with the real stored figures and the new card wording [04].
- Bounds: **R**, adding D and the Perturbation Share.
- Compare with: **K**.
- Exact definition: **R**, adding the runs at γ_obs, D and the Perturbation Share.

### English

```markdown
### Null Comparison

> **In short.** The per-pair procedure at the validated Threshold Pair, repeated on 100 networks whose game–tag table was shuffled, keeping every tag's and game's count.
>
> **Here:** shows whether the dataset's tags have more structure than random tagging with the same counts.
>
> **Caution:** shows that the network is not random, not that its Clusters are real.

Columns: `null_q`, `null_q_envelope`, `q_defined`, `beyond_scan`, `perturbation_share`, `has_selected_partition`, `reason` in `validation_replicates.csv` (arm `null`); the pair's state, R, D and U in `validation_pairs.csv`.

Each of R = 100 replicates shuffles the games × the pair's network tags with curveball trades (10 per game), exactly as the Workbench's null model, so every tag keeps its number of games and every game its number of tags; the weight is recomputed from the shuffled table. Each shuffled network then goes through **the per-pair procedure at the same Threshold Pair** (its own γ scan with the same 10 scan seeds, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, abstract, §III and §VI: a null is analysed identically). Q at the observed Selected Resolution γ_obs is the best of the network's own scan and 10 Leiden runs at exactly γ_obs with the scan seeds, and the observed network gets the same runs; on the default pairs, 50 seeds raised a shuffled network's Q by at most 0.0013. These runs serve the comparison only: they never enter a network's scan or its Selected Partition rule, and validation never changes the Selected Partition. If they find a higher Q on the observed network than its Selected Partition's, the comparison uses that Q and the card says so. A shuffled network has no Q when it has no edges or when γ_obs lies beyond its own scan end; its Q is never extrapolated.

The verdict counts only the D shuffled networks with a Q, out of R; the other U are listed with their reasons. It has three states: the observed Q is above all D when none of them reaches it; **Q not above the null** when at least one of them reaches it (reaching means ≥); and undefined when D = 0, when Q cannot be compared. There is no minimum D, but when fewer than half of the shuffled networks have a Q (D < R/2), the card says the comparison is weak. No z-score or p-value is given. γ_obs and the pair were chosen on the observed data, so the observed Q is not exchangeable with the shuffled networks' Q at the same γ, and a Monte Carlo bound p ≤ 1/(D + 1) would be only nominal: one shuffled network of the RPG dataset reached 0.129 at its own resolution against the observed 0.131. With 100 networks, "none reaches it" is the strongest result the comparison can give.

For the shuffled networks with a Selected Partition, the card also compares the number of Multi-Tag Clusters (observed, median and range) and the Optimality Domain width: the median width against the observed, and how many of them the observed width exceeds, at three decimals, with ties counted apart. Their Selected Resolutions and edge counts go to the export only, because a shuffled network's own resolution is not comparable with γ_obs. Widths are upper bounds, conditional on the partitions the γ scan finds, so the count of shuffled networks narrower than the observed tends to understate, not overstate, how distinctive its width is. On the Build of 2026-10-08, rescanning at a γ step of 0.01 instead of 0.05 left every observed Selected Partition unchanged and narrowed the median null domain width by 3–30%. The observed width was then wider than up to 11 more of the 100 shuffled networks.

Each shuffled network also records its **Perturbation Share**: the share of the observed game–tag assignments that the shuffle moved (Strona et al. 2014). It shows how far the shuffle got from the observed data. It is a diagnostic in the export, never part of the verdict, and has no threshold. On the Build of 2026-10-08, at each of the 8 validated Threshold Pairs, 400 shuffle chains per pair matched by 10 trades per game every tracked statistic of chains run to 200 (perturbation share, C-score, edge count, Q and Multi-Tag Clusters within 0.2 SD, and under 0.5% of the observed table's excess co-occurrence left), while at 5 the perturbation share still lagged by about 0.5–0.7 SD. At 10 trades per game the Perturbation Share was 0.58–0.70, depending on the pair.

*Why it matters here.* Tag frequencies alone create clusters of a sort: common tags co-occur by chance. If shuffled networks reach the same Q at the same γ, Q gives no evidence of structure beyond what the tag and game counts produce. Q is one number for the whole partition: a shuffled network can reach it with entirely different groups, and not exceeding the null is absence of evidence, not evidence of absence.

*Example.* At Overall g = 17, s = 2: "Q at resolution 1.151 is 0.067; none of the 100 shuffled networks with a Q reaches it (range over 100 shuffled networks: −0.022 to −0.009)." "Multi-Tag Clusters: observed 4, median 3 (range over 70 shuffled networks with a Selected Partition: 3 to 5)." "Median domain width 0.049 vs observed 0.158; observed wider than 70 of 70."

*Bounds.* Counts are 0 to R, with D + U = R; the Perturbation Share is 0 to 1.

*Compare with.* The Workbench's null-model baseline (20 replicates at one γ).

**Exact definition:** replicate r shuffles with `random.Random(seed_r)`, seed_r from stream 4 of the main seed; Q_r(γ_obs) is the highest (Â − γ_obs·P̂)/2m over the replicate's envelope partition at γ_obs and its 10 Leiden runs at γ_obs with the scan seeds, undefined when the replicate has no edges or γ_obs exceeds its scan end (`beyond_scan`); D = #{r : Q_r(γ_obs) defined}; reach = #{r : Q_r(γ_obs) ≥ Q_obs}; Perturbation Share = the share of the observed table's 1-cells that are 0 after the shuffle.
```

### Bulgarian

```markdown
### Сравнение с нулев модел (Null Comparison) {#null-comparison}

> **Накратко.** Процедурата за една двойка при валидираната двойка прагове, повторена върху 100 мрежи, чиято таблица игри–тагове е разбъркана при запазени бройки на всеки таг и всяка игра.
>
> **Тук:** показва дали таговете на набора имат повече структура от случайно поставяне на тагове със същите бройки.
>
> **Внимание:** показва, че мрежата не е случайна, а не че клъстерите ѝ са реални.

Колони: `null_q`, `null_q_envelope`, `q_defined`, `beyond_scan`, `perturbation_share`, `has_selected_partition`, `reason` в `validation_replicates.csv` (вариант `null`); състоянието на двойката, R, D и U в `validation_pairs.csv`.

Всяко от R = 100 повторения разбърква игрите × таговете на мрежата на двойката с размени curveball (10 на игра), точно като нулевия модел на работното място, така че всеки таг запазва броя на игрите си и всяка игра – броя на таговете си; теглото се преизчислява от разбърканата таблица. След това всяка разбъркана мрежа минава през **процедурата за една двойка при същата двойка прагове** (собствено сканиране по γ със същите 10 начални числа от сканирането, CHAMP, γ̂ и правилото за избраното разбиване), а не през решетката на параметрите или избора на двойка (Karrer, Levina & Newman 2008, резюме, §III и §VI: нулевият модел се анализира по същия начин). Q при наблюдаваната избрана резолюция γ_obs е най-доброто от собственото сканиране на мрежата и 10 изпълнения на Leiden точно при γ_obs с началните числа от сканирането, а наблюдаваната мрежа получава същите изпълнения; при двойките по подразбиране 50 начални числа повишиха Q на разбъркана мрежа най-много с 0,0013. Тези изпълнения служат само за сравнението: никога не влизат в сканирането на мрежата или в правилото ѝ за избраното разбиване, а валидирането никога не променя избраното разбиване. Ако за наблюдаваната мрежа те намерят по-високо Q от това на избраното ѝ разбиване, сравнението използва това Q и картата го казва. Разбъркана мрежа няма Q, когато няма ребра или когато γ_obs е извън края на собственото ѝ сканиране; нейното Q никога не се екстраполира.

Изводът брои само D-те разбъркани мрежи с Q от общо R; останалите U се изброяват с причините си. Той има три състояния: наблюдаваното Q е над всички D, когато нито една от тях не го достига; **Q не е над нулевия модел**, когато поне една от тях го достига (достигането означава ≥); и неопределено при D = 0, когато Q не може да се сравни. Няма минимално D, но когато по-малко от половината разбъркани мрежи имат Q (D < R/2), картата казва, че сравнението е слабо. Не се дава нито z-оценка, нито стойност p. γ_obs и двойката са избрани върху наблюдаваните данни, затова наблюдаваното Q не е взаимозаменяемо с Q на разбърканите мрежи при същата γ и границата по Monte Carlo p ≤ 1/(D + 1) би била само номинална: една разбъркана мрежа на набора RPG достигна 0,129 при собствената си резолюция срещу наблюдаваните 0,131. При 100 мрежи „никоя не го достига“ е най-силният резултат, който сравнението може да даде.

За разбърканите мрежи с избрано разбиване картата сравнява и броя на многотаговите клъстери (наблюдаван, медиана и обхват), и ширината на областта на оптималност: медианната ширина срещу наблюдаваната и от колко от тях наблюдаваната ширина е по-голяма, с три десетични знака, като равенствата се броят отделно. Избраните им резолюции и броят на ребрата им се записват само в експорта, защото собствената резолюция на разбъркана мрежа не е сравнима с γ_obs. Ширините са горни граници и зависят от разбиванията, които сканирането по γ намира, затова броят на разбърканите мрежи, по-тесни от наблюдаваната, по-скоро подценява, отколкото надценява колко отличителна е нейната ширина. При компилацията от 2026-10-08 повторното сканиране със стъпка по γ 0,01 вместо 0,05 не промени нито едно наблюдавано избрано разбиване и стесни медианната ширина на областта при нулевия модел с 3–30%. Тогава наблюдаваната ширина беше по-голяма от тази на до 11 разбъркани мрежи повече от 100-те.

Всяка разбъркана мрежа записва и своя **дял на смущението**: делът от наблюдаваните назначения игра–таг, които разбъркването е преместило (Strona et al. 2014). Той показва колко далеч от наблюдаваните данни е стигнало разбъркването. Той е диагностика в експорта, никога не е част от извода и няма граница. При компилацията от 2026-10-08, при всяка от 8-те валидирани двойки прагове, 400 вериги на разбъркване за двойка съвпаднаха още при 10 размени на игра по всяка следена статистика с вериги, продължени до 200 (дял на смущението, C-score, брой ребра, Q и многотагови клъстери в рамките на 0,2 SD и под 0,5% оставащо превишение на съвместната срещаемост от наблюдаваната таблица), докато при 5 делът на смущението все още изоставаше с около 0,5–0,7 SD. При 10 размени на игра делът на смущението беше от 0,58 до 0,70 според двойката.

*Защо има значение тук.* Самите честоти на таговете създават своего рода клъстери: честите тагове се срещат заедно случайно. Ако разбърканите мрежи достигат същото Q при същата γ, Q не дава доказателство за структура отвъд това, което създават бройките на таговете и игрите. Q е едно число за цялото разбиване: разбъркана мрежа може да го достигне с напълно различни групи, а това, че Q не надхвърля нулевия модел, е липса на доказателство, а не доказателство за липса.

*Пример.* При Overall g = 17, s = 2: „Q при резолюция 1,151 е 0,067; никоя разбъркана мрежа с Q не го достига (разбъркани мрежи с Q: 100; обхват от −0,022 до −0,009).“ „Многотагови клъстери: наблюдавани 4, медиана 3 (разбъркани мрежи с избрано разбиване: 70; обхват от 3 до 5).“ „Ширина на областта на оптималност: медиана 0,049 срещу наблюдавана 0,158; наблюдаваната е по-широка от 70 от 70.“

*Граници.* Бройките са от 0 до R, като D + U = R; делът на смущението е от 0 до 1.

*Сравнете с.* Отправната стойност от нулевия модел на работното място (20 повторения при една γ).

**Точна дефиниция:** повторението r разбърква с `random.Random(seed_r)`, seed_r от поток 4 на главното начално число; Q_r(γ_obs) е най-голямото (Â − γ_obs·P̂)/2m от разбиването от обвивката на повторението при γ_obs и неговите 10 изпълнения на Leiden при γ_obs с началните числа от сканирането, неопределено, когато повторението няма ребра или γ_obs надхвърля края на сканирането му (`beyond_scan`); D = #{r : Q_r(γ_obs) е определено}; reach = #{r : Q_r(γ_obs) ≥ Q_obs}; дял на смущението = делът от клетките с 1 в наблюдаваната таблица, които след разбъркването са 0.
```

---

## 2. Chapter 3: Subsample Stability (`03-metric-reference.md#subsample-stability`)

**Changes**
- In short: **R** "the chosen pair's Clusters" becomes "a pair's Clusters … its procedure reruns" [04]. Higher and Here: **K**.
- Caution: **R**. "absent Clusters are never scored 0" is now false for the Whole-Cluster Jaccard [01], and the limitation is added [04].
- Columns: **R** [07].
- Paragraph 1:
  - The draw and the threshold scaling: **K**.
  - The arms sentence: **R**, adding the scope phrase [04] and the runs at γ_obs [03].
  - The degenerate sentence: **R**, adding `beyond_scan` [03].
  - **+** The s′-clamp direction [05] and the clamp quote [09].
- "Both are compared … by Hennig's Jaccard … averaged over the B* subsamples where the Cluster has a tag": **R**. There are now two Jaccards, and B* requires ≥ 2 surviving tags [01].
- The retention-share sentence and the "absent" sentence: **R**. Both are now export-only facts [01].
- "A Cluster is 'Dissolved' when its mean Jaccard is ≤ 0.5, the only cut used": **X**. In its place come the figures paragraph [02] and the status paragraph [01, 02].
- **+** The small-Cluster caveat [01].
- **+** Caution marker, with the limitation sentences [04].
- Why it matters: **K**, **+** one sentence on the Whole-Cluster Jaccard.
- Example: **R** with the real stored figures.
- Bounds: **R**.
- Compare with: **K**.
- Exact definition: **R**.

### English

```markdown
### Subsample Stability

> **In short.** How much a pair's Clusters change when its procedure reruns on random 80% game subsets, in two arms.
>
> **Higher →** the Clusters depend less on which games are in the dataset.
>
> **Here:** separates Clusters the whole Top 100 carries from those a few games create.
>
> **Caution:** not evidence that the Clusters are real; slightly optimistic for a pair chosen on the same data.

Columns: `ari`, `edged_share`, `degenerate`, `degenerate_reason`, `beyond_scan` in `validation_replicates.csv`; `size`, `mean_jaccard`, `mean_jaccard_se`, `at_most_half`, `dissolution_frequency`, `wilson_low`, `wilson_high`, `recovered`, `recovery_frequency`, `dissolved_in_most`, `borderline`, `assessable`, `mean_whole_cluster_jaccard`, `present`, `mean_retention`, `absent` in `validation_clusters.csv`.

Each of S = 100 subsamples draws m = ⌊0.8·n⌋ of the n games without replacement, with thresholds scaled by floor: g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋). In the **re-selected** arm (the headline), the same per-pair procedure runs again at (g′, s′); in the **at resolution** arm, the subsample's partition at the observed γ_obs is the best of its scan envelope and 10 Leiden runs at exactly γ_obs, as in the [Null Comparison](#null-comparison). A subsample is degenerate when it has no edges, when (re-selected) it has no Selected Partition, or when (at resolution) γ_obs lies beyond its scan end; degenerate subsamples are counted as "k of S" and left out of every figure. At s = 2 the floor makes the subsample's edge threshold stricter than proportional, 2 of m games (2.5% at m = 80) instead of 2%, while g′ is looser, so those subsample networks have fewer edges than a proportional design would give. On the Build of 2026-10-08, rerunning the s = 2 validations with s′ = 1 instead of the clamped s′ = 2 moves 0 of 50 Dissolved-in-most-subsamples labels (25 Multi-Tag Clusters × 2 arms) and changes a mean Hennig's Jaccard by at most 0.07.

Both arms compare the subsample with the Selected Partition on the tags in both networks with an edge in either: by ARI, shown with the share of the edged tags it covers, and per Multi-Tag Cluster by two Jaccards (Hennig 2007, §2). **Hennig's Jaccard** is the best overlap with any subsample Cluster on the Cluster's surviving tags. It needs at least two surviving tags, and losing tags does not lower it. **Whole-Cluster Jaccard** counts lost tags as not recovered. It is never higher than Hennig's Jaccard, equals it when no tag is lost, and is 0 when no tag survives. The export also gives each Cluster's mean retention share (the part of its tags that survive) and the number of subsamples where none survives.

Hennig's Jaccard is summarised over the B* subsamples in which the Cluster keeps at least two tags. The summary gives its mean with the Monte Carlo standard error, the 10th–90th percentile spread, and two frequencies with 95% Wilson intervals (Wilson 1927): ≤ 0.5 (dissolution) and > 0.75 (good recovery, Hennig's own example). The Whole-Cluster Jaccard is summarised over every non-degenerate subsample, as a mean with its standard error and the spread only, with no frequencies and no label: Hennig's 0.5 argument assumes a common tag set, which only Hennig's Jaccard has. The standard error and the Wilson interval describe the Monte Carlo error from S subsamples, and the spread describes how much the Cluster varies between subsamples. Neither is a confidence interval: the Top 100 is not a sample.

A Cluster gets one label at most, **Dissolved in most subsamples**: Hennig's Jaccard ≤ 0.5 in more than half of B* (exactly half is not labelled). The 0.5 cut per subsample is Hennig's; the majority is this study's rule (see [Appendix A](appendix-a-rules-of-thumb.md#cluster-wise-jaccard-stability)). A Cluster is **borderline** when the Wilson interval of its dissolution frequency contains ½, labelled or not. It is **Not assessable** when B* = 0, that is, when fewer than 2 of its tags survive in every subsample. "Rarely assessable" is flagged beside its mean when B* is under half of the non-degenerate subsamples. Recovery is only ever a frequency, never a label. Clusters of 2–3 tags can take only a few Jaccard values, and they drop sharply when they lose or move one tag; no Cluster is left out for its size.

*Caution.* The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part in the choice, so the Null Comparison is barely affected.

*Why it matters here.* The Top 100 is one ranked list; a few games more or less should not redraw a combination of characteristics that many games share. A Cluster that dissolves without 20% of the games rests on few of them. The Whole-Cluster Jaccard adds what Hennig's leaves out: a Cluster whose tags drop out of the network is not recovered, even if the tags that are left still group together.

*Example.* At Overall g = 17, s = 2, re-selected: median ARI 0.78 over 100 of 100 subsamples. C4 (4 tags) has Hennig's Jaccard ≤ 0.5 in 70 of 100 subsamples (95% Wilson interval 0.60 to 0.78) and a mean of 0.45, so it is Dissolved in most subsamples, re-selected only: at resolution it is ≤ 0.5 in 24 of 100. C1–C3 (7–9 tags) are above 0.75 in 41 to 92 of 100.

*Bounds.* ARI −0.5 to 1; both Jaccards, the frequencies, the tag share and the retention share 0 to 1; B* 0 to S.

*Compare with.* Neighbour Agreement (other thresholds, same games) and the Seed-Noise Floor (another seed): see [Three kinds of stability](#three-kinds-of-stability).

**Exact definition:** subsample r draws `random.Random(seed_r).sample(games, m)`, seed_r from stream 5; for Cluster C, C′ is its tags in the comparison set and D′ a subsample Cluster restricted to it; Hennig's J_r = max_D |C′ ∩ D′| / |C′ ∪ D′|, scored when |C′| ≥ 2; Whole-Cluster J_r = max_D |C ∩ D′| / |C ∪ D′|, 0 when |C′| = 0; B* = #{non-degenerate r : |C′| ≥ 2}; `mean_jaccard_se` = sd(J_r)/√B*; `dissolution_frequency` = #{J_r ≤ 0.5}/B*, with the 95% Wilson interval (z = 1.96); `dissolved_in_most` = #{J_r ≤ 0.5} > B*/2; `borderline` = `wilson_low` ≤ 0.5 ≤ `wilson_high`; `assessable` = B* > 0.
```

### Bulgarian

```markdown
### Стабилност при подизвадки (Subsample Stability) {#subsample-stability}

> **Накратко.** Колко се променят клъстерите на една двойка, когато процедурата ѝ се изпълни отново върху случайни подмножества от 80% от игрите, в два варианта.
>
> **По-високо →** клъстерите зависят по-малко от това кои игри са в набора.
>
> **Тук:** отделя клъстерите, които носи целият Топ-100, от тези, които създават няколко игри.
>
> **Внимание:** не доказва, че клъстерите са реални; леко оптимистична за двойка, избрана върху същите данни.

Колони: `ari`, `edged_share`, `degenerate`, `degenerate_reason`, `beyond_scan` в `validation_replicates.csv`; `size`, `mean_jaccard`, `mean_jaccard_se`, `at_most_half`, `dissolution_frequency`, `wilson_low`, `wilson_high`, `recovered`, `recovery_frequency`, `dissolved_in_most`, `borderline`, `assessable`, `mean_whole_cluster_jaccard`, `present`, `mean_retention`, `absent` в `validation_clusters.csv`.

Всяка от S = 100 подизвадки изтегля m = ⌊0.8·n⌋ от n-те игри без връщане, с прагове, мащабирани със закръгляне надолу: g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋). Във варианта **при нов избор** (водещият) същата процедура за една двойка се изпълнява отново при (g′, s′); във варианта **при резолюцията** разбиването на подизвадката при наблюдаваната γ_obs е най-доброто от обвивката на сканирането ѝ и 10 изпълнения на Leiden точно при γ_obs, както при [сравнението с нулев модел](#null-comparison). Подизвадката е изродена, когато няма ребра, когато (при нов избор) няма избрано разбиване или когато (при резолюцията) γ_obs е извън края на сканирането ѝ; изродените подизвадки се броят като „k от S“ и се изключват от всички стойности. При s = 2 долната граница прави прага за ребро в подизвадката по-строг от пропорционалния – 2 от m игри (2,5% при m = 80) вместо 2% –, докато g′ е по-свободен, затова тези мрежи на подизвадките имат по-малко ребра, отколкото би им дал пропорционален дизайн. При компилацията от 2026-10-08 повторното изпълнение на валидиранията при s = 2 с s′ = 1 вместо ограниченото s′ = 2 не променя нито един от 50-те етикета „Разпаднат в повечето подизвадки“ (25 многотагови клъстера × 2 варианта) и променя средния индекс на Jaccard по Hennig най-много с 0,07.

И двата варианта сравняват подизвадката с избраното разбиване по таговете и в двете мрежи с ребро в някоя от тях: по ARI, показан с дела на таговете с ребро, които покрива, и за всеки многотагов клъстер – по два индекса на Jaccard (Hennig 2007, §2). **Индексът на Jaccard по Hennig** е най-доброто припокриване с някой клъстер на подизвадката върху оцелелите тагове на клъстера. Той изисква поне два оцелели тага и загубата на тагове не го намалява. **Индексът на Jaccard за целия клъстер** брои изгубените тагове като невъзстановени. Той никога не е по-висок от индекса по Hennig, равен е на него, когато не е изгубен нито един таг, и е 0, когато не оцелява нито един таг. Експортът дава и средния дял на запазване на всеки клъстер (частта от таговете му, които оцеляват), и броя на подизвадките, в които не оцелява нито един.

Индексът по Hennig се обобщава по B* подизвадките, в които клъстерът запазва поне два тага. Обобщението дава средното му със стандартната грешка по Monte Carlo, разсейването между персентили 10–90 и две честоти с 95% интервали на Wilson (Wilson 1927): ≤ 0,5 (разпадане) и > 0,75 (добро възстановяване – собственият пример на Hennig). Индексът за целия клъстер се обобщава по всички неизродени подизвадки само като средно със стандартната му грешка и разсейването, без честоти и без етикет: аргументът на Hennig за 0,5 предполага общо множество тагове, каквото има само индексът по Hennig. Стандартната грешка и интервалът на Wilson описват грешката по Monte Carlo от S подизвадки, а разсейването – колко варира клъстерът между подизвадките. Нито едно от тях не е доверителен интервал: Топ-100 не е извадка.

Един клъстер получава най-много един етикет – **Разпаднат в повечето подизвадки**: индекс на Jaccard по Hennig ≤ 0,5 в повече от половината от B* (точно половината не получава етикета). Границата 0,5 за една подизвадка е на Hennig, а мнозинството е правило на това изследване (вижте [Приложение A](appendix-a-rules-of-thumb.md#cluster-wise-jaccard-stability)). Клъстерът е **на границата**, когато интервалът на Wilson на честотата му на разпадане съдържа ½, независимо дали има етикет. Той е **Не може да се оцени**, когато B* = 0, т.е. когато във всяка подизвадка оцеляват по-малко от 2 негови тага. До средното се показва отметка „рядко оценим“, когато B* е под половината от неизродените подизвадки. Възстановяването е само честота, никога етикет. Клъстерите от 2–3 тага могат да приемат само няколко стойности на индекса и рязко падат, когато загубят или преместят един таг; нито един клъстер не се изключва заради размера си.

*Внимание.* Двойката е избрана върху същите данни, затова стабилността при подизвадки може да е леко оптимистична. Q не участва в избора, така че сравнението с нулев модел почти не е засегнато.

*Защо има значение тук.* Топ-100 е един ранжиран списък; няколко игри повече или по-малко не би трябвало да преначертават комбинация от характеристики, която споделят много игри. Клъстер, който се разпада без 20% от игрите, стъпва на малко от тях. Индексът за целия клъстер добавя това, което индексът по Hennig изпуска: клъстер, чиито тагове отпадат от мрежата, не е възстановен, дори ако останалите тагове все още се групират заедно.

*Пример.* При Overall g = 17, s = 2, при нов избор: медиана на ARI 0,78 при 100 от 100 подизвадки. C4 (4 тага) има индекс на Jaccard по Hennig ≤ 0,5 в 70 от 100 подизвадки (95% интервал на Wilson от 0,60 до 0,78) и средно 0,45, затова е разпаднат в повечето подизвадки само при нов избор: при резолюцията е ≤ 0,5 в 24 от 100. C1–C3 (7–9 тага) са над 0,75 в 41 до 92 от 100.

*Граници.* ARI от −0,5 до 1; двата индекса на Jaccard, честотите, делът на таговете и делът на запазване от 0 до 1; B* от 0 до S.

*Сравнете с.* Съгласието със съседите (други прагове, същите игри) и прага на шума от началното число (друго начално число): вижте [Три вида стабилност](#three-kinds-of-stability).

**Точна дефиниция:** подизвадката r изтегля `random.Random(seed_r).sample(games, m)`, seed_r от поток 5; за клъстер C C′ са таговете му в множеството за сравнение, а D′ е клъстер на подизвадката, ограничен до него; J_r по Hennig = max_D |C′ ∩ D′| / |C′ ∪ D′|, оценява се при |C′| ≥ 2; J_r за целия клъстер = max_D |C ∩ D′| / |C ∪ D′|, 0 при |C′| = 0; B* = #{неизродени r : |C′| ≥ 2}; `mean_jaccard_se` = sd(J_r)/√B*; `dissolution_frequency` = #{J_r ≤ 0,5}/B*, с 95% интервал на Wilson (z = 1,96); `dissolved_in_most` = #{J_r ≤ 0,5} > B*/2; `borderline` = `wilson_low` ≤ 0,5 ≤ `wilson_high`; `assessable` = B* > 0.
```

---

## 3. Methods paragraph (`05-citing-and-reproducing.md`, and the `selection_report.md` template)

**Changes.** Everything up to "…among pairs with ‹constraints›." is **K**. The last two sentences ("We compared the chosen pair with … not applied.") are **R** by the text below:
- "the chosen pair" becomes "each validated Threshold Pair" (point 6).
- The scope phrase [04] and the runs at γ_obs [03].
- The count-only rule and why it has no p-value [04].
- Both arms.
- B* with at least two tags [01], the s.e. and the two frequencies with Wilson intervals [02], the Whole-Cluster Jaccard [01] and the majority rule [02].
- The fpc clause: **K**.
- **+** The limitation sentence [04].

No new placeholder is needed.

### English (replaces the last two sentences)

> We compared each validated Threshold Pair with ‹replicates› networks whose game–tag table was shuffled by curveball trades (every tag and game keeps its count; Strona et al. 2014), each analysed by the identical procedure: the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, abstract, §III and §VI). Q at the observed Selected Resolution was taken as the best of each network's scan envelope and 10 Leiden runs at exactly that γ, on the observed network and every replicate alike; we report how many of the D shuffled networks with a defined Q reach the observed Q, and give no p-value, because the resolution and the pair were chosen on the observed data. We also compared the pair with ‹subsamples› random subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), once re-selecting by the same per-pair procedure and once reading the partition at the observed resolution. For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on its tags present in both networks, over the B* subsamples in which at least two of them survive, with its Monte Carlo standard error and the frequencies of values ≤ 0.5 and > 0.75 with 95% Wilson intervals (Wilson 1927), and a Whole-Cluster Jaccard that counts lost tags as not recovered. We call a Cluster dissolved in most subsamples when its Jaccard is 0.5 or less in more than half of the B* subsamples (the per-subsample cut is Hennig's, the majority our rule); the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and are not applied. The pair was chosen on the same data, so Subsample Stability may be slightly optimistic.

### Bulgarian (replaces „Сравнихме избраната двойка … не се прилагат.“)

> Сравнихме всяка валидирана двойка прагове с ‹replicates› мрежи, чиято таблица игри–тагове е разбъркана чрез размени curveball (всеки таг и всяка игра запазват броя си; Strona et al. 2014), всяка анализирана по същата процедура: процедурата за една двойка при същата двойка прагове (собствено сканиране по γ, CHAMP, γ̂ и правилото за избраното разбиване), а не решетката на параметрите или изборът на двойка (Karrer, Levina & Newman 2008, резюме, §III и §VI). Q при наблюдаваната избрана резолюция взехме като най-доброто от горната обвивка на сканирането на всяка мрежа и 10 изпълнения на Leiden точно при тази γ, еднакво за наблюдаваната мрежа и за всяко повторение; отчитаме колко от D-те разбъркани мрежи с определено Q достигат наблюдаваното Q и не даваме стойност p, защото резолюцията и двойката са избрани върху наблюдаваните данни. Сравнихме двойката и с ‹subsamples› случайни подмножества от m = ⌊0.8·n⌋ от n-те игри, с прагове, мащабирани със закръгляне надолу (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), веднъж с нов избор по същата процедура за една двойка и веднъж с разбиването при наблюдаваната резолюция. За всеки многотагов клъстер отчитаме средния индекс на Jaccard за най-добро съвпадение на Hennig (2007, §2) върху таговете му, присъстващи и в двете мрежи, по B* подизвадките, в които оцеляват поне два от тях, със стандартната му грешка по Monte Carlo и честотите на стойностите ≤ 0,5 и > 0,75 с 95% интервали на Wilson (Wilson 1927), както и индекс на Jaccard за целия клъстер, който брои изгубените тагове като невъзстановени. Наричаме клъстер разпаднат в повечето подизвадки, когато индексът му е 0,5 или по-малко в повече от половината от B* подизвадки (границата за една подизвадка е на Hennig, мнозинството е наше правило); граничните зони 0,6, 0,75 и 0,85 на пакета fpc се отнасят за bootstrap и не се прилагат. Двойката е избрана върху същите данни, затова стабилността при подизвадки може да е леко оптимистична.

---

## 4. Appendix A: Cluster-wise Jaccard stability (`appendix-a-rules-of-thumb.md#cluster-wise-jaccard-stability`)

**Changes**
- Bullet: **R**. It now says the 0.5 and 0.75 cuts apply per resample and the fpc bands to the mean (point 3).
- "Why not here", sentences 1–2: **K**, except that "bootstrap resampling" becomes "resampling", since this study subsamples.
- "The one exception … uses Hennig's measure itself: there ≤ 0.5 = dissolved … the only cut used, because … justification": **R**, by the per-subsample cut plus the majority rule [02].
- **+** borderline [02], recovery as a frequency only [02], no cut for the Whole-Cluster Jaccard [02] and Not assessable [01].
- "The 0.6, 0.75 and 0.85 values stay unused: fpc says they refer to the bootstrap": **K**, reworded to "bands on the mean" so it doesn't contradict Hennig's 0.75 frequency.

### English

```markdown
## Cluster-wise Jaccard stability

- In one resample, a cluster whose Jaccard with its best match is 0.5 or less counts as "dissolved", and values above 0.75 as "good recoveries, say"; Hennig suggests summarising a cluster by the mean or by the number of dissolutions or good recoveries (Hennig 2007, §2). The `fpc` package's `clusterboot` documentation adds bands for the mean: values below 0.6 should not be trusted, 0.6–0.75 indicate patterns with doubtful membership, and 0.85 and above highly stable clusters.

**Why not here.** Hennig's measure is per cluster under resampling of the data. Membership Stability is per tag across random seeds on fixed data, and the study decided to show it as a plain number. The one exception is Subsample Stability in the Parameter Selection mode, which uses Hennig's measure itself, on 80% subsamples rather than the bootstrap. There the study takes one cut from Hennig: in a subsample, a Cluster is dissolved when its Jaccard is ≤ 0.5 (Hennig 2007, §2), the smallest value at which every cluster of a partition can be dissolved by a new one. Over the subsamples it applies its own majority rule (**Dissolved in most subsamples**: ≤ 0.5 in more than half) instead of a cut on the mean, and marks a Cluster **borderline** when the 95% Wilson interval of that frequency contains ½. Hennig's 0.75 is reported only as a frequency, never as a label. The `fpc` bands on the mean (0.6, 0.75 and 0.85) stay unused: `fpc` says they refer to the bootstrap. The **Whole-Cluster Jaccard**, which counts lost tags, gets no cut at all, because Hennig's 0.5 argument assumes the two clusters are compared on a common tag set. A Cluster with fewer than two surviving tags in every subsample is **Not assessable** rather than scored.
```

### Bulgarian

```markdown
## Стабилност на клъстерите по индекса на Jaccard {#cluster-wise-jaccard-stability}

- В една преизвадка клъстер, чийто индекс на Jaccard с най-доброто му съвпадение е 0,5 или по-малко, се смята за „разпаднат“, а стойности над 0,75 – за „добри възстановявания, да речем“; Hennig предлага клъстерът да се обобщава чрез средното или чрез броя на разпаданията или на добрите възстановявания (Hennig 2007, §2). Документацията на `clusterboot` в пакета `fpc` добавя граници за средното: на стойности под 0,6 не бива да се вярва, 0,6–0,75 показват модели със съмнителна принадлежност, а 0,85 и повече – силно стабилни клъстери.

**Защо не тук.** Мярката на Hennig е за всеки клъстер при преизвадки на данните. Стабилността на принадлежността е за всеки таг при случайни начални числа върху фиксирани данни и изследването реши да я показва като обикновено число. Единственото изключение е стабилността при подизвадки в режим „Избор на параметри“, която използва самата мярка на Hennig, върху подизвадки от 80% вместо bootstrap. Там изследването взема от Hennig една граница: в една подизвадка клъстерът е разпаднат, когато индексът му на Jaccard е ≤ 0,5 (Hennig 2007, §2) – най-малката стойност, при която всеки клъстер на дадено разбиване може да бъде разпаднат от ново. По подизвадките то прилага собствено правило на мнозинството (**Разпаднат в повечето подизвадки**: ≤ 0,5 в повече от половината) вместо граница за средното и отбелязва клъстера като **на границата**, когато 95% интервал на Wilson на тази честота съдържа ½. Стойността 0,75 на Hennig се отчита само като честота, никога като етикет. Границите на `fpc` за средното (0,6, 0,75 и 0,85) остават неизползвани: `fpc` казва, че те се отнасят за bootstrap. **Индексът на Jaccard за целия клъстер**, който брои изгубените тагове, не получава никаква граница, защото аргументът на Hennig за 0,5 предполага, че двата клъстера се сравняват върху общо множество тагове. Клъстер, от който във всяка подизвадка оцеляват по-малко от два тага, получава статус **Не може да се оцени**, а не стойност.
```

---

## 5. Knock-on passages

These follow from tickets 04 and 07. Nothing here decides anything new.

| File | Change | English | Bulgarian |
|---|---|---|---|
| `06-known-limitations.md`, Parameter Selection, after "Validation is one 80% fraction…" | **+** bullet [04, 05] | **Validation runs on the data the pair was chosen on.** Subsample Stability may be slightly optimistic; Q played no part in the choice, so the Null Comparison is barely affected. The grid and the choice of pair are not repeated per replicate. | **Валидирането се изпълнява върху данните, върху които е избрана двойката.** Стабилността при подизвадки може да е леко оптимистична; Q не участва в избора, така че сравнението с нулев модел почти не е засегнато. Решетката и изборът на двойка не се повтарят за всяко повторение. |
| `05-citing-and-reproducing.md` ¶ "Press Export tables" | **R** "seven tables" [07] | It holds the eight tables, … | Той съдържа осемте таблици, … |
| `02-app-controls.md`, Export tables, In short | **R** "seven tables" [07] | …with eight tables, … | …с осем таблици, … |
| `04-files.md` ¶ "Export tables … writes one zip" | **R** "the two validation tables" [07] | …the three validation tables hold rows for validated pairs only. | …трите таблици на валидирането съдържат редове само за валидираните двойки. |
| `04-files.md`, **+** `### validation_pairs.csv` before `validation_replicates.csv` | **+** [07] | One row is one validated pair: the Null Comparison's state (above all defined, reached or undefined), R, D, U and U's reasons, the domain-width count with ties counted apart, and two flags: most shuffled networks have no Q (D < R/2), and a Multi-Tag Cluster is rarely assessable. | Един ред е една валидирана двойка: състоянието на сравнението с нулев модел (над всички определени, достигнато или неопределено), R, D, U и причините за U, броят по ширина на областта с отделно преброени равенства и две отметки: повечето разбъркани мрежи нямат Q (D < R/2) и многотагов клъстер е рядко оценим. |
| `04-files.md` `validation_replicates.csv` | **R** [07] | One row is one validation replicate and arm (`null`, `subsample_reselected`, `subsample_at_resolution`) of a validated pair: its seed, whether it had a Selected Partition or was degenerate and why (including `beyond_scan`), its ARI against the Selected Partition with the share of edged tags it covers, Q at the observed resolution from the envelope alone and after the runs at γ_obs, and its Perturbation Share (null arm), the scan length and capped runs. | Един ред е едно повторение на валидирането и вариант (`null`, `subsample_reselected`, `subsample_at_resolution`) за валидирана двойка: началното му число, дали е имало избрано разбиване или е било изродено и защо (включително `beyond_scan`), ARI спрямо избраното разбиване с дела на таговете с ребро, които покрива, Q при наблюдаваната резолюция само от обвивката и след изпълненията при γ_obs, и делът на смущението (вариантът `null`), дължината на сканирането и изпълненията, достигнали горната граница. |
| `04-files.md` `validation_clusters.csv` | **R** [07] | One row is one Multi-Tag Cluster of a validated pair's Selected Partition in one Subsample Stability arm: its size; Hennig's Jaccard as a mean with its standard error, with the dissolution and good-recovery counts and frequencies and their 95% Wilson intervals; the Whole-Cluster Jaccard mean; the statuses `dissolved_in_most`, `borderline` and `assessable`; the mean retention share and the absent count. | Един ред е един многотагов клъстер от избраното разбиване на валидирана двойка в един вариант на стабилността при подизвадки: размерът му; индексът на Jaccard по Hennig като средно със стандартна грешка, с броя и честотите на разпадане и на добро възстановяване и техните 95% интервали на Wilson; средният индекс на Jaccard за целия клъстер; статусите `dissolved_in_most`, `borderline` и `assessable`; средният дял на запазване и броят на отсъствията. |
| `appendix-b-column-index.md` | regenerate | Generated from `steamstudy.export.schema` (`python -m steamstudy.export.column_index`), so it is not hand-edited. The new columns need an "Explained in" anchor in the schema. | The same, in `bg/`. |
| `appendix-c-references.md` (both) | **+** | Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *J. Am. Stat. Assoc.* 22(158), 209–212. doi:10.1080/01621459.1927.10502953 | The same entry. |

**Left unchanged after checking:**
- *Three kinds of stability*: its "dissolve" is generic.
- *How Automatic Parameter Selection works*, step 8: "the chosen pair" names the automatic step, which is accurate.
- `02-app-controls.md`, Validate this pair.
- `01-getting-started.md`.

---

## 6. CONTEXT.md

No change; see point 9. Checked against tickets 01–05:
- **Subsample Stability** has "re-selected by the same per-pair procedure".
- **Null Comparison** has the scope phrase.
- **Hennig's Jaccard**, **Whole-Cluster Jaccard**, **Dissolved in most subsamples**, **Q not above the null** and **Perturbation Share** are present, with _Avoid_ lines.
- *borderline*, *Not assessable* and *rarely assessable* stay out. They are statuses defined by a figure, not domain concepts, which is how ticket 02 left them.

## 7. bg-terms.md (the glossary's Bulgarian)

| Change | English | Bulgarian | Avoid |
|---|---|---|---|
| **R** row "dissolved (a Cluster under subsampling)" | Dissolved in most subsamples | разпаднат в повечето подизвадки (a list or count: разпаднати…) | разтворен; bare *разпаднат* as the label |
| **+** | Hennig's Jaccard | индекс на Jaccard по Hennig; short Jaccard (Hennig) | индекс на стабилност, bootstrap Jaccard |
| **+** | Whole-Cluster Jaccard | индекс на Jaccard за целия клъстер; short Jaccard (цял клъстер) | пълен Jaccard |
| **+** | Q not above the null | Q не е над нулевия модел | незначимо, p > 0,05 |
| **+** | Perturbation Share | дял на смущението (point 4) | оценка на смесването, случайност |
| **+** | per-pair procedure | процедурата за една двойка | — |
| **+** | borderline · Not assessable · rarely assessable | на границата · Не може да се оцени · рядко оценим | Неоценим (reads as *invaluable*) |
| **+** | s.e. · 10th–90th percentile spread · 95% Wilson interval · Monte Carlo error | стандартна грешка (ст. гр.) · разсейване между персентили 10–90 (перс. 10–90) · 95% интервал на Wilson · грешка по Monte Carlo (point 5) | доверителен интервал (for any of them) |

The superseded-word scan (`tests/test_i18n.py`) gains nothing: *Неоценим* has never been written, and *разпаднат* survives inside the new term.
