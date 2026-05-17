# Scaling Risk Checker — Rebuild Plan

## The core problem

Adoption is low. The ten weaknesses in `TOOL_ANALYSIS.md` almost all trace back to
one root cause:

> **The tool asks people for numbers they don't actually know, then gives them a
> confident verdict built on those guesses.**

A skeptical user feels this immediately — "I'm not sure about half of what I typed,
so why would I trust the output?"

## Three principles

1. **Derive, don't ask.** Wherever a number can be computed from data the user
   already has, compute it instead of asking them to guess.
2. **Sanity-check what we must ask.** When we do need an input, validate it against
   benchmark ranges and warn on implausible values.
3. **Show uncertainty honestly.** When inputs are shaky, the output should visibly
   widen — ranges and bands, not single numbers with false precision.

New depth goes behind an **Advanced** toggle so the default flow stays simple.

## Phases

### Phase 1 — Make the tool honest about what it doesn't know
Low-risk, no data-model changes, ships fast.
- Plausibility checks on every entered number (close rate, AOV, COGS, refund rate)
  with benchmark ranges shown inline.
- Low-confidence mode actually holds back — says "not enough to advise yet" instead
  of handing out budget figures.
- Relabel every input to say where the number should come from.
- Flag the dead `repeat_purchase_value` input (collected but never used in any
  calculation) — fixed properly in Phase 2.

### Phase 2 — Replace guessed inputs with derived numbers
The heart of the diagnosis.
- Compute implied close rate from real orders / real conversations (already
  collected) and show it next to the user's guess so they can reconcile.
- Add one explicit attribution question — how many orders are new customers from
  this ad spend — so repeat customers stop inflating CAC.
- Wire `repeat_purchase_value` into the calculation.
- Guessed inputs become fallbacks, not the main path.

### Phase 3 — Show ranges instead of false precision
- Run the simulation across a low / expected / high band; render the profit curve
  as a band, not a single line.
- Let advanced users derive real CAC deterioration from "last month vs this month"
  instead of picking a preset.

### Phase 4 — Advanced inputs behind optional toggle
- Product-mix breakdown, segmented refund rates, multi-channel split — all behind
  the Advanced toggle so casual users never see them.
- Recommendations become evidence-backed: show the number and threshold that
  triggered each one, not a templated line.

### Phase 5 — Verification
- Hand-check calculations against worked examples.
- Test ranges at extremes.
- Confirm the Advanced toggle doesn't break the simple flow.

## Sequencing rationale

Phases 1–3 are what actually moves "people aren't interested" — they directly
attack the trust problem and ship incrementally. Phase 4 adds rigor for power
users without complicating the default experience.
