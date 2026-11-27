document.addEventListener('DOMContentLoaded', function () {
    //pie chart --- treks vs regio/location
    const ctxPie = document.getElementById('locationPieChart').getContext('2d');
    new Chart(ctxPie, {
        type: 'pie',
        data: {
            labels: regionLabels, 
            datasets: [{
                data: regionCounts,
                backgroundColor: ['#099110', '#1B5E20', '#47c04b', '#81C784'], 
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Trek Distribution by Region' }
            }
        }
    });

    //grouped bar-chart----- total vs booked slots of each trek ---
    const ctxBar = document.getElementById('slotsBarChart').getContext('2d');
    new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: trekNames,
            datasets: [
                {
                    label: 'Total Slots',
                    data: total_slots_data,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)', 
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Available Slots',
                    data: available_slots_data,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)', 
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                title: { display: true, text: 'Capacity vs. Current Availability' }
            }
        }
    });
});