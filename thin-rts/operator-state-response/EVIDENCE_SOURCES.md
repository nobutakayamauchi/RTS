# Evidence Sources — Operator State Response v0

This registry separates safety rules, operational-fatigue features, and evidence-bounded performance-effect profiles.

## Tier A — official safety / public-health guidance

1. Ministry of Health, Labour and Welfare (Japan), *健康づくりのための睡眠ガイド2023* (partially revised 2024-09-18).
   - Adult guidance uses 6 hours or more as a rough sleep-duration target while explicitly noting individual differences.
   - This is a public-health prior, not a clinical threshold and not a percent-performance conversion.
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
   - Smartphone typing metrics from a longitudinal physician cohort showed non-linear associations with time awake.
   - Treat as exploratory and do not assume transportability to this operator or Japanese IME behavior.

5. *Impact of one night of sleep restriction on sleepiness and cognitive function: A systematic review and meta-analysis.* 2024. PMID: 38759474.
   - Across 44 studies using 2-6 h one-night sleep restriction, sustained-attention reaction times and attentional lapses worsened with pooled SMDs around 0.51 and 0.49 respectively.
   - The review did not find a uniform significant pooled effect for choice reaction time, cognitive throughput, working memory, or inhibitory control.
   - Therefore a short-sleep profile may raise reaction/attention priors without pretending every judgment domain is equally impaired.

6. Belenky-style sleep dose-response evidence represented here by *Patterns of performance degradation and restoration during sleep restriction and subsequent recovery: a sleep dose-response study.* 2003. PMID: 12603781.
   - Repeated 5 h time-in-bed conditions showed reduced PVT speed and increased lapses.
   - This profile requires multiday history and must not be inferred from one 5 h night alone.

7. Williamson AM, Feyer AM. *Moderate sleep deprivation produces impairments in cognitive and motor performance equivalent to legally prescribed levels of alcohol intoxication.* Occup Environ Med. 2000. PMID: 10984335.
   - After 17-19 h continuous wakefulness, performance on some tests was equivalent or worse than BAC 0.05%; some response-speed measures were up to 50% slower and accuracy measures were poorer.
   - This is a task- and protocol-bounded comparator, NOT a universal conversion and NOT a "hangover equivalence".
   - The comparator may be matched only when continuous-awake duration is actually known; 5 h sleep alone does not authorize it.

Tier B sources justify testing behavioral/performance features. They do not justify diagnosis or fixed universal personal thresholds.

## Effect Catalog rule

The runtime catalog preserves four separate operational domains:

`J = judgment / R = reaction / A = accuracy / O = operation`

A population study stores its original endpoint/effect metric where possible. The runtime may assign an ordinal evidence prior (`UNKNOWN`, `CAUTION`, `MODERATE`, `HIGH`) but must not reinterpret an SMD, BAC comparison, or reaction-time change as "X% of this person's ability lost".

Comparators such as alcohol are explanatory calibration anchors only. They require their own exposure trigger and may not be inferred from a neighboring condition.

## Evidence rule

`official safety guidance > strong personal longitudinal evidence > peer-reviewed population evidence > heuristic prior`.

A feature that has not improved held-out prediction for this operator must lose weight or be removed even if the population literature is positive.
