# Round 0009 — Named candidate selection and contact packet

## Final shape and current position

```text
RTS final planning target: 100%
RTS current planning estimate: 80%
Internal evidence-report hardening: 100%
Product-readiness score: 93/100

INTERNAL_NAMED_CANDIDATE_SELECTION_AND_CONTACT_PACKET_COMPLETE
HUMAN_ONE_TIME_OUTREACH_SEND_AUTHORIZATION_REQUIRED
```

This round converts the prior public recommendation into one named **contact candidate** and a reviewed one-time outreach packet. It does not turn the candidate into a pilot participant and does not send any message.

## Selected contact candidate

```text
GitHub login       jbexta
Public repository  jbexta/AgentPilot
Fixed commit       333eb6ce4f193852f4d9fe5412e8636929b6bb4e
Public score       86/100
Prior rank         1
```

The candidate is selected only for a later one-time contact authorization review. Repository authority, contact-account identity, route acceptability, voluntary consent, and availability remain human gates.

## Public contact-route evidence

The fixed public README exposes two project links:

1. X profile `AgentPilotAI`;
2. Discord project server identifier `1169291612816420896`.

The preferred route is an X direct message **only if** the account and DM route are human-verified. Discord is a fallback only if server rules expose an appropriate maintainer-contact path.

The following routes are prohibited:

- public GitHub issue without explicit invitation;
- GitHub pull request;
- unverified email;
- scraped private contact data;
- multi-channel blast.

No recipient account is populated.

## Personalized permission-first message

The English message asks only whether the maintainer is willing to receive a one-page scope. It discloses:

- one public repository and one fixed public commit;
- one free run;
- no private code, credentials, customer data, repository access, code changes, posting rights, payment, or commercial commitment;
- a reply is interest only and does not start analysis;
- separate written scope and consent are required;
- any draft remains private unless separately approved;
- decline or withdrawal is always allowed.

The message status is `NOT_SENT` and the send-event count is zero.

## Send boundary

All eighteen pre-send checks remain `PENDING`. Partial success is prohibited. This round authorizes zero outbound messages and zero follow-ups.

A later human send decision must verify the contact account, route rules, fixed repository and commit, exact message fingerprint, absence of attachments or tracking, and continued closure of intake, execution, pricing, contract, delivery, publication, and repository-write authority.

## Response handling

```text
Positive interest       Human review; may offer separate scope and consent
Negative or decline     Stop and close
Ambiguous               Do not intake or analyze; close
No response             Close after 14 days; no follow-up
Secret/private payload  Stop, exclude raw payload, escalate to human
```

No response class creates consent. Automatic intake and automatic pilot start remain false.

## Product-readiness decision

Product readiness remains 93/100 because no external-human usability, customer value, delivery acceptance, pricing, or commercial-effectiveness evidence was created.

RTS planning progress moves from 79% to 80% because the operating layer now contains a named contact-candidate selection, public-route review, personalized message, send preflight, response protocol, signed completion, and checkpoint.

## Authority boundary

```text
Named contact candidate selected internally  YES
Pilot participant selected                   NO
Recipient populated                          NO
Message sent                                 NO
Customer intake                              NO
Pilot execution                              NO
Pricing / contract / delivery                NO
Publication / external execution             NO
Source or target repository write            NO
```
