/**
 * RE-VERSE Frontend JavaScript
 * Handles API interactions and UI updates
 */

// API Base URL
const API_BASE = '/api/v1';

// DOM Elements
const checkHealthBtn = document.getElementById('checkHealthBtn');
const healthStatus = document.getElementById('healthStatus');

// Check API Health
async function checkHealth() {
    try {
        checkHealthBtn.disabled = true;
        checkHealthBtn.textContent = 'Checking...';
        
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            healthStatus.className = 'status-display success';
            healthStatus.innerHTML = `
                <strong>✅ System Healthy</strong><br>
                Database: ${data.database}<br>
                Timestamp: ${new Date(data.timestamp).toLocaleString()}
            `;
        } else {
            healthStatus.className = 'status-display error';
            healthStatus.innerHTML = `
                <strong>⚠️ System Unhealthy</strong><br>
                Database: ${data.database}
            `;
        }
    } catch (error) {
        healthStatus.className = 'status-display error';
        healthStatus.innerHTML = `
            <strong>❌ Connection Failed</strong><br>
            ${error.message}
        `;
    } finally {
        checkHealthBtn.disabled = false;
        checkHealthBtn.textContent = 'Check API Health';
    }
}

// Event Listeners
if (checkHealthBtn) {
    checkHealthBtn.addEventListener('click', checkHealth);
}

// Auto-check health on page load
window.addEventListener('load', () => {
    console.log('RE-VERSE Frontend Loaded');
    checkHealth();
});
