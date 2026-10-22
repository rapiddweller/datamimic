# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""One Build of a project: its files, their bounded CE evidence and optional gates."""

from hashlib import sha256
from importlib import metadata
from pathlib import PurePosixPath

from pydantic import ValidationError

from datamimic_ce.authoring.application.use_cases import _codec_diagnostic
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.build_verification import (
    blocked_verification,
    replay_evidence,
    smoke_export_evidence,
    unseeded_replay_evidence,
)
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_XML_LENGTH
from datamimic_ce.authoring.domain.diagnostics import AuthoringCodecDiagnosticCode, AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonCodecError, DmJsonDocumentV1, iter_dm_json_nodes
from datamimic_ce.authoring.domain.proof import (
    BuildVerificationEvidence,
    BuildVerificationOptions,
    DeterministicReplayEvidence,
    VerificationGateStatus,
)
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    BoundedExecutionRequest,
    BuildArtifact,
    BuildAssurance,
    BuildRequestV5,
    BuildResult,
    ProjectFileDigest,
    ReadyBuild,
    RejectedBuild,
    ValidatedReviewArtifact,
)
from datamimic_ce.authoring.domain.script_semantics import requires_deterministic_replay
from datamimic_ce.authoring.ports import (
    BoundedExecutionPolicy,
    BoundedExecutor,
    DescriptorValidator,
    DmJsonDescriptorContract,
    ProjectFiles,
)
from datamimic_ce.authoring.projection.evidence import sample_evidence


class BuildDocumentWorkflow:
    def __init__(
        self,
        contract: DmJsonDescriptorContract,
        validator: DescriptorValidator,
        executor: BoundedExecutor,
        bounded_execution_policy: BoundedExecutionPolicy,
        files: ProjectFiles,
    ) -> None:
        self._files = files
        self._contract = contract
        self._validator = validator
        self._executor = executor
        self._policy = bounded_execution_policy

    def execute(self) -> BuildResult:
        from datamimic_ce.authoring.domain.acceptance_contract import AcceptanceProjectionError
        from datamimic_ce.authoring.domain.acceptance_evaluation import evaluate_acceptance
        from datamimic_ce.authoring.domain.environment_bindings import validate_environment_bindings
        from datamimic_ce.authoring.projection.acceptance import project_acceptance

        try:
            acceptance_bytes = self._files.read_project_file(PROJECT_ACCEPTANCE_PATH)
            request = BuildRequestV5.model_validate_json(acceptance_bytes)
        except ValidationError as error:
            return RejectedBuild.from_model_validation(error)
        except (OSError, ValueError):
            return RejectedBuild.from_input_error("The project has no readable acceptance/build.json.")
        try:
            entry_bytes = self._files.read_project_file(PROJECT_ENTRY_PATH)
            xml = str(entry_bytes, "utf-8")
        except (OSError, ValueError):
            return RejectedBuild.from_input_error("The project has no readable UTF-8 datamimic.xml entry.")
        if len(xml) > MAX_AUTHORING_XML_LENGTH:
            return RejectedBuild(
                phase=DiagnosticPhase.POLICY,
                diagnostics=(
                    catalog_diagnostic(
                        AuthoringRuleId.LIMIT,
                        "Descriptor exceeds the bounded XML size limit.",
                        phase=DiagnosticPhase.POLICY,
                        path=("descriptor", PROJECT_ENTRY_PATH.as_posix()),
                        expected=MAX_AUTHORING_XML_LENGTH,
                        actual=len(xml),
                    ),
                ),
                verification=blocked_verification(request.verification, "Descriptor exceeds bounded execution limits."),
            )
        lint = self._validator.validate(xml)
        if not lint.ok:
            return RejectedBuild(
                phase=DiagnosticPhase.XML,
                diagnostics=lint.diagnostics,
                verification=blocked_verification(request.verification, "XML validation failed."),
            )
        try:
            document = self._contract.decompile(xml)
        except DmJsonCodecError as error:
            return RejectedBuild(
                phase=DiagnosticPhase.DECOMPILE,
                diagnostics=(
                    _codec_diagnostic(
                        error,
                        code=AuthoringCodecDiagnosticCode.DECOMPILE_UNSUPPORTED,
                        phase=DiagnosticPhase.DECOMPILE,
                        remediation="Rewrite the entry using supported DSL elements.",
                    ),
                ),
                verification=blocked_verification(request.verification, "The entry is not provable."),
            )
        # The project is the entry plus its literal include graph; every fact below covers all of its files.
        graph = self._validator.include_graph(xml)
        if not graph.ok:
            return RejectedBuild(
                # Step lint findings are XML-phase, graph refusals policy-phase; the first error decides.
                phase=next(item.phase for item in graph.diagnostics if item.severity == "error"),
                diagnostics=graph.diagnostics,
                verification=blocked_verification(request.verification, "The include graph is not provable."),
            )
        decoded: list[tuple[str, DmJsonDocumentV1]] = []
        for step in graph.descriptors:
            try:
                decoded.append((step.uri, self._contract.decompile(step.xml)))
            except DmJsonCodecError as error:
                diagnostic = _codec_diagnostic(
                    error,
                    code=AuthoringCodecDiagnosticCode.DECOMPILE_UNSUPPORTED,
                    phase=DiagnosticPhase.DECOMPILE,
                    remediation="Rewrite the included step using supported DSL elements.",
                )
                return RejectedBuild(
                    phase=DiagnosticPhase.DECOMPILE,
                    diagnostics=(diagnostic.relocated(("include", step.uri, *diagnostic.path)),),
                    verification=blocked_verification(request.verification, "An included step is not provable."),
                )
        steps = tuple(decoded)
        binding_diagnostics = validate_environment_bindings(document, request.environment_bindings)
        if binding_diagnostics:
            return RejectedBuild(
                phase=DiagnosticPhase.ENVIRONMENT_BINDING,
                diagnostics=binding_diagnostics,
                verification=blocked_verification(request.verification, "Environment binding failed."),
            )
        verification_options = (
            BuildVerificationOptions(smoke_export=request.verification.smoke_export, deterministic_replay=True)
            if requires_deterministic_replay(document, tuple(step for _, step in steps))
            else request.verification
        )
        step_documents = tuple(step for _, step in steps)
        policy_diagnostics = (
            *self._policy.diagnostics(document, step_documents),
            *(
                diagnostic.relocated(("include", uri, *diagnostic.path[1:]))
                for index, (uri, step) in enumerate(steps)
                for diagnostic in self._policy.diagnostics(
                    step, (document, *step_documents[:index], *step_documents[index + 1 :])
                )
            ),
        )
        if policy_diagnostics:
            return RejectedBuild(
                phase=DiagnosticPhase.POLICY,
                diagnostics=policy_diagnostics,
                verification=blocked_verification(verification_options, "Bounded policy refused this descriptor."),
            )
        try:
            acceptance = project_acceptance(request, document, steps)
        except AcceptanceProjectionError as error:
            return RejectedBuild(
                phase=DiagnosticPhase.EXPECTATION,
                diagnostics=error.diagnostics,
                verification=blocked_verification(verification_options, "Expectation projection failed."),
            )

        execution_request = BoundedExecutionRequest(
            xml=xml,
            descriptor_path=PROJECT_ENTRY_PATH,
            max_count=request.max_count,
            smoke_export=verification_options.smoke_export,
        )
        first = self._executor.execute(execution_request)
        diagnostics = (
            *lint.diagnostics,
            *graph.diagnostics,
            *first.diagnostics,
            *evaluate_acceptance(acceptance, first.captured),
        )
        smoke = smoke_export_evidence(verification_options.smoke_export, first.smoke_export)
        read: list[ProjectFileDigest] = [
            ProjectFileDigest(path=PROJECT_ACCEPTANCE_PATH, sha256=sha256(acceptance_bytes).hexdigest()),
            ProjectFileDigest(path=PROJECT_ENTRY_PATH, sha256=sha256(entry_bytes).hexdigest()),
            *(ProjectFileDigest(path=PurePosixPath(step.uri), sha256=step.sha256) for step in graph.descriptors),
            *first.files,
        ]
        replay = DeterministicReplayEvidence()
        if verification_options.deterministic_replay:
            if not first.ok or not first.base_run_ok or any(item.severity == "error" for item in diagnostics):
                replay = DeterministicReplayEvidence(
                    status=VerificationGateStatus.BLOCKED, reason="The first complete acceptance capture did not pass."
                )
            elif document.root.properties.get("rng_seed") is None:
                replay = unseeded_replay_evidence()
            else:
                second = self._executor.execute(execution_request.model_copy(update={"smoke_export": False}))
                read.extend(second.files)
                replay = replay_evidence(first, second)
                replay_acceptance = evaluate_acceptance(acceptance, second.captured)
                if not second.ok or replay_acceptance:
                    replay = replay.model_copy(
                        update={
                            "status": VerificationGateStatus.FAILED,
                            "reason": "The replay did not provide complete passing acceptance evidence.",
                        }
                    )
                    diagnostics += (*second.diagnostics, *replay_acceptance)
        if replay.status is VerificationGateStatus.FAILED and not request.verification.deterministic_replay:
            diagnostics += (
                catalog_diagnostic(
                    AuthoringRuleId.VALIDATION,
                    "A seeded model that loads Python must replay identically, and this one did not: a value drawn "
                    "outside the seeded names, such as a module-level draw in the library, differs between runs.",
                    phase=DiagnosticPhase.EVIDENCE,
                ),
            )
        verification = BuildVerificationEvidence(smoke_export=smoke, deterministic_replay=replay)
        digests: dict[PurePosixPath, str] = {}
        for item in read:
            if digests.setdefault(item.path, item.sha256) != item.sha256:
                diagnostics += (
                    catalog_diagnostic(
                        AuthoringRuleId.VALIDATION,
                        "A project file changed while Build read it; the proof would not bind the bytes that ran.",
                        phase=DiagnosticPhase.EVIDENCE,
                        path=("project", item.path.as_posix()),
                    ),
                )
        artifact = BuildArtifact(
            files=tuple(ProjectFileDigest(path=path, sha256=digests[path]) for path in sorted(digests)),
            ce_version=metadata.version("datamimic_ce"),
        )
        review = ValidatedReviewArtifact.model_validate(artifact.model_dump())
        try:
            products = sample_evidence(first.captured, request.sample_rows)
        except ValueError:
            products = ()
            diagnostics += (
                catalog_diagnostic(
                    AuthoringRuleId.VALIDATION,
                    "The complete capture cannot be represented faithfully.",
                    phase=DiagnosticPhase.EVIDENCE,
                ),
            )
        if (
            not first.ok
            or not first.base_run_ok
            or not products
            or not verification.gates_passed
            or any(item.severity == "error" for item in diagnostics)
        ):
            if not diagnostics or not any(item.severity == "error" for item in diagnostics):
                diagnostics += (
                    catalog_diagnostic(
                        AuthoringRuleId.VALIDATION,
                        "Bounded execution or a requested verification gate failed.",
                        phase=DiagnosticPhase.EVIDENCE,
                    ),
                )
            return RejectedBuild(
                phase=DiagnosticPhase.EVIDENCE,
                diagnostics=diagnostics,
                review_artifact=review,
                evidence=products,
                verification=verification,
            )
        return ReadyBuild(
            artifact=artifact,
            assurance=BuildAssurance(
                mode="target_isolated"
                if any(
                    node.properties.get("target")
                    for project_document in (document, *(step for _, step in steps))
                    for node, _ in iter_dm_json_nodes(project_document)
                )
                else "local_bounded",
                source_accesses=first.source_accesses,
            ),
            evidence=products,
            verification=verification,
            diagnostics=diagnostics,
        )
