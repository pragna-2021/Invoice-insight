// ==================== STATE MANAGEMENT & CONFIG ====================
const API_URL = ""; // Relative paths since hosted on same server
let activeInvoiceId = null;

// Chart.js instances (tracked to destroy/re-render cleanly)
let trendChart = null;
let speedChart = null;
let ratioChart = null;

// Utility request helper attaching JWT authorization tokens
async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = {
        ...options.headers,
    };
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(endpoint, { ...options, headers });
    
    if (response.status === 401) {
        // Token expired or invalid, force logout
        logout();
        throw new Error("Session expired. Please log in again.");
    }
    
    return response;
}

// ==================== DOCUMENT ON LOAD INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    // Check if user is already authenticated
    const token = localStorage.getItem("access_token");
    if (token) {
        showApp();
    } else {
        showAuth();
    }

    // Login Form handler
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        const alertDiv = document.getElementById("auth-alert");
        
        alertDiv.classList.add("d-none");
        
        try {
            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);
            
            const res = await fetch("/api/auth/login", {
                method: "POST",
                body: formData,
                headers: { "Content-Type": "application/x-www-form-urlencoded" }
            });
            
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Login failed");
            
            localStorage.setItem("access_token", data.access_token);
            showApp();
        } catch (err) {
            alertDiv.textContent = err.message;
            alertDiv.classList.remove("d-none");
        }
    });

    // Register Form handler
    document.getElementById("register-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        const confirmPass = document.getElementById("register-confirm-password").value;
        const alertDiv = document.getElementById("auth-alert");
        
        alertDiv.classList.add("d-none");
        
        if (password !== confirmPass) {
            alertDiv.textContent = "Passwords do not match!";
            alertDiv.classList.remove("d-none");
            return;
        }
        
        try {
            const res = await fetch("/api/auth/register", {
                method: "POST",
                body: JSON.stringify({ email, password }),
                headers: { "Content-Type": "application/json" }
            });
            
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Registration failed");
            
            localStorage.setItem("access_token", data.access_token);
            showApp();
        } catch (err) {
            alertDiv.textContent = err.message;
            alertDiv.classList.remove("d-none");
        }
    });

    // Drag and Drop Upload logic
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const selectedFileText = document.getElementById("selected-file-name");
    const btnUpload = document.getElementById("btn-upload");

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    ["dragleave", "dragend", "drop"].forEach(event => {
        dropZone.addEventListener(event, () => dropZone.classList.remove("dragover"));
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect(fileInput.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        selectedFileText.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        selectedFileText.classList.remove("d-none");
        btnUpload.disabled = false;
    }

    // Upload Form Submit handler
    document.getElementById("upload-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        const errorDiv = document.getElementById("upload-error");
        const successDiv = document.getElementById("upload-success");
        const spinner = document.getElementById("upload-spinner");
        
        errorDiv.classList.add("d-none");
        successDiv.classList.add("d-none");
        spinner.classList.remove("d-none");
        btnUpload.disabled = true;

        try {
            const res = await fetchAPI("/api/upload/", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Upload failed");
            
            successDiv.classList.remove("d-none");
            
            // Clear upload state
            fileInput.value = "";
            selectedFileText.classList.add("d-none");
            btnUpload.disabled = true;

            // Load parsed details, refresh history lists, and auto-navigate to inspector
            await loadInvoiceDetails(data.invoice_id);
            fetchRecentInvoices();
            switchTab("inspector");
        } catch (err) {
            errorDiv.textContent = err.message;
            errorDiv.classList.remove("d-none");
            btnUpload.disabled = false;
        } finally {
            spinner.classList.add("d-none");
        }
    });

    // Details Edit Form Save
    document.getElementById("invoice-details-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!activeInvoiceId) return;

        const vendor = document.getElementById("edit-vendor").value;
        const date = document.getElementById("edit-date").value;
        const total = document.getElementById("edit-total").value;
        
        // Grab items rows
        const items = [];
        const rows = document.querySelectorAll("#edit-items-tbody tr");
        rows.forEach(row => {
            const qtyInputs = row.querySelectorAll("input");
            if (qtyInputs.length >= 3) {
                const qty = qtyInputs[0].value;
                const desc = qtyInputs[1].value;
                const price = qtyInputs[2].value;
                if (desc.trim() !== "") {
                    items.push({ Quantity: qty, Description: desc, Price: price });
                }
            }
        });

        const payload = {
            "Vendor Name": vendor,
            "Invoice Date": date,
            "Total Amount": total,
            "Items List": items
        };

        try {
            const res = await fetchAPI(`/api/analytics/invoices/${activeInvoiceId}/edit`, {
                method: "PUT",
                body: JSON.stringify(payload),
                headers: { "Content-Type": "application/json" }
            });
            if (!res.ok) throw new Error("Failed to update invoice");
            
            alert("Invoice structured data successfully corrected! Updated accuracy score.");
            loadInvoiceDetails(activeInvoiceId);
            fetchRecentInvoices();
        } catch (err) {
            alert(err.message);
        }
    });
});

// ==================== AUTHENTICATED STATE TOGGLES ====================
async function showApp() {
    document.getElementById("auth-container").classList.add("d-none");
    document.getElementById("app-container").classList.remove("d-none");
    
    // Fetch profile me
    try {
        const res = await fetchAPI("/api/auth/me");
        const data = await res.json();
        document.getElementById("user-display-email").textContent = data.email;
    } catch (err) {
        logout();
        return;
    }

    // Load initial view
    switchTab("upload");
}

function showAuth() {
    document.getElementById("app-container").classList.add("d-none");
    document.getElementById("auth-container").classList.remove("d-none");
}

function logout() {
    localStorage.removeItem("access_token");
    showAuth();
}

// ==================== NAVIGATION TAB TOGGLING ====================
function switchTab(tab) {
    const tabs = ["upload", "history", "inspector", "analytics"];
    
    // Deactivate all links and hide all tab panels
    tabs.forEach(t => {
        const link = document.getElementById(`nav-${t}-link`);
        const pane = document.getElementById(`tab-${t}`);
        if (link) link.classList.remove("active");
        if (pane) pane.classList.add("d-none");
    });
    
    // Activate selected link and show selected panel
    const activeLink = document.getElementById(`nav-${tab}-link`);
    const activePane = document.getElementById(`tab-${tab}`);
    if (activeLink) activeLink.classList.add("active");
    if (activePane) activePane.classList.remove("d-none");
    
    // Trigger data loads
    if (tab === "history") {
        fetchRecentInvoices();
    } else if (tab === "analytics") {
        fetchAnalytics();
    }
}

// ==================== DASHBOARD FLOW ====================
async function fetchRecentInvoices() {
    try {
        const res = await fetchAPI("/api/analytics/metrics");
        const data = await res.json();
        
        const tbody = document.getElementById("invoices-list-body");
        tbody.innerHTML = "";
        
        if (data.recent_invoices.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-light-muted">No invoices processed yet.</td></tr>`;
            return;
        }
        
        data.recent_invoices.forEach(inv => {
            const accClass = inv.ocr_accuracy > 85 ? "text-success" : (inv.ocr_accuracy > 65 ? "text-warning" : "text-danger");
            const langBadge = inv.language === "ru" ? '<span class="badge bg-purple">RU</span>' : '<span class="badge bg-info">EN</span>';
            const statusBadge = inv.status === "completed" 
                ? `<span class="badge badge-completed">Completed</span>`
                : (inv.status === "failed" ? `<span class="badge badge-failed">Failed</span>` : `<span class="badge badge-processing">Processing</span>`);
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="text-white small fw-bold">${inv.filename}</td>
                <td>${langBadge}</td>
                <td class="${accClass} fw-bold">${inv.ocr_accuracy ? inv.ocr_accuracy.toFixed(1) + '%' : '0%'}</td>
                <td class="text-white small">${inv.processing_time_ms ? inv.processing_time_ms.toFixed(0) : '0'}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-primary btn-xs" onclick="selectAndInspectInvoice(${inv.id})">
                        <i class="bi bi-eye"></i> Inspect
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading invoices: ", err);
    }
}

// Triggered by History Inspect button
function selectAndInspectInvoice(id) {
    loadInvoiceDetails(id);
    switchTab("inspector");
}

// Structured Details Display
async function loadInvoiceDetails(id) {
    try {
        const res = await fetchAPI(`/api/analytics/invoices/${id}`);
        if (!res.ok) throw new Error("Could not retrieve invoice details");
        const inv = await res.json();
        
        activeInvoiceId = id;
        
        // Hide placeholder, show form
        document.getElementById("details-placeholder").classList.add("d-none");
        document.getElementById("details-form-container").classList.remove("d-none");
        
        // Populate inputs
        document.getElementById("edit-invoice-id").value = inv.id;
        document.getElementById("edit-vendor").value = inv.structured_data?.["Vendor Name"] || "Unknown";
        document.getElementById("edit-date").value = inv.structured_data?.["Invoice Date"] || "Unknown";
        document.getElementById("edit-total").value = inv.structured_data?.["Total Amount"] || "0.00";
        document.getElementById("edit-raw-text").value = inv.translated_text || inv.raw_text || "";
        
        // Rebuild Line Items Table
        const tbody = document.getElementById("edit-items-tbody");
        tbody.innerHTML = "";
        
        const items = inv.structured_data?.["Items List"] || [];
        if (items.length === 0) {
            tbody.innerHTML = `<tr class="no-items-placeholder"><td colspan="4" class="text-center text-light-muted small">No items detected. Click 'Add Line Item' to insert.</td></tr>`;
        } else {
            items.forEach(item => {
                addInvoiceItemRow(item.Quantity, item.Description, item.Price);
            });
        }
    } catch (err) {
        alert(err.message);
    }
}

function addInvoiceItemRow(qty = "1", desc = "", price = "0.00") {
    const tbody = document.getElementById("edit-items-tbody");
    
    // Remove placeholder row if present
    const placeholder = tbody.querySelector(".no-items-placeholder");
    if (placeholder) {
        tbody.removeChild(placeholder);
    }
    
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td><input type="text" class="form-control item-qty" value="${qty}"></td>
        <td><input type="text" class="form-control item-desc" value="${desc}"></td>
        <td><input type="text" class="form-control item-price" value="${price}"></td>
        <td class="text-center">
            <button type="button" class="btn btn-outline-danger btn-xs" onclick="deleteInvoiceItemRow(this)">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
}

function deleteInvoiceItemRow(btn) {
    const row = btn.closest("tr");
    const tbody = row.parentNode;
    tbody.removeChild(row);
    
    if (tbody.children.length === 0) {
        tbody.innerHTML = `<tr class="no-items-placeholder"><td colspan="4" class="text-center text-light-muted small">No items detected. Click 'Add Line Item' to insert.</td></tr>`;
    }
}

// ==================== EXPORT & DOWNLOAD CHANNELS ====================
async function exportActiveInvoice(format) {
    if (!activeInvoiceId) return;
    
    try {
        const res = await fetchAPI(`/api/analytics/invoices/${activeInvoiceId}/export/${format}`);
        if (!res.ok) throw new Error("Export failed");
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `invoice_${activeInvoiceId}.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert(err.message);
    }
}

function printActiveInvoice() {
    if (!activeInvoiceId) return;
    
    const vendor = document.getElementById("edit-vendor").value;
    const date = document.getElementById("edit-date").value;
    const total = document.getElementById("edit-total").value;
    
    let itemsHTML = "";
    document.querySelectorAll("#edit-items-tbody tr").forEach(row => {
        const qtyInputs = row.querySelectorAll("input");
        if (qtyInputs.length >= 3) {
            const qty = qtyInputs[0].value;
            const desc = qtyInputs[1].value;
            const price = qtyInputs[2].value;
            itemsHTML += `
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">${qty}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">${desc}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">$${price}</td>
                </tr>
            `;
        }
    });

    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
        <html>
        <head>
            <title>Print Invoice - ID ${activeInvoiceId}</title>
            <style>
                body { font-family: Arial, sans-serif; color: #333; padding: 40px; }
                .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
                .vendor { font-size: 24px; font-weight: bold; }
                .metadata { float: right; text-align: right; }
                table { width: 100%; border-collapse: collapse; margin-top: 30px; }
                .total { text-align: right; font-size: 20px; font-weight: bold; margin-top: 30px; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="metadata">
                    <div>Date: ${date}</div>
                    <div>Invoice ID: ${activeInvoiceId}</div>
                </div>
                <div class="vendor">${vendor}</div>
            </div>
            <table>
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Quantity</th>
                        <th style="padding: 10px; text-align: left;">Description</th>
                        <th style="padding: 10px; text-align: right;">Price</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemsHTML}
                </tbody>
            </table>
            <div class="total">Total Due: $${total}</div>
            <script>
                window.onload = function() { window.print(); window.close(); }
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

// ==================== ANALYTICS GRAPHICS ====================
async function fetchAnalytics() {
    try {
        const res = await fetchAPI("/api/analytics/metrics");
        const data = await res.json();
        
        // Update metric labels
        document.getElementById("metric-total").textContent = data.total;
        document.getElementById("metric-success-rate").textContent = `${data.success_rate.toFixed(0)}%`;
        document.getElementById("metric-ocr-acc").textContent = `${data.avg_ocr_accuracy.toFixed(1)}%`;
        document.getElementById("metric-speed").textContent = `${data.avg_processing_time_ms.toFixed(0)} ms`;
        
        // Error Logs Table
        const errorTbody = document.getElementById("error-logs-body");
        errorTbody.innerHTML = "";
        if (data.error_logs.length === 0) {
            errorTbody.innerHTML = `<tr><td colspan="3" class="text-center text-light-muted">No system errors recorded.</td></tr>`;
        } else {
            data.error_logs.forEach(log => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td class="text-danger small fw-bold">${log.filename}</td>
                    <td class="text-white small">${log.created_at}</td>
                    <td class="text-white small"><code class="text-danger font-monospace">${log.error_log}</code></td>
                `;
                errorTbody.appendChild(tr);
            });
        }

        // Render Charts
        renderCharts(data);
        
    } catch (err) {
        console.error("Error loading analytics metrics: ", err);
    }
}

function renderCharts(data) {
    const ctxTrend = document.getElementById("chart-accuracy-trends").getContext("2d");
    const ctxSpeed = document.getElementById("chart-processing-times").getContext("2d");
    const ctxRatio = document.getElementById("chart-success-failure").getContext("2d");

    // Destroy existing charts to reload clean data
    if (trendChart) trendChart.destroy();
    if (speedChart) speedChart.destroy();
    if (ratioChart) ratioChart.destroy();

    // Chart 1: Accuracy trends
    const trendLabels = data.accuracy_trends.map(t => t.date);
    const ocrAccData = data.accuracy_trends.map(t => t.ocr_accuracy);
    const transAccData = data.accuracy_trends.map(t => t.translation_accuracy);

    trendChart = new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: trendLabels.length ? trendLabels : ["No Data"],
            datasets: [
                {
                    label: 'OCR Accuracy (%)',
                    data: ocrAccData.length ? ocrAccData : [0],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Post-Edit Field Match (%)',
                    data: transAccData.length ? transAccData : [0],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 100, grid: { color: 'rgba(255, 255, 255, 0.08)' }, ticks: { color: '#ffffff' } },
                x: { grid: { display: false }, ticks: { color: '#ffffff' } }
            },
            plugins: {
                legend: { labels: { color: '#ffffff', font: { weight: 'bold' } } }
            }
        }
    });

    // Chart 2: Speed comparison
    speedChart = new Chart(ctxSpeed, {
        type: 'bar',
        data: {
            labels: ['Images', 'PDFs'],
            datasets: [{
                label: 'Avg Processing Time (ms)',
                data: [data.processing_time_comparison.images_avg_ms, data.processing_time_comparison.pdfs_avg_ms],
                backgroundColor: ['#f59e0b', '#06b6d4'],
                borderWidth: 0,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255, 255, 255, 0.08)' }, ticks: { color: '#ffffff' } },
                x: { grid: { display: false }, ticks: { color: '#ffffff' } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Chart 3: Success vs Failure
    ratioChart = new Chart(ctxRatio, {
        type: 'doughnut',
        data: {
            labels: ['Success', 'Failed'],
            datasets: [{
                data: [data.success_ratio.success, data.success_ratio.failed],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#ffffff', boxWidth: 12, font: { weight: 'bold' } }
                }
            }
        }
    });
}
