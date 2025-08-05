/**
 * Charts.js - Enhanced visualization library for Quiz Master
 * Part of Phase 3 enhancements to improve data visualization
 */

class QuizMasterCharts {
    /**
     * Initialize the charts library
     */
    constructor() {
        this.chartColors = {
            primary: 'rgba(0, 123, 255, 0.7)',
            primaryBorder: 'rgba(0, 123, 255, 1)',
            success: 'rgba(40, 167, 69, 0.7)',
            successBorder: 'rgba(40, 167, 69, 1)',
            danger: 'rgba(220, 53, 69, 0.7)',
            dangerBorder: 'rgba(220, 53, 69, 1)',
            warning: 'rgba(255, 193, 7, 0.7)',
            warningBorder: 'rgba(255, 193, 7, 1)',
            info: 'rgba(23, 162, 184, 0.7)',
            infoBorder: 'rgba(23, 162, 184, 1)',
            secondary: 'rgba(108, 117, 125, 0.7)',
            secondaryBorder: 'rgba(108, 117, 125, 1)',
        };
        
        this.chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        boxWidth: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    padding: 10,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    displayColors: true,
                    caretSize: 5
                }
            }
        };
    }

    /**
     * Create a bar chart
     * @param {string} elementId - ID of the canvas element
     * @param {Array} labels - Labels for the x-axis
     * @param {Array} data - Data values
     * @param {string} label - Dataset label
     * @param {Object} options - Additional options
     */
    createBarChart(elementId, labels, data, label, options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        
        const chartOptions = {
            ...this.chartOptions,
            scales: {
                y: { 
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: options.backgroundColor || this.chartColors.primary,
                    borderColor: options.borderColor || this.chartColors.primaryBorder,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: chartOptions
        });
    }

    /**
     * Create a line chart
     * @param {string} elementId - ID of the canvas element
     * @param {Array} labels - Labels for the x-axis
     * @param {Array} data - Data values
     * @param {string} label - Dataset label
     * @param {Object} options - Additional options
     */
    createLineChart(elementId, labels, data, label, options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        
        const chartOptions = {
            ...this.chartOptions,
            scales: {
                y: { 
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: options.backgroundColor || 'rgba(40, 167, 69, 0.1)',
                    borderColor: options.borderColor || this.chartColors.successBorder,
                    borderWidth: 2,
                    pointBackgroundColor: options.pointColor || this.chartColors.successBorder,
                    tension: 0.4,
                    fill: options.fill !== undefined ? options.fill : true
                }]
            },
            options: chartOptions
        });
    }

    /**
     * Create a pie or doughnut chart
     * @param {string} elementId - ID of the canvas element
     * @param {Array} labels - Labels for segments
     * @param {Array} data - Data values
     * @param {string} type - 'pie' or 'doughnut'
     * @param {Object} options - Additional options
     */
    createPieChart(elementId, labels, data, type = 'pie', options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        
        // Generate a color array based on the number of data points
        const colors = this._generateColors(data.length);
        
        const chartOptions = {
            ...this.chartOptions,
            cutout: type === 'doughnut' ? '60%' : undefined,
            ...options
        };
        
        return new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: options.colors || colors,
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: chartOptions
        });
    }

    /**
     * Create a radar chart
     * @param {string} elementId - ID of the canvas element
     * @param {Array} labels - Labels for the axes
     * @param {Array} data - Data values
     * @param {string} label - Dataset label
     * @param {Object} options - Additional options
     */
    createRadarChart(elementId, labels, data, label, options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        
        const chartOptions = {
            ...this.chartOptions,
            scales: {
                r: {
                    beginAtZero: true,
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: options.maxScale || 100
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: options.backgroundColor || 'rgba(54, 162, 235, 0.2)',
                    borderColor: options.borderColor || 'rgba(54, 162, 235, 1)',
                    pointBackgroundColor: options.pointColor || 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                }]
            },
            options: chartOptions
        });
    }
    
    /**
     * Create a progress chart (horizontal bar)
     * @param {string} elementId - ID of the canvas element
     * @param {Array} labels - Labels for the y-axis
     * @param {Array} data - Data values
     * @param {Array} targets - Target values for comparison
     * @param {Object} options - Additional options
     */
    createProgressChart(elementId, labels, data, targets, options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        
        const chartOptions = {
            ...this.chartOptions,
            indexAxis: 'y',
            scales: {
                x: { 
                    beginAtZero: true,
                    max: options.maxScale || 100,
                    grid: {
                        drawBorder: false
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Current',
                        data: data,
                        backgroundColor: options.barColor || this.chartColors.info,
                        borderColor: options.barBorderColor || this.chartColors.infoBorder,
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Target',
                        data: targets,
                        backgroundColor: 'rgba(0, 0, 0, 0)', // Transparent
                        borderColor: options.targetColor || this.chartColors.warning,
                        borderWidth: 2,
                        borderDash: [5, 5],
                        type: 'line',
                        pointStyle: 'star',
                        pointRadius: 7
                    }
                ]
            },
            options: chartOptions
        });
    }

    /**
     * Generate an array of colors for charts
     * @param {number} count - Number of colors needed
     * @returns {Array} Array of colors
     * @private
     */
    _generateColors(count) {
        const baseColors = [
            'rgba(54, 162, 235, 0.7)', // blue
            'rgba(255, 99, 132, 0.7)',  // red
            'rgba(255, 205, 86, 0.7)',  // yellow
            'rgba(75, 192, 192, 0.7)',  // green
            'rgba(153, 102, 255, 0.7)', // purple
            'rgba(255, 159, 64, 0.7)',  // orange
            'rgba(201, 203, 207, 0.7)'  // grey
        ];
        
        if (count <= baseColors.length) {
            return baseColors.slice(0, count);
        }
        
        // If we need more colors, generate them by modifying the base colors
        const colors = [...baseColors];
        let currentLength = colors.length;
        
        while (currentLength < count) {
            // Create a new color by modifying opacity
            const baseIndex = currentLength % baseColors.length;
            const baseColor = baseColors[baseIndex];
            const newOpacity = 0.3 + Math.random() * 0.4; // Random opacity between 0.3 and 0.7
            const newColor = baseColor.replace(/[\d\.]+\)$/, `${newOpacity})`);
            colors.push(newColor);
            currentLength++;
        }
        
        return colors;
    }
    
    /**
     * Attach event handlers to make charts interactive
     * @param {Chart} chart - The Chart.js instance
     * @param {function} callback - Function to call when a chart element is clicked
     */
    attachClickHandlers(chart, callback) {
        if (!chart || !chart.canvas) return;
        
        chart.canvas.addEventListener('click', (event) => {
            const elements = chart.getElementsAtEventForMode(
                event, 
                'nearest', 
                { intersect: true }, 
                false
            );
            
            if (elements.length > 0) {
                const clickedElement = elements[0];
                const datasetIndex = clickedElement.datasetIndex;
                const index = clickedElement.index;
                
                const label = chart.data.labels[index];
                const value = chart.data.datasets[datasetIndex].data[index];
                
                if (typeof callback === 'function') {
                    callback(label, value, index, datasetIndex);
                }
            }
        });
    }
}

// Initialize the charts library when the page loads
window.QuizMasterCharts = new QuizMasterCharts();