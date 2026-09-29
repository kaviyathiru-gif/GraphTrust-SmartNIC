import unittest
from backend.app.models import NetworkNode, NetworkLink, NodeType, NodeStatus, SmartNICTelemetry, HardwareAttestation
from backend.app.trust_engine import TrustEngine

class TestTrustEngine(unittest.TestCase):
    def test_trust_engine_compute_node_trust(self):
        engine = TrustEngine()
        telem = SmartNICTelemetry(
            node_id="dpu-01",
            mac_address="00:11:22:33:44:55",
            ip_address="10.0.0.1",
            rx_packets_sec=20000,
            tx_packets_sec=20000,
            kernel_bypass_ratio=0.96,
            attestation=HardwareAttestation(pcr_quote_valid=True, secure_boot_verified=True, crypto_engine_active=True)
        )
        node = NetworkNode(
            id="dpu-01",
            label="DPU 01",
            type=NodeType.SMART_NIC,
            telemetry=telem
        )
        score = engine.compute_node_trust(node)
        self.assertGreaterEqual(score, 90.0)

    def test_trust_engine_graph_propagation(self):
        engine = TrustEngine()
        nodes = [
            NetworkNode(id="ca", label="CA", type=NodeType.ATTESTATION_AUTHORITY, trust_score=100.0),
            NetworkNode(id="sw1", label="Switch 1", type=NodeType.SDN_SWITCH, trust_score=95.0),
            NetworkNode(id="dpu1", label="DPU 1", type=NodeType.SMART_NIC, trust_score=90.0)
        ]
        links = [
            NetworkLink(id="l1", source="ca", target="sw1", trust_weight=1.0),
            NetworkLink(id="l2", source="sw1", target="dpu1", trust_weight=0.9)
        ]
        scores = engine.compute_graph_trust(nodes, links)
        self.assertIn("ca", scores)
        self.assertIn("sw1", scores)
        self.assertIn("dpu1", scores)
        self.assertGreaterEqual(scores["ca"], scores["dpu1"])

if __name__ == '__main__':
    unittest.main()
