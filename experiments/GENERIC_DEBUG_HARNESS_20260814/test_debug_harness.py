import unittest
from debug_harness import evaluate

class TestDebugHarness(unittest.TestCase):
    def test_chain(self):
        c={"deployment_identity":{"status":"ESTABLISHED","evidence_ref":"d1"},"probes":[{"probe_id":"r","status":"FAIL","evidence_refs":["p1"]}],"patch":{"applied":True,"post_deployment_identity":{"status":"ESTABLISHED","evidence_ref":"d2"},"replay_results":[{"probe_id":"r","status":"PASS","evidence_refs":["p2"]}],"regression_status":"PASS","regression_evidence_refs":["g1"]}}
        self.assertEqual(evaluate(c)["state"],"FIX_VALIDATED")
        c["patch"]["replay_results"]=[]
        self.assertEqual(evaluate(c)["state"],"PATCH_NOT_VALIDATED")
    def test_identity(self):
        c={"deployment_identity":{"status":"UNKNOWN"},"probes":[{"probe_id":"x","status":"PASS","evidence_refs":["p"]}]}
        self.assertEqual(evaluate(c)["state"],"BLOCKED_DEPLOYMENT_IDENTITY")

if __name__=="__main__": unittest.main()
