const API_BASE = 'http://127.0.0.1:8000';

function addLog(message, type = 'info', data = null) {
    const container = document.getElementById('logs-container');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const time = new Date().toLocaleTimeString();
    
    let html = `<strong>[${time}]</strong> ${message}`;
    if (data) {
        html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
    
    entry.innerHTML = html;
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

function clearLogs() {
    document.getElementById('logs-container').innerHTML = '';
    addLog('Logs cleared.', 'system-msg');
}

// Create Enquiry
document.getElementById('create-enquiry-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const payload = {
        channel: document.getElementById('channel').value,
        customer_name: document.getElementById('customer_name').value,
        message: document.getElementById('message').value
    };
    
    try {
        const btn = e.target.querySelector('button');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
        btn.disabled = true;

        const res = await fetch(`${API_BASE}/enquiry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        if (res.ok) {
            addLog('Enquiry Created successfully.', 'success', data);
            document.getElementById('target_id').value = data.job_id; // auto-fill for testing
            e.target.reset();
        } else {
            addLog('Failed to create enquiry.', 'error', data);
        }
    } catch (err) {
        addLog(`Network error: ${err.message}`, 'error');
    } finally {
        const btn = e.target.querySelector('button');
        btn.innerHTML = '<span>Submit Enquiry</span> <i class="fa-solid fa-paper-plane"></i>';
        btn.disabled = false;
    }
});

// Fetch History
document.getElementById('btn-fetch').addEventListener('click', async () => {
    const id = document.getElementById('target_id').value.trim();
    if (!id) return addLog('Please enter an Enquiry ID to fetch.', 'error');
    
    try {
        const res = await fetch(`${API_BASE}/enquiry/${id}/history`);
        const data = await res.json();
        
        if (res.ok) {
            addLog(`Fetched history for ${id}`, 'success', data);
        } else {
            addLog(`Failed to fetch history for ${id}`, 'error', data);
        }
    } catch (err) {
        addLog(`Network error: ${err.message}`, 'error');
    }
});

// Modal logic
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Escalate
async function submitEscalation() {
    const id = document.getElementById('target_id').value.trim();
    if (!id) {
        closeModal('escalate-modal');
        return addLog('Please enter a Target Enquiry ID first.', 'error');
    }
    
    const reason = document.getElementById('escalate_reason').value;
    
    try {
        const res = await fetch(`${API_BASE}/enquiry/${id}/escalate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason || 'Manual escalation' })
        });
        
        const data = await res.json();
        if (res.ok) {
            addLog(`Enquiry ${id} escalated.`, 'success', data);
        } else {
            addLog(`Escalation failed for ${id}.`, 'error', data);
        }
    } catch (err) {
        addLog(`Network error: ${err.message}`, 'error');
    } finally {
        closeModal('escalate-modal');
        document.getElementById('escalate_reason').value = '';
    }
}

// Follow Up
async function submitFollowUp() {
    const id = document.getElementById('target_id').value.trim();
    if (!id) {
        closeModal('followup-modal');
        return addLog('Please enter a Target Enquiry ID first.', 'error');
    }
    
    const delay = parseInt(document.getElementById('delay_minutes').value) || 5;
    const msg = document.getElementById('message_template').value;
    
    try {
        const res = await fetch(`${API_BASE}/enquiry/${id}/followup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delay_minutes: delay, message_template: msg })
        });
        
        const data = await res.json();
        if (res.ok) {
            addLog(`Follow-up scheduled for ${id}.`, 'success', data);
        } else {
            addLog(`Follow-up scheduling failed for ${id}.`, 'error', data);
        }
    } catch (err) {
        addLog(`Network error: ${err.message}`, 'error');
    } finally {
        closeModal('followup-modal');
        document.getElementById('message_template').value = '';
    }
}
