import { useEffect, useId, useMemo, useRef } from "react";
import * as d3 from "d3";

/**
 * Accessible React + D3 starter.
 * React owns the component structure; D3 owns only the contents of marksRef.
 * Adapt labels, types, styles, and the data contract to the target project.
 */
export function ResponsiveBarChart({
  data = [],
  width = 720,
  height = 400,
  title = "Values by category",
  description = "Bar chart comparing values across categories.",
  onSelect,
}) {
  const marksRef = useRef(null);
  const titleId = useId();
  const descriptionId = useId();

  const cleanData = useMemo(() => {
    if (!Array.isArray(data)) {
      throw new TypeError("data must be an array");
    }

    return data.filter(
      (datum) =>
        typeof datum?.label === "string" &&
        Number.isFinite(datum?.value) &&
        datum.value >= 0,
    );
  }, [data]);

  const margin = { top: 20, right: 20, bottom: 48, left: 56 };
  const innerWidth = Math.max(0, width - margin.left - margin.right);
  const innerHeight = Math.max(0, height - margin.top - margin.bottom);

  const x = useMemo(
    () =>
      d3
        .scaleBand()
        .domain(cleanData.map((datum) => datum.label))
        .range([0, innerWidth])
        .padding(0.2),
    [cleanData, innerWidth],
  );

  const y = useMemo(
    () =>
      d3
        .scaleLinear()
        .domain([0, d3.max(cleanData, (datum) => datum.value) ?? 0])
        .nice()
        .range([innerHeight, 0]),
    [cleanData, innerHeight],
  );

  useEffect(() => {
    const marks = d3.select(marksRef.current);

    marks
      .selectAll("rect")
      .data(cleanData, (datum, index) => datum.id ?? `${datum.label}-${index}`)
      .join(
        (enter) => enter.append("rect").attr("class", "bar"),
        (update) => update,
        (exit) => exit.remove(),
      )
      .attr("x", (datum) => x(datum.label) ?? 0)
      .attr("y", (datum) => y(datum.value))
      .attr("width", x.bandwidth())
      .attr("height", (datum) => innerHeight - y(datum.value))
      .attr("fill", "var(--chart-accent, #2563eb)")
      .attr("stroke", "none")
      .attr("tabindex", onSelect ? 0 : null)
      .attr("role", onSelect ? "button" : null)
      .attr(
        "aria-label",
        (datum) => `${datum.label}: ${d3.format(",")(datum.value)}`,
      )
      .on("click.chart", (_event, datum) => onSelect?.(datum))
      .on("focus.chart", function () {
        d3.select(this)
          .attr("stroke", "var(--chart-focus, currentColor)")
          .attr("stroke-width", 2);
      })
      .on("blur.chart", function () {
        d3.select(this).attr("stroke", "none");
      })
      .on("keydown.chart", (event, datum) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.(datum);
        }
      });

    return () => {
      marks.selectAll("*").interrupt();
      marks.selectAll("rect").on(".chart", null);
    };
  }, [cleanData, innerHeight, onSelect, x, y]);

  const xTicks = x.domain();
  const yTicks = y.ticks(Math.max(2, Math.floor(innerHeight / 48)));

  return (
    <figure style={{ margin: 0 }}>
      <svg
        role={onSelect ? "group" : "img"}
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", width: "100%", height: "auto" }}
      >
        <title id={titleId}>{title}</title>
        <desc id={descriptionId}>{description}</desc>
        <g transform={`translate(${margin.left},${margin.top})`}>
          <g aria-hidden="true" transform={`translate(0,${innerHeight})`}>
            {xTicks.map((tick) => (
              <g key={tick} transform={`translate(${(x(tick) ?? 0) + x.bandwidth() / 2},0)`}>
                <line y2="6" stroke="currentColor" />
                <text y="22" textAnchor="middle" fill="currentColor" fontSize="12">
                  {tick}
                </text>
              </g>
            ))}
          </g>
          <g aria-hidden="true">
            {yTicks.map((tick) => (
              <g key={tick} transform={`translate(0,${y(tick)})`}>
                <line x2={innerWidth} stroke="currentColor" strokeOpacity="0.12" />
                <text x="-8" dy="0.32em" textAnchor="end" fill="currentColor" fontSize="12">
                  {d3.format("~s")(tick)}
                </text>
              </g>
            ))}
          </g>
          <g ref={marksRef} />
        </g>
      </svg>
      {cleanData.length === 0 && <p>No data available.</p>}
    </figure>
  );
}
