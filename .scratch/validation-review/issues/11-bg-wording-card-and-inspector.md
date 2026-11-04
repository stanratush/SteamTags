# What is the bg wording of the validation card and the Inspector's Validation section?
Type: grilling
Status: open
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
