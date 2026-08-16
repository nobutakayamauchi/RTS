# v0.9 Knowledge Intake — Original Beginner Guide Archetype

## Source boundary

This analysis is extracted from a user-supplied public X article that appears to be an early/original form of the author's "小学生でもわかる" beginner-guide style.

We are learning **article-writing doctrine and onboarding mechanics**, not importing the article's product facts, prices, time estimates, installation commands, platform availability, feature limits, guarantees, or support promises as engine truth.

Any claim about Claude/Claude Code, subscription requirements, pricing, browser/terminal capabilities, installation methods, operating-system requirements, completion time, or success rate must separately pass the normal evidence boundary before use in a generated article.

## Why this source matters

Later reference articles show polished versions of several doctrines already present here in raw form:

- define unfamiliar terms immediately;
- remove unnecessary choice for a true beginner;
- give exact actions instead of abstract encouragement;
- explain why each important action is necessary;
- state scope limits early;
- provide recovery paths at likely failure points;
- move from fear -> first success -> practical next step;
- make the CTA/resource appear at the moment the reader has the next predictable need.

This makes the article useful as an **archetype source** rather than merely another example.

## 1. Beginner friction should be named before instruction

The opening does not start with product capabilities. It starts with the reader's likely failure state:

- terminology overload;
- too many alternative methods;
- not knowing the first action.

Useful doctrine:

```text
recognizable friction
-> writer's attested same-state experience when available
-> explicit promise of what this guide removes
-> only then begin instruction
```

Do not invent "I was exactly the same" unless it is human-attested.

## 2. A beginner guide may deliberately reduce choice

For a true zero-to-first-success guide, multiple valid paths can increase cognitive load.

Useful doctrine:

```text
if several approaches exist
-> choose one safe, evidence-supported default for the stated scope
-> explain why this guide chooses it
-> keep alternatives out of the main path unless they are necessary
```

This is not a universal "never show options" rule.

Use one-path guidance only when:

- the guide's purpose is first completion rather than exhaustive comparison;
- one default is reasonably safe for the configured reader and scope;
- omitting alternatives will not hide a material trade-off or risk.

## 3. Scope limits belong before the steps they invalidate

The article places the Mac-only boundary before detailed instructions.

Useful doctrine:

```text
important scope boundary
-> state it before the reader invests effort
-> say who the guide is for
-> say who should use a different path
```

Do not let a reader complete half a guide before discovering that their environment is unsupported.

## 4. Explain the chosen path with consequences, not labels

Instead of merely saying "use terminal version," the article tries to explain why through concrete tasks.

Generalizable pattern:

```text
option A / option B
-> what each can or cannot do for this reader's intended task
-> choose the path based on consequence
```

The specific technical claims in the source are not imported as truth.

## 5. Explain jargon at the exact point of use

Examples in the source include defining ターミナル and データベース in ordinary language.

Doctrine:

```text
unfamiliar term
-> immediate plain-language definition
-> familiar analogy/example if needed
-> continue using the shorter term
```

This reinforces v0.4/v0.5 terminology rules.

## 6. Convert instructions into observable actions

A strong beginner step tells the reader:

- where to look;
- what to click/type/copy;
- what success looks like;
- what to do if that success signal does not appear.

Useful step schema:

```text
GOAL
ACTION
EXPECTED SIGNAL
IF NOT -> RECOVERY
WHY (when important)
```

This is stronger than prose such as "install the tool and configure it properly."

## 7. Give a success signal after important steps

The source repeatedly provides visible confirmation such as a version string or a visible plan label.

Generalizable doctrine:

```text
do action
-> inspect an observable result
-> only then proceed
```

This reduces uncertainty and makes a long guide self-correcting.

The exact success indicators must be evidence-bound for the actual product/workflow.

## 8. Recovery belongs next to the likely failure

The source places troubleshooting directly after installation and again in a dedicated recovery section.

Prefer:

```text
risky step
-> expected outcome
-> common failure symptom
-> bounded recovery
```

rather than saving every error case for an appendix the reader may never reach.

Do not invent common failures. A failure mode should be sourced, observed, documented, or clearly framed as a conditional possibility.

## 9. Copy/paste ergonomics are part of comprehension

For operational tutorials, presentation is part of the instruction.

Useful doctrine:

- visually distinguish literal input from explanatory prose;
- warn when exact copying matters;
- do not force the reader to infer which characters belong in the command/input;
- keep command/example and explanation adjacent.

This should generalize beyond programming to forms, templates, emails, spreadsheet formulas, configuration values, etc.

## 10. "Why" turns imitation into transferable understanding

The guide explicitly promises to explain why an action is needed.

A beginner may be able to copy steps without understanding them, but a useful article should add enough rationale that the reader can recover when the environment changes.

Doctrine:

```text
WHAT TO DO
+
WHY THIS STEP EXISTS
+
WHAT SUCCESS MEANS
```

Not every trivial click requires a paragraph of explanation. Add WHY where it helps judgment, recovery, safety, or transfer.

## 11. Move from installation to a first real win quickly

The guide does not stop at "installed successfully." It gives small example projects immediately after setup.

Generalizable progression:

```text
setup complete
-> tiny meaningful use
-> modification / second instruction
-> reader sees the tool as usable rather than merely installed
```

For non-technical articles, the equivalent is:

```text
understand method
-> perform one small real action
-> see a concrete result
```

## 12. Predict the next wall

The source anticipates:

> インストールできた。で、何作ればいいの？

and places a resource there.

Generalizable doctrine:

```text
reader completes current milestone
-> identify the next predictable friction
-> provide the next resource only there
```

This complements v0.8's utility-timing rule.

## 13. Guide architecture can be a confidence ladder

The article gradually changes the reader state:

```text
"難しそう"
-> "何をすればいいか分かった"
-> "今の画面は正常だ"
-> "インストールできた"
-> "起動できた"
-> "日本語で動かせた"
-> "次も試せそう"
```

For Article Engine, this suggests tracking **reader state transitions**, not only headings/content coverage.

A practical/how-to article should know what confidence/state each section is supposed to create.

## 14. Safety warnings should be proportional and timely

The article later references a higher-risk tool and warns that setup mistakes can be dangerous.

General doctrine:

- place material risks before the risky action;
- explain what makes the action risky in plain language;
- do not use exaggerated danger language only for attention;
- give a safer prerequisite/path where appropriate.

## 15. What must NOT be imported as doctrine

The source contains several patterns that should become METEOR attack targets rather than rules:

### Absolute completion promises

Examples in the source include forms equivalent to:

- "100%できます"
- "絶対に完了できる"
- "保証します"
- fixed completion-time promises

These conflict with evidence/safety doctrine.

Engine rule candidate:

> Never convert beginner friendliness into a universal success guarantee.

### Overconfident product/technical claims

Claims such as:

- one version "can do anything";
- another version cannot perform broad categories of work;
- one plan is "enough" for everyone;
- a specific installation method is universally current;
- a named older method "no longer works";

are time-sensitive factual claims, not writing doctrine.

### False simplicity through hidden trade-offs

"選択肢を提示しません" is useful only when the chosen default is safe and material alternatives are not being concealed.

METEOR should attack cases where one-path guidance hides:

- platform/OS differences;
- cost differences;
- security implications;
- irreversible actions;
- prerequisites;
- meaningful capability trade-offs.

### Redundant summary / boilerplate ending

The source includes a conventional "まとめ" plus motivational close and multiple follow-on links.

This is useful historical evidence, but v0.6/v0.7 should challenge whether each closing section still adds value.

### Multiple CTA drift

The article contains resource acquisition, reply support, follow, quote/repost requests, and multiple next-article links.

This is a strong METEOR tension against the current single-CTA doctrine.

Question for later battle:

> Can a long tutorial safely contain navigation/follow-on resources without becoming a multi-CTA commercial mess?

Potential distinction:

```text
PRIMARY COMMERCIAL CTA = one
UTILITY/NAVIGATION LINKS = allowed only when they directly support task completion and do not compete with the primary next action
```

This should be tested rather than assumed.

## 16. Candidate v0.9 additions

Do not promote yet. Candidates for final integration after all knowledge is ingested:

1. `BEGINNER_SINGLE_PATH_POLICY`
   - choose one safe default path for first completion;
   - explain why;
   - preserve material exceptions/trade-offs.

2. `STEP_OBSERVABILITY_SCHEMA`
   - GOAL / ACTION / EXPECTED SIGNAL / RECOVERY / WHY.

3. `EARLY_SCOPE_GATE`
   - environment/audience prerequisites before costly reader effort.

4. `RECOVERY_PROXIMITY_RULE`
   - likely recovery next to likely failure.

5. `FIRST_WIN_POLICY`
   - do not stop at setup; lead to one meaningful use/result.

6. `READER_STATE_LADDER`
   - each major section should deliberately move the intended reader's state/confidence.

7. `NEXT_WALL_TIMING`
   - resource/asset appears when the next predictable friction emerges.

8. `UTILITY_LINK_VS_CTA_DISTINCTION`
   - possible distinction between one commercial CTA and task-completion navigation; requires METEOR.

## 17. METEOR attack list created by this source

When the knowledge batch is complete, attack at least these contradictions:

- one-path simplicity vs honest alternatives;
- beginner confidence vs false guarantees;
- exact instructions vs time-sensitive product facts;
- immediate recovery vs article bloat;
- explain-everything vs cognitive overload;
- one commercial CTA vs legitimate tutorial utility links;
- short mobile lines vs excessively fragmented prose;
- progress reassurance vs repetitive padding;
- safe defaults vs unsupported "recommended" claims;
- motivational close vs redundant generic ending.

## BridgePatch implication

The strongest transferable pattern for BridgePatch is not the software tutorial itself.

It is the **guided-completion architecture**:

```text
reader pain
-> tell them exactly what this article will remove
-> narrow scope
-> explain unfamiliar terms immediately
-> choose one simple path
-> show the expected result at each meaningful stage
-> place recovery near failure
-> explain why important boundaries exist
-> reach one small real win
-> offer the next step when the next wall becomes visible
```

For BridgePatch, that can become:

```text
"この手作業、どこからAIに渡せばいいか分からない"
-> one process only
-> input / action / output in plain Japanese
-> what stays human
-> what failure looks like
-> where work returns to a human
-> one concrete sample decomposition
-> free fit check as the next wall/next step
```

This source should remain in the v0.9 intake branch until all remaining knowledge has been collected and METEOR has resolved the conflicts.