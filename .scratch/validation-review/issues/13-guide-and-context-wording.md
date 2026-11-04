# What do the User Guide's validation passages and CONTEXT.md entries say, in English and Bulgarian?
Type: prototype
Status: resolved
Blocked by:

## Question

Draft the User Guide and CONTEXT.md text that the resolved tickets call for, in English and bg, so the spec can quote it verbatim:
- ch. 3 entries for Null Comparison and Subsample Stability;
- the methods paragraph;
- Appendix A's Jaccard bands (Hennig's Jaccard, Whole-Cluster Jaccard, Dissolved in most subsamples, borderline, Not assessable);
- the CONTEXT.md entries (e.g. Q not above the null, Perturbation Share, Whole-Cluster Jaccard).

Many sentences are already fixed in their tickets: ticket 04's "no evidence beyond the counts" and scope/limitation sentences, ticket 05's s′-clamp direction and "conditional on the scan" sentences, ticket 12's direction clause, and the guide quotes of tickets 08, 09 and 10. This ticket places them, writes the connective text, and gives every passage its Bulgarian with [What is the bg wording of the validation card and the Inspector's Validation section?](11-bg-wording-card-and-inspector.md)'s term table and conventions. Read the current guide passages first, and mark which existing sentences are replaced or removed.

## Answer

Resolved 2026-11-05 by prototype with the researcher, who accepted the draft and all nine of its open points. The verbatim text, English and Bulgarian, is in **[guide-text.md](../prototypes/13-guide-wording/guide-text.md)**. That file is the asset the spec quotes. Each passage in it lists which current sentences are kept, replaced, removed or added, and which ticket fixed each sentence.

**What it covers**
- **Chapter 3, Null Comparison.** Changes:
  - the scope phrase;
  - the runs at γ_obs and their residual, with no extrapolation;
  - the three states over D and the D < R/2 flag;
  - the two reasons for giving no p-value;
  - the Multi-Tag Cluster and width paragraph, with ticket 05's scan sentence, ticket 12's direction clause and ticket 10's quote;
  - the Perturbation Share, with ticket 08's quote and the 0.58–0.70 range;
  - ticket 04's "absence of evidence" sentence.
- **Chapter 3, Subsample Stability.** Changes:
  - both Jaccards, and B* with at least two surviving tags;
  - the s.e., the 10th–90th percentile spread and both frequencies with Wilson intervals;
  - the three statuses and the "rarely assessable" flag;
  - the small-Cluster caveat;
  - the s′-clamp direction with ticket 09's quote;
  - the limitation sentence, which appears in the In short Caution and in a Caution marker.
- **Both entries** use real example figures from the stored Overall g = 17, s = 2 run. Every In short block passes the guide parser's 60-word check (en 51 / 59, bg 55 / 59).
- **Methods paragraph:** its last two sentences are replaced. No new placeholder is needed.
- **Appendix A, Cluster-wise Jaccard stability:** the bullet and the "Why not here" paragraph are rewritten.
- **Knock-on edits:**
  - a known-limitations bullet;
  - "seven tables" becomes "eight" in `05-citing` and `02-app-controls`;
  - in `04-files`, three validation tables, a new `validation_pairs.csv` section and new descriptions of the replicates and clusters tables;
  - Appendix B is regenerated from the schema;
  - Wilson (1927) is added to Appendix C.
- **Glossary:** CONTEXT.md doesn't change, because commit 9f3b2ec already holds every term tickets 01–05 named. `docs/i18n/bg-terms.md` replaces its "dissolved" row and gains seven rows. The superseded-word list doesn't change.

**The nine points, as settled**
1. **Ticket 12's guide clause is reworded,** because "outwidths" is not a word. It now reads "so the count of shuffled networks narrower than the observed tends to understate, not overstate, how distinctive its width is". **This amends 12's wording, not its meaning.**
2. **A gap is closed: the card note for when the observed network's runs at γ_obs beat its Selected Partition's Q.**
   - English: "The runs at γ_obs found a Q of {q} on the observed network, above its Selected Partition's {q0}; the comparison uses {q}."
   - Bulgarian: "Изпълненията при γ_obs намериха Q {q} за наблюдаваната мрежа, над {q0} на избраното ѝ разбиване; сравнението използва {q}."
   - The guide mentions it in one sentence. It is a new catalogue entry, on top of ticket 11's.
3. **Appendix A's misattribution is corrected.** Hennig's 0.5 and 0.75 apply per resample, and the fpc bands apply to the mean.
4. **Perturbation Share** is "дял на смущението" in Bulgarian.
5. **"Monte Carlo"** stays in Latin script in Bulgarian ("грешка по Monte Carlo").
6. **The methods paragraph** says "each validated Threshold Pair", not "the chosen pair".
7. **Wilson (1927)** joins Appendix C in both languages.
8. **The percentile spreads and the Whole-Cluster Jaccard's s.e. stay card-only.** The export columns are ticket 07's, unchanged. The per-replicate Jaccards they come from stay in the cache JSON.
9. **CONTEXT.md doesn't change.** "borderline", "Not assessable" and "rarely assessable" stay statuses, not glossary terms.

**For the spec**
- **Guide quotes on the new Build.** The rerun issue (ticket 07's final issue) updates the figures in the quotes from tickets 08, 09 and 10, and the 0.58–0.70 range. If the examples' stored figures move, it updates those too.
- **Retired catalogue keys.** The guide's "Dissolved" / "mean Jaccard" wording goes with them.

No new ADR. The only new glossary changes are the bg-terms rows above.
