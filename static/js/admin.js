// Initialize Mermaid diagrams
document.addEventListener("DOMContentLoaded", function() {
    if (typeof mermaid !== "undefined") {
        mermaid.initialize({ startOnLoad: true });
    }

    // Safely get data from window object
    const classes = window.classes || [];
    const studentsCount = window.studentsCount || [];
    const courseTitles = window.courseTitles || [];
    const courseStudents = window.courseStudents || [];

    // Students by Class Chart (Bar)
    const classChartEl = document.getElementById('classChart');
    if (classChartEl) {
        new Chart(classChartEl.getContext('2d'), {
            type: 'bar',
            data: {
                labels: classes.length ? classes : ['No Data'],
                datasets: [{
                    label: 'Number of Students',
                    data: studentsCount.length ? studentsCount : [0],
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // Students per Course Chart (Pie)
    const courseChartEl = document.getElementById('courseChart');
    if (courseChartEl) {
        new Chart(courseChartEl.getContext('2d'), {
            type: 'pie',
            data: {
                labels: courseTitles.length ? courseTitles : ['No Courses'],
                datasets: [{
                    label: 'Students Enrolled',
                    data: courseStudents.length ? courseStudents : [0],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)'
                    ],
                    borderWidth: 1
                }]
            },
            options: { responsive: true }
        });
    }
});
