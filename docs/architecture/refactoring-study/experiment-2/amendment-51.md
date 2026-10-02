# Amendment 51: require unseeded export structure

Date: 2026-09-28.

Matching export filenames do not prove matching unseeded output. The Step-0
oracle now records observed JSON object/array shape, including nested field
names, presence and exported row count. It requires concrete shape evidence for
every unseeded output file. Unsupported, empty-schema or unreadable formats are
marked `UNVERIFIED`; identical unverified or unsuccessful records never prove
parity. Seeded byte-digest comparison is unchanged.

This tightens the behavioral gate; it changes no descriptor or runtime behavior.
Older snapshots must be recaptured. CSV, XML, NDJSON, XLSX, fixed-width and
service-backed outputs remain open until format-specific or disposable-service
evidence exists.
