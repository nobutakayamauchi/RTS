import json
import unittest
from pathlib import Path
from external_seed_corpus import SeedValidationError, load_registry, match_candidates, validate_registry, validate_seed


class ExternalSeedCorpusTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(Path('external_seeds/registry.json').read_text())

    def test_committed_registry_validates(self):
        result = validate_registry(self.registry)
        self.assertTrue(result['valid'])
        self.assertEqual(result['seed_count'], 2)
        self.assertEqual(result['canon_authority'], 'NONE')

    def test_match_is_bounded_and_non_authorizing(self):
        result = match_candidates(self.registry, ['batch-limit', 'retry-avoidance'])
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['candidates'][0]['seed_id'], 'ext-openclaw-embedding-item-limit-split-v1')
        self.assertEqual(result['routing_authority'], 'NONE')
        self.assertEqual(result['canon_authority'], 'NONE')

    def test_duplicate_seed_ids_fail(self):
        registry = dict(self.registry)
        registry['seeds'] = [self.registry['seeds'][0], self.registry['seeds'][0]]
        with self.assertRaises(SeedValidationError):
            validate_registry(registry)

    def test_load_registry_round_trip(self):
        self.assertEqual(len(load_registry('external_seeds/registry.json')['seeds']), 2)
