/**
 * Cytoscape.js Network Topology & Drag-and-Drop Controller.
 */

export class GraphController {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.onNodeSelected = options.onNodeSelected || (() => {});
    this.onNodeAdded = options.onNodeAdded || (() => {});
    this.onLinkAdded = options.onLinkAdded || (() => {});
    this.onElementDeleted = options.onElementDeleted || (() => {});

    this.linkMode = false;
    this.linkSourceNode = null;
    this.cy = null;

    this.initCytoscape();
    this.initDragAndDrop();
  }

  initCytoscape() {
    this.cy = window.cytoscape({
      container: this.container,
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        // Base Node Style
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-family': 'Plus Jakarta Sans, sans-serif',
            'font-size': '10px',
            'font-weight': 600,
            'color': '#cbd5e1',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-background-opacity': 0.85,
            'text-background-color': '#0f172a',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-border-opacity': 0.5,
            'text-border-width': 1,
            'text-border-color': '#1e293b',
            'transition-property': 'background-color, border-color, border-width, width, height',
            'transition-duration': '0.3s'
          }
        },
        // Node Types
        {
          selector: 'node[type = "smart_nic"]',
          style: {
            'shape': 'round-diamond',
            'width': 44,
            'height': 44,
            'background-color': '#0891b2',
            'border-width': 2,
            'border-color': '#06b6d4',
            'border-opacity': 0.8
          }
        },
        {
          selector: 'node[type = "sdn_switch"]',
          style: {
            'shape': 'round-hexagon',
            'width': 48,
            'height': 48,
            'background-color': '#7c3aed',
            'border-width': 2,
            'border-color': '#8b5cf6'
          }
        },
        {
          selector: 'node[type = "host_compute"]',
          style: {
            'shape': 'round-rectangle',
            'width': 40,
            'height': 40,
            'background-color': '#2563eb',
            'border-width': 2,
            'border-color': '#3b82f6'
          }
        },
        {
          selector: 'node[type = "gateway"]',
          style: {
            'shape': 'vee',
            'width': 42,
            'height': 42,
            'background-color': '#059669',
            'border-width': 2,
            'border-color': '#10b981'
          }
        },
        {
          selector: 'node[type = "attestation_authority"]',
          style: {
            'shape': 'star',
            'width': 50,
            'height': 50,
            'background-color': '#d97706',
            'border-width': 2,
            'border-color': '#f59e0b'
          }
        },
        // Security Statuses
        {
          selector: 'node[status = "suspicious"]',
          style: {
            'border-color': '#f59e0b',
            'border-width': 4,
            'border-opacity': 1.0
          }
        },
        {
          selector: 'node[status = "isolated"], node[status = "compromised"]',
          style: {
            'background-color': '#b91c1c',
            'border-color': '#ef4444',
            'border-width': 5,
            'border-opacity': 1.0
          }
        },
        // Selected Node
        {
          selector: 'node:selected',
          style: {
            'border-color': '#38bdf8',
            'border-width': 4,
            'shadow-blur': 15,
            'shadow-color': '#38bdf8',
            'shadow-opacity': 0.8
          }
        },
        // Filter Dimmed State
        {
          selector: 'node.dimmed',
          style: {
            'opacity': 0.18
          }
        },
        // Base Edge Style
        {
          selector: 'edge',
          style: {
            'width': 'mapData(bandwidth, 10, 400, 2, 6)',
            'line-color': '#334155',
            'target-arrow-shape': 'none',
            'curve-style': 'bezier',
            'opacity': 0.8,
            'transition-property': 'line-color, width, opacity',
            'transition-duration': '0.3s'
          }
        },
        // High Trust Edge (Hardware IPsec Active)
        {
          selector: 'edge[trust >= 0.85]',
          style: {
            'line-color': '#10b981'
          }
        },
        // Moderate Trust Edge
        {
          selector: 'edge[trust < 0.85][trust >= 0.65]',
          style: {
            'line-color': '#f59e0b'
          }
        },
        // Degraded Trust Edge
        {
          selector: 'edge[trust < 0.65]',
          style: {
            'line-color': '#ef4444',
            'line-style': 'dashed'
          }
        },
        {
          selector: 'edge.dimmed',
          style: {
            'opacity': 0.1
          }
        }
      ],
      elements: []
    });

    // Event Handlers
    this.cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      if (this.linkMode) {
        if (!this.linkSourceNode) {
          this.linkSourceNode = node.id();
          node.addClass('link-source');
        } else if (this.linkSourceNode !== node.id()) {
          this.onLinkAdded({
            id: `link-${Date.now()}`,
            source: this.linkSourceNode,
            target: node.id(),
            bandwidth_gbps: 100,
            latency_ms: 0.35,
            trust_weight: 0.95,
            ipsec_hw_offloaded: true,
            active_flows: 10
          });
          const srcEle = this.cy.getElementById(this.linkSourceNode);
          if (srcEle) srcEle.removeClass('link-source');
          this.linkSourceNode = null;
        }
      } else {
        this.onNodeSelected(node.data());
      }
    });

    this.cy.on('tap', (evt) => {
      if (evt.target === this.cy) {
        if (this.linkSourceNode) {
          const srcEle = this.cy.getElementById(this.linkSourceNode);
          if (srcEle) srcEle.removeClass('link-source');
          this.linkSourceNode = null;
        }
      }
    });
  }

  initDragAndDrop() {
    const paletteItems = document.querySelectorAll('.palette-item');
    paletteItems.forEach(item => {
      item.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', item.getAttribute('data-type'));
      });
    });

    this.container.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    });

    this.container.addEventListener('drop', (e) => {
      e.preventDefault();
      const nodeType = e.dataTransfer.getData('text/plain');
      if (!nodeType) return;

      const rect = this.container.getBoundingClientRect();
      const renderedPosition = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };
      const modelPos = this.cy.renderer().projectIntoViewport(renderedPosition.x, renderedPosition.y);

      const count = this.cy.nodes().length + 1;
      const typeLabels = {
        smart_nic: `Smart NIC DPU 0${count}`,
        sdn_switch: `SDN Switch 0${count}`,
        host_compute: `Compute Host 0${count}`,
        gateway: `Border GW 0${count}`
      };

      const newNode = {
        id: `node-${nodeType}-${Date.now().toString().slice(-4)}`,
        label: typeLabels[nodeType] || `Node ${count}`,
        type: nodeType,
        status: 'trusted',
        trust_score: 95.0,
        ip: `10.0.${Math.floor(count/10)}.${count % 254}`,
        role: nodeType.replace('_', ' ').toUpperCase(),
        x: modelPos[0],
        y: modelPos[1]
      };

      this.onNodeAdded(newNode);
    });
  }

  updateTopology(nodes, links) {
    if (!this.cy) return;

    const existingNodeIds = new Set(this.cy.nodes().map(n => n.id()));
    const existingEdgeIds = new Set(this.cy.edges().map(e => e.id()));

    const incomingNodeIds = new Set(nodes.map(n => n.id));
    const incomingEdgeIds = new Set(links.map(l => l.id));

    // Remove deleted elements
    this.cy.batch(() => {
      this.cy.nodes().forEach(n => {
        if (!incomingNodeIds.has(n.id())) this.cy.remove(n);
      });
      this.cy.edges().forEach(e => {
        if (!incomingEdgeIds.has(e.id())) this.cy.remove(e);
      });

      // Add or update nodes
      nodes.forEach(node => {
        const nodeData = {
          id: node.id,
          label: `${node.label}\n[${Math.round(node.trust_score)}]`,
          type: node.type,
          status: node.status,
          trust_score: node.trust_score,
          rawNode: node
        };

        if (existingNodeIds.has(node.id)) {
          const ele = this.cy.getElementById(node.id);
          ele.data(nodeData);
        } else {
          this.cy.add({
            group: 'nodes',
            data: nodeData,
            position: { x: node.x || 300, y: node.y || 300 }
          });
        }
      });

      // Add or update edges
      links.forEach(link => {
        const edgeData = {
          id: link.id,
          source: link.source,
          target: link.target,
          bandwidth: link.bandwidth_gbps,
          trust: link.trust_weight,
          rawLink: link
        };

        if (existingEdgeIds.has(link.id)) {
          this.cy.getElementById(link.id).data(edgeData);
        } else {
          if (this.cy.getElementById(link.source).length && this.cy.getElementById(link.target).length) {
            this.cy.add({
              group: 'edges',
              data: edgeData
            });
          }
        }
      });
    });
  }

  applyFilter(typeFilter, minTrust) {
    if (!this.cy) return;
    this.cy.batch(() => {
      this.cy.nodes().forEach(n => {
        const type = n.data('type');
        const trust = n.data('trust_score') || 0;
        const matchesType = (typeFilter === 'all' || type === typeFilter);
        const matchesTrust = trust >= minTrust;

        if (matchesType && matchesTrust) {
          n.removeClass('dimmed');
        } else {
          n.addClass('dimmed');
        }
      });

      this.cy.edges().forEach(e => {
        const src = this.cy.getElementById(e.data('source'));
        const dst = this.cy.getElementById(e.data('target'));
        if (src.hasClass('dimmed') || dst.hasClass('dimmed')) {
          e.addClass('dimmed');
        } else {
          e.removeClass('dimmed');
        }
      });
    });
  }

  runLayout(layoutName = 'cose') {
    if (!this.cy) return;
    const layout = this.cy.layout({
      name: layoutName,
      animate: true,
      animationDuration: 500,
      fit: true,
      padding: 40
    });
    layout.run();
  }

  fit() {
    if (this.cy) this.cy.fit(null, 30);
  }
}
