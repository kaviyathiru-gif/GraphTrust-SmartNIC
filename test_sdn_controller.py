import unittest
from backend.app.models import NetworkNode, NetworkLink, NodeType, NodeStatus, FlowRuleAction
from backend.app.sdn_controller import SDNController

class TestSDNController(unittest.TestCase):
    def test_sdn_controller_routing_and_quarantine(self):
        controller = SDNController(trust_quarantine_threshold=40.0)
        nodes = [
            NetworkNode(id="n1", label="Node 1", type=NodeType.SMART_NIC, trust_score=95.0),
            NetworkNode(id="n2", label="Node 2", type=NodeType.SDN_SWITCH, trust_score=92.0),
            NetworkNode(id="n3", label="Node 3", type=NodeType.HOST_COMPUTE, trust_score=90.0)
        ]
        links = [
            NetworkLink(id="l1", source="n1", target="n2", latency_ms=0.2, trust_weight=0.95),
            NetworkLink(id="l2", source="n2", target="n3", latency_ms=0.3, trust_weight=0.90)
        ]

        G = controller.build_topology_graph(nodes, links)
        path = controller.compute_trust_optimal_path(G, "n1", "n3")
        self.assertEqual(path, ["n1", "n2", "n3"])

        nodes[1].trust_score = 25.0
        actions = controller.evaluate_zero_trust_policies(nodes)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action"], "QUARANTINE_ISOLATE")
        self.assertIn("n2", controller.quarantined_nodes)

        path_after_quarantine = controller.compute_trust_optimal_path(G, "n1", "n3")
        self.assertIsNone(path_after_quarantine)

if __name__ == '__main__':
    unittest.main()
