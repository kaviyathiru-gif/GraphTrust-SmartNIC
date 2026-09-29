# TrustNet-SDN: Dynamic Graph Trust Networks with Smart NICs & SDN

[![CI Pipeline](https://github.com/trustnet-sdn/trustnet-sdn-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/trustnet-sdn/trustnet-sdn-platform/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Cytoscape.js](https://img.shields.io/badge/Cytoscape.js-3.28-brightgreen.svg)](https://js.cytoscape.org/)
[![Power BI Style](https://img.shields.io/badge/Dashboard-Power%20BI%20Style-F2C811.svg)](#power-bi-style-analytical-dashboard)

A full-stack, enterprise-grade cloud networking and security platform that integrates **Dynamic Graph Trust Networks**, **Data Processing Units (Smart NICs/DPUs)**, and **Software-Defined Networking (SDN)**. 

TrustNet-SDN models real-time cryptographic hardware attestation, kernel-bypass packet offload (eBPF/XDP/P4), and automated zero-trust quarantine policies across distributed network topologies.

---

## 🏛 System Architecture

```
                      +------------------------------------------+
                      |   Attestation Authority / Root of Trust  |
                      |          (TPM 2.0 / PCR Quotes)          |
                      +--------------------+---------------------+
                                           |
                   Attestation Verification & Dynamic Trust Scoring
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                           TrustNet SDN Controller Core                            |
|  - Dynamic Graph Trust Engine (EigenTrust / PageRank graph propagation)           |
|  - Trust-Weighted Dijkstra Optimal Path Calculation (High-Trust Low-Latency)      |
|  - Autonomous Zero-Trust Quarantine & Micro-segmentation State Machine            |
+------------------------------------------+----------------------------------------+
                                           |
                     OpenFlow / P4 Flow Table Push & Telemetry Pull
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|               Hardware Data Plane: Smart NIC / DPU Infrastructure                 |
|  - NVIDIA BlueField-3 / AMD Pensando DPU emulation                                |
|  - Hardware Root-of-Trust (RoT) & Secure Boot verification                        |
|  - Hardware IPsec/WireGuard Crypto Engine Offload & Kernel Bypass                 |
|  - Real-time P4 Flow Counters & Anomaly Detection Hooks                           |
+------------------------------------------+----------------------------------------+
                                           |
                               WebSocket Stream (1Hz)
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                       Frontend Web Application Interface                          |
|  [ Interactive Topology (Cytoscape.js) ] <---> [ Power BI Analytical Dashboard ] |
|  - Drag-and-drop node provisioning             - Real-time KPI tiles (Health,    |
|  - Dynamic edge trust rendering                  EigenTrust, Offload %, Crypto)  |
|  - Interactive hardware inspector              - Throughput vs Crypto Stream     |
|  - Threat injection & remediation triggers     - SDN OpenFlow table inspector    |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Key Features

### 1. Interactive Drag-and-Drop Topology Canvas (Cytoscape.js)
- **Visual Hardware Representation**: Nodes render with distinct geometric profiles and glowing status indicators for Smart NIC DPUs, SDN Core Switches, Compute Hosts, Border Gateways, and Attestation Authorities.
- **Drag-and-Drop Provisioning**: Drag components directly from the palette to instantiate new Smart NICs or hosts.
- **Dynamic Trust Edges**: Edges dynamically adjust width and color based on real-time bandwidth and cryptographic trust ($T \ge 0.85$ Emerald Green, $0.65 \le T < 0.85$ Amber, $T < 0.65$ Dashed Red).
- **Interactive Inspector**: Inspect real-time DPU CPU load, temperature, tamper counters, TPM PCR quote validity, and trigger simulated hardware attacks.

### 2. Offline Hardware Simulator
- **Device Emulation**: Simulates PCIe Smart NIC registers, ARM processing cores, hardware crypto accelerators, and TPM 2.0 PCR measured boot state.
- **Threat Vector Injection**:
  - `inject_tamper`: Injects firmware modifications into DPU flash memory, invalidating TPM quotes and lowering trust.
  - `inject_flood`: Simulates high-rate volumetric DDoS exceeding P4 hardware ingress thresholds.
  - `remediate`: Triggers remote cryptographically signed firmware re-flashing and re-attestation.
- **Zero-Dependency Fallback**: The frontend includes a standalone client-side simulator mode so the entire UI can run offline directly in the browser even without a backend.

### 3. Software-Defined Networking (SDN) Controller
- **Trust-Aware Dijkstra Routing**: Routes data exclusively through paths satisfying minimum hardware trust guarantees.
- **Autonomous Micro-Segmentation**: If a Smart NIC's trust score drops below the quarantine threshold ($T < 40.0$), the controller automatically installs `ISOLATE` flow rules across adjacent switches and reroutes flows.

### 4. Power BI Style Analytical Dashboard
- **Executive KPI Cards**: Real-time tiles for Network Health Index, EigenTrust Index, Hardware Offload Ratio, Cryptographic Integrity, Dropped Untrusted Packets, and Mean Latency.
- **Dynamic Cross-Filtering Slicers**: Filter the visual graph and distribution charts by node category (`Smart NIC`, `Switch`, `Host`, `Gateway`) or slider-based minimum trust score.
- **Live Stream Visuals**: Multi-axis real-time line charts tracking offload throughput (kpps) vs hardware crypto load (%).
- **SDN Flow Table Matrix**: Live inspection of active OpenFlow/P4 flow match criteria, action badges (`HW_OFFLOAD`, `ISOLATE`), and byte volume.
- **Live Security Audit Feed**: Color-coded security logs for anomaly detection and mitigation tracking.

---

## 📁 Repository Structure

```
trustnet-sdn-platform/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI test and lint pipeline
├── backend/
│   ├── Dockerfile               # Production container definition for backend
│   ├── requirements.txt         # Python dependencies (FastAPI, uvicorn, etc.)
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI server, REST routes & WebSocket telemetry
│       ├── models.py            # Pydantic schemas for nodes, links, telemetry
│       ├── trust_engine.py      # Multi-factor trust computation & EigenTrust
│       ├── sdn_controller.py    # Topology graph routing & Zero-Trust quarantine
│       └── graph_engine.py      # Pure-Python Dijkstra & PageRank algorithms
├── simulator/
│   ├── __init__.py
│   ├── smart_nic_simulator.py   # DPU hardware registers, TPM & crypto simulation
│   └── traffic_generator.py     # Flow telemetry and security anomaly logger
├── frontend/
│   ├── index.html               # Main single-page web application
│   ├── package.json             # Optional frontend tooling (Vite / npm)
│   └── src/
│       ├── app.js               # Application coordinator & WS / offline lifecycle
│       ├── graph.js             # Cytoscape.js drag-and-drop graph canvas
│       ├── dashboard.js         # Power BI dashboard, KPI cards, Chart.js visuals
│       └── styles.css           # Dark cybersecurity theme & Power BI UI system
├── scripts/
│   ├── seed_topology.json       # Initial 9-node enterprise network fixture
│   └── run_demo.sh              # One-command quickstart script
├── tests/
│   ├── __init__.py
│   ├── test_smart_nic.py        # Smart NIC hardware state & telemetry tests
│   ├── test_trust_engine.py     # Local scoring & graph propagation tests
│   └── test_sdn_controller.py   # Trust routing & quarantine isolation tests
├── docker-compose.yml           # Multi-container orchestration (FastAPI + NGINX)
├── Makefile                     # Build, run, test, and container shortcuts
├── LICENSE                      # MIT Open Source License
└── README.md                    # Comprehensive technical documentation
```

---

## ⚡ Quickstart Guide

### Option 1: Native Local Run

1. **Clone the repository**:
   ```bash
   git clone https://github.com/trustnet-sdn/trustnet-sdn-platform.git
   cd trustnet-sdn-platform
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Launch the platform**:
   ```bash
   chmod +x scripts/run_demo.sh
   ./scripts/run_demo.sh
   ```
   * The web application is served at: `http://localhost:8000`
   * The WebSocket telemetry stream runs at: `ws://localhost:8000/ws/telemetry`
   * The interactive REST API docs are available at: `http://localhost:8000/docs`

---

### Option 2: Docker Compose

Launch the full stack with zero manual dependencies:
```bash
docker-compose up --build -d
```
- Open `http://localhost:3000` for the frontend.
- Backend API and WebSocket runs at `http://localhost:8000`.

---

### Option 3: Instant Standalone Offline Mode (Zero Setup)

Double click or serve `frontend/index.html` in any modern web browser:
```bash
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000`. The frontend will detect that the WebSocket server is offline and automatically engage the built-in **Offline Hardware Simulator**, providing a fully interactive drag-and-drop experience, live telemetry animations, and attack simulations right in the browser!

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
python3 -m unittest discover tests -v
```
All unit tests verify:
- Hardware state machines, TPM PCR validation, and remediation
- Multidimensional trust scoring and EigenTrust graph ranking
- SDN trust-weighted shortest path calculations and automated zero-trust quarantine isolation

---

## 📐 Mathematical Trust Formulation

The dynamic trust score $T_i \in [0, 100]$ of each network node $i$ is calculated using a composite model:

$$T_i = \alpha \cdot H_{\text{attest}}(i) + \beta \cdot F_{\text{offload}}(i) + \gamma \cdot (100 - P_{\text{anomaly}}(i))$$

Where:
- $H_{\text{attest}} \in \{0, 100\}$ reflects cryptographic hardware root-of-trust (TPM 2.0 PCR quotes and measured secure boot).
- $F_{\text{offload}} \in [0, 100]$ evaluates kernel-bypass ratio and hardware crypto coprocessor health.
- $P_{\text{anomaly}} \in [0, 100]$ applies penalty discounts based on detected flow tampering or flood events.
- $\alpha = 0.45$, $\beta = 0.25$, and $\gamma = 0.30$.

The topology-wide trust distribution is propagated using an **EigenTrust Power-Iteration** anchored to designated Root Attestation Authorities (CAs):

$$\mathbf{r}^{(k+1)} = (1 - d) \mathbf{p} + d \mathbf{W}^T \mathbf{r}^{(k)}$$

Where $\mathbf{W}$ is the normalized trust-weighted stochastic matrix of the physical network graph and $\mathbf{p}$ is the cryptographic authority personalization vector.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for additional P4 match-action pipelines, DPDK acceleration bindings, or new visualization themes.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
