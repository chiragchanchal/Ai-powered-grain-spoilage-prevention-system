/**
 * Interactive Canvas Visualizer for Climate-to-Spoilage Knowledge Graph.
 * Visualizes nodes: Region, ClimateEvent, SpoilageHazard, GrainType, and their active relationships.
 */

class KnowledgeGraphCanvas {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.nodes = [];
    this.edges = [];
    this.selectedNode = null;
    this.isDragging = false;
    this.draggedNode = null;
    this.activeHazards = [];

    this._initEvents();
  }

  setData(graphData, activeHazards = []) {
    this.activeHazards = activeHazards;
    const rawNodes = graphData.nodes || [];
    const rawEdges = graphData.edges || [];

    // Layout nodes neatly across 4 horizontal columns:
    // Col 1: Regions
    // Col 2: Climate Events
    // Col 3: Spoilage Hazards
    // Col 4: Grain Types
    const width = this.canvas.width;
    const height = this.canvas.height;

    const colX = {
      "Region": width * 0.12,
      "ClimateEvent": width * 0.38,
      "SpoilageType": width * 0.68,
      "GrainType": width * 0.90,
    };

    const countByLabel = {};
    rawNodes.forEach(n => {
      countByLabel[n.label] = (countByLabel[n.label] || 0) + 1;
    });

    const indexByLabel = {};
    this.nodes = rawNodes.map(n => {
      const idx = indexByLabel[n.label] || 0;
      indexByLabel[n.label] = idx + 1;
      const total = countByLabel[n.label] || 1;
      const stepY = height / (total + 1);
      const y = stepY * (idx + 1);
      const x = colX[n.label] || width * 0.5;

      return {
        ...n,
        x: x + (Math.random() * 20 - 10),
        y: y,
        radius: n.label === "SpoilageType" ? 22 : 18,
      };
    });

    // Map node id to index
    this.nodeMap = {};
    this.nodes.forEach(n => { this.nodeMap[n.id] = n; });

    this.edges = rawEdges.map(e => ({
      source: this.nodeMap[e.source],
      target: this.nodeMap[e.target],
      relation: e.relation,
      severity: e.severity,
      score: e.score,
    })).filter(e => e.source && e.target);

    this.render();
  }

  _initEvents() {
    this.canvas.addEventListener("mousedown", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
      const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);

      for (let n of this.nodes) {
        const dist = Math.hypot(n.x - x, n.y - y);
        if (dist <= n.radius + 5) {
          this.isDragging = true;
          this.draggedNode = n;
          this.selectedNode = n;
          this.showNodeInfo(n);
          this.render();
          return;
        }
      }
      this.selectedNode = null;
      this.render();
    });

    this.canvas.addEventListener("mousemove", (e) => {
      if (this.isDragging && this.draggedNode) {
        const rect = this.canvas.getBoundingClientRect();
        this.draggedNode.x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        this.draggedNode.y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        this.render();
      }
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
      this.draggedNode = null;
    });
  }

  showNodeInfo(node) {
    const infoBox = document.getElementById("kgNodeDetail");
    if (!infoBox) return;
    infoBox.innerHTML = `
      <div class="p-3 bg-slate-800/90 rounded-lg border border-slate-700 text-xs text-gray-200">
        <div class="flex items-center justify-between pb-1 border-b border-slate-700 mb-2">
          <span class="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">${node.label}</span>
          <span class="font-mono text-gray-400 text-[10px]">${node.id}</span>
        </div>
        <div class="font-semibold text-white text-sm mb-1">${node.name}</div>
        <p class="text-gray-300 leading-relaxed">${node.description || node.category || "Domain entity node"}</p>
      </div>
    `;
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 1. Draw Edges
    this.edges.forEach(e => {
      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.target.x, e.target.y);

      const isHigh = e.severity === "HIGH" || e.score > 0.75;
      ctx.strokeStyle = isHigh ? "rgba(239, 68, 68, 0.45)" : "rgba(100, 116, 139, 0.25)";
      ctx.lineWidth = isHigh ? 2.0 : 1.2;
      ctx.stroke();

      // Draw relationship arrow
      const angle = Math.atan2(e.target.y - e.source.y, e.target.x - e.source.x);
      const arrowX = e.target.x - Math.cos(angle) * (e.target.radius + 4);
      const arrowY = e.target.y - Math.sin(angle) * (e.target.radius + 4);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(arrowX - 7 * Math.cos(angle - Math.PI / 6), arrowY - 7 * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(arrowX - 7 * Math.cos(angle + Math.PI / 6), arrowY - 7 * Math.sin(angle + Math.PI / 6));
      ctx.closePath();
      ctx.fill();
    });

    // 2. Draw Nodes
    this.nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);

      let fillColor = "#3B82F6"; // Region
      if (n.label === "ClimateEvent") fillColor = "#F59E0B";
      if (n.label === "SpoilageType") fillColor = "#EF4444";
      if (n.label === "GrainType") fillColor = "#10B981";

      ctx.fillStyle = fillColor;
      ctx.fill();

      // Outer ring for selected
      if (this.selectedNode === n) {
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 3;
        ctx.stroke();
      } else {
        ctx.strokeStyle = "rgba(255,255,255,0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Node label text
      ctx.fillStyle = "#E2E8F0";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "center";
      const shortName = n.name.length > 14 ? n.name.slice(0, 12) + ".." : n.name;
      ctx.fillText(shortName, n.x, n.y + n.radius + 12);
    });
  }
}
