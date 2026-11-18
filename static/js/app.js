document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".counter").forEach((counter) => {
    const target = Number(counter.dataset.target || 0);
    const duration = 1100;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = target * (1 - Math.pow(1 - progress, 3));
      counter.textContent = target % 1 === 0 ? Math.round(value) : value.toFixed(1);
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  });

  if (!window.Chart || !window.PushpaRecycleCharts) return;

  const chartColors = ["#1f7a4d", "#f4a62a", "#c94d64", "#4f8fbf", "#7c6f58", "#15583a"];
  const makeBar = (id, labels, values, label) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label, data: values, backgroundColor: chartColors, borderRadius: 6 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: "#eee7dc" } }, x: { grid: { display: false } } }
      }
    });
  };

  const monthly = window.PushpaRecycleCharts.monthly || [];
  makeBar(
    "monthlyChart",
    monthly.map((item) => item.month ? new Date(item.month).toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "Month"),
    monthly.map((item) => Number(item.total || 0)),
    "Kg collected"
  );

  const temples = window.PushpaRecycleCharts.temple || [];
  makeBar("templeChart", temples.map((item) => item.temple__name || "Temple"), temples.map((item) => Number(item.total || 0)), "Kg");

  const flowers = window.PushpaRecycleCharts.flower || [];
  makeBar("flowerChart", flowers.map((item) => item.flower__name || "Flower"), flowers.map((item) => Number(item.total || 0)), "Kg");
});
