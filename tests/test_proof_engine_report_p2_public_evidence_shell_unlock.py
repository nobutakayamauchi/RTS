from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import proof_engine_pilot.report_p2_public_evidence_shell_unlock as stage


FINGERPRINT_FIELDS = {
    "proof_engine_pilot/product_readiness/round_0011/p2_public_shell_unlock_contract.json": "contract_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/approved_p3_output_binding.json": "binding_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/public_surface_inventory.json": "inventory_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/disclosure_policy.json": "policy_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/public_shell_information_architecture.json": "architecture_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/p2_unlock_decision.json": "decision_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/readiness_score_hold.json": "score_hold_fingerprint",
    "proof_engine_pilot/product_readiness/round_0011/p2_public_shell_plan_completion.json": "completion_fingerprint",
    stage.POSITION_PATH: "map_fingerprint",
    stage.CHECKPOINT_PATH: "checkpoint_fingerprint",
    stage.PRIOR_POSITION_PATH: "map_fingerprint",
    stage.PRIOR_COMPLETION_PATH: "completion_fingerprint",
    stage.PRIOR_CHECKPOINT_PATH: "checkpoint_fingerprint",
}


class P2PublicShellUnlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_root = stage.ROOT
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in stage.required_paths():
            source = self.source_root / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        stage.ROOT = self.root

    def tearDown(self) -> None:
        stage.ROOT = self.source_root
        self.temp.cleanup()

    def mutate(self, relative: str, callback, *, resign: bool = True) -> None:
        path = self.root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        callback(value)
        field = FINGERPRINT_FIELDS.get(relative)
        if resign and field:
            value.pop(field, None)
            value[field] = stage.fingerprint(value)
        path.write_text(stage.canonical_json(value), encoding="utf-8")

    def assert_stage_fails(self, func=stage.verify_all) -> None:
        with self.assertRaises(stage.P2PublicShellError):
            func()

    def test_001_complete_stage_passes(self) -> None:
        result = stage.verify_all()
        self.assertEqual(result["state"], "INTERNAL_P2_PUBLIC_EVIDENCE_SHELL_UNLOCK_AND_PLAN_COMPLETE")
        self.assertEqual(result["rts_overall_planning_estimate_percent"], 82)

    def test_002_summary_preserves_external_wait(self) -> None:
        result = stage.verify_all()
        self.assertEqual(result["external_wait_state"], "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED")
        self.assertEqual(result["external_wait_next_gate"], "HUMAN_RESPONSE_EVENT_OR_NO_RESPONSE_WINDOW_EXPIRY_REQUIRED")

    def test_003_contract_fingerprint_mismatch_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v.__setitem__("state", "ALTERED"), resign=False)
        self.assert_stage_fails(stage.verify_contract)

    def test_004_raw_instruction_storage_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["instruction_provenance"].__setitem__("raw_instruction_stored", True))
        self.assert_stage_fails(stage.verify_contract)

    def test_005_normalized_instruction_substitution_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["instruction_provenance"].__setitem__("normalized_instruction_sha256", "0" * 64))
        self.assert_stage_fails(stage.verify_contract)

    def test_006_contract_publication_authority_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["authority"].__setitem__("publication_authorized", True))
        self.assert_stage_fails(stage.verify_contract)

    def test_007_contract_build_authority_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["authority"].__setitem__("p2_public_shell_build_authorized", True))
        self.assert_stage_fails(stage.verify_contract)

    def test_008_contract_readme_authority_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["operating_boundary"].__setitem__("root_readme_change_authorized", True))
        self.assert_stage_fails(stage.verify_contract)

    def test_009_prior_position_substitution_fails(self) -> None:
        rel = stage.ARTIFACTS["contract"][0]
        self.mutate(rel, lambda v: v["prior_state"].__setitem__("outreach_waiting_position_fingerprint", "0" * 64))
        self.assert_stage_fails(stage.verify_contract)

    def test_010_approved_output_path_substitution_fails(self) -> None:
        rel = stage.ARTIFACTS["binding"][0]
        self.mutate(rel, lambda v: v["approved_output"].__setitem__("document_path", "README.md"))
        self.assert_stage_fails(stage.verify_binding)

    def test_011_approved_output_blob_substitution_fails(self) -> None:
        rel = stage.ARTIFACTS["binding"][0]
        self.mutate(rel, lambda v: v["approved_output"].__setitem__("document_blob_sha", "0" * 40))
        self.assert_stage_fails(stage.verify_binding)

    def test_012_approved_output_count_change_fails(self) -> None:
        rel = stage.ARTIFACTS["binding"][0]
        self.mutate(rel, lambda v: v["approved_output"].__setitem__("effective_output_count", 5))
        self.assert_stage_fails(stage.verify_binding)

    def test_013_public_output_source_drift_fails(self) -> None:
        path = self.root / "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        self.assert_stage_fails(stage.verify_bound_sources)

    def test_014_release_authorization_source_drift_fails(self) -> None:
        rel = "proof_engine_pilot/releases/round_0001/release_authorization.json"
        self.mutate(rel, lambda v: v["authority"].__setitem__("social_posting_authorized", True), resign=False)
        self.assert_stage_fails(stage.verify_bound_sources)

    def test_015_inventory_surface_removed_fails(self) -> None:
        rel = stage.ARTIFACTS["inventory"][0]
        self.mutate(rel, lambda v: v["surfaces"].pop())
        self.assert_stage_fails(stage.verify_inventory)

    def test_016_inventory_change_performed_fails(self) -> None:
        rel = stage.ARTIFACTS["inventory"][0]
        self.mutate(rel, lambda v: v["surfaces"][0].__setitem__("change_in_this_stage", True))
        self.assert_stage_fails(stage.verify_inventory)

    def test_017_inventory_rebuild_decision_fails(self) -> None:
        rel = stage.ARTIFACTS["inventory"][0]
        self.mutate(rel, lambda v: v.__setitem__("result", "REBUILD_FROM_ZERO"))
        self.assert_stage_fails(stage.verify_inventory)

    def test_018_inventory_dm_exclusion_removed_fails(self) -> None:
        rel = stage.ARTIFACTS["inventory"][0]
        self.mutate(rel, lambda v: v["private_or_contextual_material_excluded"].pop(0))
        self.assert_stage_fails(stage.verify_inventory)

    def test_019_policy_permits_private_messages_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v["permitted_content"].append("private messages"))
        self.assert_stage_fails(stage.verify_policy)

    def test_020_policy_sensitive_prohibition_removed_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v["prohibited_content"].__setitem__(2, "ordinary public data"))
        self.assert_stage_fails(stage.verify_policy)

    def test_021_policy_release_gate_weakened_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v["release_gates"].__setitem__("new_public_document_requires_separate_human_authorization", False))
        self.assert_stage_fails(stage.verify_policy)

    def test_022_policy_state_change_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v.__setitem__("state", "PUBLICATION_APPROVED"))
        self.assert_stage_fails(stage.verify_policy)

    def test_023_policy_manufactured_release_decision_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v["review_attribution"].__setitem__("public_release_decision", "APPROVED"))
        self.assert_stage_fails(stage.verify_policy)

    def test_024_policy_contact_identity_leak_fails(self) -> None:
        rel = stage.ARTIFACTS["policy"][0]
        self.mutate(rel, lambda v: v["permitted_content"].append("Discord contact jbexta"))
        self.assert_stage_fails(stage.verify_policy)

    def test_025_architecture_path_change_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["proposed_surface"].__setitem__("path", "README.md"))
        self.assert_stage_fails(stage.verify_architecture)

    def test_026_architecture_created_state_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["proposed_surface"].__setitem__("status", "CREATED"))
        self.assert_stage_fails(stage.verify_architecture)

    def test_027_architecture_readme_promotion_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["proposed_surface"].__setitem__("root_readme_link_status", "AUTHORIZED"))
        self.assert_stage_fails(stage.verify_architecture)

    def test_028_architecture_contact_activation_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["sections"][-1].__setitem__("current_state", "ACTIVE"))
        self.assert_stage_fails(stage.verify_architecture)

    def test_029_architecture_section_removed_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["sections"].pop(2))
        self.assert_stage_fails(stage.verify_architecture)

    def test_030_architecture_wait_detail_leak_fails(self) -> None:
        rel = stage.ARTIFACTS["architecture"][0]
        self.mutate(rel, lambda v: v["sections"][1]["must_state"].append("2026-08-12T15:48:19"))
        self.assert_stage_fails(stage.verify_architecture)

    def test_031_decision_starts_p2_fails(self) -> None:
        rel = stage.ARTIFACTS["decision"][0]
        self.mutate(rel, lambda v: v.__setitem__("p2_state", "IN_PROGRESS"))
        self.assert_stage_fails(stage.verify_decision)

    def test_032_decision_publication_authorized_fails(self) -> None:
        rel = stage.ARTIFACTS["decision"][0]
        self.mutate(rel, lambda v: v.__setitem__("publication_authorized", True))
        self.assert_stage_fails(stage.verify_decision)

    def test_033_decision_build_authorized_fails(self) -> None:
        rel = stage.ARTIFACTS["decision"][0]
        self.mutate(rel, lambda v: v.__setitem__("public_shell_build_authorized", True))
        self.assert_stage_fails(stage.verify_decision)

    def test_034_decision_next_gate_change_fails(self) -> None:
        rel = stage.ARTIFACTS["decision"][0]
        self.mutate(rel, lambda v: v.__setitem__("next_gate", "PUBLISH_NOW"))
        self.assert_stage_fails(stage.verify_decision)

    def test_035_product_readiness_inflation_fails(self) -> None:
        rel = stage.ARTIFACTS["score"][0]
        self.mutate(rel, lambda v: v.__setitem__("product_readiness_score", 94))
        self.assert_stage_fails(stage.verify_score_hold)

    def test_036_rts_progress_inflation_fails(self) -> None:
        rel = stage.ARTIFACTS["score"][0]
        self.mutate(rel, lambda v: v.__setitem__("rts_overall_planning_estimate_percent", 83))
        self.assert_stage_fails(stage.verify_score_hold)

    def test_037_completion_publication_fails(self) -> None:
        rel = stage.ARTIFACTS["completion"][0]
        self.mutate(rel, lambda v: v.__setitem__("publication_performed", True))
        self.assert_stage_fails(stage.verify_completion)

    def test_038_completion_external_wait_drop_fails(self) -> None:
        rel = stage.ARTIFACTS["completion"][0]
        self.mutate(rel, lambda v: v.__setitem__("external_wait_state", "CLOSED"))
        self.assert_stage_fails(stage.verify_completion)

    def test_039_completion_analysis_fails(self) -> None:
        rel = stage.ARTIFACTS["completion"][0]
        self.mutate(rel, lambda v: v.__setitem__("analysis_performed", True))
        self.assert_stage_fails(stage.verify_completion)

    def test_040_position_wait_expiry_change_fails(self) -> None:
        self.mutate(stage.POSITION_PATH, lambda v: v["current_position"].__setitem__("external_wait_expiry_local", "2026-08-01T00:00:00+09:00"))
        self.assert_stage_fails(stage.verify_progress)

    def test_041_position_product_axis_inflation_fails(self) -> None:
        self.mutate(stage.POSITION_PATH, lambda v: v["final_shape"]["axes"][3].__setitem__("score", 24))
        self.assert_stage_fails(stage.verify_progress)

    def test_042_checkpoint_repository_write_fails(self) -> None:
        self.mutate(stage.CHECKPOINT_PATH, lambda v: v.__setitem__("source_or_target_repository_writes_performed", True))
        self.assert_stage_fails(stage.verify_checkpoint)

    def test_043_checkpoint_unknown_field_fails(self) -> None:
        self.mutate(stage.CHECKPOINT_PATH, lambda v: v.__setitem__("silent_authority", False))
        self.assert_stage_fails(stage.verify_checkpoint)

    def test_044_unapproved_public_shell_file_fails(self) -> None:
        path = self.root / stage.PROPOSED_PUBLIC_SHELL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# unauthorized shell\n", encoding="utf-8")
        self.assert_stage_fails(stage.verify_bound_sources)


if __name__ == "__main__":
    unittest.main()
