/**
 * PhotoUploadForm - Drag-and-drop / camera photo upload component
 */
class PhotoUploadForm {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.onSuccess = options.onSuccess || (() => {});
        this.onCancel = options.onCancel || (() => {});
        this.element = null;
        this.render();
    }

    render() {
        this.element = document.createElement('div');
        this.element.className = 'photo-upload-form';
        this.element.innerHTML = `
            <div class="photo-upload-area" tabindex="0">
                <input type="file" accept="image/jpeg,image/png,image/webp" capture="environment">
                <div class="photo-upload-icon">&#128247;</div>
                <div class="photo-upload-text">Drop a photo here or tap to upload</div>
                <div class="photo-upload-hint">JPG, PNG, or WebP up to 5MB</div>
            </div>
            <div class="photo-preview-container" style="display: none;">
                <div class="photo-preview">
                    <img alt="Preview">
                    <button class="photo-preview-remove" title="Remove">&times;</button>
                </div>
                <div style="display: flex; gap: var(--space-2); margin-top: var(--space-3);">
                    <button class="btn btn-primary photo-upload-save">Save Photo</button>
                    <button class="btn btn-secondary photo-upload-cancel">Cancel</button>
                </div>
            </div>
        `;

        this.container.appendChild(this.element);
        this._attachEvents();
    }

    _attachEvents() {
        const area = this.element.querySelector('.photo-upload-area');
        const input = this.element.querySelector('input[type="file"]');
        const previewContainer = this.element.querySelector('.photo-preview-container');
        const previewImg = this.element.querySelector('.photo-preview img');
        const removeBtn = this.element.querySelector('.photo-preview-remove');
        const saveBtn = this.element.querySelector('.photo-upload-save');
        const cancelBtn = this.element.querySelector('.photo-upload-cancel');

        let selectedFile = null;

        // Click to open file picker
        area.addEventListener('click', () => input.click());
        area.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') input.click();
        });

        // File selected
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                this._showPreview(selectedFile, previewImg, previewContainer, area);
            }
        });

        // Drag and drop
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                this._showPreview(selectedFile, previewImg, previewContainer, area);
            }
        });

        // Remove preview
        removeBtn.addEventListener('click', () => {
            selectedFile = null;
            previewContainer.style.display = 'none';
            area.style.display = '';
            input.value = '';
        });

        // Save
        saveBtn.addEventListener('click', () => {
            if (!selectedFile) return;
            this._upload(selectedFile, saveBtn);
        });

        // Cancel
        cancelBtn.addEventListener('click', () => {
            selectedFile = null;
            this.onCancel();
        });
    }

    _showPreview(file, imgEl, previewContainer, area) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imgEl.src = e.target.result;
            area.style.display = 'none';
            previewContainer.style.display = '';
        };
        reader.readAsDataURL(file);
    }

    async _upload(file, btn) {
        const originalText = btn.textContent;
        btn.textContent = 'Uploading...';
        btn.disabled = true;

        const formData = new FormData();
        formData.append('photo', file);

        try {
            const headers = {};
            const token = localStorage.getItem('simple_auth_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            const resp = await fetch('/api/upload', { method: 'POST', body: formData, headers });
            const data = await resp.json();

            if (data.success) {
                this.onSuccess(data.url, data.path);
            } else {
                alert(data.error || 'Upload failed');
                btn.textContent = originalText;
                btn.disabled = false;
            }
        } catch (err) {
            alert('Upload failed: ' + err.message);
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

window.PhotoUploadForm = PhotoUploadForm;
