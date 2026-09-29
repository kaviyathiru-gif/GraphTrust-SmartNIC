"""
Data models for Smart NIC, SDN topology, trust scoring, and telemetry streams.
Compatible with Pydantic v1 and v2.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    SMART_NIC = "smart_nic"
    SDN_SWITCH = "sdn_switch"
    HOST_COMPUTE = "host_compute"
    GATEWAY = "gateway"
    ATTESTATION_AUTHORITY = "attestation_authority"

class NodeStatus(str, Enum):
    TRUSTED = "trusted"
    SUSPICIOUS = "suspicious"
    ISOLATED = "isolated"
    COMPROMISED = "compromised"
    PROBING = "probing"

class HardwareAttestation(BaseModel):
    pcr_quote_valid: bool = True
    firmware_hash: str = "sha256-a89f92b7c"
    secure_boot_verified: bool = True
    dpu_arm_cores: int = 16
    crypto_engine_active: bool = True
    last_attestation_ts: float = 0.0

class SmartNICTelemetry(BaseModel):
    node_id: str
    mac_address: str
    ip_address: str
    rx_packets_sec: int = 0
    tx_packets_sec: int = 0
    rx_bytes_sec: int = 0
    tx_bytes_sec: int = 0
    hw_offloaded_flows: int = 0
    kernel_bypass_ratio: float = 0.95
    dropped_untrusted_packets: int = 0
    crypto_offload_utilization_pct: float = 24.5
    dpu_cpu_utilization_pct: float = 18.2
    dpu_temp_celsius: float = 48.0
    packet_tamper_events: int = 0
    trust_score: float = 95.0
    attestation: HardwareAttestation = Field(default_factory=HardwareAttestation)

class NetworkNode(BaseModel):
    id: str
    label: str
    type: NodeType
    status: NodeStatus = NodeStatus.TRUSTED
    trust_score: float = 100.0
    ip: str = "10.0.0.1"
    role: str = "Edge DPU"
    telemetry: Optional[SmartNICTelemetry] = None
    x: Optional[float] = None
    y: Optional[float] = None

class NetworkLink(BaseModel):
    id: str
    source: str
    target: str
    bandwidth_gbps: float = 100.0
    latency_ms: float = 0.45
    trust_weight: float = 1.0
    ipsec_hw_offloaded: bool = True
    active_flows: int = 12

class FlowRuleAction(str, Enum):
    FORWARD = "forward"
    OFFLOAD_DPU = "offload_dpu"
    DROP = "drop"
    MIRROR_TO_SOC = "mirror_to_soc"
    ISOLATE = "isolate"

class FlowRule(BaseModel):
    rule_id: str
    match_src_ip: str
    match_dst_ip: str
    protocol: str = "TCP"
    dst_port: Optional[int] = None
    action: FlowRuleAction = FlowRuleAction.OFFLOAD_DPU
    priority: int = 100
    installed_on: List[str] = Field(default_factory=list)
    packet_count: int = 0
    byte_count: int = 0

class AnomalyEvent(BaseModel):
    timestamp: float
    target_node_id: str
    threat_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    action_taken: str

class GlobalMetrics(BaseModel):
    network_health_index: float = 98.4
    global_trust_index: float = 92.1
    active_smart_nics: int = 6
    total_switches: int = 2
    hardware_offload_ratio_pct: float = 87.5
    crypto_verification_rate_pct: float = 99.8
    total_packets_sec: int = 145000
    dropped_untrusted_packets_sec: int = 12
    avg_latency_ms: float = 0.38
    active_anomalies: int = 0

class TelemetryPayload(BaseModel):
    timestamp: float
    global_metrics: GlobalMetrics
    nodes: List[NetworkNode]
    links: List[NetworkLink]
    recent_anomalies: List[AnomalyEvent]
    flow_rules: List[FlowRule]
