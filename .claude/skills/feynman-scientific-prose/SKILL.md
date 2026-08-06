---
name: feynman-scientific-prose
description: Use when writing or revising a scientific paper, preprint, thesis chapter, or technical report that reads as stiff, hedged, passive, or bureaucratic - when prose is technically correct but lifeless, buries the interesting result under throat-clearing, or hides uncertainty behind formal apparatus.
---

# Feynman Scientific Prose

## Overview

Richard Feynman wrote physics that a smart outsider could follow without the physics being weakened. The style is not jokes or informality. It is a set of concrete choices about who is speaking, what order things are explained in, and how honestly uncertainty is stated.

**Core principle: the reader is intelligent but uninitiated. Never perform rigor at their expense.**

This skill is for prose that must still pass referees. The constraint is real: keep the citations, the claim labels, the conventional section order, the precise numbers. Change the sentences, not the scaffolding.

## When to Use

- Draft reads as competent but dead; you would not read it yourself
- Sentences open with "It should be noted that", "It is important to emphasize"
- The interesting result is in paragraph four
- Uncertainty is expressed as apparatus ("merits further investigation") rather than as a statement ("we do not know whether")
- Nominalizations everywhere: "the application of", "the utilization of", "an examination of"
- Every sentence is the same length

**Do NOT use for:** grant boilerplate, regulatory submissions, or venues with an enforced house style that forbids first person. Check the venue first.

## The Seven Moves

**1. Lead with the phenomenon, not the literature.**
The first sentence of a section should be about the thing, not about who previously wrote about the thing. Citations support the claim; they do not open it.

**2. One idea per sentence. Vary the length.**
Feynman's rhythm is a long, carefully built sentence followed by a short one that lands. Uniform 30-word sentences are what makes prose feel like a machine wrote it.

**3. Name the mechanism physically.**
Not "a suppression effect is observed" but "you cannot suppress emissions that are not being made". If you cannot state the mechanism in physical words, you do not yet understand it.

**4. Verbs, not nominalizations.**
"Suppression acts on the emitted signal" beats "the application of suppression to the emitted signal". Search the draft for *-tion of*, *-ment of*, *-ance of*.

**5. State ignorance flatly.**
"We do not know what sets this coefficient" is stronger and shorter than "the determination of this coefficient remains an open question warranting future study". Hedging apparatus reads as evasion; a plain admission reads as confidence.

**6. Walk the reader through the reasoning, including the dead end.**
Feynman shows the attempt that failed and why. A negative result stated plainly is more persuasive than a positive one stated smoothly. When you made an error, say what it was and what it taught.

**7. Point at the surprising thing.**
If a result genuinely surprised you, say so in one clause. "The factor cancels — which is exactly what destroys the structure we were relying on." Do not bury the strange part in a subordinate clause.

## Before / After

| Bureaucratic | Feynman |
|---|---|
| It should be noted that the model does not incorporate a mortality term. | The model has no mortality term. |
| An examination of the results reveals that observability exhibits a decline. | Observability falls. |
| This behaviour is attributable to the fact that suppression scales more rapidly. | It falls because suppression grows faster than production does. |
| The utilization of a fractional formulation confers the advantage of boundedness. | Writing suppression as a fraction keeps the answer positive, and it does so by construction rather than by clamping. |
| Further investigation of this phenomenon is warranted. | We do not know how big this effect is. Measuring it would take a survey we have not done. |
| A discrepancy was identified in the initial formulation. | We got this wrong the first time, and the way we got it wrong is worth reporting. |

## Keep the Rigor

Feynman-style is **not** licence to:
- Drop citations, claim labels, or error bars
- Replace a number with an adjective ("very large" for $-1431$)
- Overclaim because the sentence sounds better
- Use jokes that a referee will read as unseriousness
- Switch to first-person singular in a multi-author paper

Precision is part of the voice. Feynman gave exact numbers and said exactly how confident he was. Vagueness is the opposite of this style, not a relaxed version of it.

## Section-Specific Guidance

| Section | What changes | What stays |
|---|---|---|
| Abstract | Lead with the result, not the field's history | Every number, every hedge that is real |
| Introduction | Open on the actual question; motivate before citing | Full citation coverage |
| Methods | Active voice where the agent matters | Passive where convention demands; full reproducibility detail |
| Results | State what happened, then why it happened | Exact values, uncertainties |
| Discussion | Say what you believe and how strongly | Claim labels, alternative explanations |
| Limitations | Plain admissions, no cushioning | Completeness — do not drop a limitation for style |

## Common Mistakes

**Mistaking informality for the style.** Contractions and asides are not the point. Clarity of mechanism is the point. A formal sentence that names the mechanism is more Feynman than a chatty one that does not.

**Over-shortening.** Not every sentence should be six words. The style needs long sentences to build, so the short one has something to land against.

**Losing the hedge that was real.** "May" and "could" are correct when the claim is genuinely uncertain. Cut hedging apparatus, not honest uncertainty.

**Rewriting the structure.** If asked to change the voice, change the voice. Section order, headings, and content coverage are a separate decision.

**Explaining what the reader already knows.** Feynman explained hard things simply; he did not explain easy things at length. Do not pad with tutorial material a referee does not need.

## Quick Self-Check

Read the draft aloud. Mark every place you would not say it that way to a colleague at a whiteboard. Those are the sentences to fix.

Then grep for: `It should be noted`, `It is important`, `In order to`, `the fact that`, `-tion of`, `has been shown to`, `serves to`, `plays a role in`, `is characterized by`, `merits further`.
