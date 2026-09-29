/**
 * TrustNet-SDN Platform Master Coordinator.
 * Handles WebSocket lifecycle, offline simulator fallback, and user event dispatch.
 */

import { GraphController } from './graph.js';
import { DashboardController } from './dashboard.js';

class TrustNetApp {
  constructor() {
    this.graph = null;
    this.dashboard = null;
    this.selectedNode = null;
    this.ws = null;
    this.isOfflineMode = false;
    this.simulationState = null;

    this.init();
  }

  init() {
    // 1. Initialize Dashboard
    this.dashboard = new DashboardController({
      onFilterChange: (filters) => {
        if (this.graph) {
          this.graph.applyFilter(filters.type, filters.minTrust);
          if (this.simulationState) {
            this.dashboard.updateCharts(this.simulationState.nodes, this.simulationState.global_metrics);
          }
        }
      }
    });

    // 2. Initialize Cytoscape Graph
    this.graph = new GraphController('cy', {
      onNodeSelected: (nodeData) => this.showNodeInspector(nodeData),
      onNodeAdded: (newNode) => this.dispatchNodeAdded(newNode),
      onLinkAdded: (newLink) => this.dispatchLinkAdded(newLink),
      onElementDeleted: (id) => this.dispatchElementDeleted(id)
    });

    // 3. UI Controls
    this.bindUIEvents();

    // 4. Connect WebSocket with Offline Simulator Fallback
    this.connectWebSocket();
  }

  bindUIEvents() {
    // Layout changer
    const layoutSelect = document.getElementById('layout-select');
    layoutSelect.addEventListener('change', (e) => this.graph.runLayout(e.target.value));

    // Reset / Auto layout button
    document.getElementById('btn-reset-layout').addEventListener('click', () => {
      this.graph.runLayout(layoutSelect.value);
    });

    // Fit graph
    document.getElementById('btn-fit-graph').addEventListener('click', () => this.graph.fit());

    // Link Mode Toggle
    const linkBtn = document.getElementById('btn-add-link-mode');
    linkBtn.addEventListener('click', () => {
      this.graph.linkMode = !this.graph.linkMode;
      linkBtn.classList.toggle('active', this.graph.linkMode);
      if (this.graph.linkMode) {
        linkBtn.textContent = '❌ Cancel Link';
      } else {
        linkBtn.textContent = '🔗 Link';
      }
    });

    // Inspector Close
    document.getElementById('btn-close-inspector').addEventListener('click', () => {
      document.getElementById('node-inspector').classList.add('hidden');
    });

    // Quick Attack Button
    document.getElementById('btn-quick-attack').addEventListener('click', () => {
      if (this.simulationState && this.simulationState.nodes) {
        const smartNics = this.simulationState.nodes.filter(n => n.type === 'smart_nic');
        if (smartNics.length) {
          const target = smartNics[Math.floor(Math.random() * smartNics.length)];
          this.sendAction({ action: 'inject_tamper', node_id: target.id });
        }
      }
    });

    // Inspector Action Buttons
    document.getElementById('btn-tamper-node').addEventListener('click', () => {
      if (this.selectedNode) this.sendAction({ action: 'inject_tamper', node_id: this.selectedNode.id });
    });

    document.getElementById('btn-flood-node').addEventListener('click', () => {
      if (this.selectedNode) this.sendAction({ action: 'inject_flood', node_id: this.selectedNode.id });
    });

    document.getElementById('btn-remediate-node').addEventListener('click', () => {
      if (this.selectedNode) this.sendAction({ action: 'remediate', node_id: this.selectedNode.id });
    });

    document.getElementById('btn-delete-node').addEventListener('click', () => {
      if (this.selectedNode) {
        this.dispatchElementDeleted(this.selectedNode.id);
        document.getElementById('node-inspector').classList.add('hidden');
      }
    });
  }

  showNodeInspector(nodeData) {
    this.selectedNode = nodeData.rawNode || nodeData;
    const inspector = document.getElementById('node-inspector');
    inspector.classList.remove('hidden');

    document.getElementById('insp-title').textContent = `${this.selectedNode.label} (${this.selectedNode.ip})`;
    const telem = this.selectedNode.telemetry;

    if (telem) {
      document.getElementById('insp-attest').textContent = telem.attestation?.pcr_quote_valid ? 'PCR VALID' : 'TAMPER DETECTED';
      document.getElementById('insp-attest').className = telem.attestation?.pcr_quote_valid ? 'value text-success' : 'value text-danger';
      document.getElementById('insp-trust').textContent = `${Math.round(this.selectedNode.trust_score)} / 100`;
      document.getElementById('insp-offload').textContent = `${telem.rx_packets_sec.toLocaleString()} pps`;
      document.getElementById('insp-crypto').textContent = telem.attestation?.crypto_engine_active ? 'HW IPsec Active' : 'Bypassed';
      document.getElementById('insp-temp').textContent = `${telem.dpu_temp_celsius}°C | ${telem.dpu_cpu_utilization_pct}%`;
      document.getElementById('insp-tamper').textContent = `${telem.packet_tamper_events} detected`;
    } else {
      document.getElementById('insp-attest').textContent = 'N/A (Switch/Host)';
      document.getElementById('insp-trust').textContent = `${Math.round(this.selectedNode.trust_score)} / 100`;
      document.getElementById('insp-offload').textContent = 'Fabric Routed';
      document.getElementById('insp-crypto').textContent = 'TLS Session';
      document.getElementById('insp-temp').textContent = 'Normal';
      document.getElementById('insp-tamper').textContent = '0 detected';
    }
  }

  connectWebSocket() {
    const loc = window.location;
    const wsProto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = loc.hostname || 'localhost';
    const wsPort = loc.port || '8000';
    const wsUrl = `${wsProto}//${wsHost}:${wsPort}/ws/telemetry`;

    const statusPill = document.getElementById('conn-status-pill');
    const statusText = document.getElementById('conn-status-text');

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isOfflineMode = false;
        statusPill.querySelector('.pulse-dot').classList.remove('offline');
        statusText.textContent = 'WS: Connected Live (8000)';
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.handleTelemetryPayload(payload);
        } catch (e) {
          console.error('Payload parse error:', e);
        }
      };

      this.ws.onerror = () => {
        this.fallbackToOfflineSimulator();
      };

      this.ws.onclose = () => {
        this.fallbackToOfflineSimulator();
      };
    } catch (err) {
      this.fallbackToOfflineSimulator();
    }
  }

  fallbackToOfflineSimulator() {
    if (this.isOfflineMode) return;
    this.isOfflineMode = true;

    const statusPill = document.getElementById('conn-status-pill');
    const statusText = document.getElementById('conn-status-text');
    statusPill.querySelector('.pulse-dot').classList.add('offline');
    statusText.textContent = 'Offline Sim Mode (Stand-alone)';

    // Seed mock state
    this.initMockSimulation();
    setInterval(() => this.stepMockSimulation(), 1000);
  }

  initMockSimulation() {
    const nodes = [
      { id: 'ca-root', label: 'Attestation CA', type: 'attestation_authority', status: 'trusted', trust_score: 100, ip: '10.0.0.1' },
      { id: 'sdn-spine-1', label: 'SDN Spine 01', type: 'sdn_switch', status: 'trusted', trust_score: 98, ip: '10.0.0.10' },
      { id: 'sdn-spine-2', label: 'SDN Spine 02', type: 'sdn_switch', status: 'trusted', trust_score: 97, ip: '10.0.0.11' },
      {
        id: 'dpu-edge-01', label: 'Smart NIC DPU 01', type: 'smart_nic', status: 'trusted', trust_score: 96, ip: '10.0.1.101',
        telemetry: { rx_packets_sec: 28000, dpu_temp_celsius: 48, dpu_cpu_utilization_pct: 18, packet_tamper_events: 0, dropped_untrusted_packets: 4, attestation: { pcr_quote_valid: true, crypto_engine_active: true } }
      },
      {
        id: 'dpu-edge-02', label: 'Smart NIC DPU 02', type: 'smart_nic', status: 'trusted', trust_score: 95, ip: '10.0.1.102',
        telemetry: { rx_packets_sec: 32000, dpu_temp_celsius: 49, dpu_cpu_utilization_pct: 21, packet_tamper_events: 0, dropped_untrusted_packets: 6, attestation: { pcr_quote_valid: true, crypto_engine_active: true } }
      },
      { id: 'host-k8s', label: 'Compute Host K8s', type: 'host_compute', status: 'trusted', trust_score: 93, ip: '10.0.2.201' },
      { id: 'gw-border', label: 'Edge Zero-Trust GW', type: 'gateway', status: 'trusted', trust_score: 99, ip: '192.168.1.1' }
    ];

    const links = [
      { id: 'l1', source: 'ca-root', target: 'sdn-spine-1', bandwidth_gbps: 100, trust_weight: 1.0 },
      { id: 'l2', source: 'ca-root', target: 'sdn-spine-2', bandwidth_gbps: 100, trust_weight: 1.0 },
      { id: 'l3', source: 'sdn-spine-1', target: 'dpu-edge-01', bandwidth_gbps: 100, trust_weight: 0.96 },
      { id: 'l4', source: 'sdn-spine-2', target: 'dpu-edge-02', bandwidth_gbps: 100, trust_weight: 0.95 },
      { id: 'l5', source: 'dpu-edge-01', target: 'host-k8s', bandwidth_gbps: 200, trust_weight: 0.97 },
      { id: 'l6', source: 'dpu-edge-02', target: 'gw-border', bandwidth_gbps: 100, trust_weight: 0.98 }
    ];

    this.simulationState = {
      nodes,
      links,
      global_metrics: {
        network_health_index: 98.4,
        global_trust_index: 96.8,
        hardware_offload_ratio_pct: 88.5,
        crypto_verification_rate_pct: 99.9,
        dropped_untrusted_packets_sec: 10,
        avg_latency_ms: 0.34,
        total_packets_sec: 145000
      },
      flow_rules: [
        { rule_id: 'flow-1001', match_src_ip: '10.0.1.101', match_dst_ip: '10.0.2.201', protocol: 'RoCEv2', action: 'offload_dpu', packet_count: 540000, byte_count: 750000000 },
        { rule_id: 'flow-1002', match_src_ip: '10.0.1.102', match_dst_ip: '192.168.1.1', protocol: 'TCP', action: 'offload_dpu', packet_count: 310000, byte_count: 420000000 }
      ],
      recent_anomalies: [
        { timestamp: Date.now()/1000, target_node_id: 'dpu-edge-01', threat_type: 'INITIAL_BOOT_ATTEST', severity: 'LOW', description: 'TPM 2.0 PCR Quote verified against hardware gold image.' }
      ]
    };

    this.handleTelemetryPayload(this.simulationState);
    setTimeout(() => this.graph.runLayout('cose'), 300);
  }

  stepMockSimulation() {
    if (!this.simulationState) return;
    // Jitter metrics
    const metrics = this.simulationState.global_metrics;
    metrics.total_packets_sec = Math.round(145000 + (Math.random() - 0.5) * 8000);
    this.handleTelemetryPayload(this.simulationState);
  }

  handleTelemetryPayload(payload) {
    this.simulationState = payload;
    this.graph.updateTopology(payload.nodes, payload.links);
    this.dashboard.updateMetrics(payload.global_metrics);
    this.dashboard.updateCharts(payload.nodes, payload.global_metrics);
    this.dashboard.updateFlowRules(payload.flow_rules);
    this.dashboard.updateAnomalies(payload.recent_anomalies);

    // Refresh selected node in inspector if active
    if (this.selectedNode) {
      const refreshed = payload.nodes.find(n => n.id === this.selectedNode.id);
      if (refreshed) this.showNodeInspector(refreshed);
    }
  }

  sendAction(msgObj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msgObj));
    } else if (this.isOfflineMode) {
      // Offline local action handling
      const node = this.simulationState.nodes.find(n => n.id === msgObj.node_id);
      if (node && msgObj.action === 'inject_tamper') {
        node.trust_score = 15;
        node.status = 'compromised';
        if (node.telemetry) {
          node.telemetry.attestation.pcr_quote_valid = false;
          node.telemetry.packet_tamper_events += 12;
        }
        this.simulationState.recent_anomalies.unshift({
          timestamp: Date.now() / 1000,
          target_node_id: node.id,
          threat_type: 'FIRMWARE_SIGNATURE_TAMPER',
          severity: 'CRITICAL',
          description: 'Offline Simulation: Injected simulated firmware tampering into DPU.'
        });
      } else if (node && msgObj.action === 'remediate') {
        node.trust_score = 96;
        node.status = 'trusted';
        if (node.telemetry) {
          node.telemetry.attestation.pcr_quote_valid = true;
          node.telemetry.packet_tamper_events = 0;
        }
        this.simulationState.recent_anomalies.unshift({
          timestamp: Date.now() / 1000,
          target_node_id: node.id,
          threat_type: 'REMEDIATION_COMPLETE',
          severity: 'LOW',
          description: 'Offline Simulation: Hardware Root of Trust re-established.'
        });
      }
      this.handleTelemetryPayload(this.simulationState);
    }
  }

  dispatchNodeAdded(newNode) {
    if (this.isOfflineMode) {
      this.simulationState.nodes.push(newNode);
      this.handleTelemetryPayload(this.simulationState);
    } else {
      this.sendAction({ action: 'add_node', node: newNode });
    }
  }

  dispatchLinkAdded(newLink) {
    if (this.isOfflineMode) {
      this.simulationState.links.push(newLink);
      this.handleTelemetryPayload(this.simulationState);
    } else {
      this.sendAction({ action: 'add_link', link: newLink });
    }
  }

  dispatchElementDeleted(id) {
    if (this.isOfflineMode) {
      this.simulationState.nodes = this.simulationState.nodes.filter(n => n.id !== id);
      this.simulationState.links = this.simulationState.links.filter(l => l.id !== id && l.source !== id && l.target !== id);
      this.handleTelemetryPayload(this.simulationState);
    } else {
      this.sendAction({ action: 'delete_element', id });
    }
  }
}

// Bootstrap
window.addEventListener('DOMContentLoaded', () => {
  new TrustNetApp();
});
