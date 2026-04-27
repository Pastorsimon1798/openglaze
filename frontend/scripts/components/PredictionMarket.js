/**
 * PredictionMarket - Prediction form, AI comparison display
 */
class PredictionMarket {
    constructor(container) {
        this.container = container;
        this.element = null;
        this.combos = [];
        this.render();
        this.loadCombos();
    }

    render() {
        this.element = document.createElement('div');
        this.element.className = 'prediction-market';

        this.element.innerHTML = `
            <div class="pred-header">
                <h3 class="pred-title">Prediction Market</h3>
                <p class="pred-subtitle">Predict glaze outcomes — can you beat the AI?</p>
            </div>
            <div class="pred-form" id="pred-form">
                <div class="form-group">
                    <label>Combination</label>
                    <select id="pred-combo-select" class="pred-select">
                        <option value="">Loading combinations...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Predicted Outcome</label>
                    <select id="pred-outcome" class="pred-select">
                        <option value="success">Will work well</option>
                        <option value="partial">Partially — mixed results</option>
                        <option value="fail">Will have issues</option>
                        <option value="surprise">Surprise — unexpected result</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Confidence: <span id="pred-confidence-val">50</span>%</label>
                    <input type="range" id="pred-confidence" min="10" max="100" value="50"
                           class="pred-confidence-slider"
                           oninput="document.getElementById('pred-confidence-val').textContent = this.value">
                </div>
                <button class="btn btn-primary pred-submit">Submit Prediction</button>
                <div class="pred-result" id="pred-result" style="display:none;"></div>
            </div>
            <div class="pred-leaderboard-section">
                <h4 class="pred-section-title">Leaderboard</h4>
                <div id="pred-leaderboard">
                    <div class="gam-loading">Loading...</div>
                </div>
            </div>
        `;
        this.element.__market = this;
        this.element.querySelector('.pred-submit').addEventListener('click', () => this.submit());
        this.container.appendChild(this.element);
    }

    async loadCombos() {
        try {
            const res = await fetch('/api/combinations?type=user-prediction');
            if (!res.ok) return;
            this.combos = await res.json();
            const select = this.element.querySelector('#pred-combo-select');
            if (!this.combos.length) {
                select.innerHTML = '<option value="">No hypothesis combos available</option>';
                return;
            }
            const sanitize = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize : (s => s);
            select.innerHTML = '<option value="">Select a combination...</option>' +
                this.combos.map(c => `<option value="${parseInt(c.id)}">${sanitize(c.base)} over ${sanitize(c.top)}</option>`).join('');
        } catch (e) {
            console.error('Load combos error:', e);
        }
    }

    async submit() {
        const comboId = this.element.querySelector('#pred-combo-select').value;
        const outcome = this.element.querySelector('#pred-outcome').value;
        const confidence = parseInt(this.element.querySelector('#pred-confidence').value);
        const resultEl = this.element.querySelector('#pred-result');

        if (!comboId) {
            resultEl.style.display = 'block';
            resultEl.className = 'pred-result pred-error';
            resultEl.textContent = 'Please select a combination';
            return;
        }

        const submitBtn = this.element.querySelector('.pred-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const res = await fetch('/api/predictions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ combo_id: parseInt(comboId), predicted_outcome: outcome, confidence })
            });
            const data = await res.json();
            if (res.ok) {
                resultEl.style.display = 'block';
                resultEl.className = 'pred-result pred-success';
                resultEl.innerHTML = `
                    Prediction submitted!<br>
                    <strong>AI predicts:</strong> ${data.ai_prediction || 'N/A'} (${data.ai_confidence || 0}%)
                `;
                this.loadLeaderboard();
            } else {
                resultEl.style.display = 'block';
                resultEl.className = 'pred-result pred-error';
                resultEl.textContent = data.error || 'Failed to submit';
            }
        } catch (e) {
            resultEl.style.display = 'block';
            resultEl.className = 'pred-result pred-error';
            resultEl.textContent = 'Network error';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Prediction';
        }
    }

    async loadLeaderboard() {
        const lbEl = this.element.querySelector('#pred-leaderboard');
        try {
            const res = await fetch('/api/predictions/leaderboard');
            if (!res.ok) { lbEl.innerHTML = '<div class="gam-empty">Not available</div>'; return; }
            const data = await res.json();
            this.renderLeaderboard(data);
        } catch (e) {
            lbEl.innerHTML = '<div class="gam-empty">Failed to load</div>';
        }
    }

    renderLeaderboard(data) {
        const lbEl = this.element.querySelector('#pred-leaderboard');
        const user = data.user || { correct: 0, total: 0, accuracy: 0, points: 0 };
        const ai = data.ai || { correct: 0, total: 0, accuracy: 0, points: 0 };

        lbEl.innerHTML = `
            <table class="pred-lb-table">
                <thead>
                    <tr><th></th><th>Correct</th><th>Total</th><th>Accuracy</th><th>Points</th></tr>
                </thead>
                <tbody>
                    <tr class="pred-lb-you">
                        <td><strong>You</strong></td>
                        <td>${user.correct}</td>
                        <td>${user.total}</td>
                        <td>${user.accuracy}%</td>
                        <td>${user.points}</td>
                    </tr>
                    <tr class="pred-lb-ai">
                        <td><strong>AI (Kama)</strong></td>
                        <td>${ai.correct}</td>
                        <td>${ai.total}</td>
                        <td>${ai.accuracy}%</td>
                        <td>${ai.points}</td>
                    </tr>
                </tbody>
            </table>
        `;
    }
}
