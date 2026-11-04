# What is the bg wording of the validation card and the Inspector's Validation section?
Type: grilling
Status: resolved
Blocked by:

## Question

The English of every card and Inspector string is now fixed by [What does the Null Comparison state, and by which rule?](04-null-comparison-rule-and-wording.md), [Which per-Cluster figures and verdict replace "Dissolved"?](02-cluster-figures-and-verdict.md) and [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md). Each string needs a bg catalogue entry (ADR 0003; parity test). Which Bulgarian wording do they take?

Scope: the new or changed strings on the card and in the Inspector only. The User Guide and CONTEXT.md bg text stays in the map's fog until their English is written.

Starting point: the draft `BG` table in [PROTOTYPE-validation-layout.html](../prototypes/06-validation-layout/PROTOTYPE-validation-layout.html). It was written only to test fit, and every string fitted at every width.

Decide:
- **Bulgarian names for the terms**, consistent with the existing catalogue (`src/steamstudy/i18n/bg/`): Hennig's Jaccard, Whole-Cluster Jaccard, Dissolved in most subsamples, borderline, Not assessable, rarely assessable, Q not above the null, per-pair procedure, 10th–90th percentile, s.e., Wilson interval. The catalogue already has "разбъркани мрежи", "при нов избор", "при резолюцията", "Сравнение с нулев модел" and "Стабилност при подизвадки".
- **Plural forms** for the counted sentences.
- **Number formatting:** the interval separators under a decimal comma ("42–62%", "от 0,45 до 0,65").
- **Column and legend abbreviations** that still fit the Cluster list at wide 1280 (card about 593 px).

## Answer

Every new or changed card and Inspector string has its Bulgarian, recorded with the conventions in **[bg-strings.md](../prototypes/11-bg-wording/bg-strings.md)**, the asset the spec cites. The 06 prototype's `BG` table now matches it.

- **Terms.** Hennig's Jaccard is "индекс на Jaccard по Hennig" (short: "Jaccard (Hennig)"), and Whole-Cluster Jaccard is "индекс на Jaccard за целия клъстер" ("Jaccard (цял клъстер)"). Dissolved in most subsamples is "Разпаднат в повечето подизвадки" for one Cluster and "Разпаднати…" for lists and counts. borderline is "на границата". Not assessable is "Не може да се оцени" (not "Неоценим", which reads as *invaluable*), and rarely assessable is "рядко оценим". Q not above the null keeps the existing "Q не е над нулевия модел", and the undefined badge is "Q на нулевия модел е неопределено". The per-pair procedure is "процедурата за една двойка". The percentile spread is "персентили 10–90" ("перс. 10–90"). s.e. is "ст. гр.", and the Wilson interval is "95% интервал на Wilson". Personal names stay in Latin script. Status is "Статус", matching the catalogue's "статус".
- **One key, two roles.** The bold lead of the dissolved list and its parenthesis become **one message**, "Dissolved in most subsamples (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's rule):", with plural Bulgarian. The template bolds the text before the first " (". The chip keeps the short singular key. The English on screen doesn't change.
- **Plurals.** The catalogue's colon form is used wherever a count isn't `{n}` or sits in a parenthesis or list. The one `tx.n` pair is "{k} of {n} Multi-Tag Clusters in both arms" (other: "…многотагови клъстера…", the counted form).
- **Numbers.** The decimal comma is used everywhere, labels included ("≤ 0,5"). Prose ranges are "от 0,45 до 0,65". Compact ranges use an en dash with no spaces ("0,45–0,65", "42–62%"), and only ever carry quantities ≥ 0. ARI always uses "от … до".
- **Fit.** 06's "every string fitted" was wrong for one string. "Размер" (39 px) overflowed the 30–34 px Size column at every width, which the earlier check missed because it only looked at the card's edges. **Amendment to 06:** the Size column is 44 px in both grids. Re-verified over 384 states (both languages × 4 widths × null states × Cluster edge cases × Inspector states × notes, rows expanded): no overflow, no cell overlap, no missing string. The bg expanded-row headers wrap to three lines at wide 1280.
- **Retired keys** (the old "Dissolved", "mean Jaccard" and "Q above all null replicates" entries, among others) are listed in the asset. The spec fixes the exact set against the final English.
- The User Guide and CONTEXT.md bg text stays in the map's fog.
