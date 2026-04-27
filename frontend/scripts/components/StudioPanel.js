/**
 * StudioPanel - Studio setup, join, and management UI
 */
class StudioPanel {
    constructor(container) {
        this.container = container;
        this.element = null;
        this.currentStudio = null;
        this.token = localStorage.getItem('simple_auth_token');
        this.displayName = localStorage.getItem('simple_auth_display_name') || '';
        this.userId = localStorage.getItem('simple_auth_user_id');
        this.render();
    }

    render() {
        this.element = document.createElement('div');
        this.element.className = 'studio-panel';

        if (!this.token) {
            this._renderLogin();
        } else {
            this._renderStudioView();
        }

        this.container.appendChild(this.element);
    }

    _renderLogin() {
        this.element.innerHTML = `
            <div class="studio-login card">
                <h3>Join the Studio</h3>
                <p class="text-secondary">Enter your name to get started.</p>
                <div class="form-group">
                    <input type="text" id="studio-display-name"
                           placeholder="Your name"
                           value="${this.displayName}"
                           maxlength="50"
                           class="form-input">
                </div>
                <button class="btn btn-primary" id="studio-login-btn">Go</button>
            </div>
        `;

        this.element.querySelector('#studio-login-btn').addEventListener('click', () => this._login());

        const input = this.element.querySelector('#studio-display-name');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._login();
        });
        if (this.displayName) input.focus();
    }

    async _login() {
        const name = (this.element.querySelector('#studio-display-name')?.value || '').trim();
        if (!name) return;

        const result = await API.simpleLogin(name);
        if (!result) {
            alert('Login failed. Please try again.');
            return;
        }

        this.token = result.token;
        this.userId = result.user_id;
        this.displayName = name;
        localStorage.setItem('simple_auth_token', result.token);
        localStorage.setItem('simple_auth_user_id', result.user_id);
        localStorage.setItem('simple_auth_display_name', name);

        // Set token for API calls
        API.setToken(result.token);

        this._renderStudioView();
        this._loadStudios();
    }

    _renderStudioView() {
        this.element.innerHTML = `
            <div class="studio-header">
                <h3>Studio</h3>
                <span class="studio-user-name">${this.displayName}</span>
            </div>
            <div id="studio-content"></div>
        `;
    }

    async _loadStudios() {
        const studios = await API.getStudios();
        const content = this.element.querySelector('#studio-content');
        if (!content) return;

        if (!studios || studios.length === 0) {
            this._renderNoStudio(content);
        } else {
            this.currentStudio = studios[0];
            this._renderStudioDetail(content, studios);
        }
    }

    _renderNoStudio(container) {
        container.innerHTML = `
            <div class="studio-actions card">
                <div class="studio-action">
                    <h4>Create a Studio</h4>
                    <input type="text" id="create-studio-name"
                           placeholder="Studio name"
                           maxlength="100"
                           class="form-input">
                    <button class="btn btn-primary" id="create-studio-btn">Create</button>
                </div>
                <div class="studio-divider">
                    <span>or</span>
                </div>
                <div class="studio-action">
                    <h4>Join a Studio</h4>
                    <input type="text" id="join-studio-code"
                           placeholder="Invite code"
                           maxlength="6"
                           class="form-input"
                           style="text-transform: uppercase;">
                    <button class="btn btn-secondary" id="join-studio-btn">Join</button>
                </div>
            </div>
        `;

        container.querySelector('#create-studio-btn').addEventListener('click', () => this._createStudio());
        container.querySelector('#join-studio-btn').addEventListener('click', () => this._joinStudio());

        container.querySelector('#create-studio-name').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._createStudio();
        });
        container.querySelector('#join-studio-code').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._joinStudio();
        });
    }

    _renderStudioDetail(container, studios) {
        const studio = studios[0];
        const members = studio.members || [];

        container.innerHTML = (typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize : (s => s))(`
            <div class="studio-detail card">
                <div class="studio-detail-header">
                    <h4>${studio.name}</h4>
                    <div class="studio-invite">
                        <span class="invite-code" id="invite-code-display">${studio.invite_code}</span>
                        <button class="btn btn-small btn-secondary" id="copy-invite-btn">Copy</button>
                    </div>
                </div>
                <div class="studio-members">
                    <h5>Members (${members.length})</h5>
                    <ul class="member-list">
                        ${members.map(m => `
                            <li>
                                <span class="member-name">${m.display_name}</span>
                                <span class="member-role">${m.role}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
            <div id="lab-queue-container" style="margin-top: 1.5rem;"></div>
        `);

        container.querySelector('#copy-invite-btn').addEventListener('click', () => {
            navigator.clipboard.writeText(studio.invite_code).then(() => {
                const btn = container.querySelector('#copy-invite-btn');
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            });
        });

        // Initialize lab queue
        const labContainer = container.querySelector('#lab-queue-container');
        if (labContainer && window.LabQueueBoard) {
            new LabQueueBoard(labContainer, studio.id);
        }
    }

    async _createStudio() {
        const name = (this.element.querySelector('#create-studio-name')?.value || '').trim();
        if (!name) return;

        const studio = await API.createStudio(name, this.displayName);
        if (studio) {
            this._loadStudios();
        } else {
            alert('Failed to create studio.');
        }
    }

    async _joinStudio() {
        const code = (this.element.querySelector('#join-studio-code')?.value || '').trim();
        if (!code) return;

        const studio = await API.joinStudio(code, this.displayName);
        if (studio) {
            this._loadStudios();
        } else {
            alert('Invalid invite code.');
        }
    }

    getStudioId() {
        return this.currentStudio?.id || null;
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

window.StudioPanel = StudioPanel;
