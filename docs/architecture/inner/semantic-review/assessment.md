# Architekturprüfung vor Freigabe

Historische Bewertung vor der Entscheidung. Alex hat danach Astra mit der
endgültigen Zielentscheidung und das Team mit der Umsetzung beauftragt;
[Amendment 20](../../refactoring-study/experiment-2/amendment-20.md) ersetzt den
unten beschriebenen Freigabestopp. Die fachlichen Befunde bleiben bestehen.

**Der bisherige Zielentwurf ist nicht freigabereif.** Die Kritik an
`GeneratorTask` trifft zu. Vollständige Dateilisten und funktionierende Links
hatten wir zu stark mit einer fachlich richtigen Zuordnung gleichgesetzt.
Das war ein Fehler im Vorgehen.

## Was jetzt anders geprüft wird

Drei Luna-Agenten bearbeiten vier getrennte Arbeitspakete: DSL, Runtime/IO,
Domains sowie Einstiegspunkte/Authoring/Querschnitt. Jeder Prüfeintrag erhält
Verantwortung, Urteil, Begründung und Implementierungsbeleg. Der Koordinator
prüft die Übergänge und widerspricht unbegründeten Vorschlägen. Astra prüft
zusätzlich die risikoreichen Schlussfolgerungen unabhängig; das ist keine
zweite vollständige Prüfung aller 773 Einträge und keine Architekturfreigabe.

Die [vollständige Prüfung](review.html) enthält die bestehenden Module,
vorgeschlagenen Ordner und Vertragskomponenten in getrennten Sichten.
Die Agentenurteile bleiben als solche erkennbar; diese Zusammenfassung
enthält die Bewertung des Koordinators. Ein gültiger Codeverweis beweist
allein noch keine sinnvolle Architektur.

## Belastbare Korrekturen

| Bereich | Tatsächliche Verantwortung | Konsequenz für den Entwurf |
| --- | --- | --- |
| `GeneratorTask` | Erstellt einen benannten Generator; dessen Factory entscheidet über Speicherung im Root-Kontext. | Aus `values/scalar` herausnehmen: Setup/Konfiguration. |
| `StateMachineTask` | Registriert eine Übergangsdefinition, aus der spätere Generatorreferenzen eigene Zustandsautomaten erzeugen. | Aus `flow/loops` herausnehmen: Setup/Konfiguration. |
| `KeyVariableTask` | Gemeinsame Wertauswertung für Key, Variable und Element. | Nicht als ausschließliches Variable-Verhalten beschreiben. |
| `ParserUtil` | Wählt Parser und baut Teilbäume; löst außerdem Verbindungsdaten auf. | Diese Aufgaben beim bereits geplanten Split getrennt prüfen. |
| `runtime/sources/selection.py` | Bestimmt Verteilung und Eindeutigkeit ausgewählter Werte. | In Runtime behalten; reines Lesen und Pagination bleiben bei IO. |
| `tasks/__init__.py` | Registriert beim Import die Statement→Task-Zuordnung. | Keine leere Paketmechanik: Eine Verlagerung braucht einen expliziten, geprüften Initialisierungspunkt. |
| `TaskUtil.evaluate_condition_value` | Wertet Bedingungen aus und weist Ergebnisse zurück, die keine booleschen Werte sind. | Beim Entfernen reiner Weiterleitungen diese echte Validierung erhalten. |

Belege: `generator_task.py:25`, `state_machine_task.py:24`,
`key_variable_task.py:65`, `parsers/parser_util.py:79,223` und
`runtime/sources/selection.py`; genaue Dateilinks stehen in den Prüfeinträgen.

Die gleiche semantische Korrektur betrifft Generator- und
StateMachine-Modelle, Parser und Statements. Das Wort „Generator“ macht
eine Deklaration noch nicht zu einer einzelnen Wertberechnung.

Astra fand zusätzlich ungenaue Agentenbeschreibungen: `StateMachineDef`
speichert Regeln; erst `StateTransitionGenerator` erzeugt Zustandswerte.
`GlobalIncrementGenerator` arbeitet mit einem gemeinsamen Runtime-Zähler,
nicht mit einem Zufallszahlengenerator. Die Zuordnung muss diese echte
Zustandsabhängigkeit berücksichtigen.
Ein fehlender Import auf Runtime ist hier keine Entkopplung: Der untypisierte
`context` transportiert die Abhängigkeit trotzdem. Eine Importregel allein
kann diese Verantwortungsgrenze nicht belegen.

Auch Include hat zwei Lebenszeiten: Statische Properties werden während
des Parsens für folgende Geschwister eingelesen; XML-Includes werden zur
Laufzeit geparst und ausgeführt. `IncludeParser` selbst validiert nur die
Deklaration und erstellt das Statement. Deshalb darf „Dokumenteingabe“
nicht pauschal den vollständigen Include-Ablauf übernehmen.

## Was ich nicht aus den Agentenbefunden ableite

- Eine Oberkomponente wird nicht überflüssig, weil sie Unterkomponenten hat.
  `model` validiert DSL-Eingaben, `parsers` baut daraus Statements,
  `statements` hält deren Laufzeitrepräsentation. Das sind nachvollziehbare
  Verantwortungen, keine drei leeren Ordner.
- Eine Aufteilung braucht weder automatisch eine neue Fassade noch ein
  Interface pro Datei. APIs gehören an tatsächlich genutzte Grenzen.
- Eine Befehlsfamilie darf Assert, Echo und Execute zusammenfassen.
  `ExecuteTask` ist trotz seiner Setup-Basisklasse auch als Kind von
  NestedKey ausführbar. Allein aus der Vererbung einen Setup-exklusiven
  Zielort abzuleiten wäre wieder eine Abkürzung statt eines Aufrufer-Traces.
- Kleine CLI-Adapter müssen nicht für jeden Befehl ein neues Modul bekommen;
  Referenz-Projektionen dürfen verschiedene kanonische Eingabeformen lesen.
  Abweichendes Verhalten allein beweist keinen schlechten Gruppenzuschnitt.
- Acht zusammengehörige Module sind nicht automatisch schlechter als sieben
  plus ein künstliches Zwischenpaket. Sieben bleibt ein Review-Auslöser.
- Ein Ordnername wie `generation` löst die Unterscheidung zwischen
  Konfiguration und Ausführung nicht. Die endgültige Benennung und Zuordnung
  braucht eine einheitliche Entscheidung über DSL und Runtime hinweg.
- Das gemeinsame Ziel mit EE bleibt bestehen. Diese Prüfung beweist noch
  keine vollständig gleiche EE-Struktur oder Verhaltensparität.
- Die Domains-Empfehlungen zu `domain_core/datasets` und dem Namen `security`
  sind noch keine belegten Architekturfehler: Ein gemeinsam genutzter
  Datensatzlader kann zum Domain-Fundament gehören; ein Themenname allein
  verspricht keine kryptografische Sicherheit. Dafür keine zusätzlichen
  Umzüge freigeben, bevor konkrete Abhängigkeits- oder Verständlichkeitsprobleme
  nachgewiesen sind.

## Der relevante Ablauf

1. CLI und MCP übersetzen Transport-Eingaben in die Authoring-Verträge.
2. Authoring kompiliert das Intent-Modell, prüft es und führt bei Scaffold
   eine begrenzte Ausführung mit anschließender Ergebnisbewertung durch.
3. Ein vollständiger Lauf über Python oder CLI benutzt den Runtime-Lebenszyklus:
   Descriptor lesen → Statements erzeugen → Setup ausführen → Datensätze erzeugen.
4. Runtime verwaltet Ausführung und Kontext; Quellen und Exporter lesen
   beziehungsweise schreiben die Daten. Domain-Generatoren liefern die
   fachlichen Werte und Entitäten.

Setup führt seine Kinder in Descriptor-Reihenfolge aus. Es gibt keine
allgemeine Vorphase, die sämtliche Deklarationen vor alle Generate-Aufrufe zieht.

Wichtig: Authoring-Prüflauf und vollständiger Lauf teilen Engine-Verhalten,
haben aber unterschiedliche Grenzen für Seiteneffekte und Datenmengen.
Ein gemeinsames Diagramm darf diesen Unterschied nicht verschlucken.

## Navigation: Ursache und Empfehlung

Im bisherigen Prototyp entscheidet `openCard` nach dem Vorhandensein eines
Untervertrags. Fehlt er, ruft es `openMember` auf; diese Funktion setzt
`tree="folders"`. Der Aufstieg folgt danach Ordnerpfaden, nicht dem besuchten
Komponentenpfad. Der beobachtete Ansichtswechsel ist also im Prototyp
programmiert, nicht durch die Architektur notwendig.

Im Browser reproduziert: `runtime → tasks → flow` schaltet auf Dateibaum;
„Eine Ebene zurück“ zeigt anschließend unter `tasks` nur `flow`, weil
zusätzlich der vorherige Komponentenfilter aktiv bleibt. Das ist kein
vollständiger Überblick über das übergeordnete Paket.

Empfehlung: Komponentenansicht beim Vertiefen erhalten. Darunter enthaltene
Pakete und Module sichtbar machen und klar von Vertragsgrenzen unterscheiden.
„Zurück“ stellt Ansicht und Auswahl wieder her; „Übergeordnete Komponente“
steigt eine Ebene auf. Der Dateibaum bleibt eine ausdrücklich wählbare,
synchronisierte zweite Perspektive. Hier wurde diese Navigation nicht geändert.

Zusätzlich muss die Soll-Sicht nach künftiger Zuständigkeit aufgebaut werden.
Dateien einer heutigen Gruppe bis zu ihren Umzugszielen zu verfolgen ist eine
Migrationssicht, aber noch kein reines Ziel-Komponentendiagramm.

## Freigabe und nächster Schritt

Eine zentrale Entwurfsentscheidung ist die Gruppierung der Deklarationen;
weitere nicht abschließend geklärte Zuordnungen bleiben in der vollständigen
Prüfung ausdrücklich als „Offen“ markiert:

| Option für Generator-/StateMachine-/Demographics-Deklarationen | Vorteil | Nachteil |
| --- | --- | --- |
| Gemeinsame Setup-/Definitionsgruppe in Model, Parser und Statements — Empfehlung | Konfiguration ist klar von Datensatzerzeugung getrennt; passt zur Aufgabe der Runtime-Setup-Tasks. | Die Zuordnung der bisherigen Ressourcen-/Setup-Gruppe muss mit angepasst werden. |
| Untergruppe `generation/definitions` | Erzeugungsbezogene Typen bleiben gemeinsam auffindbar. | Die Unterscheidung Deklaration/Ausführung wird eine Ebene tiefer sichtbar. |

Keine Option braucht einen neuen Dienst oder Wrapper. Die falschen
Scalar-/Loop-Zuordnungen sind unabhängig von dieser Namensentscheidung zu
korrigieren. Die gleiche physische Kernstruktur der EE wird danach gegen
ihre konkrete Implementierung geprüft, nicht hier schon als erreicht erklärt.

Zuerst die Verantwortungssätze und die korrigierte Gruppierung freigeben.
Erst danach Verträge, Umzugsplan und Diagramm gemeinsam daraus ableiten;
keine drei unabhängig gepflegten Wahrheiten. Anschließend folgt das
kleinschrittige Refactoring mit unabhängiger Implementierung und QA.

Bis zu dieser Freigabe bleiben Quellcode, Deskriptoren, Baseline und bestehende
Vertragsentwürfe unverändert. Die Prüfung selbst liegt separat vor.

## Nachweisgrenzen

LOCAL VERIFIED:

- 773 eindeutige Prüfeinträge; Implementierungsbelege mit gültigen Dateizeilen.
- 1.339 eingefrorene Eingabedateien unverändert.
- Playwright: alle Einträge vorhanden, verschachteltes Aufklappen,
  390-/1440-Pixel-Layout, keine JS-Fehler oder externen Requests.
- Unerwarteter Perspektivwechsel und erhaltener Filter im alten Prototyp
  per Browser reproduziert.
- 31 gezielte Tests zu Generator-Caching, State-Machine-DSL und
  Authoring-Gateway bestanden; Hilfsskripte mit Ruff geprüft.

Das sind keine vollständigen DSL- oder Seeded/Unseeded-Vergleichsläufe.
Die formalen Prüfungen ersetzen weder semantischen Review noch deine Freigabe.

CI-ONLY VERIFICATION: In diesem Review keine CI ausgeführt oder neu verifiziert.
