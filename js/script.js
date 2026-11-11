/* ==========================================================================
   Somchand Ratangwal — Personal Portfolio Scripts
   Handles: Theme Toggle, Interactive Navigation & ScrollSpy, Skill Bars,
   Category Filters, Certificate & Project Modals, and Contact Form Validation
   ========================================================================== */

(function () {
  'use strict';

  /* ------------------------------------------------------------------------
     Certificate & Project Metadata Dictionaries
     ------------------------------------------------------------------------ */
  const CERTIFICATES = {
    'columbia-ai-gov': {
      title: 'AI Cybersecurity and Governance',
      issuer: 'Columbia Engineering Executive Education • Columbia+',
      date: 'Completed: September 16, 2026',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/columbia-ai-cybersecurity-governance.jpg',
      alt: 'Columbia Engineering Certificate for AI Cybersecurity and Governance',
      description:
        'Successfully completed the Columbia+ / Columbia Engineering Executive Education course and passed the examination covering AI security risks, governance frameworks, and responsible enterprise deployment.'
    },
    'cs50-cyber': {
      title: "CS50's Introduction to Cybersecurity",
      issuer: 'Harvard University • HarvardX (edX)',
      date: 'Issued: September 2026',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/harvardx-cs50-cybersecurity.jpg',
      alt: 'HarvardX Verified Certificate for CS50 Introduction to Cybersecurity',
      description:
        'Verified HarvardX certificate instructed by Prof. David J. Malan covering securing accounts, data, systems, and software against real-world threats while balancing security and usability.'
    },
    'cs50-ai': {
      title: "CS50's Introduction to Artificial Intelligence with Python",
      issuer: 'Harvard University • HarvardX (edX)',
      date: 'Issued: September 2026',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/harvardx-cs50-ai-python.jpg',
      alt: 'HarvardX Verified Certificate for CS50 Introduction to Artificial Intelligence with Python',
      description:
        'Verified HarvardX certificate covering graph search algorithms, knowledge engineering, uncertainty modeling, optimization, machine learning, neural networks, and natural language processing in Python.'
    },
    'cs50-cs': {
      title: "CS50's Introduction to Computer Science",
      issuer: 'Harvard University • HarvardX (edX)',
      date: 'Issued: September 2026',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/harvardx-cs50-computer-science.jpg',
      alt: 'HarvardX Verified Certificate for CS50 Introduction to Computer Science',
      description:
        'Verified HarvardX flagship computer science credential covering computational thinking, abstraction, algorithms, data structures, C, Python, SQL, HTML, CSS, and JavaScript.'
    },
    'internshala-iitm': {
      title: 'Cyber Security with AI (8-Week Training — 96% Top Performer)',
      issuer: 'Internshala Trainings & IITM Pravartak Technologies Foundation',
      date: 'Certified: July 11, 2026',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/internshala-iitm-cybersecurity-ai.jpg',
      alt: 'Internshala Trainings and IITM Pravartak Certificate for Cyber Security with AI',
      description:
        'Completed 8-week online training in Basics of Information Security, Computer Networking, Web Development, Information Gathering, OWASP Top 10 VAPT, Automating VAPT, and Vulnerability Reporting. Scored 96% in the final assessment and recognized as a Top Performer.'
    },
    'shaastra-web': {
      title: 'Ethical Web Hacking Workshop',
      issuer: 'Shaastra 2026 • IIT Madras',
      date: 'Conducted: January 2, 2026',
      credential: 'Certificate of Participation',
      image: 'assets/images/certificates/iitm-shaastra-ethical-web-hacking.jpg',
      alt: 'Shaastra 2026 IIT Madras Certificate of Participation in Ethical Web Hacking',
      description:
        'Participated in the Ethical Web Hacking technical workshop conducted during Shaastra 2026 at Indian Institute of Technology Madras, exploring web application security testing and responsible disclosure practices.'
    },
    'shaastra-cloud': {
      title: 'Cloud Computing Workshop',
      issuer: 'Shaastra 2026 • IIT Madras',
      date: 'Conducted: January 3, 2026',
      credential: 'Certificate of Participation',
      image: 'assets/images/certificates/iitm-shaastra-cloud-computing.jpg',
      alt: 'Shaastra 2026 IIT Madras Certificate of Participation in Cloud Computing',
      description:
        'Participated in the Cloud Computing workshop conducted during Shaastra 2026 at IIT Madras, covering cloud deployment models, virtualization, and scalable infrastructure fundamentals.'
    },
    hackerx: {
      title: 'Ethical Hacking & Cybersecurity Certification',
      issuer: 'HackerX',
      date: 'Granted: April 16, 2024',
      credential: 'Credential ID: Protected (Privacy Redacted)',
      image: 'assets/images/certificates/hackerx-ethical-hacking.jpg',
      alt: 'HackerX Certificate of Achievement in Ethical Hacking and Cybersecurity',
      description:
        'Awarded Certificate of Achievement after completing all HackerX certification courses on Ethical Hacking & Cybersecurity and passing the domain assessment.'
    },
    resume: {
      title: 'Somchand Ratangwal — Professional Resume',
      issuer: 'Curriculum Vitae',
      date: 'Current Profile (2026)',
      credential: 'B.Tech. CSE (2030) • Joint B.Cyber. 2027 Aspirant',
      image: 'assets/images/resume-somchand.png',
      alt: 'Professional Resume of Somchand Ratangwal',
      description:
        'Updated one-page resume covering academic status (B.Tech. CSE Cybersecurity & AI in progress, Joint IITM & IITK B.Cyber. 2027 aspirant), AI Orchestration & Prompt Engineering, HTML5/CSS3, Python & SQLite (learning), projects (KAKIEBO & SHIVAY), 4+ years of financial markets exposure, and 8 verified certifications.'
    }
  };

  const PROJECTS = {
    kakiebo: {
      title: 'KAKIEBO — Personal Budgeting App',
      category: 'Personal Project • Python & SQLite',
      image: 'assets/images/projects/kakiebo-budget-app.svg',
      alt: 'KAKIEBO Personal Budgeting App Interface Preview',
      summary:
        'Inspired by the Japanese Kakeibo mindful budgeting method, KAKIEBO is a personal finance application designed to record income, categorize expenses, and enforce savings targets using local SQLite persistence.',
      highlights: [
        'Uses parameterized SQLite queries to protect financial records against injection risks.',
        'Organizes spending into Needs, Wants, Culture, and Savings categories.',
        'Offline-first local architecture keeping sensitive budgeting records private on-device.'
      ],
      tech: ['Python', 'SQLite', 'Secure Input Handling', 'Data Modeling'],
      github: 'https://github.com/Somchand-Max'
    },
    shivay: {
      title: 'SHIVAY & Authorized Bug Bounty Practice',
      category: 'Security Toolset • Ethical Security',
      image: 'assets/images/projects/shivay-security-toolkit.svg',
      alt: 'SHIVAY Security Toolset and Recon Dashboard Preview',
      summary:
        'SHIVAY is a personal security toolkit built to automate repetitive reconnaissance and web vulnerability checks during authorized bug bounty hunting, lab practice, and CTF competitions.',
      highlights: [
        'Integrates Nmap port/service enumeration and HTTP security header auditing workflows.',
        'Maps findings against OWASP Top 10 categories for structured VAPT reporting.',
        'Operates in virtualized Kali Linux, Parrot OS, and Termux testing environments.'
      ],
      tech: ['Python', 'Kali Linux', 'Parrot OS', 'Nmap', 'OWASP Top 10', 'VAPT'],
      github: 'https://github.com/Somchand-Max'
    },
    financial: {
      title: 'Financial Markets & Risk Compliance Workflow',
      category: 'Domain Experience • 4+ Years Exposure',
      image: 'assets/images/projects/financial-analytics.svg',
      alt: 'Financial Markets Compliance and Risk Analytics Visual',
      summary:
        'Over 4 years of practical exposure working under a Chartered Accountant, focusing on stock market behavior, regulatory compliance workflows, risk modeling, and operational trading analytics.',
      highlights: [
        'Analyzed equity market metrics, volatility patterns, and capital allocation risk.',
        'Built structured compliance documentation and audit-ready reporting habits.',
        'Bridges domain financial governance knowledge with AI and cybersecurity governance.'
      ],
      tech: ['Financial Markets', 'Regulatory Compliance', 'Risk Modeling', 'Trading Analytics'],
      github: null
    },
    portfolio: {
      title: 'Personal Portfolio Website',
      category: 'Frontend Engineering • HTML5 / CSS3 / JS',
      image: 'assets/images/projects/portfolio-architecture.svg',
      alt: 'Responsive Personal Portfolio Website Architecture',
      summary:
        'A responsive personal digital profile built using pure HTML5, CSS3 design tokens, and vanilla JavaScript with zero external UI frameworks.',
      highlights: [
        'Implements all 11 required features: Home, About, Education, Skills, Projects, Hobbies, Achievements, Contact, Dark/Light Mode, Interactive Navigation, and Responsive Design.',
        'Features persistent Dark & Light theme switching, IntersectionObserver ScrollSpy, and animated skill bars.',
        'Includes accessible keyboard-navigable certificate & project modals and real-time JS contact form validation.'
      ],
      tech: ['HTML5', 'CSS3 Variables', 'Vanilla JavaScript', 'IntersectionObserver', 'Responsive Grid'],
      github: 'https://github.com/Somchand-Max'
    }
  };

  /* ------------------------------------------------------------------------
     1. Dark Mode / Light Mode Toggle
     ------------------------------------------------------------------------ */
  function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle');
    const labelEl = document.getElementById('theme-label');
    if (!toggleBtn || !labelEl) return;

    function applyTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      const isLight = theme === 'light';
      toggleBtn.setAttribute('aria-pressed', String(isLight));
      toggleBtn.setAttribute('aria-label', isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode');
      labelEl.textContent = isLight ? 'Dark' : 'Light';
    }

    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(currentTheme);

    toggleBtn.addEventListener('click', function () {
      const nextTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
      try {
        localStorage.setItem('portfolio-theme', nextTheme);
      } catch (e) {}
    });
  }

  /* ------------------------------------------------------------------------
     2. Interactive Navigation, Mobile Drawer, ScrollSpy & Progress Bar
     ------------------------------------------------------------------------ */
  function initNavigation() {
    const menuBtn = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');
    const navLinks = Array.from(document.querySelectorAll('.nav-link'));
    const progressBar = document.getElementById('scroll-progress');
    const sections = Array.from(document.querySelectorAll('main section[id]'));

    function closeMobileNav() {
      if (!menuBtn || !mainNav) return;
      mainNav.classList.remove('is-open');
      menuBtn.setAttribute('aria-expanded', 'false');
      menuBtn.setAttribute('aria-label', 'Open navigation menu');
    }

    if (menuBtn && mainNav) {
      menuBtn.addEventListener('click', function () {
        const isOpen = mainNav.classList.toggle('is-open');
        menuBtn.setAttribute('aria-expanded', String(isOpen));
        menuBtn.setAttribute('aria-label', isOpen ? 'Close navigation menu' : 'Open navigation menu');
      });

      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && mainNav.classList.contains('is-open')) {
          closeMobileNav();
          menuBtn.focus();
        }
      });

      document.addEventListener('click', function (event) {
        if (
          mainNav.classList.contains('is-open') &&
          !mainNav.contains(event.target) &&
          !menuBtn.contains(event.target)
        ) {
          closeMobileNav();
        }
      });
    }

    function setActiveLink(sectionId) {
      navLinks.forEach(function (link) {
        link.classList.toggle('active', link.getAttribute('data-section') === sectionId);
      });
    }

    navLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        const targetSection = link.getAttribute('data-section');
        if (targetSection) setActiveLink(targetSection);
        closeMobileNav();
      });
    });

    if ('IntersectionObserver' in window && sections.length > 0) {
      const observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              setActiveLink(entry.target.id);
            }
          });
        },
        { rootMargin: '-35% 0px -55% 0px', threshold: 0 }
      );
      sections.forEach(function (section) {
        observer.observe(section);
      });
    }

    if (progressBar) {
      window.addEventListener(
        'scroll',
        function () {
          const docHeight = document.documentElement.scrollHeight - window.innerHeight;
          const pct = docHeight > 0 ? Math.min(100, Math.max(0, (window.scrollY / docHeight) * 100)) : 0;
          progressBar.style.width = pct.toFixed(1) + '%';
        },
        { passive: true }
      );
    }
  }

  /* ------------------------------------------------------------------------
     3. Reusable Category Filter Helper (Skills & Certificates)
     ------------------------------------------------------------------------ */
  function initFilterGroup(buttonAttr, itemSelector, itemCategoryAttr) {
    const buttons = Array.from(document.querySelectorAll('[' + buttonAttr + ']'));
    const items = Array.from(document.querySelectorAll(itemSelector));
    if (!buttons.length || !items.length) return;

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const selected = btn.getAttribute(buttonAttr);

        buttons.forEach(function (other) {
          const active = other === btn;
          other.classList.toggle('active', active);
          other.setAttribute('aria-pressed', String(active));
        });

        items.forEach(function (item) {
          const categories = (item.getAttribute(itemCategoryAttr) || '').split(/\s+/);
          const show = selected === 'all' || categories.includes(selected);
          item.classList.toggle('is-hidden', !show);
        });
      });
    });
  }

  /* ------------------------------------------------------------------------
     4. Animated Skill Progress Bars
     ------------------------------------------------------------------------ */
  function initSkillBars() {
    const skillsSection = document.getElementById('skills');
    const bars = Array.from(document.querySelectorAll('.progress-fill'));
    if (!bars.length) return;

    function fillAllBars() {
      bars.forEach(function (bar) {
        const level = bar.getAttribute('data-level') || '0';
        bar.style.width = level + '%';
      });
    }

    if ('IntersectionObserver' in window && skillsSection) {
      const observer = new IntersectionObserver(
        function (entries) {
          if (entries.some(function (entry) { return entry.isIntersecting; })) {
            fillAllBars();
            observer.disconnect();
          }
        },
        { threshold: 0.15 }
      );
      observer.observe(skillsSection);
    } else {
      fillAllBars();
    }
  }

  /* ------------------------------------------------------------------------
     5. Accessible Modals (Certificates, Resume & Project Details)
     ------------------------------------------------------------------------ */
  function initModals() {
    let activeModal = null;
    let lastFocusedEl = null;

    function openModal(modalId) {
      const modal = document.getElementById(modalId);
      if (!modal) return;
      lastFocusedEl = document.activeElement;
      activeModal = modal;
      modal.hidden = false;
      document.body.style.overflow = 'hidden';

      const closeBtn = modal.querySelector('.modal-close');
      if (closeBtn) closeBtn.focus();
    }

    function closeActiveModal() {
      if (!activeModal) return;
      activeModal.hidden = true;
      document.body.style.overflow = '';
      if (lastFocusedEl && typeof lastFocusedEl.focus === 'function') {
        lastFocusedEl.focus();
      }
      activeModal = null;
      lastFocusedEl = null;
    }

    document.querySelectorAll('[data-close-modal]').forEach(function (btn) {
      btn.addEventListener('click', closeActiveModal);
    });

    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
      backdrop.addEventListener('click', function (event) {
        if (event.target === backdrop) closeActiveModal();
      });
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && activeModal) {
        closeActiveModal();
      }
    });

    /* Interactive Image Zoom & Pan Controller for #cert-modal */
    const zoomViewport = document.getElementById('cert-zoom-viewport');
    const zoomImg = document.getElementById('cert-modal-img');
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const zoomResetBtn = document.getElementById('zoom-reset-btn');
    const zoomFitBtn = document.getElementById('zoom-fit-btn');
    const zoomLabel = document.getElementById('zoom-level-label');

    const MIN_ZOOM = 0.5;
    const MAX_ZOOM = 3.0;
    const ZOOM_STEP = 0.25;
    let zoomMode = 'fit'; // 'fit' | 'scale'
    let zoomScale = 1.0;

    function updateZoomUI() {
      if (!zoomViewport || !zoomImg) return;

      if (zoomMode === 'fit') {
        zoomImg.style.width = '100%';
        zoomImg.style.maxWidth = '100%';
        zoomImg.style.maxHeight = '58vh';
        zoomViewport.classList.remove('is-zoomed', 'is-panning');
        zoomViewport.scrollTo(0, 0);
        if (zoomLabel) zoomLabel.textContent = 'Fit';
        if (zoomFitBtn) zoomFitBtn.classList.add('active');
        if (zoomResetBtn) zoomResetBtn.classList.remove('active');
        if (zoomOutBtn) zoomOutBtn.disabled = false;
        if (zoomInBtn) zoomInBtn.disabled = false;
        return;
      }

      const baseWidth = Math.max(260, zoomViewport.clientWidth - 20);
      const targetWidth = Math.round(baseWidth * zoomScale);
      zoomImg.style.maxWidth = 'none';
      zoomImg.style.maxHeight = 'none';
      zoomImg.style.width = targetWidth + 'px';

      const zoomedIn = zoomScale > 1.0;
      zoomViewport.classList.toggle('is-zoomed', zoomedIn);
      if (!zoomedIn) zoomViewport.classList.remove('is-panning');

      if (zoomLabel) zoomLabel.textContent = Math.round(zoomScale * 100) + '%';
      if (zoomFitBtn) zoomFitBtn.classList.remove('active');
      if (zoomResetBtn) zoomResetBtn.classList.toggle('active', Math.abs(zoomScale - 1.0) < 0.01);
      if (zoomOutBtn) zoomOutBtn.disabled = zoomScale <= MIN_ZOOM;
      if (zoomInBtn) zoomInBtn.disabled = zoomScale >= MAX_ZOOM;
    }

    function setZoomScale(nextScale) {
      zoomMode = 'scale';
      zoomScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(nextScale * 100) / 100));
      updateZoomUI();
    }

    function stepZoom(delta) {
      if (zoomMode === 'fit') {
        setZoomScale(delta > 0 ? 1.25 : 0.75);
      } else {
        setZoomScale(zoomScale + delta);
      }
    }

    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', function () {
        stepZoom(ZOOM_STEP);
      });
    }

    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', function () {
        stepZoom(-ZOOM_STEP);
      });
    }

    if (zoomResetBtn) {
      zoomResetBtn.addEventListener('click', function () {
        setZoomScale(1.0);
      });
    }

    if (zoomFitBtn) {
      zoomFitBtn.addEventListener('click', function () {
        zoomMode = 'fit';
        zoomScale = 1.0;
        updateZoomUI();
      });
    }

    if (zoomViewport) {
      zoomViewport.addEventListener(
        'wheel',
        function (event) {
          if (!activeModal || activeModal.id !== 'cert-modal') return;
          event.preventDefault();
          const direction = event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
          stepZoom(direction);
        },
        { passive: false }
      );

      let isPanning = false;
      let startX = 0;
      let startY = 0;
      let startScrollLeft = 0;
      let startScrollTop = 0;

      zoomViewport.addEventListener('pointerdown', function (event) {
        if (zoomMode !== 'scale' || zoomScale <= 1.0) return;
        isPanning = true;
        startX = event.clientX;
        startY = event.clientY;
        startScrollLeft = zoomViewport.scrollLeft;
        startScrollTop = zoomViewport.scrollTop;
        zoomViewport.classList.add('is-panning');
        zoomViewport.setPointerCapture(event.pointerId);
      });

      zoomViewport.addEventListener('pointermove', function (event) {
        if (!isPanning) return;
        zoomViewport.scrollLeft = startScrollLeft - (event.clientX - startX);
        zoomViewport.scrollTop = startScrollTop - (event.clientY - startY);
      });

      function stopPanning(event) {
        if (!isPanning) return;
        isPanning = false;
        zoomViewport.classList.remove('is-panning');
        if (event.pointerId !== undefined && zoomViewport.hasPointerCapture(event.pointerId)) {
          zoomViewport.releasePointerCapture(event.pointerId);
        }
      }

      zoomViewport.addEventListener('pointerup', stopPanning);
      zoomViewport.addEventListener('pointercancel', stopPanning);
    }

    const printableResumeLink = document.getElementById('open-printable-resume-link');

    function showCertificateModal(certId) {
      const data = CERTIFICATES[certId];
      if (!data) return;

      document.getElementById('cert-modal-issuer').textContent = data.issuer;
      document.getElementById('cert-modal-title').textContent = data.title;
      zoomImg.src = data.image;
      zoomImg.alt = data.alt;
      document.getElementById('cert-modal-date').textContent = data.date;
      document.getElementById('cert-modal-credential').textContent = data.credential;
      document.getElementById('cert-modal-desc').textContent = data.description;
      if (printableResumeLink) {
        printableResumeLink.hidden = certId !== 'resume';
      }

      zoomMode = 'fit';
      zoomScale = 1.0;
      openModal('cert-modal');
      updateZoomUI();
    }

    document.querySelectorAll('[data-cert-id]').forEach(function (trigger) {
      trigger.addEventListener('click', function () {
        showCertificateModal(trigger.getAttribute('data-cert-id'));
      });
    });

    const resumeBtn = document.getElementById('open-resume-btn');
    if (resumeBtn) {
      resumeBtn.addEventListener('click', function () {
        showCertificateModal('resume');
      });
    }

    document.querySelectorAll('.project-detail-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const data = PROJECTS[btn.getAttribute('data-project')];
        if (!data) return;

        document.getElementById('project-modal-category').textContent = data.category;
        document.getElementById('project-modal-title').textContent = data.title;
        const img = document.getElementById('project-modal-img');
        img.src = data.image;
        img.alt = data.alt;
        document.getElementById('project-modal-summary').textContent = data.summary;

        const listEl = document.getElementById('project-modal-highlights');
        listEl.innerHTML = '';
        data.highlights.forEach(function (point) {
          const li = document.createElement('li');
          li.textContent = point;
          listEl.appendChild(li);
        });

        const techEl = document.getElementById('project-modal-tech');
        techEl.innerHTML = '';
        data.tech.forEach(function (item) {
          const span = document.createElement('span');
          span.className = 'tag';
          span.textContent = item;
          techEl.appendChild(span);
        });

        const actionsEl = document.getElementById('project-modal-actions');
        actionsEl.innerHTML = '';
        if (data.github) {
          const ghLink = document.createElement('a');
          ghLink.href = data.github;
          ghLink.target = '_blank';
          ghLink.rel = 'noopener noreferrer';
          ghLink.className = 'btn btn-primary btn-sm';
          ghLink.textContent = 'View GitHub Profile';
          actionsEl.appendChild(ghLink);
        }

        openModal('project-modal');
      });
    });
  }

  /* ------------------------------------------------------------------------
     6. Contact Form Validation & Clipboard Email Copy
     ------------------------------------------------------------------------ */
  function initContactSection() {
    const copyBtn = document.getElementById('copy-email-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        const email = 'somchandratangwal7@gmail.com';
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(email).then(function () {
            copyBtn.textContent = 'Copied!';
            setTimeout(function () {
              copyBtn.textContent = 'Copy';
            }, 2000);
          }).catch(function () {});
        }
      });
    }

    const form = document.getElementById('contact-form');
    if (!form) return;

    const nameInput = document.getElementById('contact-name');
    const emailInput = document.getElementById('contact-email');
    const messageInput = document.getElementById('contact-message');
    const charCount = document.getElementById('char-count');
    const feedbackEl = document.getElementById('form-feedback');

    const validators = [
      {
        input: nameInput,
        errorEl: document.getElementById('name-error'),
        validate: function (val) {
          if (!val) return 'Please enter your name.';
          if (val.length < 2) return 'Name must be at least 2 characters long.';
          return '';
        }
      },
      {
        input: emailInput,
        errorEl: document.getElementById('email-error'),
        validate: function (val) {
          if (!val) return 'Please enter your email address.';
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(val)) {
            return 'Please enter a valid email address (e.g., name@domain.com).';
          }
          return '';
        }
      },
      {
        input: messageInput,
        errorEl: document.getElementById('message-error'),
        validate: function (val) {
          if (!val) return 'Please enter a message.';
          if (val.length < 10) return 'Message should be at least 10 characters long.';
          return '';
        }
      }
    ];

    function runFieldValidation(field) {
      const value = field.input.value.trim();
      const message = field.validate(value);
      field.errorEl.textContent = message;
      field.input.classList.toggle('invalid', Boolean(message));
      field.input.setAttribute('aria-invalid', String(Boolean(message)));
      return !message;
    }

    validators.forEach(function (field) {
      field.input.addEventListener('blur', function () {
        runFieldValidation(field);
      });
      field.input.addEventListener('input', function () {
        if (field.input.classList.contains('invalid')) {
          runFieldValidation(field);
        }
      });
    });

    if (messageInput && charCount) {
      messageInput.addEventListener('input', function () {
        charCount.textContent = messageInput.value.length + ' / 500';
      });
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      let allValid = true;
      let firstInvalid = null;

      validators.forEach(function (field) {
        const valid = runFieldValidation(field);
        if (!valid) {
          allValid = false;
          if (!firstInvalid) firstInvalid = field.input;
        }
      });

      if (!allValid) {
        feedbackEl.hidden = false;
        feedbackEl.className = 'form-feedback error';
        feedbackEl.textContent = 'Please fix the highlighted fields above before submitting.';
        if (firstInvalid) firstInvalid.focus();
        return;
      }

      const senderName = nameInput.value.trim();
      feedbackEl.hidden = false;
      feedbackEl.className = 'form-feedback success';
      feedbackEl.textContent =
        'Thank you, ' +
        senderName +
        '! All details passed validation. (Note: As this is a static portfolio without a backend email server, no email was transmitted — you can reach me directly at somchandratangwal7@gmail.com.)';

      form.reset();
      if (charCount) charCount.textContent = '0 / 500';
      validators.forEach(function (field) {
        field.input.classList.remove('invalid');
        field.input.setAttribute('aria-invalid', 'false');
        field.errorEl.textContent = '';
      });
    });
  }

  /* ------------------------------------------------------------------------
     Initialize All Modules
     ------------------------------------------------------------------------ */
  document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initNavigation();
    initFilterGroup('data-skill-filter', '.skill-card', 'data-skill-category');
    initFilterGroup('data-cert-filter', '.cert-card', 'data-cert-category');
    initSkillBars();
    initModals();
    initContactSection();
  });
})();
