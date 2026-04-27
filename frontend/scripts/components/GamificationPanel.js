/**
 * GamificationPanel - Points display, streak counter, badge grid, activity feed
 */
class GamificationPanel {
    constructor(container) {
        this.container = container;
        this.element = null;
        this.stats = null;
        this.badges = [];
        this.render();
        this.fetch();
    }

    render() {
        this.element = document.createElement('div');
        this.element.className = 'gamification-panel';

        this.element.innerHTML = `
            <div class="gam-header">
                <h3 class="gam-title">Your Progress</h3>
                <button class="gam-refresh">&#x21bb;</button>
            </div>
            <div class="gam-stats" id="gam-stats">
                <div class="gam-stat loading">
                    <span class="gam-stat-value">--</span>
                    <span class="gam-stat-label">Points</span>
                </div>
                <div class="gam-stat loading">
                    <span class="gam-stat-value">--</span>
                    <span class="gam-stat-label">Streak</span>
                </div>
                <div class="gam-stat loading">
                    <span class="gam-stat-value">--</span>
                    <span class="gam-stat-label">Level</span>
                </div>
            </div>
            <div class="gam-badges-section">
                <h4 class="gam-section-title">Badges</h4>
                <div class="gam-badges-grid" id="gam-badges">
                    <div class="gam-loading">Loading...</div>
                </div>
            </div>
            <div class="gam-activity-section">
                <h4 class="gam-section-title">Recent Activity</h4>
                <div class="gam-activity-feed" id="gam-activity">
                    <div class="gam-loading">Loading...</div>
                </div>
            </div>
        `;
        // Wire up refresh button without inline onclick
        this.element.querySelector('.gam-refresh').addEventListener('click', () => this.fetch());
        this.container.appendChild(this.element);
    }

    async fetch() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();
            this.stats = data.stats;
            this.badges = data.badges || [];
            this.renderStats();
            this.renderBadges();
        } catch (e) {
            console.error('Gamification fetch error:', e);
        }
    }

    renderStats() {
        const statsEl = this.element.querySelector('#gam-stats');
        if (!this.stats) return;
        const s = this.stats;
        const streak = s.current_streak || 0;
        statsEl.innerHTML = `
            <div class="gam-stat">
                <span class="gam-stat-value gam-points">${s.points || 0}</span>
                <span class="gam-stat-label">Points</span>
            </div>
            <div class="gam-stat ${streak >= 3 ? 'gam-streak-fire' : ''}">
                <span class="gam-stat-value">${streak}${streak >= 3 ? ' 🔥' : ''}</span>
                <span class="gam-stat-label">Day Streak</span>
            </div>
            <div class="gam-stat">
                <span class="gam-stat-value">${s.level || 1}</span>
                <span class="gam-stat-label">Level</span>
            </div>
        `;
    }

    renderBadges() {
        const grid = this.element.querySelector('#gam-badges');
        if (!this.badges.length) {
            grid.innerHTML = '<div class="gam-empty">No badges earned yet</div>';
            return;
        }
        const _s = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize : (x => x);
        grid.innerHTML = _s(this.badges.map(b => `
            <div class="gam-badge" title="${b.description || b.name}">
                <span class="gam-badge-icon">${b.icon || '⭐'}</span>
                <span class="gam-badge-name">${b.name}</span>
            </div>
        `).join(''));
    }
}
