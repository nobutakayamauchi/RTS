import copy
import json
import unittest
from pathlib import Path
from external_seed_corpus import SeedValidationError, match_candidates, validate_seed


class ExternalSeedCorpusDA(unittest.TestCase):
    def setUp(self):
        self.seed = json.loads(Path('external_seeds/registry.json').read_text())['seeds'][0]

    def test_missing_exact_provenance_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['source_refs'] = []
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_missing_counterconditions_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['counterconditions'] = []
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_external_merge_cannot_be_canonical(self):
        seed = copy.deepcopy(self.seed)
        self.assertTrue(any(x['merged'] for x in seed['source_refs']))
        seed['state'] = 'CANONICAL'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_authority_escalation_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['authority']['canon'] = 'APPROVED'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_missing_license_posture_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['license'] = {}
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_reference_only_is_mandatory(self):
        seed = copy.deepcopy(self.seed)
        seed['reuse_mode'] = 'COPY_CODE'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_rejected_seed_is_not_matched(self):
        registry = json.loads(Path('external_seeds/registry.json').read_text())
        registry['seeds'][0]['state'] = 'REJECTED'
        result = match_candidates(registry, ['batch-limit'])
        self.assertEqual(result['candidate_count'], 0)
