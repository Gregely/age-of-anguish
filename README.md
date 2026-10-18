# Age of Anguish

A research atlas on one question: **why are so many people in modern, wealthy societies depressed, anxious, numb and quietly miserable, and why does it feel like no one can explain it?**

The project lays out what different disciplines say, how strong the evidence for each claim is, where the frameworks agree and contradict each other, and what remains unexplained. It deliberately offers no unified thesis.

## Layout

- `research/`: research notes, one markdown file per area, with sources (`_BRIEF.md` is the shared brief)
- `research/verification/`: independent verification reports for each research file
- `content/`: structured JSON consolidated from the verified research
- `build/build.py`: builds the site (Python 3 standard library only)
- `index.html`: the built site. A single self-contained file that works offline.

## Build

```sh
python3 build/build.py
```

Open `index.html` in any browser. It needs no server and no network.
