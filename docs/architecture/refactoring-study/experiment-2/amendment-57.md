# Amendment 57: correct nested public classifications

Date: 2026-09-28.

The recursive target marked 24 internal implementation entries as public at
nested component boundaries. They have no cross-component use through a
declared facade and are not documented Python import APIs; some names appear
only in internal implementation guidance. Remove those entries from the
contracts while keeping their modules, implementations, module targets, and
dependencies unchanged. `KeyVariableTask` remains public at its owning values
boundary because another component imports it.

Keep the 13 domain model types whose visibility comes from inherited generic
`BaseDomainService` signatures. Their `interface.unused` findings remain open
for ArchKeel's class-method signature coverage review; they are not reclassified
as internal to make validation pass. This amendment corrects the original
contract classification and does not change CE runtime behavior.
