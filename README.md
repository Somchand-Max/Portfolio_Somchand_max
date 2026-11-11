# Personal Portfolio Website — Somchand Ratangwal

A responsive Personal Portfolio Website built with **HTML5**, **CSS3**, and **Vanilla JavaScript** showcasing cybersecurity & AI projects, verified certifications, and preparation for the **Joint IIT Madras & IIT Kanpur 4-Year Bachelor of Cybersecurity (B.Cyber.) 2027** program.

## Features Implemented (11/11)

1. **Home Section (`#home`)**: Prominent introduction, high-resolution sharpened circular profile portrait, welcome message, navigation CTA buttons, quick interactive resume viewer with zoom/pan controls, and key stats.
2. **About Me Section (`#about`)**: Personal background, interests, hobbies, career goals, 4+ years of financial markets exposure, and areas of focus.
3. **Education Section (`#education`)**: Academic timeline covering focused preparation for the Joint IIT Madras & IIT Kanpur B.Cyber. 2027 degree alongside verified HarvardX, Columbia+, and IIT Madras credentials.
4. **Skills Section (`#skills`)**: Honest, filterable technical & non-technical skills across 9 cards — HTML5 & CSS3 (Known, AI-prompt accelerated), Python & SQLite (Learning), JavaScript (Conceptual / Beginner, AI-orchestrated), AI Orchestration & Prompt Engineering (90%, Core Superpower), Kali Linux / Parrot OS / Termux, Network Security & Nmap, Communication, Teamwork & Collaboration, and Financial & Risk Analytics.
5. **Projects Section (`#projects`)**: Cards for **KAKIEBO**, **SHIVAY & Bug Bounty Practice**, **Financial Markets & Risk Compliance**, and this **Personal Portfolio Website**, complete with interactive detail modals.
6. **Hobbies & Interests Section (`#hobbies`)**: Visual cards with custom icons covering CTF & Security Labs, Reading & Market Analysis, Photography & YouTube Vlogging (`@THEEVERTHINGS.7`), Music, Travelling, and Sports & Gaming (Football & Free Fire).
7. **Achievements Section (`#achievements`)**: Interactive filterable gallery of all **8 verified certificates** (Columbia+, HarvardX CS50 x3, Internshala/IITM Pravartak 96% Top Performer, IIT Madras Shaastra x2, HackerX) with privacy-blurred QR codes/credential IDs and interactive zoom/pan lightbox inspection.
8. **Contact Section (`#contact`)**: Email (with copy button), location, GitHub & LinkedIn links, plus a JavaScript-validated contact form (`#contact-form`) connected to `POST /api/contact` on `server.py` (with CSRF tokens, honeypot filtering, IP rate limiting, XSS escaping, and spreadsheet formula injection defense) that persists submissions safely into `data/contact_messages.xlsx` (`chmod 600`).
9. **Dark Mode & Light Mode**: Accessible navbar toggle persisting theme preference in `localStorage`.
10. **Interactive Navigation**: Sticky header, smooth scrolling, active section highlighting via `IntersectionObserver`, scroll progress bar, and mobile drawer menu.
11. **Responsive Design**: Adaptive layout for desktops, laptops, tablets, and mobile phones.

## Project Structure

```text
personal-portfolio-website/
├── index.html
├── resume.html
├── server.py
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── css/
│   ├── resume.css
│   └── styles.css
├── js/
│   ├── script.js
│   └── theme-init.js
├── data/                   # Created locally at runtime (git-ignored, chmod 700/600)
│   └── contact_messages.xlsx
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

## Run Locally

Install dependencies into the project virtual environment and start the hardened backend server (serves static files + `/api/csrf-token` + `/api/contact` on port 8080):

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python server.py
```

Then visit `http://localhost:8080`. Contact submissions are saved safely to `data/contact_messages.xlsx` (`chmod 600`, git-ignored).

### Run Streamlit Cloud Wrapper (`app.py`)

```bash
./venv/bin/streamlit run app.py
```

Set `PORTFOLIO_ADMIN_KEY` in environment variables or `.streamlit/secrets.toml` to unlock the admin `.xlsx` preview and download tab.
