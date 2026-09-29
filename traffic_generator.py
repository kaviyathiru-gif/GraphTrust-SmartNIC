"""
Simulates inter-node network traffic, flow generation, and security threat events.
"""
import random
import time
from typing import List, Tuple
from backend.app.models import FlowRule, FlowRuleAction, AnomalyEvent

class TrafficGenerator:
    def __init__(self):
        self.anomaly_log: List[AnomalyEvent] = []

    def generate_random_flows(self, node_ids: List[str]) -> List[FlowRule]:
        rules = []
        protocols = ["TCP", "UDP", "QUIC", "RoCEv2"]
        ports = [443, 8443, 9092, 50051, 8080]
        
        for i in range(min(8, len(node_ids))):
            src = random.choice(node_ids)
            dst = random.choice([n for n in node_ids if n != src])
            rule = FlowRule(
                rule_id=f"flow-rule-{1000 + i}",
                match_src_ip=f"10.0.0.{node_ids.index(src) + 1}",
                match_dst_ip=f"10.0.0.{node_ids.index(dst) + 1}",
                protocol=random.choice(protocols),
                dst_port=random.choice(ports),
                action=FlowRuleAction.OFFLOAD_DPU,
                priority=100 + i * 10,
                installed_on=[src, dst],
                packet_count=random.randint(50000, 1200000),
                byte_count=random.randint(25000000, 850000000)
            )
            rules.append(rule)
        return rules

    def log_anomaly(self, node_id: str, threat: str, severity: str, desc: str, action: str):
        event = AnomalyEvent(
            timestamp=time.time(),
            target_node_id=node_id,
            threat_type=threat,
            severity=severity,
            description=desc,
            action_taken=action
        )
        self.anomaly_log.insert(0, event)
        if len(self.anomaly_log) > 50:
            self.anomaly_log.pop()
        return event
