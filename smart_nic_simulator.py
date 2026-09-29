"""
Offline Smart NIC / DPU Hardware Simulator.
Simulates hardware registers, P4/eBPF offload pipeline, TPM 2.0 attestation,
and crypto coprocessor telemetry.
"""
import time
import random
import hashlib
from typing import Dict, Any, List
from backend.app.models import SmartNICTelemetry, HardwareAttestation, NodeStatus

class SmartNICDevice:
    def __init__(self, node_id: str, ip: str, mac: str, dpu_type: str = "NVIDIA BlueField-3 DPU"):
        self.node_id = node_id
        self.ip = ip
        self.mac = mac
        self.dpu_type = dpu_type
        self.status = NodeStatus.TRUSTED
        self.dpu_arm_cores = 16
        self.base_firmware_hash = hashlib.sha256(f"fw-verified-{node_id}".encode()).hexdigest()[:16]
        self.current_firmware_hash = self.base_firmware_hash
        self.pcr_valid = True
        self.secure_boot = True
        self.crypto_active = True
        
        # Hardware Metrics
        self.rx_rate = random.randint(15000, 35000)
        self.tx_rate = random.randint(15000, 35000)
        self.hw_offloaded_flows = random.randint(40, 120)
        self.kernel_bypass_ratio = 0.94 + random.uniform(0.01, 0.05)
        self.dropped_packets = 0
        self.packet_tamper_count = 0
        self.crypto_util = 35.0
        self.cpu_util = 22.0
        self.temp_celsius = 47.0
        self.trust_score = 98.0
        
        # Attack states
        self.compromised = False
        self.ddos_active = False

    def step_telemetry(self, delta_time: float = 1.0) -> SmartNICTelemetry:
        jitter = random.uniform(-0.05, 0.05)
        
        if self.ddos_active:
            self.rx_rate = int(random.randint(180000, 250000))
            self.dropped_packets += random.randint(2500, 5000)
            self.cpu_util = min(99.0, self.cpu_util + 15.0)
            self.temp_celsius = min(85.0, self.temp_celsius + 2.0)
        elif self.compromised:
            self.packet_tamper_count += random.randint(5, 20)
            self.pcr_valid = False
            self.current_firmware_hash = "tampered_fw_bad0"
            self.trust_score = max(5.0, self.trust_score - 15.0)
            self.dropped_packets += random.randint(10, 50)
            self.status = NodeStatus.COMPROMISED
        else:
            self.rx_rate = max(1000, int(self.rx_rate * (1 + jitter)))
            self.tx_rate = max(1000, int(self.tx_rate * (1 + jitter)))
            self.cpu_util = max(10.0, min(60.0, self.cpu_util + random.uniform(-2, 2)))
            self.temp_celsius = max(42.0, min(65.0, self.temp_celsius + random.uniform(-0.5, 0.5)))
            self.crypto_util = max(15.0, min(80.0, self.crypto_util + random.uniform(-3, 3)))
            
            if self.trust_score < 95.0 and not self.status == NodeStatus.ISOLATED:
                self.trust_score = min(100.0, self.trust_score + 1.5)
                if self.trust_score > 80.0:
                    self.status = NodeStatus.TRUSTED

        attestation = HardwareAttestation(
            pcr_quote_valid=self.pcr_valid,
            firmware_hash=self.current_firmware_hash,
            secure_boot_verified=self.secure_boot,
            dpu_arm_cores=self.dpu_arm_cores,
            crypto_engine_active=self.crypto_active,
            last_attestation_ts=time.time()
        )

        return SmartNICTelemetry(
            node_id=self.node_id,
            mac_address=self.mac,
            ip_address=self.ip,
            rx_packets_sec=self.rx_rate,
            tx_packets_sec=self.tx_rate,
            rx_bytes_sec=self.rx_rate * 1420,
            tx_bytes_sec=self.tx_rate * 1420,
            hw_offloaded_flows=self.hw_offloaded_flows,
            kernel_bypass_ratio=round(self.kernel_bypass_ratio, 3),
            dropped_untrusted_packets=self.dropped_packets,
            crypto_offload_utilization_pct=round(self.crypto_util, 1),
            dpu_cpu_utilization_pct=round(self.cpu_util, 1),
            dpu_temp_celsius=round(self.temp_celsius, 1),
            packet_tamper_events=self.packet_tamper_count,
            trust_score=round(self.trust_score, 1),
            attestation=attestation
        )

    def trigger_firmware_tamper(self):
        self.compromised = True
        self.pcr_valid = False
        self.current_firmware_hash = "unauthorized_mod_0xbeef"
        self.status = NodeStatus.COMPROMISED
        self.trust_score = 18.0

    def trigger_packet_flood(self):
        self.ddos_active = True
        self.status = NodeStatus.SUSPICIOUS
        self.trust_score = max(35.0, self.trust_score - 40.0)

    def remediate(self):
        self.compromised = False
        self.ddos_active = False
        self.pcr_valid = True
        self.current_firmware_hash = self.base_firmware_hash
        self.packet_tamper_count = 0
        self.status = NodeStatus.TRUSTED
        self.trust_score = 98.0
        self.cpu_util = 22.0
