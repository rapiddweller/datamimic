# Semantische Prüfung vor der Architekturfreigabe

Status dieser historischen Prüfung: **vor der Freigabe erhoben**.
Alex hat anschließend die endgültigen Entscheidungen an Astra und die Umsetzung
an das Implementierungs-/QA-Team delegiert; siehe
[Amendment 20](../../refactoring-study/experiment-2/amendment-20.md).
Die eingefrorenen Prüfdateien werden nicht nachträglich zur neuen Baseline.

Der frühere Vollständigkeitsnachweis prüfte Dateimengen und Navigation, nicht
die fachliche Eignung jeder Zuordnung. `GeneratorTask` unter `values/scalar`
ist ein konkreter Gegenbeleg. Ordnernamen und grüne Strukturprüfungen reichen
nicht als Begründung einer Architekturentscheidung.

## Prüfauftrag

Jeder Eintrag erhält einen kurzen Verantwortungssatz, ein Urteil und Codebelege.
Bewertet werden alle 488 vorhandenen Python-Dateien, 159 vorgeschlagenen
Paketknoten und 126 Vertragskomponenten. Diese 773 Prüfeinträge sind verschiedene
Sichten auf denselben Code, nicht 773 unabhängige fachliche Komponenten.
Nicht-Python-Ressourcen und vollständige EE-Laufzeitkompatibilität sind damit
nicht geprüft. Reine Initializer bleiben sichtbar, zählen aber nicht als
eigene fachliche Verantwortung.

Grundlage: Implementierung → Aufrufer → Zustand/IO → sichtbares Ergebnis.
Vorhandene Beschreibungen im Zielentwurf sind Hypothesen, keine Belege.
Sieben Kinder ist ein Review-Anlass, kein Grund für künstliche Zwischenpakete.

- `keep`: Vorgeschlagene Zuordnung passt zur untersuchten Verantwortung.
- `change`: Verantwortung passt nicht zum vorgeschlagenen Ort.
- `split`: Der aktuelle Knoten mischt trennbare Verantwortungen.
- `unclear`: Keine belastbare Zuordnung; Entscheidung bleibt offen.
- `scaffold`: Paket-/Exportmechanik, keine zusätzliche fachliche Komponente.

## Unabhängige Arbeitspakete

Luna prüft DSL, Runtime/IO und Domains parallel mit getrennten Ergebnissen.
Einstiegspunkte, Authoring und Querschnitt werden separat geprüft. Der
Koordinator gleicht anschließend die Übergänge und widersprüchliche Vorschläge
ab. Astra hinterfragt ausgewählte Schlussfolgerungen zusätzlich unabhängig.
Korrigierte Einzelbewertungen bleiben von der abschließenden Empfehlung
unterscheidbar; sie sind keine unveränderten Erstentwürfe der Agenten.

`manifest.json` friert Revision, Prüfknoten und Dateihashes ein. Die Prüfung
darf keine vorhandenen Quelltexte, DSL-Deskriptoren, Baselines, Architekturverträge
oder die Umzugsplanung verändern. Abdeckung und unveränderte Eingaben werden
separat geprüft; korrekte Dateizählung beweist keine korrekte Semantik.

## Zusätzlich: Navigation

Im alten Prototyp schaltet `openCard` beim Fehlen eines Untervertrags über
`openMember` automatisch von Komponenten auf Ordner um. Zurück folgt dann
Ordnerpfaden statt dem Besuchsverlauf. Das ist eine Darstellungsentscheidung,
kein Beleg für fehlende Komponenten.

Empfehlung zur Freigabe: Perspektive beim Vertiefen erhalten, Ansichtswechsel
explizit machen und „Zurück“ vom Aufstieg zum Elternknoten unterscheiden.
Enthaltene Module auch ohne eigenen Untervertrag zeigen, aber nicht als
zusätzliche Vertragsgrenzen ausgeben. Diese Navigation wird hier nicht umgebaut.
