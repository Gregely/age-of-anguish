# Verification brief

You are an independent verifier. You did NOT write the research file you are checking. Your job is to make it trustworthy, not to make it longer.

## What to check, for every source in the file's Sources list
1. **Existence:** the work exists with the stated authors, year, title, venue (and DOI/URL resolves to it).
2. **Claim match:** the source actually says what the file uses it for (statistic, finding, argument, direction of effect).
3. **Numbers and quotes:** statistics match the source; quotes are verbatim, ≤ ~25 words, and correctly located.
4. **Characterisation:** the evidence-strength label for each entry is defensible under the rubric in `research/_BRIEF.md`.

Prioritise: (a) every direct quote, (b) every specific number, (c) every source marked UNVERIFIED or SECONDARY, (d) claims that seem surprising or too neat, (e) remaining sources.

## How to check (WebSearch budget is nearly exhausted; prefer these)
- Crossref API for existence/metadata: `https://api.crossref.org/works/<DOI>` or `https://api.crossref.org/works?query.bibliographic=<title+author>&rows=3`
- Europe PMC for biomedical abstracts: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<terms>&format=json&resultType=core`
- OpenAlex: `https://api.openalex.org/works?search=<title>` (abstracts as inverted index)
- DOI resolver `https://doi.org/<DOI>`, PubMed pages, publisher pages, SEP/IEP, marxists.org, Project Gutenberg, archive.org, official statistics sites.
- Use WebSearch only if the above fail; it may be unavailable.
Use WebFetch (load via ToolSearch "select:WebFetch,WebSearch").

## What to do with what you find
Edit the research file **in place**:
- **Fix** errors you can correct (wrong year, wrong number, misattributed quote, wrong journal). Fix the source line too.
- **Update status** lines: `FETCHED-CONFIRMED` only if you or the author confirmed against primary text/abstract/official page; `SECONDARY`; or `UNVERIFIED`.
- **Flag** claims you cannot confirm but which are plausible and important by prefixing the bullet with `⚠ UNVERIFIED:`.
- **Remove** anything that is contradicted by the source, or a quote you cannot find, or a citation that does not appear to exist. Never leave an invented or non-existent citation. Paraphrase instead of a quote you cannot confirm.
- **Relabel** strength where the evidence clearly warrants a different label, and say why.
- Do not add new entries or new research. You may add a correcting source if needed to fix a claim.

## Report
Write `research/verification/NN-<area>-check.md` with:
1. Summary: counts of sources checked / confirmed / corrected / flagged / removed; quotes checked; strength labels changed.
2. A table: `| Src | What was checked | Result | Action |`
3. A list of every removal and every correction with the before/after.
4. Remaining caveats a reader should know.

Do NOT git commit. When done, reply with a 5-line summary.
