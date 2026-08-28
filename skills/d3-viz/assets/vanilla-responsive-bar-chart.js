import * as d3 from "d3";

/**
 * Render a responsive bar chart into a container.
 * Returns an idempotent cleanup function. Adapt the data contract, labels,
 * styles, and dependency import to the target project.
 *
 * @param {HTMLElement} container
 * @param {{ id?: string, label: string, value: number }[]} data
 * @param {{ title?: string, description?: string }} options
 */
export function createResponsiveBarChart(container, data, options = {}) {
  if (!(container instanceof HTMLElement)) {
    throw new TypeError("container must be an HTMLElement");
  }
  if (!Array.isArray(data)) {
    throw new TypeError("data must be an array");
  }

  const cleanData = data.filter(
    (datum) =>
      typeof datum?.label === "string" &&
      Number.isFinite(datum?.value) &&
      datum.value >= 0,
  );

  const margin = { top: 20, right: 20, bottom: 48, left: 56 };
  const svg = d3
    .select(container)
    .append("svg")
    .attr("role", "img")
    .style("display", "block")
    .style("width", "100%")
    .style("height", "auto");

  svg.append("title").text(options.title ?? "Values by category");
  svg
    .append("desc")
    .text(options.description ?? "Bar chart comparing values across categories.");

  const root = svg.append("g");
  const xAxis = root.append("g").attr("aria-hidden", "true");
  const yAxis = root.append("g").attr("aria-hidden", "true");
  const marks = root.append("g");
  const emptyMessage = root
    .append("text")
    .attr("text-anchor", "middle")
    .text("No data available.");

  function render() {
    const width = Math.max(320, container.getBoundingClientRect().width || 0);
    const height = Math.max(280, Math.min(480, width * 0.55));
    const innerWidth = Math.max(0, width - margin.left - margin.right);
    const innerHeight = Math.max(0, height - margin.top - margin.bottom);

    svg.attr("viewBox", `0 0 ${width} ${height}`);
    root.attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(cleanData.map((datum) => datum.label))
      .range([0, innerWidth])
      .padding(0.2);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(cleanData, (datum) => datum.value) ?? 0])
      .nice()
      .range([innerHeight, 0]);

    xAxis
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x));
    yAxis.call(d3.axisLeft(y).ticks(Math.max(2, Math.floor(innerHeight / 48)), "~s"));

    marks
      .selectAll("rect")
      .data(cleanData, (datum, index) => datum.id ?? `${datum.label}-${index}`)
      .join("rect")
      .attr("x", (datum) => x(datum.label) ?? 0)
      .attr("y", (datum) => y(datum.value))
      .attr("width", x.bandwidth())
      .attr("height", (datum) => innerHeight - y(datum.value))
      .attr("fill", "var(--chart-accent, #2563eb)");

    emptyMessage
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight / 2)
      .style("display", cleanData.length ? "none" : null);
  }

  const observer = new ResizeObserver(render);
  observer.observe(container);
  render();

  let destroyed = false;
  return function destroy() {
    if (destroyed) return;
    destroyed = true;
    observer.disconnect();
    svg.selectAll("*").interrupt();
    svg.remove();
  };
}
