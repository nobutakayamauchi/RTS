# /goal Final Research Summary: Operator Load Timeline -> Operator-Machine Amplification

Status: `PROVISIONAL CONCLUSION REACHED`  
PR state: keep PR #315 Draft; no promotion and no merge authority.

## One-line conclusion

Human work did not simply shrink or disappear. The observable unit of human work moved upward from direct implementation into architecture, orchestration, and adversarial judgment, while each governed machine stage began carrying larger bundles of implementation and verification.

## Core formula

```text
Lambda_W = Y_W / J_W = (S_W / J_W) * (Y_W / S_W)
Lambda_W = Gamma_J * Gamma_M
```

Where:

- `J_W`: evidence-bound human decision load, in DLU.
- `S_W`: governed or strongly bound machine stages.
- `Y_W`: named machine-visible output proxy, such as commits.
- `Gamma_J = S/J`: machine stages activated per decision-load unit.
- `Gamma_M = Y/S`: output per machine stage.
- `Lambda = Y/J`: total visible-output amplification per decision-load unit.

Important denominator rule:

```text
if J_true >= J_lower:
  Gamma_J_true <= S / J_lower
  Lambda_true <= Y / J_lower
```

So July/August decision-normalized values are upper-bound proxies, not point estimates.

## Evidence anchors retained

From v0.5:

- exact HUMAN: 57
- exact Chat USER: 37
- observed activity: 225.9 min
- observed days: 26
- March `J >= 9`
- daily peak: 2026-07-27, `OLT >= 61.53`
- monthly mass: March 36.24 -> July 71.18 -> Aug 1-12 60.09

From v0.6 extension:

- exact HUMAN stream: 66
- exact Chat USER: 46
- exact Git HUMAN: 20
- global active minutes: 237.37
- observed project-switch lower bound: 0, meaning not recovered, not absent

## Strong micro-pilot

2026-03-03:

```text
2 decision hinges -> 4 STRONG-bound PR stages
Gamma_J = 2.0 stages/DLU
median first-stage latency = 48 seconds
```

Rejected evidence matters:

- PR #100 was temporally near but scope-expanded beyond the narrow decision.
- 3/6 semantically similar PR #90-#92 were rejected because they predated the decision.

Binding requires:

```text
future temporal order + semantic agreement + scope compatibility + content/patch support
```

## Cross-window comparison

| Window | Y | S | J | Gamma_J | Gamma_M | Lambda |
|---|---:|---:|---:|---:|---:|---:|
| 3/3 pilot | 4 | 4 | 2 | 2.0 | 1.0 | 2.0 |
| 7/27 RTS | 226 | 16 | >=10 | <=1.6 | 14.125 | <=22.6 |
| 8/11 WITNESS | 107 | 3 | >=4 | <=0.75 | 35.6667 | <=26.75 |

Robust observation:

```text
8/11 has substantially larger machine-visible output per governed stage than 7/27.
```

## Human role hypothesis

```text
Human role:
Implementation -> Architecture -> Orchestration -> Adversarial Judgment
```

```text
Machine role:
Implementation -> Expansion -> Repeated Execution -> Verification
```

## Final measurement object

```text
D_W = (L_W, Gamma_J_bounds, Gamma_M_proxy, Lambda_bounds, T_return, Q)
L_W = (E, J, O, R, X)
```

For Human Return ETA:

```text
T_return_hat = P80(T_required | task_class, L_launch, Gamma_J, Gamma_M, Q)
```

## Next phase

`THEORY FROZEN - CALIBRATION / FALSIFICATION PHASE`

Do not keep rewriting the theory unless STRONG evidence breaks it. Increase the sample size, bind hinges to stages, estimate intervals, and compare against simpler baselines.
