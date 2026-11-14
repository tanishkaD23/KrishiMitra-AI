/**
 * KrishiMitra-AI — Supabase Runtime Configuration
 *
 * Reads Supabase project credentials from:
 *   1. Window globals / meta tags (injected by Netlify build or HTML meta)
 *   2. LocalStorage overrides (km_supabase_url / km_supabase_anon_key)
 *   3. Backend /api/auth/supabase-config or frontend/supabase_env.json
 */
(function () {
    const metaUrl = document.querySelector('meta[name="supabase-url"]')?.content || "";
    const metaKey = document.querySelector('meta[name="supabase-anon-key"]')?.content || "";

    window.KRISHI_SUPABASE_CONFIG = {
        supabaseUrl:
            window.SUPABASE_URL ||
            window.VITE_SUPABASE_URL ||
            window.NEXT_PUBLIC_SUPABASE_URL ||
            metaUrl ||
            localStorage.getItem("km_supabase_url") ||
            "",
        supabaseAnonKey:
            window.SUPABASE_ANON_KEY ||
            window.VITE_SUPABASE_ANON_KEY ||
            window.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
            metaKey ||
            localStorage.getItem("km_supabase_anon_key") ||
            ""
    };
})();
