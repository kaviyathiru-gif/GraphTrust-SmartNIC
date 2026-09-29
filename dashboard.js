/**
 * Power BI Style Analytical Dashboard Controller.
 * Manages KPI tiles, Chart.js visuals, flow tables, and cross-filtering slicers.
 */

export class DashboardController {
  constructor(options = {}) {
    this.onFilterChange = options.onFilterChange || (() => {});
    this.typeFilter = 'all';
    this.minTrust = 0;

    this.chartTrustDist = null;
    this.chartTelemetry = null;
    this.telemetryHistory = {
      labels: [],
      throughput: [],
      cryptoLoad: []
    };

    this.initCharts();
    this.initSlicers();
  }

  initCharts() {
    // 1. Trust Distribution Bar Chart
    const ctxTrust = document.getElementById('chart-trust-distribution').getContext('2d');
    this.chartTrustDist = new Chart(ctxTrust, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Trust Score',
          data: [],
          backgroundColor: [],
          borderRadius: 4,
          borderWidth: 1,
          borderColor: '#1f293d'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af', font: { family: 'JetBrains Mono', size: 10 } }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#9ca3af', font: { size: 9 }, maxRotation: 45 }
          }
        }
      }
    });

    // 2. Real-Time Telemetry Stream Chart
    const ctxTelem = document.getElementById('chart-telemetry-stream').getContext('2d');
    this.chartTelemetry = new Chart(ctxTelem, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Offload Throughput (kpps)',
            data: [],
            borderColor: '#06b6d4',
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            yAxisID: 'y1',
            tension: 0.35,
            fill: true,
            pointRadius: 2
          },
          {
            label: 'HW Crypto Load (%)',
            data: [],
            borderColor: '#8b5cf6',
            backgroundColor: 'transparent',
            yAxisID: 'y2',
            tension: 0.35,
            borderDash: [4, 4],
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#cbd5e1', font: { size: 10 } }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 9 }, maxTicksLimit: 6 }
          },
          y1: {
            type: 'linear',
            position: 'left',
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#06b6d4', font: { family: 'JetBrains Mono', size: 9 } }
          },
          y2: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 100,
            grid: { display: false },
            ticks: { color: '#8b5cf6', font: { family: 'JetBrains Mono', size: 9 } }
          }
        }
      }
    });
  }

  initSlicers() {
    const buttons = document.querySelectorAll('#slicer-type-buttons .slicer-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.removeClass ? b.removeClass('active') : b.classList.remove('active'));
        btn.classList.add('active');
        this.typeFilter = btn.getAttribute('data-filter');
        this.emitFilterChange();
      });
    });

    const slider = document.getElementById('trust-threshold-slider');
    const sliderVal = document.getElementById('trust-slider-val');
    slider.addEventListener('input', (e) => {
      this.minTrust = Number(e.target.value);
      sliderVal.textContent = this.minTrust;
      this.emitFilterChange();
    });
  }

  emitFilterChange() {
    this.onFilterChange({
      type: this.typeFilter,
      minTrust: this.minTrust
    });
  }

  updateMetrics(metrics) {
    if (!metrics) return;

    // Header Quick Metrics
    document.getElementById('hdr-health').textContent = `${metrics.network_health_index}%`;
    document.getElementById('hdr-trust').textContent = metrics.global_trust_index;
    document.getElementById('hdr-offload').textContent = `${metrics.hardware_offload_ratio_pct}%`;

    // Power BI KPI Tiles
    document.getElementById('kpi-health').textContent = `${metrics.network_health_index}%`;
    document.getElementById('kpi-trust').textContent = metrics.global_trust_index;
    document.getElementById('kpi-offload').textContent = `${metrics.hardware_offload_ratio_pct}%`;
    document.getElementById('kpi-crypto').textContent = `${metrics.crypto_verification_rate_pct}%`;
    document.getElementById('kpi-drops').textContent = `${metrics.dropped_untrusted_packets_sec} pps`;
    document.getElementById('kpi-latency').textContent = `${metrics.avg_latency_ms} ms`;
  }

  updateCharts(nodes, metrics) {
    if (!nodes || !this.chartTrustDist) return;

    // 1. Update Trust Score Bar Chart
    const filteredNodes = nodes.filter(n => {
      const matchesType = (this.typeFilter === 'all' || n.type === this.typeFilter);
      const matchesTrust = n.trust_score >= this.minTrust;
      return matchesType && matchesTrust;
    });

    this.chartTrustDist.data.labels = filteredNodes.map(n => n.label.replace('Smart NIC ', '').replace('SDN ', ''));
    this.chartTrustDist.data.datasets[0].data = filteredNodes.map(n => n.trust_score);
    this.chartTrustDist.data.datasets[0].backgroundColor = filteredNodes.map(n => {
      if (n.trust_score >= 85) return '#10b981';
      if (n.trust_score >= 60) return '#f59e0b';
      return '#ef4444';
    });
    this.chartTrustDist.update('none');

    // 2. Update Live Telemetry Stream
    const now = new Date().toLocaleTimeString();
    const totalPpsK = Math.round((metrics.total_packets_sec || 0) / 1000);
    const avgCryptoLoad = Math.round(metrics.crypto_verification_rate_pct > 90 ? 38 + Math.random()*8 : 15);

    this.telemetryHistory.labels.push(now);
    this.telemetryHistory.throughput.push(totalPpsK);
    this.telemetryHistory.cryptoLoad.push(avgCryptoLoad);

    if (this.telemetryHistory.labels.length > 15) {
      this.telemetryHistory.labels.shift();
      this.telemetryHistory.throughput.shift();
      this.telemetryHistory.cryptoLoad.shift();
    }

    this.chartTelemetry.data.labels = this.telemetryHistory.labels;
    this.chartTelemetry.data.datasets[0].data = this.telemetryHistory.throughput;
    this.chartTelemetry.data.datasets[1].data = this.telemetryHistory.cryptoLoad;
    this.chartTelemetry.update('none');
  }

  updateFlowRules(flowRules) {
    const tbody = document.getElementById('flow-table-body');
    const countTag = document.getElementById('flow-count-tag');
    if (!tbody || !flowRules) return;

    countTag.textContent = `${flowRules.length} Rules Active`;
    tbody.innerHTML = '';

    flowRules.forEach(rule => {
      const tr = document.createElement('tr');
      const actionBadge = rule.action === 'isolate' 
        ? '<span class="text-danger">● ISOLATE</span>'
        : '<span class="text-cyan">⚡ HW_OFFLOAD</span>';

      tr.innerHTML = `
        <td>${rule.rule_id}</td>
        <td>${rule.match_src_ip}</td>
        <td>${rule.match_dst_ip}</td>
        <td>${rule.protocol}</td>
        <td>${actionBadge}</td>
        <td>${rule.packet_count.toLocaleString()}</td>
        <td>${(rule.byte_count / (1024 * 1024)).toFixed(1)} MB</td>
      `;
      tbody.appendChild(tr);
    });
  }

  updateAnomalies(anomalies) {
    const list = document.getElementById('anomaly-feed-list');
    if (!list || !anomalies) return;

    list.innerHTML = '';
    anomalies.forEach(evt => {
      const item = document.createElement('div');
      item.className = `feed-item sev-${evt.severity}`;
      const timeStr = new Date(evt.timestamp * 1000).toLocaleTimeString();
      item.innerHTML = `
        <div class="feed-item-top">
          <span>${evt.threat_type} [${evt.target_node_id}]</span>
          <span style="color: #6b7280">${timeStr}</span>
        </div>
        <div class="feed-item-desc">${evt.description}</div>
      `;
      list.appendChild(item);
    });
  }
}
