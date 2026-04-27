/**
 * KamaPanel - AI assistant panel for glaze predictions and questions
 * Slides in from the right side
 */
class KamaPanel {
    constructor(container) {
        this.container = container;
        this.isOpen = false;
        this.messages = [];
        this.element = null;
        this.messagesContainer = null;
        this.input = null;
        this.pendingImage = null; // base64 string
        this.render();
    }

    render() {
        this.element = document.createElement('div');
        this.element.className = 'kama-panel';
        this.element.style.display = 'none';

        // Header
        const header = document.createElement('div');
        header.className = 'kama-header';

        const titleSection = document.createElement('div');
        titleSection.className = 'kama-header-title';

        const avatar = document.createElement('div');
        avatar.className = 'kama-avatar-icon';
        avatar.textContent = '🔮';

        const title = document.createElement('h3');
        title.className = 'kama-title';
        title.textContent = 'Kama';

        titleSection.appendChild(avatar);
        titleSection.appendChild(title);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'kama-close';
        closeBtn.innerHTML = '×';
        closeBtn.addEventListener('click', () => this.close());

        header.appendChild(titleSection);
        header.appendChild(closeBtn);

        // Messages container
        this.messagesContainer = document.createElement('div');
        this.messagesContainer.className = 'kama-messages';

        // Image preview area (above input)
        this.imagePreviewArea = document.createElement('div');
        this.imagePreviewArea.className = 'kama-image-preview-area';
        this.imagePreviewArea.style.display = 'none';

        this.imagePreviewImg = document.createElement('img');
        this.imagePreviewImg.className = 'kama-image-preview';

        const removeImageBtn = document.createElement('button');
        removeImageBtn.className = 'kama-remove-image';
        removeImageBtn.innerHTML = '×';
        removeImageBtn.addEventListener('click', () => this.clearPendingImage());

        this.imagePreviewArea.appendChild(this.imagePreviewImg);
        this.imagePreviewArea.appendChild(removeImageBtn);

        // Input area
        const inputArea = document.createElement('div');
        inputArea.className = 'kama-input-area';
        inputArea.style.position = 'relative';

        this.input = document.createElement('input');
        this.input.className = 'kama-input';
        this.input.placeholder = 'Ask Kama about glazes...';
        this.input.setAttribute('aria-autocomplete', 'list');

        // Inline glaze suggestion dropdown
        this.glazeDropdown = document.createElement('div');
        this.glazeDropdown.className = 'kama-autocomplete-dropdown';
        this.glazeDropdown.style.display = 'none';
        this.glazeDropdown.setAttribute('role', 'listbox');

        this.suggestionIndex = -1;
        this.suggestionMatches = [];
        this.suggestionTimer = null;

        this.input.addEventListener('input', () => {
            clearTimeout(this.suggestionTimer);
            this.suggestionTimer = setTimeout(() => this.showGlazeSuggestions(), 150);
        });

        this.input.addEventListener('keydown', (e) => {
            const dropdownVisible = this.glazeDropdown.style.display !== 'none';

            if (e.key === 'ArrowDown' && dropdownVisible) {
                e.preventDefault();
                this.suggestionIndex = Math.min(this.suggestionIndex + 1, this.suggestionMatches.length - 1);
                this.updateSuggestionActive();
            } else if (e.key === 'ArrowUp' && dropdownVisible) {
                e.preventDefault();
                this.suggestionIndex = Math.max(this.suggestionIndex - 1, 0);
                this.updateSuggestionActive();
            } else if (e.key === 'Tab' && dropdownVisible && this.suggestionIndex >= 0) {
                e.preventDefault();
                this.insertSuggestion(this.suggestionIndex);
            } else if (e.key === 'Escape' && dropdownVisible) {
                e.preventDefault();
                this.hideGlazeSuggestions();
            } else if (e.key === 'Enter' && dropdownVisible && this.suggestionIndex >= 0) {
                e.preventDefault();
                this.insertSuggestion(this.suggestionIndex);
            } else if (e.key === 'Enter' && !e.shiftKey) {
                this.hideGlazeSuggestions();
                e.preventDefault();
                this.sendMessage(this.input.value);
                this.input.value = '';
            }
        });

        this.input.addEventListener('blur', () => {
            setTimeout(() => this.hideGlazeSuggestions(), 150);
        });

        // Hidden file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.accept = 'image/*';
        this.fileInput.style.display = 'none';
        this.fileInput.addEventListener('change', (e) => this.handleImageSelect(e));

        // Upload button
        const uploadBtn = document.createElement('button');
        uploadBtn.className = 'kama-upload-btn';
        uploadBtn.innerHTML = '&#x1F4F7;'; // camera emoji
        uploadBtn.addEventListener('click', () => this.fileInput.click());

        inputArea.appendChild(this.input);
        inputArea.appendChild(this.glazeDropdown);
        inputArea.appendChild(uploadBtn);
        inputArea.appendChild(this.fileInput);

        this.element.appendChild(header);
        this.element.appendChild(this.messagesContainer);
        this.element.appendChild(this.imagePreviewArea);
        this.element.appendChild(inputArea);

        this.container.appendChild(this.element);
    }

    open() {
        this.isOpen = true;
        this.element.style.display = 'flex';
        setTimeout(() => this.input.focus(), 100);
    }

    close() {
        this.isOpen = false;
        this.element.style.display = 'none';
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    addMessage(role, content, imageUrl = null) {
        const msg = document.createElement('div');
        msg.className = `kama-message kama-message-${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'kama-avatar';
        avatar.textContent = role === 'user' ? 'You' : '🔮';

        const text = document.createElement('div');
        text.className = 'kama-text';

        // Support markdown-like formatting
        if (role === 'assistant') {
            text.innerHTML = this.formatContent(content);
        } else {
            text.textContent = content;
        }

        msg.appendChild(avatar);
        msg.appendChild(text);

        // Show image thumbnail in user message if provided
        if (imageUrl) {
            const img = document.createElement('img');
            img.className = 'kama-message-image';
            img.src = imageUrl;
            text.appendChild(img);
        }

        this.messagesContainer.appendChild(msg);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

        return msg;
    }

    formatContent(content, streaming = false) {
        if (streaming) {
            // Lightweight: avoid broken markdown from partial chunks during streaming
            const raw = content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(raw) : raw;
        }
        if (typeof marked !== 'undefined' && marked.parse) {
            const raw = marked.parse(content, { breaks: true, gfm: true });
            return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(raw) : raw;
        }
        // Fallback: bold, italic, line breaks, lists, headers
        const raw = content
            .replace(/^### (.*$)/gm, '<strong style="font-size:1.05em">$1</strong>')
            .replace(/^## (.*$)/gm, '<strong style="font-size:1.1em">$1</strong>')
            .replace(/^# (.*$)/gm, '<strong style="font-size:1.2em">$1</strong>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^- (.*$)/gm, '&bull; $1')
            .replace(/^\d+\. (.*$)/gm, '<span style="margin-left:1em;display:block">$&</span>')
            .replace(/`([^`]+)`/g, '<code style="background:var(--cream);padding:1px 4px;border-radius:3px;font-size:0.9em">$1</code>')
            .replace(/\n/g, '<br>');
        return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(raw) : raw;
    }

    addLoadingMessage() {
        const msg = document.createElement('div');
        msg.className = 'kama-message kama-message-assistant kama-loading';

        const avatar = document.createElement('div');
        avatar.className = 'kama-avatar';
        avatar.textContent = '🔮';

        const text = document.createElement('div');
        text.className = 'kama-text';
        text.innerHTML = '<span class="kama-typing">Analyzing...</span>';

        msg.appendChild(avatar);
        msg.appendChild(text);

        this.messagesContainer.appendChild(msg);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

        return msg;
    }

    handleImageSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (ev) => {
            const dataUrl = ev.target.result;
            // Extract base64 part (after the comma)
            this.pendingImage = dataUrl.split(',')[1];
            this.imagePreviewImg.src = dataUrl;
            this.imagePreviewArea.style.display = 'flex';
        };
        reader.readAsDataURL(file);
        // Reset so same file can be selected again
        this.fileInput.value = '';
    }

    clearPendingImage() {
        this.pendingImage = null;
        this.imagePreviewArea.style.display = 'none';
        this.imagePreviewImg.src = '';
    }

    async sendMessage(text) {
        if (!text || !text.trim()) return;

        const imageForMessage = this.pendingImage ? `data:image/jpeg;base64,${this.pendingImage}` : null;

        this.addMessage('user', text, imageForMessage);

        // Build request body
        const body = { question: text };
        if (this.pendingImage) {
            body.images = [this.pendingImage];
        }
        this.clearPendingImage();

        const loadingMsg = this.addLoadingMessage();
        let responseMsg = null;
        let textEl = null;

        try {
            const response = await fetch('/api/ask/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value);

                // Parse SSE data
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            const eventType = data.type || 'content';

                            if (eventType === 'status') {
                                // Show tool-calling status
                                loadingMsg.remove();
                                this.showStatus(data.message);
                            } else if (eventType === 'content') {
                                // Remove loading/status on first content
                                loadingMsg.remove();
                                this.hideStatus();
                                if (!responseMsg) {
                                    responseMsg = this.addMessage('assistant', '');
                                    textEl = responseMsg.querySelector('.kama-text');
                                }
                                if (data.content) {
                                    textEl.innerHTML = this.formatContent(
                                        textEl.textContent + data.content, true
                                    );
                                }
                            } else if (eventType === 'error') {
                                loadingMsg.remove();
                                this.hideStatus();
                                if (!responseMsg) {
                                    responseMsg = this.addMessage('assistant', '');
                                    textEl = responseMsg.querySelector('.kama-text');
                                }
                                textEl.innerHTML = `<span class="error">${data.content || data.error || 'Unknown error'}</span>`;
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }

                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }

            // Re-render with full markdown after stream completes
            if (responseMsg && textEl) {
                textEl.innerHTML = this.formatContent(textEl.textContent, false);
            }

            // If we never got a response message, remove loading
            if (!responseMsg) {
                loadingMsg.remove();
            }
            this.hideStatus();
        } catch (error) {
            loadingMsg.remove();
            this.hideStatus();
            this.addMessage('assistant', `Error: ${error.message}`);
        }
    }

    showStatus(message) {
        // Reuse or create a status indicator
        let statusEl = this.messagesContainer.querySelector('.kama-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.className = 'kama-status';
            this.messagesContainer.appendChild(statusEl);
        }
        statusEl.textContent = message;
        statusEl.style.display = 'block';
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    hideStatus() {
        const statusEl = this.messagesContainer.querySelector('.kama-status');
        if (statusEl) {
            statusEl.style.display = 'none';
        }
    }

    clear() {
        this.messagesContainer.innerHTML = '';
        this.messages = [];
    }

    showGlazeSuggestions() {
        const query = this.input.value.trim().toLowerCase();
        if (!query || query.length < 1) {
            this.hideGlazeSuggestions();
            return;
        }

        const glazes = window.DATA ? window.DATA.glazes : [];
        this.suggestionMatches = glazes.filter(g =>
            g.name.toLowerCase().includes(query) ||
            (g.code && g.code.toLowerCase().includes(query))
        ).slice(0, 5);

        if (this.suggestionMatches.length === 0) {
            this.hideGlazeSuggestions();
            return;
        }

        this.suggestionIndex = -1;
        this.glazeDropdown.innerHTML = '';

        this.suggestionMatches.forEach((glaze, i) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item kama-suggestion-item';

            const swatch = document.createElement('span');
            swatch.className = 'autocomplete-item-swatch';
            swatch.style.backgroundColor = glaze.hex || '#ccc';
            swatch.style.width = '18px';
            swatch.style.height = '18px';

            const nameEl = document.createElement('span');
            nameEl.className = 'autocomplete-item-name';
            nameEl.textContent = glaze.name;

            item.appendChild(swatch);
            item.appendChild(nameEl);

            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.insertSuggestion(i);
            });

            item.addEventListener('mouseenter', () => {
                this.suggestionIndex = i;
                this.updateSuggestionActive();
            });

            this.glazeDropdown.appendChild(item);
        });

        this.glazeDropdown.style.display = 'block';
    }

    hideGlazeSuggestions() {
        this.glazeDropdown.style.display = 'none';
        this.suggestionIndex = -1;
        this.suggestionMatches = [];
    }

    updateSuggestionActive() {
        const items = this.glazeDropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, i) => {
            item.classList.toggle('active', i === this.suggestionIndex);
        });
    }

    insertSuggestion(index) {
        const glaze = this.suggestionMatches[index];
        if (!glaze) return;

        // Replace the current input value with the glaze name
        this.input.value = glaze.name;
        this.hideGlazeSuggestions();
        this.input.focus();
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

window.KamaPanel = KamaPanel;
