# Somchand Ratangwal — AI Automation & Application Security Specialist

A high-performance, standalone personal portfolio web application built with modern **semantic HTML5**, **CSS3 Design Tokens**, and **Vanilla JavaScript** (ES6+). Zero server-side runtime dependencies, ready for instant, zero-config deployment on **Vercel**, **Cloudflare Pages**, and **GitHub Pages**.

---

## 🌐 Live Website Links

- **GitHub Repository**: [https://github.com/Somchand-Max/Portfolio_Somchand_max](https://github.com/Somchand-Max/Portfolio_Somchand_max)
- **GitHub Pages Public URL**: [https://somchand-max.github.io/Portfolio_Somchand_max/](https://somchand-max.github.io/Portfolio_Somchand_max/)
- **Admin Portal URL**: [https://somchand-max.github.io/Portfolio_Somchand_max/admin.html](https://somchand-max.github.io/Portfolio_Somchand_max/admin.html) (or append `?admin=true`)
- **Local Dev URL**: `http://localhost:8080/`

---

## 🔒 Admin Portal & Message Center (`admin.html`)

You can check all contact inquiries directly through the built-in **Admin Portal**:

- **URL**: `admin.html` (accessible via the `🔒 Admin Portal` link in the website footer or `?admin=true`)
- **Authorized Email**: `somchandratangwal7@gmail.com`
- **Authorized Password**: `26112009@som7` (protected by SHA-256 cryptographic check and 5-attempt brute-force lockout)

### What You Can Do in the Admin Portal:
1. **Live Inquiries Dashboard**: View all messages submitted through the contact form with sender details, timestamps, and read/unread status badges.
2. **Instant Gmail Forwarding**: When visitors send a message, it is automatically forwarded to **`somchandratangwal7@gmail.com`** so you never miss an inquiry.
3. **One-Click Excel / CSV Export**: Click **📥 Download Excel (.csv)** to export all messages into an Excel-formatted spreadsheet with full timestamp, sender name, email, and message content.
4. **Direct One-Click Reply**: Click **✉️ Reply** on any inquiry to open a pre-filled reply in your email client.

---

## ⚡ Deployment & Hosting (Zero-Config)

This repository is structured as a pure static web application. No build step, package manager, or backend runtime is required:

### 1. GitHub Pages (Recommended)
1. Go to repository **Settings** &rarr; **Pages**.
2. Under **Build and deployment**, select **Deploy from a branch**.
3. Choose branch `main` and folder `/ (root)`.
4. Click **Save**. Your site will be live at `https://somchand-max.github.io/Portfolio_Somchand_max/` within 60 seconds.

### 2. Vercel
1. Import this repository into Vercel.
2. Framework Preset: **Other** (Static HTML).
3. Build Command: *leave empty*.
4. Output Directory: `.` (root).
5. Click **Deploy**.

### 3. Cloudflare Pages
1. Connect this repository in Cloudflare Pages Dashboard.
2. Build command: *None*.
3. Build output directory: `/` (root).
4. Click **Save and Deploy**.

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
├── admin.html           # Secure Admin Portal & live contact message hub
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
