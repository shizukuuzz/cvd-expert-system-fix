/**
 * CVD Expert System - Client-side JavaScript
 * Handles form submission, API calls, and result rendering
 */

// API Base URL
const API_BASE = '';

// Current result data (for export)
let currentResult = null;

// ============================================================
// Form Handling
// ============================================================

document.getElementById('patientForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitDiagnosis();
});

async function submitDiagnosis() {
    showLoading(true);

    try {
        const formData = collectFormData();
        console.log('Sending data:', formData);

        const response = await fetch(`${API_BASE}/api/diagnose`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Diagnosis failed');
        }

        const result = await response.json();
        console.log('Result:', result);

        currentResult = result;
        displayResults(result);

    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function collectFormData() {
    const form = document.getElementById('patientForm');

    // Demographics
    const demographics = {
        name: document.getElementById('name').value,
        age: parseInt(document.getElementById('age').value) || null,
        gender: document.getElementById('gender').value,
        race: document.getElementById('race')?.value || 'non-black'
    };

    // Vitals - termasuk weight dan height untuk BMI
    const vitals = {};
    const vitalFields = ['sbp', 'dbp', 'hr', 'bmi', 'weight', 'height'];
    vitalFields.forEach(field => {
        const el = document.getElementById(field);
        if (el && el.value) vitals[field] = parseFloat(el.value);
    });

    // Labs - termasuk creatinine dan totalChol
    const labs = {};
    const labFields = ['fbg', 'hba1c', 'ldl', 'hdl', 'ef', 'troponin', 'gfr', 'potassium', 'creatinine', 'totalChol'];
    labFields.forEach(field => {
        const el = document.getElementById(field);
        if (el && el.value) labs[field] = parseFloat(el.value);
    });

    // Scores - termasuk hasbled
    const scores = {};
    const scoreFields = ['ascvd', 'cha2ds2vasc', 'hasbled'];
    scoreFields.forEach(field => {
        const el = document.getElementById(field);
        if (el && el.value) scores[field] = parseFloat(el.value);
    });

    // Symptoms
    const symptoms = [];
    document.querySelectorAll('input[name="symptoms"]:checked').forEach(cb => {
        symptoms.push(cb.value);
    });

    // Comorbidities - some are auto-detected, some are manual checkboxes
    const comorbid = {
        asthma: document.getElementById('asthma')?.checked || false,
        pregnancy: document.getElementById('pregnancy')?.checked || false,
        liver_disease: document.getElementById('liver_disease')?.checked || false,
        // ASCVD - only treatment checkbox remains (diabetes is auto-detected)
        onHypertensionTreatment: document.getElementById('onHypertensionTreatment')?.checked || false,
        // CHA2DS2-VASc - hypertension & diabetes are auto-detected
        hasHeartFailure: document.getElementById('hasHeartFailure')?.checked || false,
        hasStrokeHistory: document.getElementById('hasStrokeHistory')?.checked || false,
        hasVascularDisease: document.getElementById('hasVascularDisease')?.checked || false,
        // HAS-BLED - only manual checkboxes (H,A,S,E are auto-detected from data)
        hasBleedingHistory: document.getElementById('hasBleedingHistory')?.checked || false,
        hasLabileINR: document.getElementById('hasLabileINR')?.checked || false,
        takesAntiplatelet: document.getElementById('takesAntiplatelet')?.checked || false,
        takesAlcohol: document.getElementById('takesAlcohol')?.checked || false,
        // Auto-detected values (for backend processing)
        hasDiabetes: detectDiabetes(),
        hasHypertension: detectHypertension()
    };

    // History
    const history = {
        smoking: document.getElementById('smoking')?.checked || false,
        cad: document.getElementById('cad')?.checked || false
    };

    return {
        demographics,
        vitals,
        labs,
        scores,
        symptoms,
        comorbid,
        history
    };
}

function resetForm() {
    document.getElementById('patientForm').reset();
    document.getElementById('resultsSection').classList.add('hidden');
    currentResult = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// Results Display
// ============================================================

function displayResults(result) {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.classList.remove('hidden');

    // Emergency alert
    const emergencyAlert = document.getElementById('emergencyAlert');
    if (result.emergency) {
        emergencyAlert.classList.remove('hidden');
    } else {
        emergencyAlert.classList.add('hidden');
    }

    // Summary cards
    document.getElementById('riskCategory').textContent = result.risk_category || '-';
    document.getElementById('severityLevel').textContent = result.severity || '-';
    document.getElementById('rulesFired').textContent = result.rules_fired || 0;

    // Color the summary cards based on severity
    colorSummaryCard('riskCard', result.risk_category);
    colorSummaryCard('severityCard', result.severity);

    // Diagnoses
    displayDiagnoses(result.diagnoses || []);

    // Medications
    displayMedications(result.medications || []);

    // Contraindications
    displayContraindications(result.contraindications || []);

    // Lifestyle recommendations
    displayLifestyle(result.lifestyle_recommendations || []);

    // Reasoning trace
    displayReasoningTrace(result.reasoning_trace || []);

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function colorSummaryCard(cardId, value) {
    const card = document.getElementById(cardId);
    card.style.borderColor = '';

    const valueLower = (value || '').toLowerCase();

    if (valueLower.includes('kritis') || valueLower.includes('sangat tinggi')) {
        card.style.borderColor = 'var(--critical)';
    } else if (valueLower.includes('berat') || valueLower.includes('tinggi')) {
        card.style.borderColor = 'var(--danger)';
    } else if (valueLower.includes('sedang')) {
        card.style.borderColor = 'var(--warning)';
    } else if (valueLower.includes('ringan') || valueLower.includes('rendah')) {
        card.style.borderColor = 'var(--success)';
    }
}

function displayDiagnoses(diagnoses) {
    const container = document.getElementById('diagnosisList');

    if (diagnoses.length === 0) {
        container.innerHTML = '<p class="no-data">Tidak ada diagnosis terdeteksi</p>';
        return;
    }

    container.innerHTML = diagnoses.map(d => {
        const severityClass = (d.severity || 'ringan').toLowerCase();
        const descHtml = d.description ? `<div class="diagnosis-description">${d.description}</div>` : '';
        return `
            <div class="diagnosis-item severity-${severityClass}" onclick="this.classList.toggle('expanded')">
                <div class="diagnosis-main">
                    <div>
                        <div class="diagnosis-name">${d.name}</div>
                        <div class="diagnosis-source">${d.source || 'SWRL Inference'}</div>
                    </div>
                    <span class="severity-badge ${severityClass}">${d.severity || 'N/A'}</span>
                </div>
                ${descHtml}
            </div>
        `;
    }).join('');
}

function displayMedications(medications) {
    const container = document.getElementById('medicationList');

    if (medications.length === 0) {
        container.innerHTML = '<p class="no-data">Tidak ada rekomendasi obat</p>';
        return;
    }

    container.innerHTML = medications.map(m => {
        const descHtml = m.description ? `<div class="medication-description">${m.description}</div>` : '';
        return `
            <div class="medication-item" onclick="this.classList.toggle('expanded')">
                <div class="medication-main">
                    <div class="medication-icon">💊</div>
                    <div class="medication-info">
                        <div class="medication-name">${m.name}</div>
                        <div class="medication-details">
                            ${m.class} • ${m.dose || ''} ${m.frequency || ''}
                        </div>
                    </div>
                </div>
                ${descHtml}
            </div>
        `;
    }).join('');
}

function displayContraindications(contraindications) {
    const card = document.getElementById('contraindicationsCard');
    const container = document.getElementById('contraindicationList');

    if (contraindications.length === 0) {
        card.classList.add('hidden');
        return;
    }

    card.classList.remove('hidden');

    container.innerHTML = contraindications.map(c => `
        <div class="contraindication-item">
            <div class="contraindication-icon">⚠️</div>
            <div>
                <div class="contraindication-drug">${c.drug} - KONTRAINDIKASI</div>
                <div class="contraindication-reason">${c.reason}</div>
            </div>
        </div>
    `).join('');
}

function displayLifestyle(recommendations) {
    const container = document.getElementById('lifestyleList');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="no-data">Tidak ada rekomendasi tambahan</p>';
        return;
    }

    // Group by category
    const grouped = {};
    recommendations.forEach(r => {
        const cat = r.category || 'Umum';
        if (!grouped[cat]) grouped[cat] = [];
        grouped[cat].push(r);
    });

    container.innerHTML = Object.entries(grouped).map(([category, items]) => `
        <div class="lifestyle-category">
            <div class="lifestyle-category-title">📌 ${category}</div>
            <div class="lifestyle-items">
                ${items.map(item => `
                    <div class="lifestyle-item" onclick="this.classList.toggle('expanded')">
                        <div class="lifestyle-item-name">${item.name}</div>
                        ${item.description ? `<div class="lifestyle-item-desc">${item.description}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function displayReasoningTrace(trace) {
    const container = document.getElementById('reasoningTrace');

    if (trace.length === 0) {
        container.innerHTML = '<p class="no-data">Tidak ada reasoning trace</p>';
        return;
    }

    container.innerHTML = trace.map(line => `
        <div class="trace-line">${escapeHtml(line)}</div>
    `).join('');
}

function toggleReasoningTrace() {
    const trace = document.getElementById('reasoningTrace');
    const icon = document.getElementById('traceCollapseIcon');

    trace.classList.toggle('collapsed');
    icon.textContent = trace.classList.contains('collapsed') ? '▶' : '▼';
}

// ============================================================
// History
// ============================================================

async function showHistory() {
    const modal = document.getElementById('historyModal');
    modal.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/history`);
        const data = await response.json();

        displayHistoryTable(data.history || []);
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('historyTable').innerHTML =
            '<p class="error">Gagal memuat riwayat</p>';
    }
}

function closeHistory() {
    document.getElementById('historyModal').classList.add('hidden');
}

function displayHistoryTable(history) {
    const container = document.getElementById('historyTable');

    if (history.length === 0) {
        container.innerHTML = '<p class="no-data">Belum ada riwayat diagnosis</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Waktu</th>
                    <th>Pasien</th>
                    <th>Usia</th>
                    <th>Diagnosis</th>
                    <th>Risiko</th>
                </tr>
            </thead>
            <tbody>
                ${history.map(h => `
                    <tr>
                        <td>${formatDate(h.timestamp)}</td>
                        <td>${h.patient_name || '-'}</td>
                        <td>${h.age || '-'}</td>
                        <td>${h.diagnoses || '-'}</td>
                        <td>${h.risk_category || '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// ============================================================
// Export
// ============================================================

function exportReport() {
    if (!currentResult) {
        alert('Tidak ada hasil untuk diexport');
        return;
    }

    const report = generateReport(currentResult);

    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnosis_${currentResult.patient_id || 'report'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function generateReport(result) {
    let report = `
╔══════════════════════════════════════════════════════════════╗
║           CVD EXPERT SYSTEM - DIAGNOSIS REPORT               ║
╚══════════════════════════════════════════════════════════════╝

📅 Tanggal: ${new Date(result.timestamp).toLocaleString('id-ID')}
🆔 ID: ${result.patient_id || 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RINGKASAN
─────────────
• Kategori Risiko: ${result.risk_category || 'N/A'}
• Tingkat Keparahan: ${result.severity || 'N/A'}
• SWRL Rules Fired: ${result.rules_fired || 0}
${result.emergency ? '\n⚠️ EMERGENCY: KONDISI KRITIS TERDETEKSI!\n' : ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🩺 DIAGNOSIS
─────────────
${(result.diagnoses || []).map(d => `• ${d.name} (${d.severity || 'N/A'})`).join('\n') || 'Tidak ada diagnosis'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💊 REKOMENDASI OBAT
─────────────────────
${(result.medications || []).map(m => `• ${m.name} (${m.class}) - ${m.dose || ''} ${m.frequency || ''}`).join('\n') || 'Tidak ada rekomendasi'}

`;

    if ((result.contraindications || []).length > 0) {
        report += `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ KONTRAINDIKASI
───────────────────
${result.contraindications.map(c => `• ${c.drug}: ${c.reason}`).join('\n')}

`;
    }

    report += `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📜 REASONING TRACE
───────────────────
${(result.reasoning_trace || []).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ DISCLAIMER
Hasil diagnosis ini dihasilkan oleh sistem pakar berbasis
SROIQ Ontology dan SWRL Rules. Selalu konsultasikan dengan
dokter untuk evaluasi dan penanganan yang tepat.

Generated by CVD Expert System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;

    return report;
}

// ============================================================
// Utilities
// ============================================================

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function formatDate(isoString) {
    if (!isoString) return '-';
    try {
        return new Date(isoString).toLocaleString('id-ID', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return isoString;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal on outside click
document.getElementById('historyModal').addEventListener('click', (e) => {
    if (e.target.id === 'historyModal') {
        closeHistory();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeHistory();
        closeTooltipModal();
    }
});

// ============================================================
// Tooltip Popup from Ontology
// ============================================================

// Store parameter descriptions from ontology
let parameterDescriptions = {};

// Load descriptions on page load
async function loadParameterDescriptions() {
    try {
        const response = await fetch(`${API_BASE}/api/descriptions`);
        if (response.ok) {
            parameterDescriptions = await response.json();
            console.log('Parameter descriptions loaded:', Object.keys(parameterDescriptions).length);
        }
    } catch (error) {
        console.error('Failed to load parameter descriptions:', error);
    }
}

// Show tooltip modal
function showTooltipModal(fieldId) {
    const desc = parameterDescriptions[fieldId];
    if (!desc) {
        console.warn('No description found for:', fieldId);
        return;
    }

    const modal = document.getElementById('tooltipModal');
    const title = document.getElementById('tooltipTitle');
    const content = document.getElementById('tooltipContent');

    title.textContent = desc.label || fieldId;
    content.textContent = desc.description || 'Tidak ada deskripsi';

    modal.classList.remove('hidden');
}

function closeTooltipModal() {
    const modal = document.getElementById('tooltipModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Setup tooltip click handlers
function setupTooltipHandlers() {
    document.querySelectorAll('.tooltip').forEach(tooltip => {
        tooltip.style.cursor = 'pointer';
        tooltip.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Get the field ID from the associated input
            const formGroup = tooltip.closest('.form-group');
            if (formGroup) {
                const input = formGroup.querySelector('input, select');
                if (input && input.id) {
                    showTooltipModal(input.id);
                }
            }
        });
    });
}

// ============================================================
// CALCULATORS
// ============================================================

/**
 * BMI Calculator
 * Formula: weight(kg) / height(m)²
 */
function calculateBMI() {
    const weight = parseFloat(document.getElementById('weight')?.value);
    const height = parseFloat(document.getElementById('height')?.value);
    
    if (weight && height && height > 0) {
        const heightM = height / 100; // convert cm to m
        const bmi = weight / (heightM * heightM);
        document.getElementById('bmi').value = bmi.toFixed(1);
        
        // Category
        const categoryEl = document.getElementById('bmiCategory');
        if (categoryEl) {
            let category = '';
            let color = '';
            if (bmi < 18.5) { category = 'Underweight'; color = '#3498db'; }
            else if (bmi < 25) { category = 'Normal'; color = '#27ae60'; }
            else if (bmi < 30) { category = 'Overweight'; color = '#f39c12'; }
            else { category = 'Obesitas'; color = '#e74c3c'; }
            categoryEl.textContent = category;
            categoryEl.style.color = color;
        }
    }
}

/**
 * Auto-detect Diabetes from lab values
 * Returns true if FBG >= 126 OR HbA1c >= 6.5%
 */
function detectDiabetes() {
    const fbg = parseFloat(document.getElementById('fbg')?.value) || 0;
    const hba1c = parseFloat(document.getElementById('hba1c')?.value) || 0;
    
    const hasDiabetes = fbg >= 126 || hba1c >= 6.5;
    
    // Update status badges
    const statusEl = document.getElementById('diabetesStatus');
    const statusEl2 = document.getElementById('diabetesStatus2');
    
    const text = hasDiabetes ? 'Ya ✓' : 'Tidak';
    const color = hasDiabetes ? '#e74c3c' : '#27ae60';
    
    if (statusEl) {
        statusEl.textContent = text;
        statusEl.style.color = color;
        statusEl.style.fontWeight = '600';
    }
    if (statusEl2) {
        statusEl2.textContent = text;
        statusEl2.style.color = color;
        statusEl2.style.fontWeight = '600';
    }
    
    return hasDiabetes;
}

/**
 * Auto-detect Hypertension from BP values
 * Returns true if SBP >= 140 OR DBP >= 90
 */
function detectHypertension() {
    const sbp = parseFloat(document.getElementById('sbp')?.value) || 0;
    const dbp = parseFloat(document.getElementById('dbp')?.value) || 0;
    
    const hasHypertension = sbp >= 140 || dbp >= 90;
    
    // Update status badge
    const statusEl = document.getElementById('hypertensionStatus');
    if (statusEl) {
        statusEl.textContent = hasHypertension ? 'Ya ✓' : 'Tidak';
        statusEl.style.color = hasHypertension ? '#e74c3c' : '#27ae60';
        statusEl.style.fontWeight = '600';
    }
    
    return hasHypertension;
}

/**
 * Update HAS-BLED auto-detected status indicators
 */
function updateHASBLEDStatus() {
    const sbp = parseFloat(document.getElementById('sbp')?.value) || 0;
    const gfr = parseFloat(document.getElementById('gfr')?.value) || 100;
    const age = parseInt(document.getElementById('age')?.value) || 0;
    const liverDisease = document.getElementById('liver_disease')?.checked || false;
    const hasStrokeHistory = document.getElementById('hasStrokeHistory')?.checked || false;
    
    // H - Hypertension (SBP > 160)
    const hStatus = document.getElementById('hasbledHStatus');
    if (hStatus) {
        const hasH = sbp > 160;
        hStatus.textContent = hasH ? 'Ya (+1)' : 'Tidak';
        hStatus.style.color = hasH ? '#e74c3c' : '#27ae60';
    }
    
    // A - Abnormal Renal (eGFR < 30)
    const aRenalStatus = document.getElementById('hasbledARenal');
    if (aRenalStatus) {
        const hasARenal = gfr < 30;
        aRenalStatus.textContent = hasARenal ? 'Ya (+1)' : 'Tidak';
        aRenalStatus.style.color = hasARenal ? '#e74c3c' : '#27ae60';
    }
    
    // A - Abnormal Liver
    const aLiverStatus = document.getElementById('hasbledALiver');
    if (aLiverStatus) {
        aLiverStatus.textContent = liverDisease ? 'Ya (+1)' : 'Tidak';
        aLiverStatus.style.color = liverDisease ? '#e74c3c' : '#27ae60';
    }
    
    // S - Stroke
    const sStatus = document.getElementById('hasbledS');
    if (sStatus) {
        sStatus.textContent = hasStrokeHistory ? 'Ya (+1)' : 'Tidak';
        sStatus.style.color = hasStrokeHistory ? '#e74c3c' : '#27ae60';
    }
    
    // E - Elderly (Age > 65)
    const eStatus = document.getElementById('hasbledE');
    if (eStatus) {
        const hasE = age > 65;
        eStatus.textContent = hasE ? 'Ya (+1)' : 'Tidak';
        eStatus.style.color = hasE ? '#e74c3c' : '#27ae60';
    }
}

/**
 * eGFR Calculator (CKD-EPI 2021)
 * Uses creatinine, age, gender
 * Reference: https://www.kidney.org/professionals/kdoqi/gfr_calculator
 */
function calculateEGFR() {
    const creatinine = parseFloat(document.getElementById('creatinine')?.value);
    const age = parseInt(document.getElementById('age')?.value);
    const gender = document.getElementById('gender')?.value;
    const race = document.getElementById('race')?.value || 'non-black';
    
    if (creatinine && age && gender) {
        let eGFR;
        const isFemale = gender === 'female';
        
        // CKD-EPI 2021 (race-free)
        const kappa = isFemale ? 0.7 : 0.9;
        const alpha = isFemale ? -0.241 : -0.302;
        const sexCoef = isFemale ? 1.012 : 1.0;
        
        const scrKappa = creatinine / kappa;
        const minVal = Math.min(scrKappa, 1);
        const maxVal = Math.max(scrKappa, 1);
        
        eGFR = 142 * Math.pow(minVal, alpha) * Math.pow(maxVal, -1.200) * Math.pow(0.9938, age) * sexCoef;
        
        // Optional: add race factor for backward compatibility (2009 formula)
        // if (race === 'black') eGFR *= 1.159;
        
        document.getElementById('gfr').value = Math.round(eGFR);
        
        // Category
        const categoryEl = document.getElementById('gfrCategory');
        if (categoryEl) {
            let category = '';
            let color = '';
            if (eGFR >= 90) { category = 'Normal'; color = '#27ae60'; }
            else if (eGFR >= 60) { category = 'CKD Stage 2'; color = '#f1c40f'; }
            else if (eGFR >= 30) { category = 'CKD Stage 3'; color = '#f39c12'; }
            else if (eGFR >= 15) { category = 'CKD Stage 4'; color = '#e67e22'; }
            else { category = 'CKD Stage 5'; color = '#e74c3c'; }
            categoryEl.textContent = category;
            categoryEl.style.color = color;
        }
        
        // Trigger HAS-BLED recalculation
        calculateHASBLED();
    }
}

/**
 * ASCVD Risk Calculator (Pooled Cohort Equations)
 * 10-year risk of atherosclerotic cardiovascular disease
 */
function calculateASCVD() {
    const age = parseInt(document.getElementById('age')?.value);
    const gender = document.getElementById('gender')?.value;
    const race = document.getElementById('race')?.value || 'non-black';
    const totalChol = parseFloat(document.getElementById('totalChol')?.value);
    const hdl = parseFloat(document.getElementById('hdl')?.value);
    const sbp = parseFloat(document.getElementById('sbp')?.value);
    const onHTTreatment = document.getElementById('onHypertensionTreatment')?.checked || false;
    const hasDiabetes = detectDiabetes(); // Auto-detect from FBG/HbA1c
    const smoking = document.getElementById('smoking')?.checked || false;
    
    if (age && gender && totalChol && hdl && sbp) {
        let risk;
        const isFemale = gender === 'female';
        const isBlack = race === 'black';
        
        // Simplified PCE calculation
        const lnAge = Math.log(age);
        const lnTotalChol = Math.log(totalChol);
        const lnHDL = Math.log(hdl);
        const lnSBP = Math.log(sbp);
        const currentSmoker = smoking ? 1 : 0;
        const diabetes = hasDiabetes ? 1 : 0;
        const treatedSBP = onHTTreatment ? 1 : 0;
        
        let sumCoef;
        let baseline;
        let meanCoef;
        
        if (isFemale && !isBlack) {
            // White Female
            sumCoef = -29.799 * lnAge + 4.884 * lnAge * lnAge + 13.540 * lnTotalChol 
                    - 3.114 * lnAge * lnTotalChol - 13.578 * lnHDL + 3.149 * lnAge * lnHDL 
                    + (treatedSBP ? 2.019 : 1.957) * lnSBP + 7.574 * currentSmoker 
                    - 1.665 * lnAge * currentSmoker + 0.661 * diabetes;
            baseline = 0.9665;
            meanCoef = -29.18;
        } else if (isFemale && isBlack) {
            // Black Female
            sumCoef = 17.114 * lnAge + 0.940 * lnTotalChol - 18.920 * lnHDL 
                    + 4.475 * lnAge * lnHDL + (treatedSBP ? 29.291 : 27.820) * lnSBP 
                    - (treatedSBP ? 6.432 : 6.087) * lnAge * lnSBP + 0.691 * currentSmoker + 0.874 * diabetes;
            baseline = 0.9533;
            meanCoef = 86.61;
        } else if (!isFemale && !isBlack) {
            // White Male
            sumCoef = 12.344 * lnAge + 11.853 * lnTotalChol - 2.664 * lnAge * lnTotalChol 
                    - 7.990 * lnHDL + 1.769 * lnAge * lnHDL 
                    + (treatedSBP ? 1.797 : 1.764) * lnSBP + 7.837 * currentSmoker 
                    - 1.795 * lnAge * currentSmoker + 0.658 * diabetes;
            baseline = 0.9144;
            meanCoef = 61.18;
        } else {
            // Black Male
            sumCoef = 2.469 * lnAge + 0.302 * lnTotalChol - 0.307 * lnHDL 
                    + (treatedSBP ? 1.916 : 1.809) * lnSBP + 0.549 * currentSmoker + 0.645 * diabetes;
            baseline = 0.8954;
            meanCoef = 19.54;
        }
        
        risk = (1 - Math.pow(baseline, Math.exp(sumCoef - meanCoef))) * 100;
        risk = Math.max(0, Math.min(100, risk)); // Clamp 0-100
        
        document.getElementById('ascvd').value = risk.toFixed(1);
        
        // Category
        const categoryEl = document.getElementById('ascvdCategory');
        if (categoryEl) {
            let category = '';
            let color = '';
            if (risk < 5) { category = 'Rendah'; color = '#27ae60'; }
            else if (risk < 7.5) { category = 'Borderline'; color = '#f1c40f'; }
            else if (risk < 20) { category = 'Menengah'; color = '#f39c12'; }
            else { category = 'Tinggi'; color = '#e74c3c'; }
            categoryEl.textContent = category;
            categoryEl.style.color = color;
        }
    }
}

/**
 * CHA₂DS₂-VASc Score Calculator
 * For stroke risk in Atrial Fibrillation
 */
function calculateCHA2DS2VASc() {
    const age = parseInt(document.getElementById('age')?.value) || 0;
    const gender = document.getElementById('gender')?.value;
    const hasHeartFailure = document.getElementById('hasHeartFailure')?.checked || false;
    const hasHypertension = detectHypertension(); // Auto-detect from SBP/DBP
    const hasDiabetes = detectDiabetes(); // Auto-detect from FBG/HbA1c
    const hasStrokeHistory = document.getElementById('hasStrokeHistory')?.checked || false;
    const hasVascularDisease = document.getElementById('hasVascularDisease')?.checked || false;
    
    let score = 0;
    
    // C - Congestive Heart Failure (1 point)
    if (hasHeartFailure) score += 1;
    
    // H - Hypertension (1 point) - AUTO-DETECTED
    if (hasHypertension) score += 1;
    
    // A₂ - Age ≥75 (2 points) or Age 65-74 (1 point)
    if (age >= 75) score += 2;
    else if (age >= 65) score += 1;
    
    // D - Diabetes (1 point) - AUTO-DETECTED
    if (hasDiabetes) score += 1;
    
    // S₂ - Stroke/TIA/Thromboembolism (2 points)
    if (hasStrokeHistory) score += 2;
    
    // V - Vascular disease (1 point)
    if (hasVascularDisease) score += 1;
    
    // A - Age 65-74 (already counted above)
    
    // Sc - Sex category (female = 1 point)
    if (gender === 'female') score += 1;
    
    document.getElementById('cha2ds2vasc').value = score;
    
    // Category & Recommendation
    const categoryEl = document.getElementById('cha2ds2vascCategory');
    if (categoryEl) {
        let category = '';
        let color = '';
        if (score === 0) { category = 'Risiko Rendah'; color = '#27ae60'; }
        else if (score === 1) { category = 'Risiko Rendah-Menengah'; color = '#f1c40f'; }
        else if (score <= 3) { category = 'Risiko Menengah'; color = '#f39c12'; }
        else { category = 'Risiko Tinggi'; color = '#e74c3c'; }
        categoryEl.textContent = category;
        categoryEl.style.color = color;
    }
    
    // Update HAS-BLED status indicators
    updateHASBLEDStatus();
}

/**
 * HAS-BLED Score Calculator
 * For bleeding risk assessment in anticoagulation
 */
function calculateHASBLED() {
    const sbp = parseFloat(document.getElementById('sbp')?.value) || 0;
    const gfr = parseFloat(document.getElementById('gfr')?.value) || 100;
    const age = parseInt(document.getElementById('age')?.value) || 0;
    const liverDisease = document.getElementById('liver_disease')?.checked || false;
    const hasStrokeHistory = document.getElementById('hasStrokeHistory')?.checked || false;
    const hasBleedingHistory = document.getElementById('hasBleedingHistory')?.checked || false;
    const hasLabileINR = document.getElementById('hasLabileINR')?.checked || false;
    const takesAntiplatelet = document.getElementById('takesAntiplatelet')?.checked || false;
    const takesAlcohol = document.getElementById('takesAlcohol')?.checked || false;
    
    let score = 0;
    
    // H - Hypertension (SBP > 160) (1 point)
    if (sbp > 160) score += 1;
    
    // A - Abnormal renal function (eGFR < 30) (1 point)
    if (gfr < 30) score += 1;
    
    // A - Abnormal liver function (1 point)
    if (liverDisease) score += 1;
    
    // S - Stroke history (1 point)
    if (hasStrokeHistory) score += 1;
    
    // B - Bleeding history (1 point)
    if (hasBleedingHistory) score += 1;
    
    // L - Labile INR (TTR < 60%) (1 point)
    if (hasLabileINR) score += 1;
    
    // E - Elderly (Age > 65) (1 point)
    if (age > 65) score += 1;
    
    // D - Drugs (Antiplatelet/NSAID) (1 point)
    if (takesAntiplatelet) score += 1;
    
    // D - Alcohol (1 point)
    if (takesAlcohol) score += 1;
    
    document.getElementById('hasbled').value = score;
    
    // Category
    const categoryEl = document.getElementById('hasBledCategory');
    if (categoryEl) {
        let category = '';
        let color = '';
        if (score <= 1) { category = 'Risiko Rendah'; color = '#27ae60'; }
        else if (score === 2) { category = 'Risiko Menengah'; color = '#f39c12'; }
        else { category = 'Risiko Tinggi (≥3)'; color = '#e74c3c'; }
        categoryEl.textContent = category;
        categoryEl.style.color = color;
    }
    
    // Update status indicators
    updateHASBLEDStatus();
}

// ============================================================
// Auto-calculate on age/gender change
// ============================================================
document.getElementById('age')?.addEventListener('input', () => {
    calculateEGFR();
    calculateASCVD();
    calculateCHA2DS2VASc();
    calculateHASBLED();
});

document.getElementById('gender')?.addEventListener('change', () => {
    calculateEGFR();
    calculateASCVD();
    calculateCHA2DS2VASc();
});

document.getElementById('sbp')?.addEventListener('input', () => {
    detectHypertension();
    calculateASCVD();
    calculateCHA2DS2VASc();
    calculateHASBLED();
});

document.getElementById('dbp')?.addEventListener('input', () => {
    detectHypertension();
    calculateCHA2DS2VASc();
});

// Auto-detect Diabetes on FBG/HbA1c change
document.getElementById('fbg')?.addEventListener('input', () => {
    detectDiabetes();
    calculateASCVD();
    calculateCHA2DS2VASc();
});

document.getElementById('hba1c')?.addEventListener('input', () => {
    detectDiabetes();
    calculateASCVD();
    calculateCHA2DS2VASc();
});

document.getElementById('hdl')?.addEventListener('input', calculateASCVD);
document.getElementById('totalChol')?.addEventListener('input', calculateASCVD);
document.getElementById('smoking')?.addEventListener('change', calculateASCVD);
document.getElementById('race')?.addEventListener('change', () => {
    calculateEGFR();
    calculateASCVD();
});
document.getElementById('liver_disease')?.addEventListener('change', () => {
    calculateHASBLED();
    updateHASBLEDStatus();
});

// Initialize
console.log('CVD Expert System initialized');
loadParameterDescriptions();
setupTooltipHandlers();
