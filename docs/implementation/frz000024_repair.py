from pathlib import Path


# K0: recognize catalog/positioning cost adjectives as descriptive, not a
# concrete operational contract by themselves.
p = Path("review_necessity_triage/core.py")
s = p.read_text()
old = '''DESCRIPTIVE_CAPABILITY_PATTERNS: tuple[str, ...] = (\n    r"\\bmodel for\\b",\n'''
new = '''DESCRIPTIVE_CAPABILITY_PATTERNS: tuple[str, ...] = (\n    r"\\b(?:cost|price)[- ](?:efficient|effective|optimized|friendly)\\b",\n    r"\\b(?:model|engine|product)\\s+(?:is\\s+)?(?:described|positioned|marketed|presented)\\s+(?:as|for)\\b",\n    r"\\b(?:described|positioned|marketed|presented)\\s+for\\b",\n    r"\\bmodel for\\b",\n'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s)


# K1: a bare cost adjective is not enough to manufacture budget work. Keep
# explicit pricing/billing language, and keep price/cost when coupled to an
# observable amount, unit, change, cap, limit, or budget context.
p = Path("human_escalation_gate/core.py")
s = p.read_text()
old = '''    (\n        "RECALIBRATE_LIMIT_OR_BUDGET",\n        (r"(?:billed|billing|token rates?|pricing|price|cost)",),\n    ),\n'''
new = '''    (\n        "RECALIBRATE_LIMIT_OR_BUDGET",\n        (\n            r"(?:\\b(?:billed|billing|pricing|token rates?|budget|spend)\\b|"\n            r"\\b(?:price|cost)s?\\b(?=[\\s\\S]{0,120}(?:[$¥€]|\\b(?:usd|dollars?|yen|eur)\\b|\\bper\\b|"\n            r"\\bincreas(?:e|ed|es|ing)?\\b|\\bdecreas(?:e|ed|es|ing)?\\b|\\bchang(?:e|ed|es|ing)?\\b|"\n            r"\\blimit\\b|\\bcap\\b|\\bbudget\\b)))",\n        ),\n    ),\n'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s)


# K0 direct DA regression.
p = Path("tests/test_review_necessity_triage_da.py")
s = p.read_text()
needle = '''    def test_operational_reasoning_guidance_remains_human_now(self):\n'''
insert = '''    def test_catalog_cost_positioning_is_not_concrete_operational_contract(self):\n        anchors = [\n            "A cost-efficient creative model is described for routine media drafts.",\n            "The catalog presents a cost-effective model for routine image drafts.",\n            "A cost-optimized model is marketed for everyday creative drafts.",\n        ]\n        for anchor in anchors:\n            with self.subTest(anchor=anchor):\n                j = make_j(anchor)\n                triage = triage_refinement_report(j)\n                record = triage["records"][0]\n                self.assertNotEqual(record["classification"], "HUMAN_NOW")\n                self.assertFalse(record["da"]["explicit_contract_signal"])\n                self.assertLessEqual(record["da"]["impact"], 2)\n                self.assertLessEqual(record["da"]["causal_reach"], 2)\n\n'''
assert s.count(needle) == 1, s.count(needle)
s = s.replace(needle, insert + needle)
p.write_text(s)


# K1 route boundary + end-to-end FG-001 regression.
p = Path("tests/test_human_escalation_gate_da.py")
s = p.read_text()
old_import = '''from human_escalation_gate import (\n    EXHAUSTION_SEARCH_ROUTE,\n    HumanEscalationError,\n    evaluate_escalation_report,\n)\n'''
new_import = '''from human_escalation_gate import (\n    EXHAUSTION_SEARCH_ROUTE,\n    HumanEscalationError,\n    evaluate_escalation_report,\n    recover_escape_routes,\n)\n'''
assert s.count(old_import) == 1, s.count(old_import)
s = s.replace(old_import, new_import)
needle = '''    def test_attempts_do_not_exhaust_an_open_route(self):\n'''
insert = '''    def test_fg001_catalog_cost_does_not_manufacture_budget_work(self):\n        anchors = [\n            "A cost-efficient creative model is described for routine media drafts.",\n            "The catalog presents a cost-effective model for routine image drafts.",\n            "A cost-optimized model is marketed for everyday creative drafts.",\n        ]\n        for anchor in anchors:\n            with self.subTest(anchor=anchor):\n                self.assertNotIn("RECALIBRATE_LIMIT_OR_BUDGET", recover_escape_routes(anchor))\n\n    def test_operational_pricing_and_cost_changes_keep_budget_route(self):\n        anchors = [\n            "Pricing for input tokens is $5 per million tokens.",\n            "API cost increases from $5 to $7 per million tokens.",\n            "Billing changed and the budget cap must be recalibrated before rollout.",\n            "The token price is 7 USD per million input tokens.",\n        ]\n        for anchor in anchors:\n            with self.subTest(anchor=anchor):\n                self.assertIn("RECALIBRATE_LIMIT_OR_BUDGET", recover_escape_routes(anchor))\n\n    def test_fg001_end_to_end_is_safe_defer(self):\n        k0 = make_k0("A cost-efficient creative model is described for routine media drafts.")\n        self.assertNotEqual(k0["records"][0]["classification"], "HUMAN_NOW")\n        report = evaluate_escalation_report(k0)\n        row = report["records"][0]\n        self.assertEqual(row["disposition"], "WAIT_SAFE_DEFER")\n        self.assertNotIn("RECALIBRATE_LIMIT_OR_BUDGET", row["recovered_escape_routes"])\n\n'''
assert s.count(needle) == 1, s.count(needle)
s = s.replace(needle, insert + needle)
p.write_text(s)


# K2 expected state transition. The held-out expected outcome itself is not
# changed; only the aggregate assertion changes because the row should now pass.
p = Path("tests/test_test_adequacy_gate.py")
s = p.read_text()
old = '''    def test_known_bad_and_metamorphic_pass_while_held_out_exposes_false_green(self):\n        self.assertTrue(all(row["passed"] for row in self.known_bad), self.known_bad)\n        self.assertTrue(all(row["passed"] for row in self.metamorphic), self.metamorphic)\n        failed = [row for row in self.held_out if not row["passed"]]\n        self.assertEqual([row["case_id"] for row in failed], ["HO_LOW_PRIORITY_CATALOG_TEXT"], self.held_out)\n\n    def test_full_adequacy_requires_all_lanes(self):\n'''
new = '''    def test_all_independent_lanes_pass_after_fg001_repair(self):\n        self.assertTrue(all(row["passed"] for row in self.known_bad), self.known_bad)\n        self.assertTrue(all(row["passed"] for row in self.held_out), self.held_out)\n        self.assertTrue(all(row["passed"] for row in self.metamorphic), self.metamorphic)\n\n    def test_full_adequacy_requires_all_lanes(self):\n'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old = '''        self.assertEqual(report["status"], "HOLD_FALSE_GREEN_RISK")\n        self.assertFalse(report["lanes"]["held_out"])\n'''
new = '''        self.assertEqual(report["status"], "ADEQUATE")\n        self.assertTrue(report["lanes"]["held_out"])\n'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s)
