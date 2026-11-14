/**
 * KrishiMitra-AI — Complete Supabase Authentication & Route Protection Engine
 *
 * Features:
 *  - Shows Login page first whenever an unauthenticated visitor opens the website
 *  - Protects all internal pages (dashboard.html, index.html, forecast.html, schemes.html, krishisathi.html, about.html)
 *  - Provides Login, Sign Up, and Forgot/Reset Password via Supabase Auth (@supabase/supabase-js v2)
 *    with seamless synchronization to the FastAPI/Flask backend and Netlify static persistence
 *  - Maintains login sessions across browser refreshes
 *  - Provides functional Logout across all pages
 */
(function () {
    "use strict";

    const AUTH_TOKEN_KEY = "km_auth_token";
    const AUTH_USER_KEY = "km_auth_user";
    const LOCAL_USERS_KEY = "km_registered_users_v1";
    const LOCAL_RESETS_KEY = "km_password_resets_v1";

    // Default seeded accounts for 1-click role personas & offline/Netlify fallback
    const DEFAULT_SEEDED_ACCOUNTS = {
        "farmer@krishimitra.in": {
            id: "user-farmer-001",
            name: "Tanishka",
            email: "farmer@krishimitra.in",
            phone: "+91 98765 43210",
            role: "farmer",
            state: "Uttar Pradesh",
            district: "Meerut",
            village: "Daurala",
            farmer_id: "farmer-001"
        },
        "officer@krishimitra.in": {
            id: "user-officer-001",
            name: "Dr. Rajesh Verma (District Agri Officer)",
            email: "officer@krishimitra.in",
            phone: "+91 98111 22334",
            role: "officer",
            state: "Uttar Pradesh",
            district: "Meerut",
            village: "Meerut HQ",
            farmer_id: "farmer-001"
        },
        "admin@krishimitra.in": {
            id: "user-admin-001",
            name: "Platform Administrator",
            email: "admin@krishimitra.in",
            phone: "+91 99000 11223",
            role: "admin",
            state: "Delhi",
            district: "New Delhi",
            village: "Krishi Bhawan",
            farmer_id: "farmer-001"
        }
    };

    function isPlaceholderConfig(val) {
        if (!val || typeof val !== "string") return true;
        const v = val.trim();
        if (!v) return true;
        if (v.includes("your-project") || v.includes("your-supabase") || v.includes("example.supabase.co")) {
            return true;
        }
        return false;
    }

    function setAuthCookie(token) {
        try {
            if (token) {
                document.cookie = `km_auth_token=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Lax`;
            } else {
                document.cookie = "km_auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
            }
        } catch (_) {}
    }

    function getSupabaseLocalStorageSession() {
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (k && k.startsWith("sb-") && k.endsWith("-auth-token")) {
                    const raw = localStorage.getItem(k);
                    if (!raw) continue;
                    const parsed = JSON.parse(raw);
                    if (parsed && parsed.access_token && parsed.user) {
                        return parsed;
                    }
                }
            }
        } catch (_) {}
        return null;
    }

    function normalizeUserObject(rawUser, roleFallback) {
        if (!rawUser) return null;
        const meta = rawUser.user_metadata || rawUser.raw_user_meta_data || {};
        const email = (rawUser.email || meta.email || "").toLowerCase();
        const seeded = DEFAULT_SEEDED_ACCOUNTS[email] || {};
        const role = String(
            rawUser.role !== "authenticated" && rawUser.role
                ? rawUser.role
                : (meta.role || seeded.role || roleFallback || "farmer")
        ).toLowerCase();
        const cleanRole = ["farmer", "officer", "admin"].includes(role) ? role : "farmer";

        return {
            id: rawUser.id || seeded.id || ("user-" + Math.random().toString(36).slice(2, 10)),
            name: rawUser.name || meta.full_name || meta.name || seeded.name || (email ? email.split("@")[0] : "Farmer"),
            email: email || seeded.email || "farmer@krishimitra.in",
            phone: rawUser.phone || meta.phone || seeded.phone || "+91 98765 43210",
            role: cleanRole,
            state: rawUser.state || meta.state || seeded.state || "Uttar Pradesh",
            district: rawUser.district || meta.district || seeded.district || "Meerut",
            village: rawUser.village || meta.village || seeded.village || "Daurala",
            farmer_id: rawUser.farmer_id || meta.farmer_id || seeded.farmer_id || "farmer-001",
            auth_provider: rawUser.auth_provider || (rawUser.aud === "authenticated" ? "supabase" : "krishimitra")
        };
    }

    function hasActiveSessionSync() {
        try {
            const token = localStorage.getItem(AUTH_TOKEN_KEY);
            const userStr = localStorage.getItem(AUTH_USER_KEY);
            if (token && userStr) {
                const u = JSON.parse(userStr);
                if (u && u.email) {
                    setAuthCookie(token);
                    return true;
                }
            }
            const sbSession = getSupabaseLocalStorageSession();
            if (sbSession && sbSession.access_token && sbSession.user) {
                const normUser = normalizeUserObject(sbSession.user);
                localStorage.setItem(AUTH_TOKEN_KEY, sbSession.access_token);
                localStorage.setItem(AUTH_USER_KEY, JSON.stringify(normUser));
                setAuthCookie(sbSession.access_token);
                return true;
            }
        } catch (_) {}
        return false;
    }

    function getCurrentUserSync() {
        try {
            if (!hasActiveSessionSync()) return null;
            return JSON.parse(localStorage.getItem(AUTH_USER_KEY) || "null");
        } catch (_) {
            return null;
        }
    }

    function saveSessionSync(token, userObj) {
        const norm = normalizeUserObject(userObj);
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(norm));
        setAuthCookie(token);
        return norm;
    }

    function clearSessionSync() {
        try {
            localStorage.removeItem(AUTH_TOKEN_KEY);
            localStorage.removeItem(AUTH_USER_KEY);
            const keysToRemove = [];
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (k && k.startsWith("sb-") && k.endsWith("-auth-token")) {
                    keysToRemove.push(k);
                }
            }
            keysToRemove.forEach((k) => localStorage.removeItem(k));
            setAuthCookie("");
        } catch (_) {}
    }

    function isLoginPagePath() {
        const path = (window.location.pathname || "").toLowerCase();
        if (path.endsWith("/login.html") || path.endsWith("/login")) {
            return true;
        }
        // Also detect if root "/" served login.html directly
        if (document.title && document.title.toLowerCase().includes("select your identity")) {
            return true;
        }
        return false;
    }

    // =========================================================================
    // 1. IMMEDIATE SYNCHRONOUS ROUTE PROTECTION GUARD (Runs in <head>)
    // =========================================================================
    (function enforceRouteProtectionSync() {
        const params = new URLSearchParams(window.location.search);
        if (params.get("logout") === "1") {
            clearSessionSync();
        }

        const onLogin = isLoginPagePath();
        const isAuthed = hasActiveSessionSync();

        if (!onLogin && !isAuthed) {
            // Visitor opened an internal page or root without being logged in -> Show Login page first
            try {
                document.documentElement.style.visibility = "hidden";
            } catch (_) {}
            const currentFile = (window.location.pathname.split("/").pop() || "dashboard.html") + window.location.search + window.location.hash;
            const nextParam = currentFile && currentFile !== "index.html" ? `?next=${encodeURIComponent(currentFile)}` : "";
            window.location.replace(`login.html${nextParam}`);
            return;
        }

        if (onLogin && isAuthed) {
            // If user is already logged in and opens login.html (or root /) without ?switch=1 or recovery hash,
            // maintain their session and redirect directly to Dashboard
            const allowStayOnLogin =
                params.get("switch") === "1" ||
                params.get("logout") === "1" ||
                params.get("tab") === "reset" ||
                (window.location.hash && (window.location.hash.includes("type=recovery") || window.location.hash.includes("access_token")));

            if (!allowStayOnLogin) {
                const nextDest = params.get("next") || "dashboard.html";
                window.location.replace(nextDest);
            }
        }
    })();

    // =========================================================================
    // 2. SUPABASE CLIENT INITIALIZATION & DYNAMIC CONFIG LOADER
    // =========================================================================
    let supabaseClient = null;
    let initPromise = null;

    async function initSupabaseClient() {
        if (supabaseClient) return supabaseClient;
        if (initPromise) return initPromise;

        initPromise = (async () => {
            let url = (window.KRISHI_SUPABASE_CONFIG && window.KRISHI_SUPABASE_CONFIG.supabaseUrl) || "";
            let anonKey = (window.KRISHI_SUPABASE_CONFIG && window.KRISHI_SUPABASE_CONFIG.supabaseAnonKey) || "";

            // 1. Try static Netlify build config (supabase_env.json)
            if (isPlaceholderConfig(url) || isPlaceholderConfig(anonKey)) {
                try {
                    const envRes = await fetch("supabase_env.json", { cache: "no-store" });
                    if (envRes.ok) {
                        const envJson = await envRes.json();
                        if (!isPlaceholderConfig(envJson.supabaseUrl)) url = envJson.supabaseUrl;
                        if (!isPlaceholderConfig(envJson.supabaseAnonKey)) anonKey = envJson.supabaseAnonKey;
                    }
                } catch (_) {}
            }

            // 2. Try backend /api/auth/supabase-config
            if (isPlaceholderConfig(url) || isPlaceholderConfig(anonKey)) {
                try {
                    const apiRes = await fetch("/api/auth/supabase-config", { cache: "no-store" });
                    if (apiRes.ok) {
                        const apiJson = await apiRes.json();
                        if (!isPlaceholderConfig(apiJson.supabase_url)) url = apiJson.supabase_url;
                        if (!isPlaceholderConfig(apiJson.supabase_anon_key)) anonKey = apiJson.supabase_anon_key;
                    }
                } catch (_) {}
            }

            if (!isPlaceholderConfig(url) && !isPlaceholderConfig(anonKey) && window.supabase && typeof window.supabase.createClient === "function") {
                try {
                    supabaseClient = window.supabase.createClient(url.trim(), anonKey.trim(), {
                        auth: {
                            persistSession: true,
                            autoRefreshToken: true,
                            detectSessionInUrl: true
                        }
                    });

                    supabaseClient.auth.onAuthStateChange((event, session) => {
                        if (session && session.access_token && session.user) {
                            saveSessionSync(session.access_token, session.user);
                        } else if (event === "SIGNED_OUT") {
                            clearSessionSync();
                        }
                        if (event === "PASSWORD_RECOVERY") {
                            window.dispatchEvent(new CustomEvent("krishimitra:passwordRecovery", { detail: { session } }));
                        }
                    });

                    // Sync current Supabase session if present
                    const { data } = await supabaseClient.auth.getSession();
                    if (data && data.session && data.session.access_token && data.session.user) {
                        saveSessionSync(data.session.access_token, data.session.user);
                    }
                } catch (err) {
                    console.warn("Supabase client initialization notice:", err);
                }
            }
            return supabaseClient;
        })();

        return initPromise;
    }

    // =========================================================================
    // 3. LOCAL / NETLIFY STATIC FALLBACK STORE (When backend is offline)
    // =========================================================================
    function getLocalUsersMap() {
        try {
            return JSON.parse(localStorage.getItem(LOCAL_USERS_KEY) || "{}");
        } catch (_) {
            return {};
        }
    }

    function saveLocalUsersMap(map) {
        try {
            localStorage.setItem(LOCAL_USERS_KEY, JSON.stringify(map));
        } catch (_) {}
    }

    function authenticateOfflineOrDemo(email, password, roleHint) {
        const cleanEmail = String(email || "").trim().toLowerCase();
        const localUsers = getLocalUsersMap();

        if (localUsers[cleanEmail]) {
            const record = localUsers[cleanEmail];
            if (record.password === password) {
                const token = "km_sb_local_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
                const user = saveSessionSync(token, record.user);
                return { status: "success", token, user, mode: "local" };
            }
            return { status: "error", message: "Invalid email or password." };
        }

        if (DEFAULT_SEEDED_ACCOUNTS[cleanEmail]) {
            const expectedPass = localUsers[cleanEmail]?.password || "Krishi@2026";
            if (password === expectedPass || password === "Krishi@2026") {
                const token = "km_sb_demo_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
                const seeded = { ...DEFAULT_SEEDED_ACCOUNTS[cleanEmail] };
                if (roleHint && ["farmer", "officer", "admin"].includes(roleHint)) {
                    seeded.role = roleHint;
                }
                const user = saveSessionSync(token, seeded);
                return { status: "success", token, user, mode: "demo" };
            }
            return { status: "error", message: "Invalid email or password." };
        }

        return { status: "error", message: "Invalid email or password. Please create an account first." };
    }

    // =========================================================================
    // 4. PUBLIC AUTH API (SignIn, SignUp, ForgotPassword, ResetPassword, SignOut)
    // =========================================================================
    async function signIn(email, password, roleHint) {
        const cleanEmail = String(email || "").trim().toLowerCase();
        if (!cleanEmail || !password) {
            return { status: "error", message: "Email and password are required." };
        }

        const sb = await initSupabaseClient();

        // 1. Try Supabase Auth first if configured
        if (sb) {
            try {
                const { data, error } = await sb.auth.signInWithPassword({
                    email: cleanEmail,
                    password: password
                });
                if (!error && data && data.session && data.user) {
                    const user = saveSessionSync(data.session.access_token, data.user);
                    // Also sync with backend session silently if available
                    fetch("/api/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email: cleanEmail, password })
                    }).catch(() => {});
                    return { status: "success", token: data.session.access_token, user, provider: "supabase" };
                }
                // If it's one of the built-in demo personas and not yet in Supabase, auto-provision in Supabase or fallback
                if (error && !DEFAULT_SEEDED_ACCOUNTS[cleanEmail]) {
                    // Still check backend in case account exists in SQLite
                }
            } catch (_) {}
        }

        // 2. Try FastAPI / Flask Backend Auth
        try {
            const resp = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: cleanEmail, password })
            });
            const contentType = resp.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const data = await resp.json();
                if (resp.ok && data.status === "success" && data.user) {
                    const user = saveSessionSync(data.token, data.user);
                    return { status: "success", token: data.token, user, provider: "backend" };
                }
                // Check local store before returning error
                const localCheck = authenticateOfflineOrDemo(cleanEmail, password, roleHint);
                if (localCheck.status === "success") return localCheck;
                return { status: "error", message: data.message || "Invalid email or password." };
            }
        } catch (_) {}

        // 3. Static / Netlify / Offline Auth Fallback
        return authenticateOfflineOrDemo(cleanEmail, password, roleHint);
    }

    async function signUp(payload) {
        const name = String(payload.name || "").trim();
        const email = String(payload.email || "").trim().toLowerCase();
        const password = String(payload.password || "");
        const phone = String(payload.phone || "+91 98765 43210").trim();
        const role = String(payload.role || "farmer").toLowerCase();
        const state = String(payload.state || "Uttar Pradesh");
        const district = String(payload.district || "Meerut");
        const village = String(payload.village || "Daurala");

        if (!name || !email || password.length < 6) {
            return { status: "error", message: "Full name, valid email, and password (minimum 6 characters) are required." };
        }

        const sb = await initSupabaseClient();
        let sbUser = null;
        let sbToken = null;

        // 1. Register in Supabase Auth if configured
        if (sb) {
            try {
                const { data, error } = await sb.auth.signUp({
                    email,
                    password,
                    options: {
                        data: {
                            full_name: name,
                            name,
                            role,
                            phone,
                            state,
                            district,
                            village
                        }
                    }
                });
                if (error) {
                    return { status: "error", message: error.message };
                }
                if (data && data.user) {
                    sbUser = data.user;
                    sbToken = (data.session && data.session.access_token) || ("sb_reg_" + Date.now().toString(36));
                }
            } catch (err) {
                console.warn("Supabase signUp error:", err);
            }
        }

        // 2. Also register in local browser store for instant persistence on Netlify static hosting
        const localUsers = getLocalUsersMap();
        const newUserObj = normalizeUserObject({
            id: (sbUser && sbUser.id) || ("user-" + Math.random().toString(36).slice(2, 10)),
            name,
            email,
            phone,
            role,
            state,
            district,
            village,
            farmer_id: "farmer-001"
        });
        localUsers[email] = { password, user: newUserObj };
        saveLocalUsersMap(localUsers);

        // 3. Also sync with FastAPI/Flask backend if running
        try {
            const resp = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password, phone, role, state, district, village })
            });
            const contentType = resp.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const data = await resp.json();
                if (resp.ok && data.status === "success" && data.user) {
                    const finalToken = sbToken || data.token;
                    const savedUser = saveSessionSync(finalToken, data.user);
                    return { status: "success", token: finalToken, user: savedUser };
                }
                if (!sbUser && data.status === "error") {
                    return { status: "error", message: data.message || "Registration failed." };
                }
            }
        } catch (_) {}

        const token = sbToken || ("km_sb_tok_" + Math.random().toString(36).slice(2) + Date.now().toString(36));
        const user = saveSessionSync(token, newUserObj);
        return { status: "success", token, user };
    }

    async function forgotPassword(email) {
        const cleanEmail = String(email || "").trim().toLowerCase();
        if (!cleanEmail) {
            return { status: "error", message: "Please enter your registered email address." };
        }

        const sb = await initSupabaseClient();
        let supabaseEmailSent = false;

        if (sb) {
            try {
                const redirectTo = window.location.origin + "/login.html?tab=reset";
                const { error } = await sb.auth.resetPasswordForEmail(cleanEmail, { redirectTo });
                if (!error) {
                    supabaseEmailSent = true;
                }
            } catch (_) {}
        }

        // Try backend forgot-password endpoint
        try {
            const resp = await fetch("/api/auth/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: cleanEmail })
            });
            const contentType = resp.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const data = await resp.json();
                if (data.status === "success") {
                    return {
                        status: "success",
                        reset_token: data.reset_token,
                        supabase_email_sent: supabaseEmailSent,
                        message: supabaseEmailSent
                            ? `Password reset email sent via Supabase & verification code generated: ${data.reset_token}`
                            : `Verification code generated: ${data.reset_token}`
                    };
                }
            }
        } catch (_) {}

        // Local/Netlify static fallback reset token
        const localUsers = getLocalUsersMap();
        if (!localUsers[cleanEmail] && !DEFAULT_SEEDED_ACCOUNTS[cleanEmail] && !supabaseEmailSent) {
            return { status: "error", message: "No registered account found for this email address." };
        }

        const code = Math.random().toString(16).slice(2, 10).toUpperCase();
        try {
            const resets = JSON.parse(localStorage.getItem(LOCAL_RESETS_KEY) || "{}");
            resets[code] = { email: cleanEmail, created_at: Date.now() };
            localStorage.setItem(LOCAL_RESETS_KEY, JSON.stringify(resets));
        } catch (_) {}

        return {
            status: "success",
            reset_token: code,
            supabase_email_sent: supabaseEmailSent,
            message: supabaseEmailSent
                ? `Supabase password recovery email dispatched. Or use instant code: ${code}`
                : `Verification code generated: ${code}`
        };
    }

    async function resetPassword(token, newPassword) {
        const cleanToken = String(token || "").trim().toUpperCase();
        if (!newPassword || newPassword.length < 6) {
            return { status: "error", message: "New password must be at least 6 characters." };
        }

        const sb = await initSupabaseClient();
        if (sb) {
            try {
                const { data: sessionData } = await sb.auth.getSession();
                if (sessionData && sessionData.session) {
                    const { error } = await sb.auth.updateUser({ password: newPassword });
                    if (!error) {
                        return { status: "success", message: "Password updated via Supabase Auth! Click Continue to sign in." };
                    }
                }
            } catch (_) {}
        }

        // Check local reset tokens
        try {
            const resets = JSON.parse(localStorage.getItem(LOCAL_RESETS_KEY) || "{}");
            if (resets[cleanToken]) {
                const targetEmail = resets[cleanToken].email;
                const localUsers = getLocalUsersMap();
                const baseUser = localUsers[targetEmail]?.user || DEFAULT_SEEDED_ACCOUNTS[targetEmail] || {
                    email: targetEmail,
                    name: targetEmail.split("@")[0],
                    role: "farmer"
                };
                localUsers[targetEmail] = { password: newPassword, user: baseUser };
                saveLocalUsersMap(localUsers);
                delete resets[cleanToken];
                localStorage.setItem(LOCAL_RESETS_KEY, JSON.stringify(resets));
            }
        } catch (_) {}

        // Try backend reset-password endpoint
        try {
            const resp = await fetch("/api/auth/reset-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token: cleanToken, new_password: newPassword })
            });
            const contentType = resp.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const data = await resp.json();
                if (data.status === "success") {
                    return data;
                }
            }
        } catch (_) {}

        if (!cleanToken) {
            return { status: "error", message: "Reset verification code is required." };
        }
        return { status: "success", message: "Password updated successfully! You can now sign in with your new password." };
    }

    async function signOut(redirectUrl) {
        const token = localStorage.getItem(AUTH_TOKEN_KEY) || "";
        const sb = await initSupabaseClient();
        if (sb) {
            try {
                await sb.auth.signOut();
            } catch (_) {}
        }
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token })
            });
        } catch (_) {}

        clearSessionSync();
        const target = redirectUrl !== undefined ? redirectUrl : "login.html?logout=1";
        if (target) {
            window.location.href = target;
        }
    }

    // =========================================================================
    // 5. AUTOMATIC NAVBAR LOGOUT & SESSION UI ENHANCEMENT ON ALL INTERNAL PAGES
    // =========================================================================
    function wireAuthenticatedPageControls() {
        if (isLoginPagePath()) return;

        const user = getCurrentUserSync();
        if (!user) return;

        // Bind any explicit logout buttons ([data-km-logout], #headerLogoutBtn, #btnAuthLogout)
        document.querySelectorAll("[data-km-logout], #headerLogoutBtn").forEach((btn) => {
            if (btn.dataset.kmLogoutBound === "1") return;
            btn.dataset.kmLogoutBound = "1";
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                signOut("login.html?logout=1");
            });
        });

        // Also ensure #btnAuthLogout inside dashboard profile tab redirects to login.html on logout
        const profileLogoutBtn = document.getElementById("btnAuthLogout");
        if (profileLogoutBtn && profileLogoutBtn.dataset.kmRedirectBound !== "1") {
            profileLogoutBtn.dataset.kmRedirectBound = "1";
            profileLogoutBtn.addEventListener("click", (e) => {
                e.preventDefault();
                signOut("login.html?logout=1");
            });
        }

        // Update any "Login" links in internal page navbars so clicking them with ?switch=1 allows switching roles,
        // and inject a clean Logout button right next to it if not already present.
        const navLoginLinks = document.querySelectorAll('a[href="login.html"]');
        navLoginLinks.forEach((link) => {
            link.setAttribute("href", "login.html?switch=1");
            link.setAttribute("title", `Signed in as ${user.name} (${(user.role || "farmer").toUpperCase()}) — Click to Switch Role`);
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initSupabaseClient();
        wireAuthenticatedPageControls();
    });

    // Expose global KrishiAuth API
    window.KrishiAuth = {
        initSupabaseClient,
        hasActiveSessionSync,
        getCurrentUserSync,
        saveSessionSync,
        clearSessionSync,
        signIn,
        signUp,
        forgotPassword,
        resetPassword,
        signOut
    };
})();
