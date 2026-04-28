/**
 * OpenGlaze API Client
 */

const API = {
    _baseUrl: '/api',
    _token: localStorage.getItem('simple_auth_token') || null,

    setToken(token) {
        this._token = token;
        localStorage.setItem('simple_auth_token', token);
    },

    _headers() {
        const h = { 'Content-Type': 'application/json' };
        if (this._token) {
            h['Authorization'] = `Bearer ${this._token}`;
        }
        return h;
    },

    async _fetch(path, options = {}) {
        try {
            const resp = await fetch(this._baseUrl + path, {
                headers: this._headers(),
                ...options,
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        } catch (e) {
            console.warn(`API ${path} failed, using fallback:`, e.message);
            return null;
        }
    },

    // ---- Existing ----

    async getGlazes() {
        const result = await this._fetch('/glazes');
        return result || [];
    },

    async getCombinations() {
        const result = await this._fetch('/combinations');
        if (result && result.length > 0) {
            return result.map(c => ({
                ...c,
                stage: c.stage || 'idea',
                prediction_grade: c.prediction_grade || 'unknown',
            }));
        }
        return [];
    },

    async createCombination(data) {
        const result = await this._fetch('/combinations', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        return result;
    },

    async updateCombination(id, updates) {
        return await this._fetch(`/combinations/${id}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    },

    async simulateCombination(id) {
        return await this._fetch(`/combinations/${id}/simulate`, {
            method: 'POST',
        });
    },

    // ---- Simple Auth ----

    async simpleLogin(displayName) {
        return await this._fetch('/auth/simple-login', {
            method: 'POST',
            body: JSON.stringify({ display_name: displayName }),
        });
    },

    async getMe() {
        return await this._fetch('/auth/me');
    },

    // ---- Studios ----

    async createStudio(name, displayName) {
        return await this._fetch('/studios', {
            method: 'POST',
            body: JSON.stringify({ name, display_name: displayName }),
        });
    },

    async joinStudio(inviteCode, displayName) {
        return await this._fetch('/studios/join', {
            method: 'POST',
            body: JSON.stringify({ invite_code: inviteCode, display_name: displayName }),
        });
    },

    async getStudios() {
        return await this._fetch('/studios');
    },

    async getStudioDetail(studioId) {
        return await this._fetch(`/studios/${studioId}`);
    },

    // ---- Lab Queue ----

    async getLabQueue(studioId) {
        return await this._fetch(`/studios/${studioId}/lab-queue`);
    },

    async claimCombo(studioId, comboId) {
        return await this._fetch(`/studios/${studioId}/lab-queue/${comboId}/claim`, {
            method: 'POST',
        });
    },

    async releaseCombo(studioId, comboId) {
        return await this._fetch(`/studios/${studioId}/lab-queue/${comboId}/release`, {
            method: 'POST',
        });
    },

    // ---- Firing Log ----

    async logFiringResult(expId, logData) {
        return await this._fetch(`/experiments/${expId}/firing-log`, {
            method: 'POST',
            body: JSON.stringify(logData),
        });
    },

    async shareExperiment(expId, studioId) {
        return await this._fetch(`/experiments/${expId}/share`, {
            method: 'POST',
            body: JSON.stringify({ studio_id: studioId }),
        });
    },

    async getStudioExperiments(studioId) {
        return await this._fetch(`/studios/${studioId}/experiments`);
    },
};

window.API = API;
