# OpenGlaze FAQ

Frequently asked questions about the open-source ceramic glaze calculator.

## Table of Contents

- [General](#general)
  - [What is OpenGlaze?](#q-what-is-openglaze)
  - [Is OpenGlaze free? What does it cost?](#q-is-openglaze-free-what-does-it-cost)
  - [What license does OpenGlaze use?](#q-what-license-does-openglaze-use)
  - [What programming languages is OpenGlaze written in?](#q-what-programming-languages-is-openglaze-written-in)
  - [Is there a mobile app?](#q-is-there-a-mobile-app)
- [Comparisons](#comparisons)
  - [How is OpenGlaze different from Glazy?](#q-how-is-openglaze-different-from-glazy)
  - [How is OpenGlaze different from DigitalFire?](#q-how-is-openglaze-different-from-digitalfire)
  - [How is OpenGlaze different from INSIGHT?](#q-how-is-openglaze-different-from-insight)
- [Glaze Chemistry](#glaze-chemistry)
  - [What is UMF in ceramics?](#q-what-is-umf-in-ceramics)
  - [Why should I calculate UMF for my glazes?](#q-why-should-i-calculate-umf-for-my-glazes)
  - [What is CTE and why does it matter for glazes?](#q-what-is-cte-and-why-does-it-matter-for-glazes)
  - [How accurate is the CTE calculator?](#q-how-accurate-is-the-cte-calculator)
  - [How does the recipe optimizer work?](#q-how-does-the-recipe-optimizer-work)
- [Self-Hosting and Installation](#self-hosting-and-installation)
  - [Can I self-host OpenGlaze?](#q-can-i-self-host-openglaze)
  - [What are the minimum requirements to self-host?](#q-what-are-the-minimum-requirements-to-self-host)
  - [Does OpenGlaze work on Raspberry Pi?](#q-does-openglaze-work-on-raspberry-pi)
  - [Does OpenGlaze work offline?](#q-does-openglaze-work-offline)
- [Features and Usage](#features-and-usage)
  - [What cone temperatures are supported?](#q-what-cone-temperatures-are-supported)
  - [What atmospheres does OpenGlaze support?](#q-what-atmospheres-does-openglaze-support)
  - [How do I add my own glaze recipes?](#q-how-do-i-add-my-own-glaze-recipes)
  - [Can I import recipes from Glazy?](#q-can-i-import-recipes-from-glazy)
  - [What is the Kama assistant?](#q-what-is-the-kama-assistant)
  - [Does OpenGlaze use AI?](#q-does-openglaze-use-ai)
  - [What is the experiment pipeline?](#q-what-is-the-experiment-pipeline)
  - [Can I collaborate with my studio members?](#q-can-i-collaborate-with-my-studio-members)
  - [Does OpenGlaze replace physical test tiles?](#q-does-openglaze-replace-physical-test-tiles)
- [Privacy and Data](#privacy-and-data)
  - [Is my data private?](#q-is-my-data-private)
- [Community and Contributing](#community-and-contributing)
  - [How do I contribute to OpenGlaze?](#q-how-do-i-contribute-to-openglaze)
  - [Can I use OpenGlaze for teaching?](#q-can-i-use-openglaze-for-teaching)
  - [How do I report a bug or request a feature?](#q-how-do-i-report-a-bug-or-request-a-feature)

---

## General

## Q: What is OpenGlaze?

**A:** OpenGlaze is a free, open-source ceramic glaze calculator and recipe manager built for potters, ceramic artists, studios, and educators. It calculates Unity Molecular Formula (UMF), estimates thermal expansion coefficient (CTE), performs oxide analysis, and includes a computational recipe optimizer. The application is self-hosted, meaning your glaze recipes and data stay on your own infrastructure.

## Q: Is OpenGlaze free? What does it cost?

**A:** OpenGlaze is completely free with no paywalls, subscriptions, or feature gates. The project is funded through voluntary support only -- if the tool saves you materials or a failed kiln load, you can contribute, but you are never required to. Every feature, including the recipe optimizer and AI assistant, is available at no cost.

## Q: What license does OpenGlaze use?

**A:** The code is licensed under the MIT License, which means you can use, modify, distribute, and even sell derivative works with minimal restrictions. Glaze templates and documentation use CC-BY-4.0, which requires attribution. There are no CLAs -- contributions stay MIT-licensed permanently.

## Q: What programming languages is OpenGlaze written in?

**A:** The backend is Python with the Flask web framework. The frontend is a vanilla JavaScript single-page application with no build step -- it loads static scripts directly from the browser. The database layer uses SQLite. The project also includes YAML data files for ceramic reference data and recipes.

## Q: Is there a mobile app?

**A:** There is no native mobile app, but OpenGlaze is a Progressive Web App (PWA). You can install it on your phone or tablet's home screen from the browser and it will behave like a standalone application. The interface is responsive and works in mobile browsers.

---

## Comparisons

## Q: How is OpenGlaze different from Glazy?

**A:** Glazy is a community recipe database with over 100,000 shared recipes. OpenGlaze is a computational chemistry tool focused on UMF analysis, CTE prediction, and recipe optimization. They are complementary: many users maintain their recipe libraries in Glazy and export recipes into OpenGlaze for analysis and optimization. OpenGlaze is also fully self-hosted, while Glazy is a hosted web service.

## Q: How is OpenGlaze different from DigitalFire?

**A:** DigitalFire is an educational reference site with deep content on ceramic chemistry, oxide behavior, and glaze defects. OpenGlaze is a practical calculator -- you enter a recipe and get UMF, CTE, and optimization suggestions immediately. Many potters use DigitalFire for learning the theory and OpenGlaze for the daily calculation work.

## Q: How is OpenGlaze different from INSIGHT?

**A:** INSIGHT is a desktop glaze calculation program with a similar chemistry engine. OpenGlaze provides comparable UMF and CTE calculations but is web-based, open source, and self-hosted. INSIGHT is proprietary software, while OpenGlaze is MIT-licensed and free to modify. OpenGlaze also includes AI-powered consulting and a structured experiment pipeline that INSIGHT does not offer.

---

## Glaze Chemistry

## Q: What is UMF in ceramics?

**A:** UMF stands for Unity Molecular Formula. It is a standardized way to express a glaze recipe as molecular proportions of its oxide components, normalized so that the flux (RO group) oxides sum to 1.0. This allows direct comparison of glazes regardless of their batch size or recipe format. UMF reveals the silica-to-alumina ratio, flux balance, and other properties that determine how a glaze behaves in the kiln.

## Q: Why should I calculate UMF for my glazes?

**A:** UMF tells you what a glaze will do at the molecular level -- something batch percentages alone cannot reveal. With UMF you can predict whether a glaze will be glossy or matte (based on the SiO2:Al2O3 ratio), assess crazing risk (from thermal expansion), compare two recipes on equal footing, and make targeted adjustments instead of guessing. It transforms glaze development from trial-and-error into informed experimentation.

## Q: What is CTE and why does it matter for glazes?

**A:** CTE stands for Coefficient of Thermal Expansion. It measures how much a material expands when heated and contracts when cooled. If a glaze's CTE is too high relative to the clay body, the glaze contracts more on cooling and develops a network of fine cracks (crazing). If the CTE is too low, the glaze can compress and shear off the surface (shivering). Matching CTE between glaze and clay body is essential for a durable, defect-free surface.

## Q: How accurate is the CTE calculator?

**A:** OpenGlaze estimates CTE from published additive oxide expansion coefficients, which gives a useful relative ranking of glazes but is not a substitute for physical measurement. Real-world CTE depends on firing schedule, cooling rate, glaze thickness, and material impurities that the calculator cannot account for. Use the CTE estimate to identify potential problems and guide recipe adjustments, then confirm with actual test tiles.

## Q: How does the recipe optimizer work?

**A:** The optimizer uses stoichiometric analysis to suggest specific material adjustments that move a glaze toward a target property -- such as a target CTE, a matte or glossy surface, reduced alkali content, or less running. You select a target, and the optimizer returns ranked suggestions with predicted outcomes for each reformulated recipe. It predicts chemistry, not firing behavior, so you should always fire a test tile to confirm.

---

## Self-Hosting and Installation

## Q: Can I self-host OpenGlaze?

**A:** Yes. Self-hosting is the primary deployment model. Clone the repository, copy the environment file, and run `docker compose up -d` to have a working instance in about two minutes. The application runs a single Flask container with SQLite and local file uploads. You can also install it manually with Python 3.11+ and `pip install -r requirements.txt`.

## Q: What are the minimum requirements to self-host?

**A:** The minimum requirements are 1 CPU core, 1 GB RAM, and 10 GB storage. You need either Docker with Docker Compose (recommended) or Python 3.11+ for a manual installation. The application runs on port 8768 inside Docker (8767 for manual installs) and works behind any reverse proxy such as nginx, Caddy, or Traefik.

## Q: Does OpenGlaze work on Raspberry Pi?

**A:** Yes. OpenGlaze runs on any platform that supports Python 3.11+ or Docker, including ARM-based devices like the Raspberry Pi. This makes it suitable for offline or local studio use where you run the application on a device connected to your studio network without internet access.

## Q: Does OpenGlaze work offline?

**A:** The core features -- UMF calculation, CTE estimation, recipe optimization, and glaze management -- work entirely offline with no internet connection required. The only feature that requires network access is the Kama AI assistant, which calls either a local Ollama instance or the Anthropic Claude API. If you use Ollama locally, the entire application works offline.

---

## Features and Usage

## Q: What cone temperatures are supported?

**A:** OpenGlaze supports cone 06 through cone 10, covering the full range from low-fire earthenware to high-fire stoneware and porcelain. The included community glaze collection includes 44 recipes across cone 6 oxidation, cone 6 reduction, and cone 10 reduction. The ceramics-foundation data directory includes firing schedules for each cone range.

## Q: What atmospheres does OpenGlaze support?

**A:** OpenGlaze supports three firing atmospheres: oxidation (typical of electric kilns), reduction (typical of gas kilns), and neutral. Atmosphere is tracked per glaze and per firing log, and the chemistry engine accounts for atmosphere when predicting glaze behavior. Community glaze templates are organized by both cone and atmosphere.

## Q: How do I add my own glaze recipes?

**A:** Navigate to the All Glazes view and click Add Glaze. Enter the recipe in percentage, gram, or UMF format along with the cone, atmosphere, and optional metadata like family, surface, and food-safety status. For bulk imports, you can create a YAML file following the community-glazes format in the templates directory and load it through the database seeder or the API.

## Q: Can I import recipes from Glazy?

**A:** Direct Glazy CSV and DigitalFire INSIGHT .dfd import are planned roadmap features. Today, you can import recipes via OpenGlaze's native YAML format or enter them manually through the web interface. The recommended workflow is to create a YAML file following the community-glazes template and load it through the database seeder or API.

## Q: What is the Kama assistant?

**A:** Kama is OpenGlaze's built-in AI assistant that answers technical questions about glaze chemistry. It has access to your glaze library, the ceramics-foundation reference data, and general ceramic chemistry knowledge. You can ask it questions like "Why is my glaze crawling at cone 6?" or "What would 2% rutile do to this celadon?" Kama supports both local LLMs (Ollama) for full privacy and cloud LLMs (Anthropic Claude) for higher-quality responses.

## Q: Does OpenGlaze use AI?

**A:** OpenGlaze includes optional AI features through the Kama assistant. AI is not used for calculations -- the UMF, CTE, and optimization engines are deterministic chemistry code. AI is used only for the conversational assistant that answers glaze chemistry questions and suggests experiments. You can use a local Ollama instance so that no data leaves your machine, or disable AI entirely.

## Q: What is the experiment pipeline?

**A:** The experiment pipeline is a structured six-stage workflow for glaze development: Ideation, Prediction, Application, Firing, Analysis, and Documentation. Each stage has specific fields to fill in, from your initial hypothesis through application method and firing schedule to final results and lessons learned. The pipeline ensures reproducibility and creates a searchable record of your glaze experiments.

## Q: Can I collaborate with my studio members?

**A:** Yes. OpenGlaze includes studio collaboration features where you can create a studio group, invite members by email, and assign roles (Owner, Admin, Member, Viewer). Members share a glaze library, experiment history, firing logs, and photo galleries. Lab assignments let you assign experiments to specific members with deadlines.

## Q: Does OpenGlaze replace physical test tiles?

**A:** No. OpenGlaze is a computational tool that predicts glaze chemistry and suggests adjustments. It cannot predict the actual fired result -- color, texture, surface quality, and defects all depend on factors the software cannot measure, such as your specific materials' impurities, application thickness, and kiln atmosphere. Always fire a physical test tile before committing to a reformulated recipe.

---

## Privacy and Data

## Q: Is my data private?

**A:** Yes. OpenGlaze is self-hosted, meaning your recipes and data live on your own server and never leave your infrastructure unless you choose to share them. The application does not phone home, track usage, or send data to any third-party service. The only exception is the Kama AI assistant -- if you configure it to use the cloud-based Anthropic Claude API, your questions are sent to Anthropic. Using a local Ollama instance keeps all AI queries on your machine.

---

## Community and Contributing

## Q: How do I contribute to OpenGlaze?

**A:** Fork the repository on GitHub, create a feature branch, make your changes, and submit a pull request. Contributions are welcome in chemistry engine improvements, AI features, frontend UI, documentation, testing, DevOps, and ceramic data (recipes, materials, firing schedules). All code contributions are licensed under MIT. See the CONTRIBUTING.md file in the repository for detailed guidelines and commit message conventions.

## Q: Can I use OpenGlaze for teaching?

**A:** Yes. OpenGlaze is well suited for ceramics education. The MIT license permits use in any educational setting without cost. The UMF calculator provides transparent, reproducible results that students can verify by hand. The experiment pipeline teaches systematic glaze development methodology. Universities and community studios can install it on a shared machine for multiple students to use simultaneously through the studio collaboration features.

## Q: How do I report a bug or request a feature?

**A:** Open a GitHub Issue at `https://github.com/Pastorsimon1798/openglaze/issues` for bug reports or feature requests. For general questions and community discussion, use GitHub Discussions at `https://github.com/Pastorsimon1798/openglaze/discussions`. When reporting a bug, include your OpenGlaze version, browser, and steps to reproduce the issue.

---

Have a question not answered here? Ask the community on [GitHub Discussions](https://github.com/Pastorsimon1798/openglaze/discussions).
