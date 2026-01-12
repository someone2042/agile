const fileInput = document.getElementById('fileInput');
const imagePreview = document.getElementById('imagePreview');
const uploadPrompt = document.getElementById('uploadPrompt');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultDiv = document.getElementById('result');
const downloadBox = document.getElementById('downloadBox');

let analysisResult = null;

// 1. Image Upload & Preview
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
            uploadPrompt.style.display = 'none'; // Hide the icon/text
            analyzeBtn.disabled = false;

            // Reset UI for new scan
            resultDiv.style.display = 'none';
            downloadBox.style.display = 'none';
            analysisResult = null;
        };
        reader.readAsDataURL(file);
    }
});

// 2. Analyze (Lightweight)
analyzeBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    // UI Loading State
    const originalText = analyzeBtn.innerHTML;
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Server Error");

        const data = await response.json();
        analysisResult = data;

        // Show Result
        resultDiv.style.display = 'block';
        const isCancer = data.prediction.toLowerCase() === 'cancerous';

        resultDiv.className = isCancer ? 'result-cancerous' : 'result-non-cancerous';
        resultDiv.innerHTML = `
            <h3 style="margin-bottom: 0.5rem;">${data.prediction.toUpperCase()}</h3>
            <p>Confidence: <strong>${(data.confidence * 100).toFixed(2)}%</strong></p>
        `;

        downloadBox.style.display = 'block'; // Reveal download options

    } catch (err) {
        console.error(err);
        alert("Could not connect to the analysis server.");
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = originalText;
    }
});

// 3. Download (Heavy Generation)
document.getElementById('downloadBtn').addEventListener('click', async () => {
    if (!analysisResult) return;

    const file = fileInput.files[0];
    const type = document.getElementById('reportType').value;
    const lang = document.getElementById('language').value;
    const downloadBtn = document.getElementById('downloadBtn');

    // UI Loading State
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Generating Report...';
    downloadBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('prediction', analysisResult.prediction);
    formData.append('confidence', analysisResult.confidence);
    formData.append('report_type', type);
    formData.append('language', lang);

    try {
        const response = await fetch('http://localhost:8000/generate_report', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Report generation failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Medical_Report_${Date.now()}.${type === 'pdf' ? 'pdf' : 'docx'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch (err) {
        alert("Error generating report. Please check the backend console.");
    } finally {
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
});