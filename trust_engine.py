"""
Dynamic Graph Trust Network Calculation Engine.
Calculates multidimensional trust weights based on TPM measurements,
Smart NIC hardware offload health, and dynamic EigenTrust graph propagation.
"""
from typing import Dict, List, Tuple, Optional
from backend.app.models import NetworkNode, NetworkLink, NodeStatus
from backend.app.graph_engine import SimpleGraph

class TrustEngine:
    def __init__(self, damping_factor: float = 0.85):
        self.damping_factor = damping_factor

    def compute_node_trust(self, node: NetworkNode) -> float:
        """
        Calculates individual node trust:
        T_node = w1 * H_attest + w2 * F_offload + w3 * S_anomaly
        """
        if not node.telemetry:
            return node.trust_score

        attest = node.telemetry.attestation
        # Hardware Attestation component (45%)
        h_score = 100.0 if (attest.pcr_quote_valid and attest.secure_boot_verified) else 0.0
        
        # Operational component (25%): Kernel bypass ratio & crypto health
        op_score = (node.telemetry.kernel_bypass_ratio * 50.0) + (50.0 if attest.crypto_engine_active else 0.0)
        
        # Anomaly Penalty component (30%)
        tamper_penalty = min(60.0, node.telemetry.packet_tamper_events * 5.0)
        anomaly_score = max(0.0, 100.0 - tamper_penalty)
        
        raw_trust = (0.45 * h_score) + (0.25 * op_score) + (0.30 * anomaly_score)
        return round(float(raw_trust), 1)

    def compute_graph_trust(self, nodes: List[NetworkNode], links: List[NetworkLink]) -> Dict[str, float]:
        """
        Propagates trust across the topology using EigenTrust / PageRank.
        Trust flows from highly verified Smart NICs and Attestation Authorities.
        """
        if not nodes:
            return {}

        G = SimpleGraph(directed=True)
        node_map = {n.id: n for n in nodes}
        
        for n in nodes:
            G.add_node(n.id, base_trust=self.compute_node_trust(n))
            
        for l in links:
            if l.source in node_map and l.target in node_map:
                src_node = node_map[l.source]
                hw_crypto_mult = 1.2 if l.ipsec_hw_offloaded else 0.7
                edge_weight = max(0.1, (src_node.trust_score / 100.0) * hw_crypto_mult)
                G.add_edge(l.source, l.target, weight=edge_weight)
                G.add_edge(l.target, l.source, weight=edge_weight)

        personalization = {}
        for n in nodes:
            if n.type.value == "attestation_authority":
                personalization[n.id] = 5.0
            else:
                personalization[n.id] = max(0.1, n.trust_score / 100.0)

        ranks = G.pagerank(alpha=self.damping_factor, personalization=personalization)
        max_r = max(ranks.values()) if ranks and max(ranks.values()) > 0 else 1.0
        scaled_ranks = {k: round((v / max_r) * 100.0, 1) for k, v in ranks.items()}

        final_scores = {}
        for n in nodes:
            local = self.compute_node_trust(n)
            graph_val = scaled_ranks.get(n.id, local)
            blended = (0.65 * local) + (0.35 * graph_val)
            final_scores[n.id] = round(float(blended), 1)

        return final_scores
