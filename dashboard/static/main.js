let responseTimeChart = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    fetchAndUpdateData();
    // Update data every 30 seconds
    setInterval(fetchAndUpdateData, 30000);
});

function initializeChart() {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');
    responseTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Response Time (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'URL Response Times'
                }
            }
        }
    });
}

function fetchAndUpdateData() {
    fetch('/api/monitoring-data')
        .then(response => response.json())
        .then(data => {
            updateChart(data);
            updateStatusTable(data);
        })
        .catch(error => {
            console.error('Error fetching monitoring data:', error);
        });
}

function updateChart(data) {
    const datasets = [];
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'
    ];

    data.urls.forEach((url, index) => {
        const urlData = data.data[url];
        datasets.push({
            label: urlData.name,
            data: urlData.response_times,
            borderColor: colors[index % colors.length],
            fill: false,
            tension: 0.1
        });
    });

    responseTimeChart.data.labels = data.data[data.urls[0]].timestamps.map(timestamp => 
        new Date(timestamp).toLocaleTimeString()
    );
    responseTimeChart.data.datasets = datasets;
    responseTimeChart.update();
}

function updateStatusTable(data) {
    const tableHtml = `
        <table class="table">
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Last Response Time</th>
                </tr>
            </thead>
            <tbody>
                ${data.urls.map(url => {
                    const urlData = data.data[url];
                    const lastIndex = urlData.status.length - 1;
                    const status = urlData.status[lastIndex];
                    const responseTime = urlData.response_times[lastIndex];
                    
                    return `
                        <tr>
                            <td>${urlData.name}</td>
                            <td>
                                <span class="status-indicator status-${status.toLowerCase()}"></span>
                                ${status}
                            </td>
                            <td>${responseTime ? responseTime.toFixed(2) + ' ms' : 'N/A'}</td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    document.getElementById('statusTable').innerHTML = tableHtml;
} 