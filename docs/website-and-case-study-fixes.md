# Website & Case Study Fixes — Tracker für Eri & Bao

**Owner:** Eri (form), Bao (technische Umsetzung im CMS), Alex (content sign-off)
**Datum erstellt:** 2026-05-18
**Status:** Active
**Quelle:** Multi-Agent-Review (Compliance · Marketing Voice · CE/EE Boundary)

---

## Wichtige Vorabklärungen

1. **Volle Synthese ≠ Pseudonymisierung.** Wo eine Case Study ein vollsynthetisches Pipeline-Modell beschreibt (keine Quelldaten eingelesen), sind absolute Aussagen wie „0% PII", „no live data", „100% automated runs" **faktisch korrekt** und müssen NICHT entschärft werden. Zu unterscheiden:
   - **Daten-Eigenschaft** (synthetic ⇒ no PII) — Absolute okay
   - **Programm-Eigenschaft** (compliance = governance, training, procedures) — Absolute NICHT okay
   - **Engineering-Eigenschaft** (zero latency, no perf impact) — braucht Messwert

2. **CE bleibt low-profile auf der Website** (Owner-Präferenz). Keine CE-vs-EE-Vergleichstabellen auf marketing-relevanten Seiten. Diskreter GitHub-Link im Footer ist genug.

3. **Consulting-Positioning ist das eigentliche Differenzierungsmerkmal** — sollte über dem Fold sichtbar werden.

---

## Track A: Homepage (datamimic.io)

**Owner:** Eri (form), Bao (CMS), Alex (sign-off)

### A1 [P0] — Falsche Anonymisierungs-Begrifflichkeit

**Aktuell (Hero / FAQ-Antwort):**
> "Teams generate compliant data on demand — without production data ever leaving your environment."
> "...excels at generating fully anonymized synthetic data"

**Probleme:**
- „compliant data" — Compliance ist eine Programm-Eigenschaft (Governance, Procedures, Schulungen), keine Daten-Eigenschaft
- „fully anonymized" — Anonymisierung unter GDPR Recital 26 ist eine **Dataset-Level**-Bestimmung (singling-out, linkability, inference), nicht ein Output-Garantie
- Direkter Widerspruch zur README-Disclaimer (die ist sauber)

**Ersetzen mit:**
> "Teams generate synthetic test data on demand inside your own environment — no production data egress."
> "DATAMIMIC generates fully synthetic data and supports privacy-maximized pseudonymization; full GDPR anonymization status depends on a re-identification risk assessment across the complete dataset."

### A2 [P0] — Consulting-Positioning über dem Fold

**Aktuell:** Hero = pures Produkt-Framing („Test Data Platform For Regulated Enterprises"). Consulting-Differentiator erst weit unten in „Going Beyond for You!".

**Vorschlag — Sub-Headline unter Hero ergänzen:**
> "Software plus the team that built it — deployed across Oracle, MongoDB, and Kafka in EU tier-1 banking."

Einzeiler, kein CE-Branding, macht das eigentliche Differenzierungsmerkmal sichtbar.

### A3 [P1] — Compliance-Claims ohne Methodik

**Aktuell:**
> "satisfying DORA, GDPR, and BCBS 239 data lineage requirements"
> "directly aligned with the traceability, accuracy, and resilience testing requirements of DORA"

**Probleme:**
- „satisfying" / „directly aligned" sind bindende Compliance-Behauptungen. Ein Tool **produziert Evidenz**; es **erfüllt** keine regulatorischen Pflichten alleine.
- BCBS 239 gilt **nur** für G-SIBs/D-SIBs (global/domestic systemically important banks) — als generischer Constraint missverständlich.
- DORA-Pflichten liegen bei den **Financial Entities**, nicht beim Vendor (außer bei CTPP-Designation Art. 31).

**Ersetzen mit:**
> "Supporting evidence for DORA Art. 25 ICT-testing requirements, GDPR Art. 30 records, and — for in-scope banks — BCBS 239 lineage documentation."
> "Helps in-scope financial entities meet DORA Art. 25 ICT-testing requirements."

### A4 [P1] — GitHub-Link im Footer

**Aktuell:** Footer-Link zeigt auf `github.com/rapiddweller` (Organisation).

**Problem:** Org hat mehrere Repos — neugieriger Developer muss raten.

**Fix:** Link auf `https://github.com/rapiddweller/datamimic` umstellen. Eine-Zeichen-Änderung. Respektiert Positioning-Präferenz (immer noch Footer-only, immer noch diskret).

### Sign-off
- [ ] Eri: A1 Texte ersetzt, A2 Sub-Headline live, A4 Link korrigiert
- [ ] Alex: A3 Compliance-Texte review & sign-off

---

## Track B: Data Protection Software Page

**URL:** https://datamimic.io/data-protection-software/
**Owner:** Eri + Bao, Alex sign-off
**Hinweis:** Track C in Eris Blog-Tracker behandelt diese Seite separat als Landingpage-Umbau. Diese Punkte ergänzen den Umbau, ersetzen ihn nicht.

### B1 [P0] — SWIFT CSP Disclaimer ergänzen

**Aktuell:** SWIFT MT wird als unterstütztes Format gelistet, ohne CSP-Kontext.

**Ergänzen (an passender Stelle, z. B. als Disclaimer-Box oder Footnote):**
> SWIFT MT message generation is for test and training environments only. Generated messages do not satisfy SWIFT CSCF v2025 secure-zone controls (1.1 environment protection, 1.4 internet restriction) and must not be transmitted from a CSP-attested production zone.

### B2 [P1] — Compliance-Mapping-Tabelle ergänzen

**Status quo:** GDPR Art. 25/32, DORA, BCBS 239 werden in einem Binding-Constraints-Diagramm gezeigt, ohne explizite Erklärung welche Frameworks adressiert werden.

**Vorschlag — kompakter Mapping-Block:**

| Framework | Was DATAMIMIC beiträgt |
|---|---|
| GDPR Art. 4(5) / Art. 25 / Art. 32 | Seeded pseudonymization mit deterministischem Mapping; provenance-hashed Outputs als TOMs-Evidenz |
| DORA (Reg. 2022/2554) Art. 25 | Reproducible test datasets für ICT-Tools-Testing (nicht TLPT) |
| ISO/IEC 27701:2019 A.7.2.1 / 7.2.8 | Synthetic data statt PII in Non-Prod; dokumentierte Model-Definitionen als Privacy-by-Design-Evidenz |
| PCI DSS 4.0 Req. 6.5.5 | Synthetic PAN generation für Test/Dev (kein Live-PAN-Test) |
| HIPAA §164.312 *(US Covered Entities / Business Associates only)* | Synthetic Patient-Daten ohne ePHI-Exposition |
| BCBS 239 *(G-SIBs / D-SIBs only)* | Reproducible lineage documentation für Risk-Data-Aggregation |

**Footnote:** „BCBS 239 applies to globally and domestically systemically important banks."

### B3 [P1] — „Rust fastpath" als EE-Feature labeln

**Aktuell:** „Performance via Rust fastpath and Ray cluster distribution" steht ohne Edition-Kontext.

**Fix:** Sicherstellen dass im Kontext klar ist, dass das ein **EE-Core-Feature** ist (Rust fastpath, ML/auto-regressive engine, keyset/manifest building sind EE-only). Da die Seite primär die Enterprise Platform vermarktet ist das implizit — aber ein explizites „in the Enterprise Platform core" verhindert Missverständnisse.

### Sign-off
- [ ] Eri: B1 Disclaimer eingebaut, B3 Edition-Label gesetzt
- [ ] Alex: B2 Compliance-Mapping content review

---

## Track C: User Interface Page

**URL:** https://datamimic.io/user-interface/
**Owner:** Eri (form), Bao (CMS), Alex (sign-off)

### C1 [P0] — Buzzword-CTA ersetzen

**Aktuell:**
> "Embrace the power of DATAMIMIC UI today and begin transforming your test data generation processes immediately."

**Probleme:** „Embrace the power", „transforming", „immediately" — pure Infomercial-Sprache. Failt den bank-CTO-reshare test.

**Ersetzen mit:**
> "Try DATAMIMIC UI — open a scenario, edit the model, run it locally."

### C2 [P0] — „Monotonous dweller tasks" verständlich machen

**Aktuell:**
> "monotonous dweller tasks to leave meaningful work for humans"

**Problem:** „Dweller tasks" ist internes Brand-Sprech (rapiddweller), Leser parsen das nicht.

**Ersetzen mit:**
> "Automate repetitive test-data preparation so engineers can focus on test design."

### C3 [P1] — Hero und Grammatik

**Aktuell:**
> "Test Data made easy with DATAMIMIC UI's"

**Probleme:** „Made easy" ist Consumer-Software-Register; Stray Apostrophe-S.

**Ersetzen mit:**
> "Author, run, and schedule DATAMIMIC scenarios from the browser."

### C4 [P1] — Seite als EE-only labeln

**Aktuell:** Die UI-Seite beschreibt EE-only Features (DataWorkbench, visuelle Editoren, Auto-Model-Generation) ohne Edition-Marker. Reader vom GitHub-README (wo DataWorkbench explizit EE ist) wird verwirrt.

**Fix — eine Zeile in der Intro ergänzen:**
> "DATAMIMIC UI is part of the DATAMIMIC Enterprise Platform."

Kein Vergleich, keine CE-Erwähnung — nur ein klares Label.

### Sign-off
- [ ] Eri: C1/C2/C3 Texte ersetzt, C4 Label eingebaut
- [ ] Alex: review

---

## Track D: Case Studies

**Owner:** Eri (form), Alex (content sign-off + reference rights confirmation)

### D1 [P0] — School Case Study: Wortwahl

**URL:** https://datamimic.io/case-study/school-management-system-...

**Aktuell:** „Bulletproof Compliance & Risk Mitigation"

**Problem:** „Bulletproof" failt den bank-CTO-reshare test unabhängig von der Substanz. Die Substanz ist verteidigbar (vollsynthetisch ⇒ keine Live-Daten), nur die Wortwahl muss raus.

**Ersetzen mit:**
> "PII exposure eliminated in dev and test environments across 30 schemas."

**Behalten (Substanz korrekt bei vollsynthetischem Pipeline-Modell):**
- ✅ „0% PII exposure"
- ✅ „No live student data outside production"
- ✅ „100% automated reporting" (wenn jeder Run einen Report emittiert)

### D2 [P1] — School Case Study: „Zero compliance risk" nuancieren

**Aktuell:** „Zero compliance risk, full development velocity"

**Problem:** „Zero compliance risk" ist zu breit. Synthetic eliminiert die **PII-Leg** des Compliance-Risikos, nicht das gesamte Compliance-Risiko (AVV mit Hosting-Provider, GDPR Art. 8 child-consent processes, organisatorische Maßnahmen, RoPA-Pflege).

**Ersetzen mit:**
> "No production student data in non-production environments; no measured slowdown in feature delivery."

### D3 [P1] — School Case Study: Framework benennen

**Aktuell:** „child safety requirements" und „child protection laws" generisch erwähnt.

**Fix:** Jurisdiktion benennen, z. B.:
> "GDPR Art. 8 (children's consent under 16) and applicable national child-protection statutes."

### D4 [P0] — ACI Case Study: Begriffspräzision Anonymisierung

**URL:** https://datamimic.io/case-study/aci-worldwide-real-time-anonymisation-of-streaming-payment-data/

**Aktuell:** „Real-Time Anonymisation of Streaming Payment Data"

**Problem:** Inline-Anonymisierung pro Event ist unter GDPR Recital 26 fast immer **Pseudonymisierung**, nicht Anonymisierung — echte Anonymisierung verlangt Dataset-Level-Risk-Assessment, das pro-Event nicht durchführbar ist.

**Ersetzen mit:**
> "Real-Time Pseudonymisation of Streaming Payment Data"

Im Body durchgehend `anonymisation` → `pseudonymisation`.

### D5 [P0] — ACI Case Study: „Zero latency impact" mit Messwert

**Aktuell:** „Millions of payment records anonymised hourly with zero latency impact"

**Problem:** Engineering-Absolute. Kein reales Streaming-System hat literally zero added latency.

**Ersetzen mit:**
> "Added P99 latency of <X> ms across the Kafka topic under <M>-record/hour load."

**Aktion Alex:** Konkreten Latenz-Wert vom ACI-Engagement liefern (oder von Eri über Kunden-Kontakt einholen).

### D6 [P1] — ACI Case Study: PCI DSS Kontext ergänzen

**Aktuell:** Payment-Streaming-Case ohne PCI-DSS-Erwähnung.

**Ergänzen — „Regulatory context" Box:**
> "PAN handling aligned with PCI DSS 4.0 Req. 3.5 (PAN rendering unreadable) via deterministic tokenisation. Not a PCI-DSS-validated tokenisation solution; customer remains responsible for QSA assessment of the integrated environment."

### D7 [P2] — ACI Case Study: Wortwahl-Sweep

| Aktuell | Ersetzen |
|---|---|
| „bulletproof data protection at global scale" | „high-throughput protection for streaming payment data" |
| „existential threats to payment processors" | „regulatory fines and customer-trust loss" |
| „Full deterministic integrity across entities" | „Same input record produces identical pseudonymized output across consumer topics" |

### D8 [P1] — Tier-1 Bank Case Study: Anonyme Attribution

**URL:** https://datamimic.io/case-study/tier-1-european-bank-...

**Aktuell:** Gesamte Page basiert auf unverifizierbarer „Tier-1 European Bank"-Attribution mit Quote von unbenanntem Program Manager.

**Optionen — Alex muss entscheiden:**
1. **(A) Kunden namentlich machen** mit schriftlicher Reference-Permission. Massive Stärkung. Idealer Lead-Case.
2. **(B) Deskriptiv ohne Tier-Claim:** „A regulated EU retail banking engagement (customer name available under NDA)." Quote-Attribution: „Program Manager, EU retail banking engagement."
3. **(C) Case Study durch ACI als Lead ersetzen** — ACI ist namentlich und unter D4-D7 reparierbar.

**Empfehlung:** B oder C. A nur wenn realistisch erreichbar.

### D9 [P1] — Tier-1 Bank Case Study: Wortwahl + Units

**Wortwahl:**
| Aktuell | Ersetzen |
|---|---|
| „Bulletproof Compliance & Risk Mitigation" | „Reduced compliance and re-identification risk in non-production environments" |
| „dependency hell" | „cross-schema dependency conflicts" |

**Units im Results-Table:**
- „Parallel execution capability \| 0% \| 90%" → Nenner unklar. Konkret:
> "Share of refresh jobs runnable in parallel: 0 of 12 → 11 of 12"

### D10 [P1] — Tier-1 Bank Case Study: PII-Methodik

**Aktuell:** „Pre-production environments reduced live PII from ~100% to ≤5% residual, on track to zero"

**Probleme:**
- „On track to zero" ist forward-looking ohne Zeitrahmen.
- „5% residual live PII" in pre-prod ist eine notable Veröffentlichung — Regulator könnte nachfragen.

**Fix:** Methodik ergänzen oder weicher formulieren:
> "Residual live PII in pre-production reduced from ~100% to <5% (measured by the customer's PII scanner at confidence threshold X)."

Forward-looking-Phrase entweder entfernen oder mit Datum anchoren.

### D11 [P1] — Tier-1 Bank Case Study: DORA-Kontext

**Aktuell:** Bank-Context, kein DORA-Mention.

**Ergänzen — kurze „Regulatory context" Sektion:**
> "Engagement contributed reproducible test datasets to the customer's DORA Art. 25 (testing of ICT tools and systems) testing programme. DATAMIMIC outputs are not in SWIFT CSP scope."

### D12 [P2] — Alle Case Studies: Software/Consulting-Split

**Pattern:** Jede Case Study mischt Software-Capability und Consulting-Outcome. Buyer fragt zurecht: „Wenn ich nur Software kaufe, bekomme ich das?"

**Fix pro Case Study:** „How we delivered" Mini-Sektion mit zwei Bullets:
- **Software delivered:** <was das Produkt tat>
- **Consulting delivered:** <was das Team rapiddweller tat>

Verstärkt die Consulting-Led-Positionierung statt sie zu verstecken.

### Sign-off
- [ ] Alex: D8 entschieden (A / B / C)
- [ ] Alex: D5 Latenz-Wert geliefert oder „measured by customer"-Verweis bestätigt
- [ ] Alex: D10 PII-Methodik geliefert
- [ ] Eri: alle Wortwahl-Sweeps D1/D7/D9 angewendet
- [ ] Eri: D2/D3/D6/D11 Texte eingebaut
- [ ] Eri: D12 Software/Consulting-Split-Pattern auf alle drei Case Studies angewendet

---

## Track E: FAQ

**URL:** https://datamimic.io/faq/
**Owner:** Eri, Alex sign-off

### E1 [P1] — Anonymisierungs-Antwort mit README angleichen

**Aktuell:** FAQ behauptet „excels at generating fully anonymized synthetic data" — widerspricht direkt der vorsichtigen README-Disclaimer.

**Ersetzen mit:**
> "DATAMIMIC generates fully synthetic data and supports privacy-maximized pseudonymization. Full GDPR anonymization status (Recital 26) depends on a re-identification risk assessment across the complete dataset, which DATAMIMIC does not perform on the customer's behalf."

### E2 [P1] — Generic-Marketing-Phrasen ersetzen

| Aktuell | Ersetzen |
|---|---|
| „an advanced test data tool" | „a Python+Rust core with multi-process execution and a browser-based scenario editor" |
| „user-friendly UI" | „a browser-based editor for scenario authoring" |
| „generate and anonymize data more quickly and efficiently" | „Run N worker processes in parallel; observed Mx speedup vs single-process on the bundled benchmark" (Alex: konkrete Zahlen liefern) |

### E3 [P2] — „Ensure secure testing" entschärfen

**Aktuell:** „data obfuscation and anonymization features to ensure secure testing"

**Problem:** Vermischt Anonymisierung (Privacy) mit Security; „ensure" ist absolut.

**Ersetzen mit:**
> "data masking and pseudonymisation features that support secure non-production testing workflows"

### Sign-off
- [ ] Alex: E2 konkrete Benchmark-Zahlen geliefert
- [ ] Eri: E1/E2/E3 Texte ersetzt

---

## Universal Checks (für alle Track-A bis Track-E Änderungen)

### Forbidden Words — auf Sicht entfernen
unleash, revolutionary, AI-driven, AI-powered, AI-enhanced, AI-native, leverage, seamless(ly), empower, ecosystem, journey, comprehensive solution, cutting-edge, innovative, unparalleled, robust, state-of-the-art, next-generation, trusted solution, effortless(ly), bulletproof, world-class, best-in-class, embrace the power, made easy.

### Fünf Marketing-Tests vor Sign-off
1. **Specificity** — würde der Satz auch auf Mostly-AI / Gretel / Tonic passen? Wenn ja: umschreiben.
2. **Audience** — wer ist der Reader (architect / CISO / DPO / QA Lead)?
3. **Persona** — kannst du 1-3 namentliche Personas benennen?
4. **Promise** — jeder Claim beweisbar? Absolutwerte unter den richtigen Kategorien angewendet (siehe Vorabklärung 1)?
5. **Scope** — nur die vereinbarte Änderung, kein Layout-Drift.

### Bank-CTO-Reshare-Test
Würde ein Head of Engineering einer Tier-1-Bank das ohne Peinlichkeit weiterleiten?

---

## Prioritäts-Übersicht

| Prio | Track | Items |
|---|---|---|
| **P0** | A, B, C, D | A1, A2, B1, C1, C2, D1, D4, D5 |
| **P1** | A, B, C, D, E | A3, A4, B2, B3, C3, C4, D2, D3, D6, D8, D9, D10, D11, E1, E2 |
| **P2** | D, E | D7, D12, E3 |

---

## Empfohlene Sequenz

**Sprint 1 (diese Woche):**
- P0-Block durch Eri (A1, B1, C1, C2, D1, D4) — alles reine Text-Ersetzungen ohne Alex-Input
- A4 (GitHub-Link) durch Bao

**Sprint 2 (nach Alex-Input):**
- A3, B2, D5, D10, E2 — brauchen Content-Input/Bestätigung von Alex
- D8 (Tier-1 Entscheidung A/B/C) — Strategie-Call

**Sprint 3 (parallel):**
- A2 (Sub-Headline) — wenn Consulting-Positioning als richtige Richtung bestätigt
- C4, D11, B3 — Edition-Labels und Compliance-Kontext-Ergänzungen
- D12 — Software/Consulting-Split-Pattern auf alle Case Studies (etwas mehr Arbeit)

**Sprint 4:**
- D7, E3, alle P2-Polish
