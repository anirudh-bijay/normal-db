let fds = [];
let candidate_keys = [];
let editingIndex = -1; // Track which FD is being edited

function addFD() {
    const leftInput = document.querySelector('.fd-left');
    const rightInput = document.querySelector('.fd-right');
    
    const left = leftInput.value.trim();
    const right = rightInput.value.trim();
    
    if (!left || !right) {
        showNotification('Please fill both left and right sides of FD', 'error');
        return;
    }
    
    if (editingIndex >= 0) {
        // Update existing FD
        fds[editingIndex] = { left, right };
        editingIndex = -1;
        leftInput.placeholder = 'A, B';
        rightInput.placeholder = 'C';
        document.querySelector('.btn-add-fd i').className = 'fas fa-plus';
        document.querySelector('.btn-add-fd').onclick = addFD;
    } else {
        // Add new FD
        fds.push({ left, right });
    }
    
    renderFDs();
    leftInput.value = '';
    rightInput.value = '';
    updateNormalizeButton();
}

function addCandidateKey(){
    const keyInput = document.querySelector(".key");
    const keyValue = keyInput.value.trim();

    if(!keyValue){
        showNotification("Please give the candidate keys", 'error');
        return;
    }

    candidate_keys.push(keyValue.split(",").map(key => key.trim()).filter(Boolean));
    renderKeys();
    keyInput.value = '';
    updateNormalizeButton();
}

function renderKeys(){
    const container = document.querySelector(".key-container");

    container.innerHTML = candidate_keys.map((key, index) => `
        <div class="key-tag" data-index="${index}">
            <span class="key-display">${key.join(', ')}</span>
            <button class="btn-remove-tag" onclick="removeKey(${index})" title="Delete Key">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeKey(index) {
    if (confirm(`Remove key: ${candidate_keys[index].join(', ')}?`)) {
        candidate_keys.splice(index, 1);
        renderKeys();
        updateNormalizeButton();
    }
}

function editFD(index) {
    const fd = fds[index];
    const leftInput = document.querySelector('.fd-left');
    const rightInput = document.querySelector('.fd-right');
    const addBtn = document.querySelector('.btn-add-fd');
    
    // Set editing state
    editingIndex = index;
    leftInput.value = fd.left;
    rightInput.value = fd.right;
    leftInput.placeholder = 'Edit left side';
    rightInput.placeholder = 'Edit right side';
    
    // Change button to save
    addBtn.innerHTML = '<i class="fas fa-check"></i>';
    addBtn.onclick = addFD;
    
    // Scroll input into view
    leftInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    leftInput.focus();
}

function removeFD(index) {
    if (confirm(`Remove FD: ${fds[index].left} → ${fds[index].right}?`)) {
        fds.splice(index, 1);
        renderFDs();
        updateNormalizeButton();
    }
}

function renderFDs() {
    const container = document.getElementById('fds-container');
    
    if (fds.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-arrow-right"></i>
                Add your first FD
            </div>
        `;
        return;
    }
    
    container.innerHTML = fds.map((fd, index) => `
        <div class="fd-item" data-index="${index}">
            <div class="fd-display">
                <span class="fd-left-display">${fd.left}</span>
                <span class="fd-arrow">→</span>
                <span class="fd-right-display">${fd.right}</span>
            </div>
            <div class="fd-actions">
                <button class="btn-edit" onclick="editFD(${index})" title="Edit FD">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-remove" onclick="removeFD(${index})" title="Delete FD">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function updateNormalizeButton() {
    const btn = document.getElementById('normalizeBtn');
    const attributes = document.getElementById('attributes').value.trim();

    const hasData = fds.length > 0 && attributes && candidate_keys.length > 0;
    btn.disabled = !hasData;
    btn.textContent = hasData ? 'Normalize to 3NF' : 'Add FDs and keys first';
}

function clearAll() {
    if (confirm('Clear all data?')) {
        fds = [];
        candidate_keys = [];  // Add this line to clear keys
        editingIndex = -1;
        document.getElementById('attributes').value = '';
        document.querySelector('.fd-left').value = '';
        document.querySelector('.fd-right').value = '';
        document.querySelector('.btn-add-fd').innerHTML = '<i class="fas fa-plus"></i>';
        document.querySelector('.btn-add-fd').onclick = addFD;
        renderFDs();
        renderKeys();  // Add this line to re-render empty keys
        updateNormalizeButton();
        showResults([]);
    }
}

function showNotification(message, type = 'success') {
    // Simple notification (you can enhance this)
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

async function normalizeDB() {
    const btn = document.getElementById('normalizeBtn');
    const resultsContainer = document.getElementById('results-container');
    const attributes = document.getElementById('attributes').value
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

    btn.disabled = true;
    resultsContainer.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Computing 3NF decomposition...</p>
        </div>
    `;

    try {
        const response = await fetch('/normalize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                attributes,
                keys: candidate_keys,
                functional_deps: fds.map(fd => [
                    fd.left.split(',').map(s => s.trim()).filter(Boolean),
                    fd.right.split(',').map(s => s.trim()).filter(Boolean)
                ])
            })
        });
        
        const data = await response.json();
        console.log(data);
        
        if (data.success) {
            showResults(data.relations, data.summary);
            showNotification('Normalization successful!', 'success');
        } else {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${data.error}
                </div>
                <div class="empty-state">
                    <p>Try adjusting your input and normalize again</p>
                </div>
            `;
            showNotification(data.error, 'error');
        }
    } catch (error) {
        resultsContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                Network error: ${error.message}
            </div>
        `;
        showNotification('Network error occurred', 'error');
    } finally {
        btn.disabled = false;
    }
}

function showResults(relations, summary) {
    const container = document.getElementById('results-container');
    
    if (!relations || relations.length === 0) {
        container.innerHTML = `
            <div class="empty-state large">
                <i class="fas fa-info-circle"></i>
                <h3>No decomposition needed</h3>
                <p>Your relation is already in 3NF</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="summary">${summary}</div>
        ${relations.map((relation, index) => `
            <div class="relation-card">
                <div class="relation-header">
                    <div class="relation-name">R${index + 1}</div>
                    <div class="relation-count">${relation.attributes?.length || 0} attrs</div>
                </div>
                <div class="relation-attributes">${Array.isArray(relation.attributes) ? relation.attributes.join(', ') : 'No attributes'}</div>
            </div>
        `).join('')}
    `;
}

// Event listeners
document.getElementById('attributes').addEventListener('input', updateNormalizeButton);
document.querySelector('.fd-left').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addFD();
});
document.querySelector('.fd-right').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addFD();
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateNormalizeButton();
});