# Somchand Ratangwal — AI Automation & Application Security Specialist

A high-performance, standalone personal portfolio web application built with modern **semantic HTML5**, **CSS3 Design Tokens**, and **Vanilla JavaScript** (ES6+). Zero server-side runtime dependencies, ready for instant, zero-config deployment on **Vercel**, **Cloudflare Pages**, and **GitHub Pages**.

---

## ⚡ Deployment & Hosting (Zero-Config)

This repository is structured as a pure static web application. No build step, package manager, or backend runtime is required:

### 1. Vercel
1. Import this repository into Vercel.
2. Framework Preset: **Other** (Static HTML).
3. Build Command: *leave empty*.
4. Output Directory: `.` (root).
5. Click **Deploy**.

### 2. Cloudflare Pages
1. Connect this repository in Cloudflare Pages Dashboard.
2. Build command: *None*.
3. Build output directory: `/` (root).
4. Click **Save and Deploy**.

### 3. GitHub Pages
1. Go to repository **Settings** &rarr; **Pages**.
2. Under **Build and deployment**, select **Deploy from a branch**.
3. Choose branch `main` and folder `/ (root)`.
4. Click **Save**.

---

## 🚀 Local Preview

You can open `index.html` directly in any web browser, or serve it with any lightweight static file server:

```bash
# Using Python's built-in static HTTP module:
python3 -m http.server 8080

# Or using Node.js npx:
npx serve .
```

---

## 📁 Repository Structure

```text
Portfolio_Somchand_max/
├── index.html           # Main portfolio entrypoint with OpenGraph & SEO tags
├── resume.html          # Clean, printable curriculum vitae
├── style.css            # Responsive CSS variables, typography, and dark/light themes
├── resume.css           # Styling for resume view
├── script.js            # Theme switcher, scrollspy, modal controls, and contact validation
├── theme-init.js        # Instant zero-flicker theme loader
├── .gitignore           # Clean git ignore for OS metadata and temporary files
├── README.md            # Project documentation and deployment guide
└── assets/
    └── images/
        ├── profile.png
        ├── resume-somchand.png
        ├── certificates/
        │   ├── columbia-ai-cybersecurity-governance.jpg
        │   ├── hackerx-ethical-hacking.jpg
        │   ├── harvardx-cs50-ai-python.jpg
        │   ├── harvardx-cs50-computer-science.jpg
        │   ├── harvardx-cs50-cybersecurity.jpg
        │   ├── iitm-shaastra-cloud-computing.jpg
        │   ├── iitm-shaastra-ethical-web-hacking.jpg
        │   └── internshala-iitm-cybersecurity-ai.jpg
        └── projects/
            ├── financial-analytics.svg
            ├── kakiebo-budget-app.svg
            ├── portfolio-architecture.svg
            └── shivay-security-toolkit.svg
```

---

## ✨ Features & Capabilities

1. **AI Automation & AppSec Positioning**: Clear value proposition tailored for startup retainers, AI workflow automation, and application security audits.
2. **Interactive `whoami.sh` Terminal**: Terminal simulation highlighting core stack, security focus, and verified competencies.
3. **Verified Credentials Lightbox**: Interactive pan/zoom modal inspector for all 8 verified credentials from Columbia Engineering, HarvardX, IIT Madras, and HackerX.
4. **Persistent Dark / Light Mode**: Instant theme switching persisted across sessions via `localStorage` with system preference detection.
5. **Client-Side Form Validation**: Real-time schema and length validation, honeypot bot defense, and fallback email client integration.
6. **SEO & Social Share Cards**: Complete OpenGraph and Twitter card metadata for professional rendering on LinkedIn, WhatsApp, and social media.
