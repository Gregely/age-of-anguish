# Research brief (shared by every research agent)

## The question
Why are so many people in modern, wealthy societies depressed, anxious, numb and quietly miserable, and why does it feel like no one can explain it? The obvious answers (loss of community, social media, economic precarity) seem true but insufficient. We want the subtler layers: what each discipline says, where they agree, where they contradict, and what remains unexplained.

**This project lays out material. It does NOT argue a thesis.** Do not write a unified theory or a conclusion. End your file with open questions, not answers.

## Non-negotiable rules
1. **No invented citations, statistics, or quotes.** If you cannot find or confirm a source, do not cite it. If you're relying on memory for a claim and cannot confirm it online, mark it `UNVERIFIED` or leave it out.
2. **Primary sources first.** Prefer the paper, the book, the official dataset, the thinker's own words. Use reputable summaries (SEP, IEP, review articles, publisher pages, major newspapers' reviews) only to confirm or when the primary text is unavailable, and say so.
3. **Quotes are short.** At most ~25 words each, with location (page, chapter, section, or URL anchor). Paraphrase by default. No long block quotes.
4. **Steelman rivals.** In every area, give the strongest version of the opposing or deflationary view, including views that deny the premise (e.g., "it isn't actually rising") or favour purely biomedical / individual explanations.
5. **Label evidence strength** for every claim/theory entry with exactly one of:
   - `WELL-SUPPORTED`: empirically well-supported. Replicated across designs/datasets or backed by meta-analyses; robust direction of effect.
   - `CONTESTED`: supported but contested. Real evidence exists but is mixed, small-effect, confounded, or credibly disputed.
   - `THEORETICAL`: theoretical / interpretive. A coherent framework judged on explanatory power; not tested or not straightforwardly testable.
   - `SPECULATIVE`: plausible but with thin or no evidence.
   - `CONTRADICTED`: contradicted by evidence. The best evidence points against it (e.g., the simple "low serotonin causes depression" story).
   Give a **one-line justification** for the label.
6. **Be honest about effect sizes.** Report the number, the sample, the design, and the population (country, age) when you cite empirical findings. Distinguish correlation from causal evidence.
7. Write in clear, plain English. UK or US spelling is fine; be consistent.

## Output file
Write a single markdown file at the path you were given. Aim for roughly 6,000–12,000 words and 25–60 sources. Depth over breadth, but cover every named item in your area.

## Required structure

```
# NN · Area name

## Overview
3–6 paragraphs: what this area contributes to the question, the main camps, the main fault lines.

## Entries
### <Entry name>
- **id:** short-kebab-slug (unique, descriptive, e.g. `capitalist-realism`, `haidt-great-rewiring`)
- **type:** theory | concept | empirical-finding | debate | intervention
- **disciplines:** e.g. critical theory; sociology
- **themes:** pick from the theme list below (1–4)
- **layer:** pick ONE from the layer list below
- **proponents:** names
- **core claim:** 2–5 sentences, paraphrased
- **evidence / arguments for:** bullet points with inline source keys like [S3]
- **evidence / arguments against, and critics:** bullet points, named critics, source keys
- **strength:** LABEL — one-line justification
- **related:** other entry ids (yours or plausible ones from other areas; use descriptive slugs)
- **quote (optional):** "≤25 words" — Author, Work, location [Sx]

(repeat for 8–20 entries)

## Steelman of the rival / deflationary view(s)
The strongest case against the main explanations in this area.

## Internal tensions
Where thinkers within this area contradict each other.

## Cross-area tensions
Where this area's claims conflict with likely claims from other areas (biomedical vs social, etc.).

## Open questions / what this area cannot explain

## Thinkers (for the who's who)
For each: **Name (dates)**, discipline, 1–3 key works, key ideas (2–3 lines), key critics (named, with the gist of the critique).

## Glossary
Term: 1–2 line definition (as used in this literature).

## Reading list
For each: Author, *Title* (year). Difficulty: intro | intermediate | advanced. Argues: one line. Best for: one line.

## Sources
[S1] Full citation (authors, year, title, journal/publisher, volume/pages). URL or DOI.
     Status: FETCHED-CONFIRMED (you read the primary text or its abstract/official page and it says what you claim) | SECONDARY (confirmed only via a reliable secondary source; name it) | UNVERIFIED (could not confirm; explain)
     Supports: which claim(s) this source is used for.
```

## Theme list (use these tags)
`community-belonging`, `work-economy`, `meaning-purpose`, `self-identity`, `status-comparison`, `time-acceleration`, `technology-attention`, `body-biology`, `measurement-diagnosis`, `stigma-silence`, `future-ecology`, `institutions-power`, `ritual-religion`, `treatment-help`

## Layer list (for the map diagram)
- `premise`: is it really rising? (measurement, diagnosis)
- `body`: body & brain (genes, inflammation, sleep, neurotransmitters, physical environment)
- `mind`: individual mind (cognition, rumination, attention to self, learned patterns)
- `relationships`: relationships & community (loneliness, belonging, family, social capital)
- `institutions`: institutions & economy (work, housing, debt, inequality, meritocracy, welfare)
- `technology`: technology & attention
- `culture`: culture & meaning (values, religion, authenticity, therapeutic culture, ideology)
- `time`: time, future & ecology (acceleration, lost futures, climate)

## Boundaries (who covers what, so we don't duplicate)
- **01 Critical & cultural theory:** Fisher, Rosa, Han, Fromm, Debord, Bauman, Lasch (narcissism as cultural critique), Durkheim's *theory* of anomie, Marx on alienation, Weber on disenchantment, Gramsci, Adorno/Horkheimer/Marcuse, Illich, Polanyi, Ehrenberg, Berardi, Honneth, Sennett, Baudrillard.
- **02 Sociology & political economy:** Putnam, Klinenberg, social capital data, decline of institutions (religion, unions, clubs, marriage), work & precarity (Standing, Graeber's *Bullshit Jobs*), housing, debt, atomisation, meritocracy (Sandel, Markovits, Michael Young), inequality & status anxiety (Wilkinson & Pickett), deaths of despair (Case & Deaton), suicide data by group, Easterlin paradox, happiness economics.
- **03 Psychology & psychiatry:** causal models (biomedical, monoamine, genetic, cognitive, stress-diathesis, inflammatory, evolutionary-psychiatric e.g. Nesse), anhedonia & reward circuits, chemical-imbalance critique (Moncrieff et al. 2022 and responses), critique of the social-causes story, WEIRD and cross-cultural psychiatry (Kleinman, Kirmayer, Henrich, Watters), evidence on what helps (drugs, therapies, exercise, social prescribing, behavioural activation).
- **04 Epidemiology & measurement:** is it actually rising? GBD, NSDUH, YRBS, APMS, OECD/WHO, Monitoring the Future, cohort vs period effects, diagnostic expansion (DSM history, Horwitz & Wakefield), help-seeking/screening artefacts, prevalence inflation (Foulkes & Andrews), suicide & self-harm as harder outcomes, the "happiness"/life satisfaction data, gender and age patterns.
- **05 Anthropology & evolutionary mismatch:** small-scale societies, being needed, ritual, belonging, status; Junger, Hari (as popularisers; check claims), evolutionary mismatch literature, hunter-gatherer data, collective effervescence (as observed), Kleinman's local worlds; critique of romanticisation.
- **06 Technology & attention:** attention economy (Wu, Williams, Zuboff, Crawford), Haidt/Twenge and their critics (Odgers, Orben & Przybylski, Ferguson, Candice Odgers), specification curves, deactivation experiments (Allcott et al., Hunt et al.), parasocial relationships, social comparison, self-curation, algorithmic feeds, smartphones & sleep, policy responses.
- **07 Philosophy:** meaning, absurdity (Camus), nihilism (Nietzsche), authenticity (Heidegger, Sartre, Kierkegaard, Taylor's *Ethics of Authenticity*), Taylor's *A Secular Age*, the self as project, phenomenology of depression (Ratcliffe, Fuchs, Svenaeus), first-person accounts (Solomon, Styron), Kierkegaard on despair, philosophical pessimism (Schopenhauer, Benatar briefly), Susan Wolf on meaning.
- **08 Self-presentation & identity:** identity as brand, self-surveillance and the quantified self, therapeutic culture and critics (Rieff, Illouz, Furedi, Lasch on therapeutic sensibility, Haslam's concept creep), rumination/self-focus (Nolen-Hoeksema, Ingram), the paradox of pursuing happiness (Mauss et al.), Goffman, Riesman's other-directed self, perfectionism trends (Curran & Hill).
- **09 Ecological & temporal anxiety:** climate anxiety (Hickman et al. 2021, Clayton scale, critiques), solastalgia (Albrecht), slow cancellation of the future (Fisher, Berardi), stagnation (Graeber's "flying cars", Gordon, Cowen, Thiel), "no future" youth sentiment surveys, pessimism about children's prospects.
- **10 Historical comparison:** acedia (Evagrius, Cassian), melancholy (Burton), the "English malady" (Cheyne), neurasthenia (Beard), "nerves", Auden's *Age of Anxiety*, May's *The Meaning of Anxiety*, mid-century tranquilliser era (Miltown/Valium), the rise of "depression" as a category, what's new vs recurring.
- **11 The silence itself:** stigma (Goffman, Link & Phelan), self-stigma, individualised framing (Fisher's privatisation of stress), hermeneutical injustice (Fricker), alexithymia, the mental-health awareness paradox, masculinity norms and non-disclosure, loneliness disclosure, why collective naming fails, "quiet quitting"/"languishing" (Keyes; Adam Grant's popularisation) as attempts at naming.
- **12 Body, environment & lifestyle:** sleep, physical activity, sedentary/indoor life, light & circadian disruption, nature exposure, urbanicity, diet & ultra-processed food, alcohol and cannabis trends, loneliness physiology (Cacioppo), obesity–depression links, microbiome (cautiously), inflammation as mechanism (cross-link to 03).

If something important falls in your area but isn't listed, include it. If you stumble on something in another agent's area, mention it briefly in Cross-area tensions with a pointer rather than covering it fully.
