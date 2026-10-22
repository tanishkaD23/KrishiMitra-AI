/**
 * KrishiMitra AI - Shared UI, Theme & Internationalization Controller
 * Manages language switching (Hindi/English), theme switching (Light/Dark),
 * persistent user preferences, and common components.
 */

(function () {
    // Language State
    let currentLang = getStoredLanguage();

    // Theme State ('light' or 'dark')
    let currentTheme = getStoredTheme();

    function applyTranslations(lang) {
        currentLang = lang;
        setStoredLanguage(lang);
        document.documentElement.lang = lang;

        const dict = window.TRANSLATIONS && window.TRANSLATIONS[lang];
        if (!dict) return;

        // Translate text elements
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (dict[key]) {
                el.innerHTML = dict[key];
            }
        });

        // Translate placeholders
        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (dict[key]) {
                el.placeholder = dict[key];
            }
        });

        // Update Toggle Buttons across all pages
        document.querySelectorAll(".lang-toggle-btn").forEach((btn) => {
            const currentBadge = btn.querySelector(".lang-current");
            const altBadge = btn.querySelector(".lang-alt");

            if (lang === "hi") {
                if (currentBadge) currentBadge.textContent = "हिंदी";
                if (altBadge) altBadge.textContent = "EN";
                btn.title = "Switch to English";
            } else {
                if (currentBadge) currentBadge.textContent = "EN";
                if (altBadge) altBadge.textContent = "हिंदी";
                btn.title = "हिंदी में बदलें";
            }
        });

        // Dispatch global event for page-specific controllers
        window.dispatchEvent(new CustomEvent("krishimitra:languageChanged", { detail: { lang } }));
    }

    function toggleLanguage() {
        const nextLang = currentLang === "hi" ? "en" : "hi";
        applyTranslations(nextLang);
    }

    // Theme Management
    function getStoredTheme() {
        return localStorage.getItem("krishimitra_theme") || "light";
    }

    function setStoredTheme(theme) {
        localStorage.setItem("krishimitra_theme", theme);
    }

    function applyTheme(theme) {
        currentTheme = theme;
        setStoredTheme(theme);
        document.documentElement.setAttribute("data-theme", theme);

        document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
            const icon = btn.querySelector(".theme-icon");
            const text = btn.querySelector(".theme-text");

            if (theme === "dark") {
                if (icon) icon.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
                if (text) text.textContent = "Light";
                btn.title = "Switch to Light Theme";
            } else {
                if (icon) icon.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
                if (text) text.textContent = "Dark";
                btn.title = "Switch to Dark Theme";
            }
        });

        window.dispatchEvent(new CustomEvent("krishimitra:themeChanged", { detail: { theme } }));
    }

    function toggleTheme() {
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        applyTheme(nextTheme);
    }

    // Expose helpers globally
    window.krishiI18n = {
        getCurrentLang: () => currentLang,
        setLanguage: applyTranslations,
        toggleLanguage: toggleLanguage,
        t: (key) => (window.TRANSLATIONS && window.TRANSLATIONS[currentLang] && window.TRANSLATIONS[currentLang][key]) || key,
    };

    window.krishiTheme = {
        getCurrentTheme: () => currentTheme,
        setTheme: applyTheme,
        toggleTheme: toggleTheme,
    };

    document.addEventListener("DOMContentLoaded", () => {
        // Attach click listeners to all language toggle buttons
        document.querySelectorAll(".lang-toggle-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                toggleLanguage();
            });
        });

        // Attach click listeners to all theme toggle buttons
        document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                toggleTheme();
            });
        });

        // Mobile Nav Toggle if present
        const menuBtn = document.getElementById("mobileMenuBtn");
        const navMenu = document.getElementById("mainNavLinks");
        if (menuBtn && navMenu) {
            menuBtn.addEventListener("click", () => {
                navMenu.classList.toggle("nav-open");
                menuBtn.classList.toggle("open");
            });
        }

        // Apply initial preferences
        applyTheme(currentTheme);
        applyTranslations(currentLang);
    });
})();
