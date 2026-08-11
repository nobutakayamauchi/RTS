# Evidence Sources — Operator State Response v0

This registry separates safety rules from exploratory fatigue features.

## Tier A — official safety / public-health guidance

1. Ministry of Health, Labour and Welfare (Japan), *健康づくりのための睡眠ガイド2023* (partially revised 2024-09-18).
   - Sleep insufficiency is associated with daytime sleepiness/fatigue, complaints such as headache, reduced attention/judgment and lower work efficiency.
   - Adult guidance includes securing necessary sleep with 6 hours or more as a rough target, while explicitly noting individual differences.
   - https://www.mhlw.go.jp/content/001305530.pdf

2. Ministry of Health, Labour and Welfare (Japan), *熱中症が疑われる人を見かけたら*.
   - Heat illness symptom examples and emergency response; inability to drink or loss of consciousness requires emergency response.
   - https://www.mhlw.go.jp/seisakunitsuite/bunya/kenkou_iryou/kenkou/nettyuu/nettyuu_taisaku/happen.html

3. Ministry of Health, Labour and Welfare / Fire and Disaster Management Agency (Japan), *こんな時は迷わず119へ* and *Q助*.
   - Public emergency triage examples including sudden severe headache, acute breathing difficulty, neurological deficits, altered consciousness and seizures.
   - https://kakarikata.mhlw.go.jp/kakaritsuke/urgency.html
   - https://www.fdma.go.jp/mission/enrichment/appropriate/appropriate003.html

Tier A sources may drive medical safety messages. They do NOT define the operational fatigue score.

## Tier B — peer-reviewed fatigue / performance evidence

1. de Jong M, Bonvanie AM, Jolij J, Lorist MM. *Dynamics in typewriting performance reflect mental fatigue during real-life office work.* PLoS One. 2020;15(10):e0239984. DOI: 10.1371/journal.pone.0239984.
   - Six-week real-world office study; typing speed/accuracy/error correction changed with time-on-task and time-of-day.
   - Interpretation is population-level and context-dependent; not a personal diagnostic rule.

2. Lowe CJ, Safati A, Hall PA. *The neurocognitive consequences of sleep restriction: A meta-analytic review.* Neurosci Biobehav Rev. 2017;80:586-604. DOI: 10.1016/j.neubiorev.2017.07.010.
   - Experimental sleep restriction affects neurocognitive performance across domains.

3. Hsieh S et al. *Impairment of error monitoring following sleep deprivation.* Sleep. 2005;28(6):707-713. PMID: 16477957.
   - One night of sleep deprivation increased response errors/omissions and impaired post-error adjustments in a small laboratory study.

4. Fang Y et al. *Patterns of smartphone typing performance by time awake: implications for unobtrusive ambulatory mental fatigue assessment.* PLOS Digital Health. 2026;5(3):e0001281. DOI: 10.1371/journal.pdig.0001281.
   - Smartphone typing metrics from a large longitudinal physician cohort showed non-linear associations with time awake.
   - New evidence; treat as exploratory and do not assume transportability to this operator or Japanese IME behavior.

Tier B sources justify testing behavioral features. They do not justify diagnosis or fixed universal thresholds.

## Evidence rule

`official safety guidance > strong personal longitudinal evidence > peer-reviewed population evidence > heuristic prior`.

A feature that has not improved held-out prediction for this operator must lose weight or be removed even if the population literature is positive.
