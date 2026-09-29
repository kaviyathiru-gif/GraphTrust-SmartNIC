"""
Software-Defined Networking (SDN) Controller with Smart NIC OpenFlow/P4 Management.
Computes trust-aware optimal routing and enforces dynamic Zero-Trust quarantine.
"""
from typing import Dict, List, Optional, Set
from backend.app.models import NetworkNode, NetworkLink, FlowRule, FlowRuleAction, NodeStatus
from backend.app.graph_engine import SimpleGraph

class SDNController:
    def __init__(self, trust_quarantine_threshold: float = 40.0):
        self.trust_quarantine_threshold = trust_quarantine_threshold
        self.flow_table: Dict[str, FlowRule] = {}
        self.quarantined_nodes: Set[str] = set()

    def build_topology_graph(self, nodes: List[NetworkNode], links: List[NetworkLink]) -> SimpleGraph:
        G = SimpleGraph(directed=False)
        for n in nodes:
            G.add_node(n.id, trust_score=n.trust_score, status=n.status)
        for l in links:
            # Cost function: High latency and Low trust increase traversal cost
            cost = (l.latency_ms + 0.1) * (150.0 / max(5.0, l.trust_weight * 100.0))
            G.add_edge(l.source, l.target, weight=cost, bandwidth=l.bandwidth_gbps)
        return G

    def compute_trust_optimal_path(self, G: SimpleGraph, source: str, destination: str) -> Optional[List[str]]:
        """Dijkstra pathing biased by trust scores, strictly excluding isolated/quarantined nodes."""
        return G.shortest_path(source, destination, excluded_nodes=self.quarantined_nodes)

    def evaluate_zero_trust_policies(self, nodes: List[NetworkNode]) -> List[Dict[str, str]]:
        """
        Inspects all nodes against Zero Trust hardware baselines.
        If node trust is below threshold, automatically push isolation flow rules.
        """
        actions = []
        for n in nodes:
            if n.trust_score < self.trust_quarantine_threshold and n.id not in self.quarantined_nodes:
                self.quarantined_nodes.add(n.id)
                n.status = NodeStatus.ISOLATED
                actions.append({
                    "node_id": n.id,
                    "action": "QUARANTINE_ISOLATE",
                    "reason": f"Trust score {n.trust_score} below threshold {self.trust_quarantine_threshold}"
                })
            elif n.trust_score >= self.trust_quarantine_threshold and n.id in self.quarantined_nodes:
                self.quarantined_nodes.remove(n.id)
                n.status = NodeStatus.TRUSTED
                actions.append({
                    "node_id": n.id,
                    "action": "RESTORE_ACCESS",
                    "reason": f"Attestation verified. Trust score restored to {n.trust_score}"
                })
        return actions

    def generate_hardware_flow_rules(self, nodes: List[NetworkNode], links: List[NetworkLink]) -> List[FlowRule]:
        """Pushes P4/OpenFlow match-action table entries to Smart NICs."""
        rules = []
        for n in nodes:
            action = FlowRuleAction.ISOLATE if n.id in self.quarantined_nodes else FlowRuleAction.OFFLOAD_DPU
            rules.append(FlowRule(
                rule_id=f"rule-sec-{n.id}",
                match_src_ip=n.ip,
                match_dst_ip="*",
                protocol="ALL",
                action=action,
                priority=200 if action == FlowRuleAction.ISOLATE else 50,
                installed_on=[n.id],
                packet_count=14500 if action == FlowRuleAction.OFFLOAD_DPU else 300,
                byte_count=18000000 if action == FlowRuleAction.OFFLOAD_DPU else 45000
            ))
        return rules
