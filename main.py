"""
FastAPI application & WebSocket Telemetry Gateway for TrustNet-SDN Platform.
Compatible with Pydantic v1 & v2.
"""
import os
import json
import time
import asyncio
from typing import List, Dict, Any, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.models import (
    NetworkNode, NetworkLink, TelemetryPayload, GlobalMetrics,
    NodeType, NodeStatus, FlowRule, AnomalyEvent
)
from simulator.smart_nic_simulator import SmartNICDevice
from simulator.traffic_generator import TrafficGenerator
from backend.app.trust_engine import TrustEngine
from backend.app.sdn_controller import SDNController

app = FastAPI(
    title="TrustNet-SDN Dynamic Graph Trust Network",
    description="Smart NIC & SDN Dynamic Graph Trust Network Telemetry and Orchestration Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_model(model_obj) -> str:
    """Cross-compatible serializer for Pydantic v1 and v2."""
    if hasattr(model_obj, "model_dump_json"):
        return model_obj.model_dump_json()
    elif hasattr(model_obj, "json"):
        return model_obj.json()
    else:
        return json.dumps(model_obj)

class OrchestratorState:
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.links: Dict[str, NetworkLink] = {}
        self.smart_nics: Dict[str, SmartNICDevice] = {}
        self.traffic_gen = TrafficGenerator()
        self.trust_engine = TrustEngine()
        self.sdn_controller = SDNController(trust_quarantine_threshold=40.0)
        self.clients: Set[WebSocket] = set()
        self.load_initial_topology()

    def load_initial_topology(self):
        seed_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "seed_topology.json")
        try:
            with open(seed_path, "r") as f:
                data = json.load(f)
                for n_dict in data.get("nodes", []):
                    node = NetworkNode(**n_dict)
                    self.nodes[node.id] = node
                    if node.type == NodeType.SMART_NIC:
                        dpu = SmartNICDevice(
                            node_id=node.id,
                            ip=node.ip,
                            mac=f"00:15:5d:{len(self.smart_nics)+10:02x}:44:01"
                        )
                        self.smart_nics[node.id] = dpu
                for l_dict in data.get("links", []):
                    link = NetworkLink(**l_dict)
                    self.links[link.id] = link
        except Exception as e:
            print(f"Error loading seed topology: {e}")

    def step(self) -> TelemetryPayload:
        for nid, dpu in self.smart_nics.items():
            telem = dpu.step_telemetry()
            if nid in self.nodes:
                self.nodes[nid].telemetry = telem
                self.nodes[nid].trust_score = telem.trust_score
                self.nodes[nid].status = dpu.status

        n_list = list(self.nodes.values())
        l_list = list(self.links.values())
        graph_trust = self.trust_engine.compute_graph_trust(n_list, l_list)
        for nid, score in graph_trust.items():
            if nid in self.nodes:
                self.nodes[nid].trust_score = score
                if score < 40.0:
                    self.nodes[nid].status = NodeStatus.ISOLATED
                elif score < 70.0:
                    self.nodes[nid].status = NodeStatus.SUSPICIOUS

        sdn_actions = self.sdn_controller.evaluate_zero_trust_policies(n_list)
        for act in sdn_actions:
            self.traffic_gen.log_anomaly(
                node_id=act["node_id"],
                threat="ZERO_TRUST_VIOLATION",
                severity="CRITICAL" if act["action"] == "QUARANTINE_ISOLATE" else "LOW",
                desc=act["reason"],
                action=act["action"]
            )

        flow_rules = self.sdn_controller.generate_hardware_flow_rules(n_list, l_list)

        avg_trust = sum(n.trust_score for n in n_list) / max(1, len(n_list))
        active_compromises = sum(1 for n in n_list if n.status in (NodeStatus.COMPROMISED, NodeStatus.ISOLATED))
        health = max(0.0, 100.0 - (active_compromises * 22.0))
        
        metrics = GlobalMetrics(
            network_health_index=round(health, 1),
            global_trust_index=round(avg_trust, 1),
            active_smart_nics=len(self.smart_nics),
            total_switches=sum(1 for n in n_list if n.type == NodeType.SDN_SWITCH),
            hardware_offload_ratio_pct=88.4 if active_compromises == 0 else 64.2,
            crypto_verification_rate_pct=99.9 if active_compromises == 0 else 72.1,
            total_packets_sec=sum(n.telemetry.rx_packets_sec for n in n_list if n.telemetry) + 85000,
            dropped_untrusted_packets_sec=sum(n.telemetry.dropped_untrusted_packets for n in n_list if n.telemetry),
            avg_latency_ms=0.32 if active_compromises == 0 else 1.25,
            active_anomalies=active_compromises
        )

        return TelemetryPayload(
            timestamp=time.time(),
            global_metrics=metrics,
            nodes=n_list,
            links=l_list,
            recent_anomalies=self.traffic_gen.anomaly_log[:15],
            flow_rules=flow_rules
        )

state = OrchestratorState()

async def telemetry_broadcaster():
    while True:
        try:
            payload = state.step()
            payload_json = serialize_model(payload)
            disconnected = []
            for ws in state.clients:
                try:
                    await ws.send_text(payload_json)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                state.clients.discard(ws)
        except Exception as e:
            print(f"Error in telemetry loop: {e}")
        await asyncio.sleep(1.0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telemetry_broadcaster())

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.clients.add(websocket)
    try:
        initial_payload = state.step()
        await websocket.send_text(serialize_model(initial_payload))
    except Exception:
        pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                action = cmd.get("action")
                node_id = cmd.get("node_id")

                if action == "inject_tamper" and node_id in state.smart_nics:
                    state.smart_nics[node_id].trigger_firmware_tamper()
                    state.traffic_gen.log_anomaly(
                        node_id=node_id,
                        threat="TPM_PCR_CORRUPTION",
                        severity="CRITICAL",
                        desc="Hardware secure boot PCR 0x8 signature invalid. Firmware mismatch.",
                        action="ISOLATION_REQUESTED"
                    )
                elif action == "inject_flood" and node_id in state.smart_nics:
                    state.smart_nics[node_id].trigger_packet_flood()
                    state.traffic_gen.log_anomaly(
                        node_id=node_id,
                        threat="DPU_INGRESS_FLOOD",
                        severity="HIGH",
                        desc="Ingress rate exceeded hardware P4 threshold limit (200k pps).",
                        action="RATE_LIMIT_POLICED"
                    )
                elif action == "remediate" and node_id in state.smart_nics:
                    state.smart_nics[node_id].remediate()
                    state.traffic_gen.log_anomaly(
                        node_id=node_id,
                        threat="REMEDIATION_COMPLETE",
                        severity="LOW",
                        desc="Remote TPM measurement verified and clean firmware re-flashed.",
                        action="TRUST_RESTORED"
                    )
                elif action == "add_node":
                    new_node = NetworkNode(**cmd.get("node"))
                    state.nodes[new_node.id] = new_node
                    if new_node.type == NodeType.SMART_NIC:
                        state.smart_nics[new_node.id] = SmartNICDevice(
                            node_id=new_node.id,
                            ip=new_node.ip,
                            mac=f"00:15:5d:{len(state.smart_nics)+10:02x}:99:02"
                        )
                elif action == "add_link":
                    new_link = NetworkLink(**cmd.get("link"))
                    state.links[new_link.id] = new_link
                elif action == "delete_element":
                    target_id = cmd.get("id")
                    if target_id in state.nodes:
                        del state.nodes[target_id]
                        state.smart_nics.pop(target_id, None)
                        state.links = {k: v for k, v in state.links.items() if v.source != target_id and v.target != target_id}
                    elif target_id in state.links:
                        del state.links[target_id]

            except Exception as e:
                print(f"Error handling WS message: {e}")
    except WebSocketDisconnect:
        state.clients.discard(websocket)

@app.get("/api/topology")
async def get_topology():
    return {
        "nodes": [n.dict() if hasattr(n, "dict") else n.model_dump() for n in state.nodes.values()],
        "links": [l.dict() if hasattr(l, "dict") else l.model_dump() for l in state.links.values()]
    }

@app.post("/api/actions/inject-attack")
async def inject_attack(payload: Dict[str, Any]):
    node_id = payload.get("node_id")
    attack_type = payload.get("type", "tamper")
    if node_id not in state.smart_nics:
        raise HTTPException(status_code=404, detail="Smart NIC not found")
    if attack_type == "tamper":
        state.smart_nics[node_id].trigger_firmware_tamper()
    elif attack_type == "flood":
        state.smart_nics[node_id].trigger_packet_flood()
    return {"status": "attack_injected", "node_id": node_id, "type": attack_type}

@app.post("/api/actions/remediate")
async def remediate_node(payload: Dict[str, Any]):
    node_id = payload.get("node_id")
    if node_id not in state.smart_nics:
        raise HTTPException(status_code=404, detail="Smart NIC not found")
    state.smart_nics[node_id].remediate()
    return {"status": "remediated", "node_id": node_id}

@app.get("/api/metrics")
async def get_metrics():
    payload = state.step()
    return payload.global_metrics.dict() if hasattr(payload.global_metrics, "dict") else payload.global_metrics.model_dump()

frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
