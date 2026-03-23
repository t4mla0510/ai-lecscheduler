import { useEffect, useRef } from "react";
import * as d3 from "d3";

export interface GenStat {
  generation: number;
  best: number;
  avg: number;
  worst: number;
  elites: number;
  mutants: number;
  crossovers: number;
}

interface Props {
  history: GenStat[];
  generation: number;
  status: "idle" | "running" | "completed";
}

export function GAVisualizer({ history, generation, status }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const W = 520, H = 300;
  const m = { top: 24, right: 24, bottom: 44, left: 52 };
  const iW = W - m.left - m.right;
  const iH = H - m.top - m.bottom;

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    /* ── one-time scaffold ── */
    if (svg.select(".root-g").empty()) {
      const g = svg.append("g").attr("class", "root-g")
        .attr("transform", `translate(${m.left},${m.top})`);

      /* grid */
      g.append("g").attr("class", "grid-y");

      /* axes */
      g.append("g").attr("class", "x-axis").attr("transform", `translate(0,${iH})`);
      g.append("g").attr("class", "y-axis");

      /* axis labels */
      g.append("text").attr("class", "lbl-x")
        .attr("x", iW / 2).attr("y", iH + 36)
        .attr("text-anchor", "middle")
        .attr("font-size", 11).attr("fill", "var(--text-muted)")
        .text("Generation");
      g.append("text").attr("class", "lbl-y")
        .attr("transform", "rotate(-90)")
        .attr("x", -iH / 2).attr("y", -40)
        .attr("text-anchor", "middle")
        .attr("font-size", 11).attr("fill", "var(--text-muted)")
        .text("Fitness");

      /* line paths */
      g.append("path").attr("class", "line-worst").attr("fill", "none")
        .attr("stroke", "#94a3b8").attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "4 3").attr("opacity", 0.7);
      g.append("path").attr("class", "line-avg").attr("fill", "none")
        .attr("stroke", "#00afef").attr("stroke-width", 2);
      g.append("path").attr("class", "line-best").attr("fill", "none")
        .attr("stroke", "#1f5ca9").attr("stroke-width", 2.5);

      /* area under best */
      g.append("path").attr("class", "area-best")
        .attr("fill", "#1f5ca9").attr("opacity", 0.06);

      /* dots layer */
      g.append("g").attr("class", "dots");

      /* vertical cursor */
      g.append("line").attr("class", "cursor")
        .attr("y1", 0).attr("y2", iH)
        .attr("stroke", "var(--border-hover)").attr("stroke-width", 1)
        .attr("stroke-dasharray", "3 3").attr("opacity", 0);

      /* tooltip */
      const tip = svg.append("g").attr("class", "tip").attr("opacity", 0).attr("pointer-events", "none");
      tip.append("rect").attr("rx", 6).attr("fill", "#1e293b").attr("opacity", 0.92);
      tip.append("text").attr("class", "tip-text").attr("fill", "#f1f5f9").attr("font-size", 11).attr("font-family", "monospace");

      /* invisible overlay for hover */
      g.append("rect").attr("class", "overlay")
        .attr("width", iW).attr("height", iH)
        .attr("fill", "transparent")
        .attr("cursor", "crosshair");
    }

    if (history.length === 0) return;

    const g = svg.select<SVGGElement>(".root-g");

    /* ── scales ── */
    const xDom: [number, number] = [0, Math.max(history[history.length - 1].generation, 10)];
    const allVals = history.flatMap(d => [d.best, d.avg, d.worst]);
    const minVal = d3.min(allVals) as number;
    const maxVal = d3.max(allVals) as number;

    // Dynamic Y range with a bit of padding (allow negative for Lexicographic/Penalty)
    const diff = maxVal - minVal;
    const pad = diff === 0 ? 1 : diff * 0.1;
    const yMin = minVal - pad;
    const yMax = maxVal + pad;

    const x = d3.scaleLinear().domain(xDom).range([0, iW]);
    const y = d3.scaleLinear().domain([yMin, yMax]).range([iH, 0]);

    /* ── axes ── */
    const xAxis = d3.axisBottom(x).ticks(6).tickSize(0);
    const yAxis = d3.axisLeft(y).ticks(5).tickSize(0).tickFormat((v: any) => {
      const absV = Math.abs(v);
      if (absV >= 1000) return d3.format(".2s")(v);
      if (absV >= 1) return v.toFixed(1);
      return v.toFixed(3);
    });

    g.select<SVGGElement>(".x-axis").transition().duration(200)
      .call(xAxis as any)
      .call((a: any) => a.select(".domain").attr("stroke", "var(--border)"))
      .call((a: any) => a.selectAll("text").attr("fill", "var(--text-muted)").attr("font-size", 10));

    g.select<SVGGElement>(".y-axis").transition().duration(200)
      .call(yAxis as any)
      .call((a: any) => a.select(".domain").attr("stroke", "var(--border)"))
      .call((a: any) => a.selectAll("text").attr("fill", "var(--text-muted)").attr("font-size", 10));

    /* ── grid ── */
    g.select<SVGGElement>(".grid-y").transition().duration(200)
      .call(d3.axisLeft(y).ticks(5).tickSize(-iW).tickFormat(() => "") as any)
      .call((gr: any) => gr.select(".domain").remove())
      .call((gr: any) => gr.selectAll("line")
        .attr("stroke", "var(--border)").attr("stroke-dasharray", "3 3").attr("opacity", 0.5));

    /* ── line generators ── */
    const lineGen = (key: "best" | "avg" | "worst") =>
      d3.line<GenStat>().x(d => x(d.generation)).y(d => y(d[key])).curve(d3.curveCatmullRom);

    const areaGen = d3.area<GenStat>()
      .x(d => x(d.generation))
      .y0(iH).y1(d => y(d.best))
      .curve(d3.curveCatmullRom);

    g.select(".area-best").transition().duration(300).attr("d", areaGen(history) ?? "");
    g.select(".line-worst").transition().duration(300).attr("d", lineGen("worst")(history) ?? "");
    g.select(".line-avg").transition().duration(300).attr("d", lineGen("avg")(history) ?? "");
    g.select(".line-best").transition().duration(300).attr("d", lineGen("best")(history) ?? "");

    /* ── latest-point dot on best line ── */
    const last = history[history.length - 1];
    const dots = g.select(".dots").selectAll<SVGCircleElement, GenStat>("circle.live-dot")
      .data([last], () => "live");

    dots.enter().append("circle").attr("class", "live-dot")
      .attr("r", 0).attr("fill", "#1f5ca9")
      .merge(dots as any)
      .transition().duration(300)
      .attr("cx", x(last.generation)).attr("cy", y(last.best)).attr("r", 4);

    /* ── hover overlay ── */
    g.select(".overlay")
      .on("mousemove", function (event: MouseEvent) {
        const [mx] = d3.pointer(event, this);
        const gen = Math.round(x.invert(mx));
        const d = history.find(h => h.generation === gen) ?? history[history.length - 1];
        if (!d) return;

        const cx = x(d.generation);
        g.select(".cursor").attr("x1", cx).attr("x2", cx).attr("opacity", 1);

        const lines = [
          `gen  ${d.generation}`,
          `best ${d.best.toFixed(4)}`,
          `avg  ${d.avg.toFixed(4)}`,
          `wrst ${d.worst.toFixed(4)}`,
        ];
        const tip = svg.select(".tip");
        const txt = tip.select(".tip-text");
        txt.selectAll("tspan").remove();
        lines.forEach((l, i) => txt.append("tspan").attr("x", 8).attr("dy", i === 0 ? 14 : 14).text(l));
        const bw = 130, bh = lines.length * 14 + 10;
        tip.select("rect").attr("width", bw).attr("height", bh);
        const tx = Math.min(cx + m.left + 10, W - bw - 4);
        const ty = m.top + 4;
        tip.attr("transform", `translate(${tx},${ty})`).attr("opacity", 1);
      })
      .on("mouseleave", () => {
        g.select(".cursor").attr("opacity", 0);
        svg.select(".tip").attr("opacity", 0);
      });
  }, [history, iH, iW, m.bottom, m.left, m.right, m.top]);

  const phaseLabel =
    status === "running" ? `Gen ${generation} — evolving…` :
      status === "completed" ? `Completed · ${generation} generations` :
        "Idle — press Run GA";

  return (
    <div className="ga-viz-wrapper">
      <div className="ga-viz-header">
        <span className="ga-viz-title">Fitness over generations</span>
        <span className={`ga-viz-phase ${status}`}>{phaseLabel}</span>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: "auto", display: "block" }}
      />

      <div className="ga-viz-legend-row">
        <span className="leg-line" style={{ background: "#1f5ca9" }} />Best
        <span className="leg-line" style={{ background: "#00afef" }} />Average
        <span className="leg-line leg-dashed" style={{ background: "#94a3b8" }} />Worst
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
          hover to inspect
        </span>
      </div>
    </div>
  );
}
