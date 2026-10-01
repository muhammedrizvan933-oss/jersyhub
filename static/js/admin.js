// JerseyHub - Admin Dashboard Scripts

document.addEventListener('DOMContentLoaded', () => {
  initAdminSalesChart();
  initInventoryInlineUpdate();
});

function initAdminSalesChart() {
  const chartCanvas = document.getElementById('adminSalesChart');
  if (!chartCanvas) return;

  fetch('/api/admin/sales-chart')
    .then(res => res.json())
    .then(data => {
      const ctx = chartCanvas.getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.labels && data.labels.length > 0 ? data.labels : ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
          datasets: [{
            label: 'Sales Revenue (₹)',
            data: data.revenue && data.revenue.length > 0 ? data.revenue : [120, 240, 180, 310, 450],
            borderColor: '#00e676',
            backgroundColor: 'rgba(0, 230, 118, 0.12)',
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#00e676',
            pointRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: '#94a3b8' }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#94a3b8' }
            },
            y: {
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: {
                color: '#94a3b8',
                callback: function(val) { return '₹' + val; }
              }
            }
          }
        }
      });
    })
    .catch(err => console.error('Sales chart load error:', err));
}

function initInventoryInlineUpdate() {
  const stockForms = document.querySelectorAll('.inventory-stock-form');
  stockForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const submitBtn = form.querySelector('button[type="submit"]');

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(res => res.json())
      .then(data => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-check2"></i>';
        submitBtn.classList.remove('btn-outline-primary');
        submitBtn.classList.add('btn-success');
        setTimeout(() => {
          submitBtn.innerHTML = '<i class="bi bi-save"></i>';
          submitBtn.classList.remove('btn-success');
          submitBtn.classList.add('btn-outline-primary');
        }, 1500);
      })
      .catch(() => {
        form.submit();
      });
    });
  });
}
