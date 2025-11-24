// API Configuration
const API_BASE = '/api/v1';
const POLL_INTERVAL = 2000; // 2 seconds

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const uploadSection = document.getElementById('uploadSection');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

const pdfFileInput = document.getElementById('pdfFile');
const fileName = document.getElementById('fileName');
const promptInput = document.getElementById('prompt');
const charCount = document.querySelector('.char-count');

const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const jobIdDisplay = document.getElementById('jobIdDisplay');

const audioPlayer = document.getElementById('audioPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const errorMessage = document.getElementById('errorMessage');

// State
let currentJobId = null;
let pollInterval = null;

// File Upload Handler
pdfFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    }
});

// Character Counter
promptInput.addEventListener('input', (e) => {
    const length = e.target.value.length;
    charCount.textContent = `${length} / 2000`;
    
    if (length > 1900) {
        charCount.style.color = 'var(--error)';
    } else {
        charCount.style.color = 'var(--text-light)';
    }
});

// Form Submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(uploadForm);
    
    try {
        showSection('progress');
        updateProgress(10, 'Uploading PDF...');
        
        const response = await fetch(`${API_BASE}/generate-job`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.status === 202) {
            currentJobId = data.job_id;
            saveJobToHistory(data.job_id);
            jobIdDisplay.textContent = currentJobId;
            startPolling();
        } else {
            throw new Error(data.detail || 'Job creation failed');
        }
        
    } catch (error) {
        showError(error.message);
    }
});

// Polling Function
function startPolling() {
    updateProgress(20, 'Processing PDF...');
    activateStep(1);
    
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/job/${currentJobId}`);
            const job = await response.json();
            
            handleJobStatus(job);
            
        } catch (error) {
            clearInterval(pollInterval);
            showError('Failed to check job status');
        }
    }, POLL_INTERVAL);
}

// Job Status Handler
function handleJobStatus(job) {
    const status = job.status;
    
    switch(status) {
        case 'PENDING':
            updateProgress(25, 'Waiting in queue...');
            break;
            
        case 'PROCESSING':
            const progressValue = estimateProgress(job.created_at);
            updateProgress(progressValue, getProcessingMessage(progressValue));
            updateStepsBasedOnProgress(progressValue);
            break;
            
        case 'COMPLETED':
            clearInterval(pollInterval);
            completeStep(4);
            updateProgress(100, 'Complete!');
            showResult(job);
            break;
            
        case 'FAILED':
            clearInterval(pollInterval);
            showError(job.error_message || 'Generation failed');
            break;
    }
}

// Progress Estimation
function estimateProgress(createdAt) {
    const elapsed = Date.now() - new Date(createdAt).getTime();
    const estimatedTotal = 45000; // 45 seconds average
    const progress = Math.min((elapsed / estimatedTotal) * 70 + 25, 95);
    return Math.round(progress);
}

// Processing Messages
function getProcessingMessage(progress) {
    if (progress < 40) return 'Extracting text from PDF...';
    if (progress < 60) return 'Generating script with AI...';
    if (progress < 80) return 'Creating multi-speaker audio...';
    return 'Uploading to cloud storage...';
}

// Step Management
function updateStepsBasedOnProgress(progress) {
    if (progress >= 30) activateStep(1);
    if (progress >= 45) { completeStep(1); activateStep(2); }
    if (progress >= 65) { completeStep(2); activateStep(3); }
    if (progress >= 85) { completeStep(3); activateStep(4); }
}

function activateStep(stepNum) {
    const step = document.getElementById(`step${stepNum}`);
    if (step) step.classList.add('active');
}

function completeStep(stepNum) {
    const step = document.getElementById(`step${stepNum}`);
    if (step) {
        step.classList.remove('active');
        step.classList.add('completed');
    }
}

// UI Updates
function updateProgress(percent, message) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = message;
}

function showSection(section) {
    uploadSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    document.getElementById(`${section}Section`).style.display = 'block';
}

function showResult(job) {
    audioPlayer.src = job.audio_url;
    downloadBtn.href = job.audio_url;
    
    document.getElementById('resultFilename').textContent = job.pdf_filename;
    document.getElementById('resultStyle').textContent = job.style;
    document.getElementById('resultDuration').textContent = job.duration;
    document.getElementById('resultCreated').textContent = formatDate(job.created_at);
    
    showSection('result');
}

function showError(message) {
    errorMessage.textContent = message;
    showSection('error');
}

function resetForm() {
    uploadForm.reset();
    fileName.textContent = 'Choose PDF file (max 50MB)';
    charCount.textContent = '0 / 2000';
    currentJobId = null;
    showSection('upload');
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

// ========== History Management ==========

function saveJobToHistory(jobId) {
    let history = JSON.parse(localStorage.getItem('jobHistory') || '[]');
    if (!history.includes(jobId)) {
        history.unshift(jobId);
        if (history.length > 20) history = history.slice(0, 20);
        localStorage.setItem('jobHistory', JSON.stringify(history));
        loadHistory();
    }
}

async function loadHistory() {
    const history = JSON.parse(localStorage.getItem('jobHistory') || '[]');
    const historyList = document.getElementById('historyList');
    
    if (history.length === 0) {
        historyList.innerHTML = '<p class="empty-history">No podcasts yet</p>';
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/history?job_ids=${history.join(',')}`);
        const data = await response.json();
        
        historyList.innerHTML = data.jobs.map(job => `
            <div class="history-item" onclick="loadPodcast('${job.audio_url}', '${job.status}')">
                <div class="history-item-title">${job.title}</div>
                <div class="history-item-date">${formatDate(job.created_at)}</div>
                <span class="history-item-status ${job.status.toLowerCase()}">${job.status}</span>
            </div>
        `).join('');
    } catch (e) {
        historyList.innerHTML = '<p class="empty-history">Failed to load</p>';
    }
}

function loadPodcast(audioUrl, status) {
    if (status === 'COMPLETED' && audioUrl) {
        document.getElementById('audioPlayer').src = audioUrl;
        document.getElementById('resultSection').style.display = 'block';
    } else {
        alert('Podcast not ready');
    }
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const hours = Math.floor((Date.now() - new Date(dateString)) / 3600000);
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (hours < 48) return 'Yesterday';
    return new Date(dateString).toLocaleDateString();
}

document.getElementById('clearHistoryBtn').addEventListener('click', () => {
    if (confirm('Clear history?')) {
        localStorage.removeItem('jobHistory');
        loadHistory();
    }
});

// Call after job creation - add this line where you get job_id
// saveJobToHistory(job_id);

// Load on startup
window.addEventListener('DOMContentLoaded', loadHistory);
