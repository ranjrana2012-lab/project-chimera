async function send() {
    const text = document.getElementById('userInput').value;
    if (!text) return;
    
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('output').style.opacity = '0.5';
    
    try {
        const res = await fetch('/api/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        });
        const data = await res.json();
        
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('output').style.opacity = '1';
        
        document.getElementById('output').innerHTML = `
            <div style="margin-bottom: 1rem;">
                <span class="badge badge-strategy">${data.strategy}</span>
                <span class="badge badge-primary" style="margin-left: 0.5rem;">${data.sentiment} (${(data.score*100).toFixed(1)}%)</span>
            </div>
            <div style="color: var(--text); font-size: 1.15rem; font-style: italic;">
                "${data.response}"
            </div>
            <div class="meta">
                <span>Latency: ${(data.latency_ms).toFixed(0)} ms</span>
                <span>🔉 Audio Broadcasted</span>
            </div>
        `;
        
        // Virtual DMX Lighting Simulation Transitions
        if (data.strategy === 'momentum_build') {
            document.body.style.background = 'linear-gradient(135deg, #450a0a 0%, #0f172a 100%)';
            document.querySelector('.glow').style.background = 'radial-gradient(circle, #f43f5e 0%, transparent 70%)';
            document.querySelector('.glow').style.opacity = '0.35';
        } else if (data.strategy === 'supportive_care') {
            document.body.style.background = 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)';
            document.querySelector('.glow').style.background = 'radial-gradient(circle, #38bdf8 0%, transparent 70%)';
            document.querySelector('.glow').style.opacity = '0.25';
        } else {
            document.body.style.background = 'linear-gradient(135deg, #020617 0%, var(--bg) 100%)';
            document.querySelector('.glow').style.background = 'radial-gradient(circle, var(--secondary) 0%, transparent 70%)';
            document.querySelector('.glow').style.opacity = '0.15';
        }
    } catch (e) {
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('output').style.opacity = '1';
        document.getElementById('output').innerHTML = `<span style="color: #f87171;">Error processing request. Ensure Chimera backend is healthy.</span>`;
    } finally {
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') send();
});
