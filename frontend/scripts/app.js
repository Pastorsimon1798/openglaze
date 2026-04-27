/**
 * OpenGlaze Main Application
 * State management, rendering, and UI functions
 */

// State
const state = {
    glazes: [],
    combinations: [],
    currentStage: 'idea',
    view: 'canvas',
    currentFamily: 'all'
};

// Components
let stageBar = null;
let kamaPanel = null
let comboDetail = null
let baseAutocomplete = null;
let topAutocomplete = null;
let studioPanel = null;
let glazeTips = null;

// Sanitize HTML to prevent XSS — uses DOMPurify if available
function safeHTML(str) {
    if (typeof DOMPurify !== 'undefined') {
        return DOMPurify.sanitize(str, { ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'span', 'br', 'p', 'h3', 'h4', 'pre', 'code', 'a', 'div', 'ul', 'ol', 'li'], ALLOWED_ATTR: ['class', 'style', 'href', 'title'] });
    }
    const el = document.createElement('div');
    el.textContent = str;
    return el.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log('OpenGlaze initializing...')
    console.log('window.DATA exists:', !!window.DATA)

    // Mobile sidebar toggle
    initMobileSidebar()

    // Initialize components
    const stageBarContainer = document.getElementById('stage-bar')
    const kamaContainer = document.getElementById('kama-container')

    console.log('stageBarContainer:', stageBarContainer)
    console.log('kamaContainer:', kamaContainer)

    try {
        stageBar = new StageBar(
            stageBarContainer,
            ['idea', 'predicting', 'testing', 'fired', 'documented'],
            (stage) => filterByStage(stage)
        )
        console.log('StageBar created')
    } catch (e) {
        console.error('StageBar error:', e)
    }

    try {
        kamaPanel = new KamaPanel(kamaContainer)
        window.kamaPanel = kamaPanel
        console.log('KamaPanel created')
    } catch (e) {
        console.error('KamaPanel error:', e)
    }

    try {
        comboDetail = new ComboDetailPanel(document.body)
        console.log('ComboDetailPanel created')
    } catch (e) {
        console.error('ComboDetailPanel error:', e)
    }

    try {
        const canvas = document.getElementById('canvas')
        glazeTips = new GlazeTips(canvas)
        console.log('GlazeTips created')
    } catch (e) {
        console.error('GlazeTips error:', e)
    }

    // Load data from API or fallback to DATA module
    state.glazes = window.DATA ? window.DATA.glazes : []
    console.log('Loaded glazes:', state.glazes.length)

    // Load combinations with new type system
    if (window.DATA) {
        const researchBacked = (window.DATA.research_backed || []).map(c => ({...c, stage: 'documented', type: 'research-backed', prediction_grade: c.prediction_grade || 'unknown'}))
        const userPredictions = (window.DATA.user_predictions || []).map(c => ({...c, stage: 'idea', type: 'user-prediction', prediction_grade: c.prediction_grade || 'unknown'}))
        state.combinations = [...researchBacked, ...userPredictions]
        console.log('Loaded combinations:', state.combinations.length)
        console.log('Research-backed:', researchBacked.length, 'User predictions:', userPredictions.length)
    }

    console.log('Current stage:', state.currentStage)
    console.log('Combinations with stage "idea":', state.combinations.filter(c => c.stage === 'idea').length)

    populateGlazeSelects()
    initAutocompletes()
    renderCombinations()
    updateStageCounts()

    console.log('OpenGlaze ready')
})

// Render Functions
function renderCombinations() {
    console.log('renderCombinations called')
    const canvas = document.getElementById('canvas')
    const emptyState = document.getElementById('empty-state')

    console.log('Canvas element:', canvas)
    console.log('Empty state element:', emptyState)
    console.log('Total combinations:', state.combinations.length)
    console.log('Current stage filter:', state.currentStage)

    // Filter by stage and family
    let filtered = state.combinations.filter(c => c.stage === state.currentStage)
    console.log('Filtered combinations:', filtered.length)

    // Apply family filter if set
    if (state.currentFamily !== 'all') {
        filtered = filtered.filter(combo => {
            const baseGlaze = state.glazes.find(g => g.name === combo.base)
            return baseGlaze && baseGlaze.family === state.currentFamily
        })
    }

    canvas.innerHTML = ''

    if (filtered.length === 0) {
        emptyState.style.display = 'flex'
        if (state.currentFamily !== 'all') {
            emptyState.querySelector('h2').textContent = `No ${state.currentFamily} combinations in ${state.currentStage}`
        } else {
            emptyState.querySelector('h2').textContent = `No combinations in ${state.currentStage}`
        }
        emptyState.querySelector('p').textContent = 'Create new combinations or change the filter'
    } else {
        emptyState.style.display = 'none'
        filtered.forEach(combo => {
            // Find glaze colors
            const baseGlaze = state.glazes.find(g => g.name === combo.base)
            const topGlaze = state.glazes.find(g => g.name === combo.top)

            new ComboCard(canvas, {
                ...combo,
                baseColor: baseGlaze?.hex,
                topColor: topGlaze?.hex
            })
        })
    }
}

function updateStageCounts() {
    const counts = {}
    state.combinations.forEach(c => {
        const stage = c.stage || 'idea'
        counts[stage] = (counts[stage] || 0) + 1
    })

    if (stageBar) {
        stageBar.updateCounts(counts)
    }
}

// UI Functions
function switchView(view) {
    state.view = view
    document.querySelectorAll('.sidebar-item[data-view]').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view)
    })

    // Handle different views
    if (view === 'canvas') {
        renderCombinations()
        if (glazeTips) glazeTips.hide()
    } else if (view === 'glazes') {
        renderGlazesView()
        if (glazeTips) glazeTips.hide()
    } else if (view === 'archive') {
        renderArchiveView()
        if (glazeTips) glazeTips.hide()
    } else if (view === 'photos') {
        renderPhotosView()
        if (glazeTips) glazeTips.hide()
    } else if (view === 'studio') {
        renderStudioView()
        if (glazeTips) glazeTips.hide()
    } else if (view === 'tips') {
        if (glazeTips) glazeTips.show()
    }
}

function renderGlazesView() {
    const canvas = document.getElementById('canvas')
    const emptyState = document.getElementById('empty-state')

    canvas.innerHTML = ''

    // Filter glazes by family
    let filteredGlazes = state.glazes
    if (state.currentFamily !== 'all') {
        filteredGlazes = state.glazes.filter(g => g.family === state.currentFamily)
    }

    if (filteredGlazes.length === 0) {
        emptyState.style.display = 'flex'
        emptyState.querySelector('h2').textContent = state.currentFamily === 'all' ? 'No glazes loaded' : `No ${state.currentFamily} glazes`
        emptyState.querySelector('p').textContent = 'Glazes will appear here when loaded from the studio inventory'
    } else {
        emptyState.style.display = 'none'

        // Group glazes by family
        const grouped = {}
        window.FAMILY_ORDER.forEach(family => {
            grouped[family] = []
        })

        filteredGlazes.forEach(glaze => {
            const family = glaze.family || 'Other'
            if (grouped[family]) {
                grouped[family].push(glaze)
            }
        })

        // Render each family section
        window.FAMILY_ORDER.forEach(family => {
            const glazes = grouped[family]
            if (glazes.length === 0) return

            const section = document.createElement('div')
            section.className = 'glaze-family-section'
            section.innerHTML = safeHTML(`
                <div class="glaze-family-header">
                    <h3 class="glaze-family-title">${family}</h3>
                    <span class="glaze-family-count">${glazes.length} glazes</span>
                </div>
                <div class="glaze-family-grid"></div>
            `)

            const grid = section.querySelector('.glaze-family-grid')
            glazes.forEach(glaze => {
                const card = document.createElement('div')
                card.className = 'glaze-detail-card card'
                card.innerHTML = safeHTML(`
                    <div class="glaze-detail-header">
                        <div class="glaze-detail-swatch" style="background-color: ${glaze.hex || '#ccc'}"></div>
                        <div class="glaze-detail-info">
                            <h4 class="glaze-detail-title">${glaze.name}</h4>
                            ${glaze.code ? `<span class="glaze-detail-code">${glaze.code}</span>` : ''}
                            ${glaze.family ? `<span class="glaze-detail-family">${glaze.family}</span>` : ''}
                        </div>
                    </div>
                    ${glaze.chemistry ? `
                        <div class="glaze-detail-section">
                            <h4>Chemistry</h4>
                            <p>${glaze.chemistry}</p>
                        </div>
                    ` : ''}
                    ${glaze.behavior ? `
                        <div class="glaze-detail-section">
                            <h4>Behavior</h4>
                            <p>${glaze.behavior}</p>
                        </div>
                    ` : ''}
                    ${glaze.layering ? `
                        <div class="glaze-detail-section">
                            <h4>Layering</h4>
                            <p>${glaze.layering}</p>
                        </div>
                    ` : ''}
                    ${glaze.recipe ? `
                        <div class="glaze-detail-section">
                            <h4>Recipe</h4>
                            <pre class="glaze-detail-recipe">${glaze.recipe}</pre>
                        </div>
                    ` : ''}
                    ${glaze.warning ? `
                        <div class="glaze-detail-warning">
                            ⚠ ${glaze.warning}
                        </div>
                    ` : ''}
                    ${glaze.source ? `
                        <p class="glaze-detail-source">Source: ${glaze.source}</p>
                    ` : ''}
                `)
                grid.appendChild(card)
            })

            canvas.appendChild(section)
        })
    }
}

function renderArchiveView() {
    const canvas = document.getElementById('canvas')
    const emptyState = document.getElementById('empty-state')

    const archived = state.combinations.filter(c => c.stage === 'proven' || c.stage === 'fired')

    canvas.innerHTML = ''

    if (archived.length === 0) {
        emptyState.style.display = 'flex'
        emptyState.querySelector('h2').textContent = 'Archive is empty'
        emptyState.querySelector('p').textContent = 'Proven combinations will be archived here'
    } else {
        emptyState.style.display = 'none'
        archived.forEach(combo => {
            const baseGlaze = state.glazes.find(g => g.name === combo.base)
            const topGlaze = state.glazes.find(g => g.name === combo.top)

            new ComboCard(canvas, {
                ...combo,
                baseColor: baseGlaze?.hex,
                topColor: topGlaze?.hex
            })
        })
    }
}

async function renderPhotosView() {
    const canvas = document.getElementById('canvas')
    const emptyState = document.getElementById('empty-state')

    canvas.innerHTML = ''
    emptyState.style.display = 'none'

    const gallery = new PhotoGallery(canvas)
    await gallery.load()
    gallery.render()
}

function renderStudioView() {
    const canvas = document.getElementById('canvas')
    const emptyState = document.getElementById('empty-state')

    canvas.innerHTML = ''
    emptyState.style.display = 'none'

    if (studioPanel) {
        studioPanel.destroy()
    }
    studioPanel = new StudioPanel(canvas)
}

function filterByStage(stage) {
    state.currentStage = stage
    renderCombinations()
}

function filterByFamily(family) {
    state.currentFamily = family
    // Update sidebar active state
    document.querySelectorAll('.family-filter').forEach(item => {
        item.classList.toggle('active', item.dataset.family === family)
    })
    // Re-render current view
    if (state.view === 'canvas') {
        renderCombinations()
    } else if (state.view === 'glazes') {
        renderGlazesView()
    }
}

function populateGlazeSelects() {
    // No-op — replaced by autocomplete
}

function initAutocompletes() {
    const baseContainer = document.getElementById('base-glaze-autocomplete')
    const topContainer = document.getElementById('top-glaze-autocomplete')
    if (!baseContainer || !topContainer) return

    baseAutocomplete = new GlazeAutocomplete(baseContainer, {
        glazes: state.glazes,
        placeholder: 'Search base glaze...',
        onSelect: (glaze) => {
            // Exclude selected base from top suggestions
            if (topAutocomplete) {
                topAutocomplete.setExclude([glaze.name])
            }
        }
    })

    topAutocomplete = new GlazeAutocomplete(topContainer, {
        glazes: state.glazes,
        placeholder: 'Search top glaze...',
        onSelect: (glaze) => {
            // Exclude selected top from base suggestions
            if (baseAutocomplete) {
                baseAutocomplete.setExclude([glaze.name])
            }
        }
    })
}

// Modal Functions
function openCreateModal() {
    document.getElementById('create-modal').style.display = 'flex'
}

function closeCreateModal() {
    document.getElementById('create-modal').style.display = 'none'
}

async function createCombination() {
    const base = baseAutocomplete ? baseAutocomplete.getValue().trim() : ''
    const top = topAutocomplete ? topAutocomplete.getValue().trim() : ''

    if (!base || !top) {
        alert('Please select both glazes')
        return
    }

    // Validate against known glazes
    const baseGlaze = state.glazes.find(g => g.name.toLowerCase() === base.toLowerCase())
    const topGlaze = state.glazes.find(g => g.name.toLowerCase() === top.toLowerCase())

    if (!baseGlaze || !topGlaze) {
        alert('Please select valid glaze names from the suggestions')
        return
    }

    // Create new combo object
    const newCombo = {
        id: Date.now(),
        base: baseGlaze.name,
        top: topGlaze.name,
        type: 'user-prediction',
        stage: 'idea',
        prediction_grade: 'unknown',
        prediction: null,
        risk: 'unknown'
    }

    state.combinations.push(newCombo)
    closeCreateModal()
    renderCombinations()
    updateStageCounts()

    // Show combo detail panel
    comboDetail.show(newCombo, baseGlaze, topGlaze)

    // Reset autocompletes
    if (baseAutocomplete) baseAutocomplete.reset()
    if (topAutocomplete) topAutocomplete.reset()
}

// Command Palette
function openCommandPalette() {
    toggleKama()
}

// Kama Toggle
function toggleKama() {
    if (kamaPanel) {
        kamaPanel.toggle()
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + K for command palette
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        openCommandPalette()
    }

    // Escape to close modals
    if (e.key === 'Escape') {
        closeCreateModal()
        if (comboDetail && comboDetail.isOpen) {
            comboDetail.hide()
        }
        if (kamaPanel && kamaPanel.isOpen) {
            kamaPanel.close()
        }
    }
})

// Listen for combo selection events
document.addEventListener('combo-selected', (e) => {
    const combo = e.detail.combo
    const baseGlaze = state.glazes.find(g => g.name === combo.base)
    const topGlaze = state.glazes.find(g => g.name === combo.top)

    if (comboDetail) {
        comboDetail.show(combo, baseGlaze, topGlaze)
    }
})

// Listen for stage changes
document.addEventListener('combo-stage-changed', async (e) => {
    const { comboId, stage } = e.detail

    // Update local state
    const combo = state.combinations.find(c => c.id === comboId)
    if (combo) {
        combo.stage = stage
    }

    renderCombinations()
    updateStageCounts()
})

// ==========================================
// MOBILE SIDEBAR
// ==========================================

function initMobileSidebar() {
    const sidebar = document.getElementById('sidebar')
    const toggleBtn = document.querySelector('.menu-toggle')
    if (!sidebar || !toggleBtn) return

    // Create backdrop
    const backdrop = document.createElement('div')
    backdrop.className = 'sidebar-backdrop'
    backdrop.id = 'sidebar-backdrop'
    document.body.appendChild(backdrop)

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open')
        backdrop.classList.toggle('active')
    })

    backdrop.addEventListener('click', () => {
        sidebar.classList.remove('open')
        backdrop.classList.remove('active')
    })

    // Close sidebar on view switch (mobile)
    document.querySelectorAll('.sidebar-item[data-view]').forEach(item => {
        item.addEventListener('click', () => {
            sidebar.classList.remove('open')
            backdrop.classList.remove('active')
        })
    })
}

// ==========================================
// PWA
// ==========================================

let deferredInstallPrompt = null

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredInstallPrompt = e
    const btn = document.getElementById('pwa-install-btn')
    if (btn) btn.classList.add('visible')
})

function installPWA() {
    if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt()
        deferredInstallPrompt.userChoice.then(choice => {
            deferredInstallPrompt = null
            const btn = document.getElementById('pwa-install-btn')
            if (btn) btn.classList.remove('visible')
        })
    }
}

// Register service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
}
