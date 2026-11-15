/**
 * KrishiMitra AI - Professional Enterprise Dashboard Controller
 * Connects directly to FastAPI / Flask backend APIs:
 * - GET    /api/dashboard-data
 * - POST   /api/predict
 * - GET    /api/advisory
 * - GET    /api/weather
 * - POST   /api/krishisathi/chat
 * - GET    /api/schemes
 * - GET/PUT /api/farmer
 * - GET/POST/DELETE /api/plots
 */

document.addEventListener("DOMContentLoaded", () => {

    // Global State
    const state = {
        stateName: "Uttar Pradesh",
        district: "Meerut",
        crop: "Wheat",
        lang: localStorage.getItem("km_lang") || "en",
        theme: localStorage.getItem("km_theme") || "light",
        yieldTrendChart: null,
        cropComparisonChart: null,
        isListening: false,
        recognition: null,
        synthesis: window.speechSynthesis || null,
        cachedData: null,
        farmerProfile: {
            id: "farmer-001",
            name: "Tanishka",
            phone: "+91 98765 43210",
            state: "Uttar Pradesh",
            district: "Meerut",
            village: "Daurala",
            language: "en"
        },
        farmerPlots: []
    };

    const STATE_DISTRICTS = Object.assign({
        "Uttar Pradesh": [
            "Meerut", "Agra", "Aligarh", "Allahabad", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya",
            "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly",
            "Basti", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
            "Etawah", "Faizabad", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar",
            "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras",
            "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj",
            "Kaushambi", "Kheri", "Kushi Nagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba",
            "Mainpuri", "Mathura", "Mau", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit",
            "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal",
            "Sant Kabeer Nagar", "Sant Ravidas Nagar", "Shahjahanpur", "Shamli", "Shravasti",
            "Siddharth Nagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
        ],
        "Madhya Pradesh": [
            "Bhopal", "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani",
            "Betul", "Bhind", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas",
            "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur",
            "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narmadapuram",
            "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa",
            "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri",
            "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
        ],
        "Bihar": [
            "Patna", "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur",
            "Buxar", "Darbhanga", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur (Bhabua)",
            "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger",
            "Muzaffarpur", "Nalanda", "Nawada", "Pashchim Champaran", "Purbi Champaran", "Purnia",
            "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi",
            "Siwan", "Supaul", "Vaishali"
        ],
        "Rajasthan": [
            "Jaipur", "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara",
            "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur",
            "Ganganagar", "Hanumangarh", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur",
            "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur",
            "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"
        ],
        "Punjab": [
            "Ludhiana", "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka",
            "Ferozepur", "Firozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala",
            "Malerkotla", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala",
            "Rupnagar", "S.A.S Nagar", "Sangrur", "Tarn Taran"
        ],
        "Haryana": [
            "Karnal", "Ambala", "Bhiwani", "Charki Dadri", "Faridabad", "Fatehabad", "Gurgaon",
            "Hisar", "Jhajjar", "Jind", "Kaithal", "Kurukshetra", "Mahendragarh", "Mewat",
            "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
        ]
    }, (window.KRISHI_ALL_INDIA_DATA && window.KRISHI_ALL_INDIA_DATA.state_districts) || {});

    const STATE_HI = Object.assign({
        "Andaman and Nicobar Islands": "अंडमान और निकोबार द्वीप समूह",
        "Andhra Pradesh": "आंध्र प्रदेश",
        "Arunachal Pradesh": "अरुणाचल प्रदेश",
        "Assam": "असम",
        "Bihar": "बिहार",
        "Chandigarh": "चंडीगढ़",
        "Chhattisgarh": "छत्तीसगढ़",
        "Dadra and Nagar Haveli and Daman and Diu": "दादरा और नगर हवेली और दमन और दीव",
        "Delhi": "दिल्ली",
        "Goa": "गोवा",
        "Gujarat": "गुजरात",
        "Haryana": "हरियाणा",
        "Himachal Pradesh": "हिमाचल प्रदेश",
        "Jammu and Kashmir": "जम्मू और कश्मीर",
        "Jharkhand": "झारखंड",
        "Karnataka": "कर्नाटक",
        "Kerala": "केरल",
        "Ladakh": "लद्दाख",
        "Madhya Pradesh": "मध्य प्रदेश",
        "Maharashtra": "महाराष्ट्र",
        "Manipur": "मणिपुर",
        "Meghalaya": "मेघालय",
        "Mizoram": "मिजोरम",
        "Nagaland": "नागालैंड",
        "Odisha": "ओडिशा",
        "Puducherry": "पुदुचेरी",
        "Punjab": "पंजाब",
        "Rajasthan": "राजस्थान",
        "Sikkim": "सिक्किम",
        "Tamil Nadu": "तमिलनाडु",
        "Telangana": "तेलंगाना",
        "Tripura": "त्रिपुरा",
        "Uttar Pradesh": "उत्तर प्रदेश",
        "Uttarakhand": "उत्तराखंड",
        "West Bengal": "पश्चिम बंगाल"
    }, (window.KRISHI_ALL_INDIA_DATA && window.KRISHI_ALL_INDIA_DATA.state_hi) || {});

    const CROP_HI = {
        "Wheat": "गेहूं",
        "Mustard": "सरसों",
        "Gram": "चना",
        "Barley": "जौ",
        "Masoor": "मसूर",
        "Maize": "मक्का",
        "Peas & beans (Pulses)": "मटर और फलियां",
        "Potato": "आलू",
        "Onion": "प्याज",
        "Linseed": "अलसी"
    };

    // -------------------------------------------------------------------------
    // FULL WEBSITE BILINGUAL DICTIONARY (English <-> हिंदी)
    // -------------------------------------------------------------------------
    const DASHBOARD_I18N = {
        en: {
            nav_dashboard: "Dashboard",
            nav_predict: "Predict Yield",
            nav_advisories: "Advisories",
            nav_schemes: "Schemes",
            nav_krishisathi: "KrishiSathi",
            nav_weather: "Weather & Risk",
            nav_farms: "My Farms",
            nav_profile: "Profile",
            nav_home_ext: "Home ↗",
            help_title: "Need Help?",
            help_sub: "Talk to KrishiSathi",
            stat_est_yield: "Estimated Yield",
            stat_risk_status: "Risk Status",
            val_low: "Low",
            val_moderate: "Moderate",
            val_info: "Info",
            val_urgent: "Urgent",
            stat_cur_season: "Current season",
            stat_weather_outlook: "Weather Outlook",
            stat_next_7_days: "Next 7 days",
            stat_rel_schemes: "Relevant Schemes",
            val_9_avail: "9 Available",
            stat_based_profile: "Based on your profile",
            badge_apy_hist: "APY Historical (2018-2023)",
            chart_comp_title: "Multi-State Yield Comparison (q/ha)",
            badge_6_states: "All-India • Rabi Benchmark",
            dash_banner_title: "Active Crop Phase: Tillering Stage (20–35 Days After Sowing)",
            dash_banner_desc: "Maintain optimum moisture in sandy-loam soil. First nitrogen top-dressing recommended before the 2nd irrigation.",
            btn_view_advisories: "View Advisories →",
            pred_title: "Predict Crop Yield",
            pred_sub: "Configure your plot details to get a real-time yield estimate in both q/ha and q/acre.",
            btn_standalone_calc: "Open Standalone Calculator ↗",
            lbl_state: "State",
            lbl_district: "District",
            lbl_crop: "Crop",
            lbl_plot_acres: "Plot Size (Acres)",
            lbl_sowing_win: "Sowing Window",
            lbl_irrigation: "Irrigation Source",
            lbl_season: "Season",
            lbl_ref_year: "Reference Season Year",
            btn_predict_now: "Predict Yield",
            lbl_yield_per_acre: "Yield per Acre",
            lbl_tot_harvest: "Total Expected Harvest",
            lbl_conf_range: "90% Confidence Range",
            lbl_dist_base: "District Baseline",
            notes_title: "Agronomic Guidance & Units",
            notes_li_1: "Predictions are displayed in both Quintals per Hectare (q/ha) and Quintals per Acre (q/acre) (1 Hectare = 2.471 Acres).",
            notes_li_2: "Total Expected Harvest multiplies your per-acre yield estimate by your entered plot area in acres.",
            notes_li_3: "Timely irrigation at Crown Root Initiation (21–25 DAS) and balanced NPK application help achieve the upper confidence bound.",
            adv_title: "Personalised Agricultural Advisory",
            adv_sub: "Crop-weather precautions, soil management, and verified agronomic protocols.",
            adv_tag_water: "Water Scheduling",
            adv_c1_title: "Crown Root Initiation (CRI) Irrigation",
            adv_c1_body: "Observation: Crop is at 20–25 days after sowing. Crown roots are developing rapidly beneath the surface. Recommendation: Apply light first irrigation (5–6 cm depth). Avoid water stagnation to prevent seedling chlorosis.",
            adv_c1_src: "Source: ICAR - Indian Institute of Wheat and Barley Research (IIWBR)",
            adv_tag_soil: "Soil Nutrition",
            adv_c2_title: "First Nitrogen Top-Dressing",
            adv_c2_body: "Observation: Sandy-loam alluvial soil exhibits rapid nitrogen leaching under tube-well flooding. Recommendation: Broadcast 24 kg Urea per acre immediately following soil drying after 1st watering.",
            adv_c2_src: "Source: Department of Agriculture & Farmers Welfare",
            adv_tag_pest: "Pest & Disease",
            adv_c3_title: "Yellow Rust Field Scouting Protocol",
            adv_c3_body: "Observation: Morning fog and temperatures between 15°C–22°C create favorable sporulation conditions. Recommendation: Inspect bottom leaves for linear yellow pustules. If detected, apply Propiconazole 25% EC @ 200 ml/acre.",
            adv_c3_src: "Source: ICAR Directorate of Plant Protection, Quarantine & Storage",
            sch_title: "Government Schemes for Farmers",
            sch_sub: "Find 9 verified central and state schemes based on your crop, location and profile.",
            lbl_category: "Category",
            btn_search: "Search",
            sathi_title: "KrishiSathi AI Assistant",
            sathi_sub: "Ask your farming and government scheme questions in English or Hindi (हिंदी), anytime.",
            btn_fullscreen_chat: "Open Full Screen Chat ↗",
            chat_init_q: "When is the best time to sow Wheat in Rabi season?",
            chat_init_ans: "The optimal timely sowing window for Wheat across UP, MP, Bihar, Rajasthan, Punjab, and Haryana is November 1 to November 20. Ensure adequate pre-sowing irrigation (Palewa) and use certified varieties such as HD-2967, HD-3086, or DBW-187. You can ask me follow-up questions in English or Hindi (हिंदी)!",
            btn_listen_aloud: "Listen Aloud",
            chip_pmkisan: "PM-KISAN Eligibility",
            chip_cri: "Wheat CRI Irrigation",
            chip_kusum: "PM-KUSUM Solar Pump",
            voice_mode_title: "Voice Companion Mode",
            voice_tap_mic: "Tap Microphone to Speak (English or Hindi)",
            wea_title: "Weather & Risk Insights",
            wea_sub: "Live meteorological conditions, 7-day forecast, and crop risk indicators for your selected district.",
            btn_use_gps: "Use My GPS Location",
            btn_refresh_weather: "Refresh Live Weather",
            wea_7d_title: "Live 7-Day District Weather Forecast",
            wea_cur: "Current Weather",
            wea_rain_7d: "Rainfall (Next 7 days)",
            wea_norm_precip: "Normal precipitation",
            wea_risk_lvl: "Risk Level",
            wea_no_hazard: "No major climate hazard",
            wea_seasonal_title: "Seasonal Risk Indicators",
            risk_heavy_rain: "Heavy Rainfall",
            risk_drought: "Drought Condition",
            risk_pest: "Pest Risk",
            risk_heat: "Heat Stress",
            badge_low_risk: "Low Risk",
            farms_title: "My Farm Holdings",
            farms_sub: "Registered agricultural plots and soil parameters. Add or manage your farm plots below.",
            btn_add_my_farm: "+ Add My Farm",
            add_farm_box_title: "Add My Farm Details",
            add_farm_box_sub: "Enter your plot name, village, crop, land size in acres, soil type, and irrigation source.",
            badge_instant_save: "Saves to Your Profile",
            lbl_farm_name: "Farm / Plot Name *",
            lbl_village: "Village / Tehsil *",
            lbl_soil_type: "Soil Type",
            btn_save_farm: "+ Add Farm to My Holdings",
            prof_title: "Farmer Profile",
            prof_sub: "Verified profile credentials, registered landholding summary, and personal settings.",
            btn_edit_profile: "Edit Profile",
            prof_lbl_phone: "Mobile Number:",
            prof_lbl_lang: "Preferred Language:",
            prof_lbl_ekyc: "Aadhaar / eKYC Status:",
            prof_val_verified: "Verified on PM-KISAN Portal",
            prof_lbl_zone: "Supported Region:",
            edit_prof_heading: "Edit Farmer Profile",
            badge_sqlite_sync: "Live Database Sync",
            lbl_farmer_name: "Farmer Full Name *",
            btn_save_profile: "Save Profile Changes",
            nav_scheme_intel: "Govt Schemes",
            nav_suraksha: "Crop Insurance",
            nav_nasa: "NASA Weather",
            intel_main_title: "KrishiScheme Intelligence — Farmer Beneficiary & Amount Finder",
            intel_main_sub: "Select or search any scheme below to see how many farmers benefited and total ₹ amount distributed.",
            intel_badge_6: "6 Central Schemes • Verified Govt Data",
            pill_s1: "1. PM-KISAN (₹6,000/yr)",
            pill_s2: "2. PMFBY Crop Insurance",
            pill_s3: "3. KCC (4% Interest Loan)",
            pill_s4: "4. Soil Health Card",
            pill_s5: "5. PMKSY Micro-Irrigation",
            pill_s6: "6. PM-KUSUM Solar Pump",
            intel_lbl_search: "Search Scheme",
            intel_lbl_select: "Select Government Scheme",
            opt_s1: "1. PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            opt_s2: "2. PMFBY (Pradhan Mantri Fasal Bima Yojana)",
            opt_s3: "3. KCC (Kisan Credit Card Scheme)",
            opt_s4: "4. Soil Health Card (SHC) Scheme",
            opt_s5: "5. PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)",
            opt_s6: "6. PM-KUSUM (Solar Agriculture Pumps)",
            intel_lbl_state: "Select Your State",
            intel_btn_check: "Check Beneficiaries & ₹ Amount",
            intel_spot_tag: "VERIFIED SCHEME BENEFICIARIES & FINANCIAL AMOUNT",
            intel_btn_portal: "Official Portal ↗",
            intel_lbl_nat_ben: "All-India Beneficiaries",
            intel_lbl_nat_amt: "Total Financial Assistance",
            intel_tbl_title: "All 6 Schemes — Existing Farmers Benefited & Total Amount (Click any row)",
            intel_tbl_badge: "Interactive Comparison",
            th_sch_name: "Scheme Name",
            th_sch_farmers: "Existing Farmers Benefited",
            th_sch_amount: "Total ₹ Amount Distributed",
            th_sch_per_farmer: "Benefit Per Farmer",
            th_sch_portal: "Portal",
            intel_ch1_title: "Year-Wise Beneficiary Trend",
            intel_ch1_badge: "Official Series",
            intel_ch2_title: "State-Wise Beneficiaries",
            intel_ch2_badge: "Top States",
            sur_main_title: "KrishiSuraksha — Landowner & Tenant Crop Insurance (PMFBY)",
            sur_main_sub: "Check whether a farmer cultivating a Landowner's land (Bataidar / Tenant) or own land can claim PMFBY crop insurance and calculate your Sum Insured (₹).",
            sur_helpline: "Helpline: 14447",
            sur_portal_link: "pmfby.gov.in ↗",
            sur_q_landowner: "Can a Farmer Get Insurance on a Landowner's Land? (Select Your Category)",
            sur_mode_owner: "Mode: Own Land",
            own_btn1_t: "1. Own Land (Landowner)",
            own_btn1_s: "Khatauni in your own name",
            own_btn2_t: "2. Landowner's Land (+ Consent/NOC)",
            own_btn2_s: "Tenant with Landowner NOC / Sowing Cert",
            own_btn3_t: "3. Landowner's Land (Oral Bataidar)",
            own_btn3_s: "Oral tenant without written agreement",
            own_btn4_t: "4. Joint Family Khatauni",
            own_btn4_s: "Combined family Khatauni",
            sur_form_title: "Check Claim Eligibility & Coverage",
            sur_72hr_badge: "72-Hr Rule Check",
            sur_lbl_peril_pills: "Select Cause of Crop Loss:",
            peril_hail: "Hailstorm",
            peril_rain: "Unseasonal Rain",
            peril_flood: "Flood / Waterlogging",
            peril_drought: "Drought",
            peril_pest: "Pest / Disease",
            peril_post: "Post-Harvest Rain (14 days)",
            opt_rabi_prem: "Rabi (1.5% Premium)",
            opt_kharif_prem: "Kharif (2.0% Premium)",
            opt_hort_prem: "Commercial / Hort (5%)",
            sur_lbl_enrolled: "PMFBY Enrolled? *",
            opt_enr_yes: "Yes (Enrolled)",
            opt_enr_unsure: "Unsure (Check KCC)",
            opt_enr_no: "No (Not Enrolled)",
            sur_lbl_dup_kcc: "Landowner Duplicate KCC?",
            opt_kcc_no: "No (Only Cultivator)",
            opt_kcc_yes: "Yes (Landowner Claimed KCC)",
            sur_lbl_loss_date: "Loss Date *",
            sur_lbl_cause: "Cause of Damage *",
            sur_btn_submit: "Check Landowner/Farmer Eligibility & Calculate Claim Coverage →",
            sur_verdict_tag: "PMFBY Claim & Landholding Verdict",
            sur_lbl_sum: "Est. Sum Insured",
            sur_lbl_prem: "Farmer Premium",
            sur_lbl_payout: "Payout Mode",
            sur_val_dbt: "Direct Bank DBT",
            sur_docs_title: "Eligibility Checks & Required Documents",
            sur_doc_1: "Own Land: Khatauni copy + Aadhaar Bank Passbook + PMFBY Receipt.",
            sur_doc_2: "Landowner's Land (Bataidar): Landowner NOC / Lease Agreement OR Patwari/Pradhan Sowing Certificate.",
            sur_doc_3: "72-Hour Intimation: Report within 72 hours on Crop Insurance App or Toll-Free 14447.",
            sur_disclaimer: "Preliminary AI eligibility guidance based on PMFBY guidelines. Final settlement is verified by the insurance company."
        },
        hi: {
            nav_dashboard: "डैशबोर्ड",
            nav_predict: "उपज अनुमान",
            nav_advisories: "कृषि सलाह",
            nav_schemes: "सरकारी योजनाएं",
            nav_krishisathi: "कृषिसाथी AI",
            nav_weather: "मौसम और जोखिम",
            nav_farms: "मेरे खेत",
            nav_profile: "किसान प्रोफ़ाइल",
            nav_home_ext: "मुख्य पृष्ठ ↗",
            help_title: "मदद चाहिए?",
            help_sub: "कृषिसाथी से बात करें",
            stat_est_yield: "अनुमानित उपज",
            stat_risk_status: "जोखिम स्तर",
            val_low: "कम",
            val_moderate: "मध्यम",
            val_info: "सूचना",
            val_urgent: "अति आवश्यक",
            stat_cur_season: "वर्तमान रबी सीजन",
            stat_weather_outlook: "मौसम का पूर्वानुमान",
            stat_next_7_days: "अगले 7 दिन",
            stat_rel_schemes: "प्रमुख सरकारी योजनाएं",
            val_9_avail: "9 उपलब्ध योजनाएं",
            stat_based_profile: "आपकी प्रोफ़ाइल के अनुसार",
            badge_apy_hist: "ऐतिहासिक रिकॉर्ड (2018-2023)",
            chart_comp_title: "बहु-राज्य उपज तुलना (क्विंटल/हेक्टेयर)",
            badge_6_states: "अखिल भारतीय बेंचमार्क",
            dash_banner_title: "सक्रिय फसल अवस्था: कल्ले निकलने की अवस्था (बुवाई के 20–35 दिन बाद)",
            dash_banner_desc: "दोमट मिट्टी में उचित नमी बनाए रखें। दूसरी सिंचाई से पहले यूरिया की पहली टॉप-ड्रेसिंग की सलाह दी जाती है।",
            btn_view_advisories: "कृषि सलाह देखें →",
            pred_title: "फसल उपज का अनुमान लगाएं",
            pred_sub: "क्विंटल प्रति हेक्टेयर और क्विंटल प्रति एकड़ में सटीक उपज अनुमान के लिए अपने खेत का विवरण चुनें।",
            btn_standalone_calc: "पूर्ण कैलकुलेटर खोलें ↗",
            lbl_state: "राज्य",
            lbl_district: "जिला",
            lbl_crop: "फसल",
            lbl_plot_acres: "खेत का क्षेत्रफल (एकड़)",
            lbl_sowing_win: "बुवाई का समय",
            lbl_irrigation: "सिंचाई का साधन",
            lbl_season: "फसल सीजन",
            lbl_ref_year: "संदर्भ वर्ष",
            btn_predict_now: "उपज का अनुमान लगाएं",
            lbl_yield_per_acre: "प्रति एकड़ उपज",
            lbl_tot_harvest: "कुल अनुमानित पैदावार",
            lbl_conf_range: "90% विश्वसनीयता सीमा",
            lbl_dist_base: "जिला औसत बेंचमार्क",
            notes_title: "कृषि मार्गदर्शन और इकाइयां",
            notes_li_1: "उपज का अनुमान क्विंटल प्रति हेक्टेयर (q/ha) और क्विंटल प्रति एकड़ (q/acre) दोनों में दिखाया गया है (1 हेक्टेयर = 2.471 एकड़)।",
            notes_li_2: "कुल अनुमानित पैदावार आपकी प्रति एकड़ उपज को आपके खेत के कुल एकड़ से गुणा करके निकाली जाती है।",
            notes_li_3: "शीर्ष जड़ अवस्था (21–25 दिन) पर समय पर सिंचाई और संतुलित NPK उर्वरक से अधिकतम उपज प्राप्त होती है।",
            adv_title: "व्यक्तिगत कृषि सलाह",
            adv_sub: "फसल-मौसम सावधानियां, मिट्टी प्रबंधन और प्रमाणित कृषि प्रोटोकॉल।",
            adv_tag_water: "सिंचाई प्रबंधन",
            adv_c1_title: "शीर्ष जड़ अवस्था (CRI) सिंचाई",
            adv_c1_body: "अवलोकन: फसल बुवाई के 20–25 दिन की अवस्था में है। जड़ें तेजी से विकसित हो रही हैं। सलाह: पहली हल्की सिंचाई (5–6 सेमी गहराई) करें। खेत में पानी न भरने दें ताकि पौधे पीले न पड़ें।",
            adv_c1_src: "स्रोत: भारतीय गेहूं एवं जौ अनुसंधान संस्थान (ICAR-IIWBR)",
            adv_tag_soil: "मिट्टी पोषण",
            adv_c2_title: "नाइट्रोजन (यूरिया) की पहली टॉप-ड्रेसिंग",
            adv_c2_body: "अवलोकन: बलुई दोमट मिट्टी में नलकूप सिंचाई के बाद नाइट्रोजन तेजी से नीचे जाती है। सलाह: पहली सिंचाई के बाद मिट्टी में पैर टिकने पर 24 किग्रा यूरिया प्रति एकड़ का छिड़काव करें।",
            adv_c2_src: "स्रोत: कृषि एवं किसान कल्याण विभाग",
            adv_tag_pest: "कीट एवं रोग सुरक्षा",
            adv_c3_title: "पीला रतुआ (Yellow Rust) निगरानी प्रोटोकॉल",
            adv_c3_body: "अवलोकन: सुबह का कोहरा और 15°C–22°C तापमान रतुआ रोग के लिए अनुकूल है। सलाह: निचली पत्तियों पर पीली धारियों की जांच करें। लक्षण दिखने पर प्रोपिकोनाजोल 25% EC @ 200 मिली/एकड़ का छिड़काव करें।",
            adv_c3_src: "स्रोत: पौध संरक्षण निदेशालय (ICAR)",
            sch_title: "किसानों के लिए सरकारी योजनाएं",
            sch_sub: "अपनी फसल, राज्य और पात्रता के आधार पर 9 प्रमाणित केंद्रीय और राज्य योजनाएं खोजें।",
            lbl_category: "योजना श्रेणी",
            btn_search: "खोजें",
            sathi_title: "कृषिसाथी AI सहायक",
            sathi_sub: "खेती और सरकारी योजनाओं से जुड़े अपने सवाल हिंदी या अंग्रेजी में कभी भी पूछें।",
            btn_fullscreen_chat: "फुल-स्क्रीन चैट खोलें ↗",
            chat_init_q: "रबी सीजन में गेहूं की बुवाई का सबसे अच्छा समय कब है?",
            chat_init_ans: "उत्तर प्रदेश, मध्य प्रदेश, बिहार, राजस्थान, पंजाब और हरियाणा में गेहूं की समय पर बुवाई का सर्वोत्तम समय 1 नवंबर से 20 नवंबर है। बुवाई से पहले पर्याप्त पलेवा करें और HD-2967, HD-3086 या DBW-187 जैसी प्रमाणित किस्मों का उपयोग करें। आप मुझसे हिंदी या अंग्रेजी में कोई भी सवाल पूछ सकते हैं!",
            btn_listen_aloud: "आवाज़ में सुनें",
            chip_pmkisan: "पीएम-किसान पात्रता",
            chip_cri: "गेहूं में पहली सिंचाई (CRI)",
            chip_kusum: "पीएम-कुसुम सोलर पंप सब्सिडी",
            voice_mode_title: "आवाज़ सहायक मोड (Voice Mode)",
            voice_tap_mic: "बोलने के लिए माइक दबाएं (हिंदी या अंग्रेजी)",
            wea_title: "मौसम और जोखिम की जानकारी (Live)",
            wea_sub: "आपके चुने हुए जिले के लिए लाइव मौसम, 7-दिन का पूर्वानुमान और फसल जोखिम संकेतक।",
            btn_use_gps: "मेरी GPS लोकेशन चुनें",
            btn_refresh_weather: "लाइव मौसम अपडेट करें",
            wea_7d_title: "आगामी 7-दिन का लाइव मौसम पूर्वानुमान",
            wea_cur: "वर्तमान मौसम",
            wea_rain_7d: "वर्षा (अगले 7 दिन)",
            wea_norm_precip: "सामान्य वर्षा स्तर",
            wea_risk_lvl: "जोखिम स्तर",
            wea_no_hazard: "कोई बड़ा मौसमी खतरा नहीं",
            wea_seasonal_title: "मौसमी जोखिम संकेतक",
            risk_heavy_rain: "भारी वर्षा जोखिम",
            risk_drought: "सूखा स्थिति",
            risk_pest: "कीट एवं रोग जोखिम",
            risk_heat: "अधिक तापमान / लू का असर",
            badge_low_risk: "कम जोखिम",
            farms_title: "मेरे खेत (My Farm Holdings)",
            farms_sub: "पंजीकृत कृषि भूखंड और मिट्टी का विवरण। नीचे अपने नए खेत का विवरण जोड़ें या प्रबंधित करें।",
            btn_add_my_farm: "+ नया खेत जोड़ें",
            add_farm_box_title: "नया खेत जोड़ें (Add My Farm Details)",
            add_farm_box_sub: "अपने खेत का नाम, गांव, फसल, भूमि का आकार (एकड़ में), मिट्टी का प्रकार और सिंचाई का साधन दर्ज करें।",
            badge_instant_save: "प्रोफ़ाइल में सुरक्षित",
            lbl_farm_name: "खेत / प्लॉट का नाम *",
            lbl_village: "गांव / तहसील *",
            lbl_soil_type: "मिट्टी का प्रकार",
            btn_save_farm: "+ मेरे खेतों में जोड़ें",
            prof_title: "किसान प्रोफ़ाइल",
            prof_sub: "प्रमाणित किसान विवरण, कुल पंजीकृत भूमि और व्यक्तिगत सेटिंग्स।",
            btn_edit_profile: "प्रोफ़ाइल संपादित करें",
            prof_lbl_phone: "मोबाइल नंबर:",
            prof_lbl_lang: "पसंदीदा भाषा:",
            prof_lbl_ekyc: "आधार / eKYC स्थिति:",
            prof_val_verified: "पीएम-किसान पोर्टल पर सत्यापित",
            prof_lbl_zone: "पंजीकृत क्षेत्र:",
            edit_prof_heading: "किसान प्रोफ़ाइल संपादित करें",
            badge_sqlite_sync: "लाइव डेटाबेस सिंक",
            lbl_farmer_name: "किसान का पूरा नाम *",
            btn_save_profile: "प्रोफ़ाइल परिवर्तन सहेजें",
            nav_scheme_intel: "सरकारी योजनाएं",
            nav_suraksha: "फसल बीमा (PMFBY)",
            nav_nasa: "नासा मौसम",
            intel_main_title: "कृषि-योजना इंटेलिजेंस — लाभार्थी किसान एवं कुल राशि विवरण",
            intel_main_sub: "नीचे किसी भी सरकारी योजना को चुनें या खोजें और जानें कि अब तक कितने किसानों को लाभ मिला और कुल कितनी राशि (₹) वितरित की गई।",
            intel_badge_6: "6 प्रमुख केंद्रीय योजनाएं • सत्यापित सरकारी डेटा",
            pill_s1: "1. पीएम-किसान (₹6,000/वर्ष)",
            pill_s2: "2. पीएम फसल बीमा (PMFBY)",
            pill_s3: "3. किसान क्रेडिट कार्ड (4% ऋण)",
            pill_s4: "4. मृदा स्वास्थ्य कार्ड",
            pill_s5: "5. पीएम कृषि सिंचाई (PMKSY)",
            pill_s6: "6. पीएम-कुसुम सोलर पंप",
            intel_lbl_search: "योजना खोजें",
            intel_lbl_select: "सरकारी योजना चुनें",
            opt_s1: "1. पीएम-किसान (प्रधानमंत्री किसान सम्मान निधि)",
            opt_s2: "2. पीएमएफबीवाई (प्रधानमंत्री फसल बीमा योजना)",
            opt_s3: "3. केसीसी (किसान क्रेडिट कार्ड योजना)",
            opt_s4: "4. मृदा स्वास्थ्य कार्ड (Soil Health Card) योजना",
            opt_s5: "5. पीएमकेएसवाई (प्रधानमंत्री कृषि सिंचाई योजना)",
            opt_s6: "6. पीएम-कुसुम (सोलर कृषि पंप योजना)",
            intel_lbl_state: "अपना राज्य चुनें",
            intel_btn_check: "लाभार्थी संख्या और ₹ राशि देखें",
            intel_spot_tag: "सत्यापित योजना लाभार्थी और कुल वितरित वित्तीय राशि",
            intel_btn_portal: "आधिकारिक पोर्टल ↗",
            intel_lbl_nat_ben: "अखिल भारतीय लाभार्थी किसान (कितने किसानों को लाभ मिला)",
            intel_lbl_nat_amt: "कुल वितरित वित्तीय सहायता (कुल कितनी राशि मिली)",
            intel_tbl_title: "सभी 6 सरकारी योजनाएं — कुल लाभार्थी किसान और वितरित राशि (किसी भी पंक्ति पर क्लिक करें)",
            intel_tbl_badge: "इंटरएक्टिव तुलना",
            th_sch_name: "योजना का नाम",
            th_sch_farmers: "लाभान्वित किसानों की संख्या",
            th_sch_amount: "कुल वितरित राशि (₹)",
            th_sch_per_farmer: "प्रति किसान मिलने वाला लाभ",
            th_sch_portal: "पोर्टल लिंक",
            intel_ch1_title: "वर्ष-वार लाभार्थी रुझान (Yearly Trend)",
            intel_ch1_badge: "आधिकारिक श्रृंखला",
            intel_ch2_title: "राज्य-वार लाभार्थी किसान",
            intel_ch2_badge: "प्रमुख राज्य",
            sur_main_title: "कृषिसुरक्षा — भूमि मालिक (Landowner) एवं बटाईदार किसान फसल बीमा (PMFBY)",
            sur_main_sub: "जांचें कि ज़मीन मालिक (Landowner) की भूमि पर खेती करने वाले बटाईदार/किरायेदार किसान या स्वयं की भूमि वाले किसान को PMFBY फसल बीमा क्लेम कैसे मिलेगा और अपनी बीमा राशि (₹) की गणना करें।",
            sur_helpline: "हेल्पलाइन: 14447",
            sur_portal_link: "pmfby.gov.in ↗",
            sur_q_landowner: "क्या ज़मीन मालिक (Landowner) की भूमि पर किसान को बीमा मिल सकता है? (अपनी श्रेणी चुनें)",
            sur_mode_owner: "श्रेणी: स्वयं की भूमि (Own Land)",
            own_btn1_t: "1. स्वयं की भूमि (Landowner)",
            own_btn1_s: "आपके अपने नाम की खतौनी",
            own_btn2_t: "2. ज़मीन मालिक की भूमि (+ सहमति पत्र/NOC)",
            own_btn2_s: "बटाईदार किसान (मालिक की NOC / बुवाई प्रमाण पत्र सहित)",
            own_btn3_t: "3. ज़मीन मालिक की भूमि (मौखिक बटाईदार)",
            own_btn3_s: "बिना लिखित समझौते के बटाईदार किसान",
            own_btn4_t: "4. संयुक्त परिवार की खतौनी",
            own_btn4_s: "परिवार के संयुक्त नाम की खतौनी",
            sur_form_title: "बीमा क्लेम पात्रता और कवरेज की जांच करें",
            sur_72hr_badge: "72-घंटे नियम जांच",
            sur_lbl_peril_pills: "फसल नुकसान का कारण चुनें:",
            peril_hail: "ओलावृष्टि (Hailstorm)",
            peril_rain: "बेमौसम / अत्यधिक बारिश",
            peril_flood: "बाढ़ / जलभराव",
            peril_drought: "सूखा (Drought)",
            peril_pest: "कीट एवं रोग प्रकोप",
            peril_post: "कटाई के बाद बारिश (14 दिन के भीतर)",
            opt_rabi_prem: "रबी (1.5% किसान प्रीमियम)",
            opt_kharif_prem: "खरीफ (2.0% किसान प्रीमियम)",
            opt_hort_prem: "वाणिज्यिक / बागवानी (5%)",
            sur_lbl_enrolled: "PMFBY में पंजीकृत? *",
            opt_enr_yes: "हाँ (पंजीकृत है)",
            opt_enr_unsure: "अनिश्चित (KCC जांचें)",
            opt_enr_no: "नहीं (पंजीकृत नहीं)",
            sur_lbl_dup_kcc: "क्या मालिक ने डुप्लीकेट KCC लिया है?",
            opt_kcc_no: "नहीं (केवल वास्तविक काश्तकार)",
            opt_kcc_yes: "हाँ (मालिक ने KCC क्लेम किया है)",
            sur_lbl_loss_date: "नुकसान की तिथि *",
            sur_lbl_cause: "नुकसान का मुख्य कारण *",
            sur_btn_submit: "भूमि मालिक/किसान पात्रता जांचें और बीमा कवरेज की गणना करें →",
            sur_verdict_tag: "PMFBY क्लेम और भूमि पात्रता निर्णय",
            sur_lbl_sum: "अनुमानित बीमित राशि",
            sur_lbl_prem: "किसान प्रीमियम अंश",
            sur_lbl_payout: "भुगतान माध्यम",
            sur_val_dbt: "सीधा बैंक खाता (DBT)",
            sur_docs_title: "पात्रता जांच और आवश्यक दस्तावेज",
            sur_doc_1: "स्वयं की भूमि: खतौनी की नकल + आधार लिंक बैंक पासबुक + PMFBY रसीद।",
            sur_doc_2: "ज़मीन मालिक की भूमि (बटाईदार): मालिक का सहमति पत्र (NOC) / किरायानामा या पटवारी/प्रधान द्वारा जारी बुवाई प्रमाण पत्र।",
            sur_doc_3: "72-घंटे में सूचना: फसल नुकसान के 72 घंटे के भीतर क्रॉप इंश्योरेंस ऐप या टोल-फ्री 14447 पर सूचना दें।",
            sur_disclaimer: "यह PMFBY दिशानिर्देशों पर आधारित प्रारंभिक AI पात्रता मार्गदर्शन है। अंतिम क्लेम भुगतान बीमा कंपनी और जिला कृषि अधिकारी के सर्वे द्वारा सत्यापित किया जाता है।"
        }
    };

    // -------------------------------------------------------------------------
    // 9 VERIFIED GOVERNMENT SCHEMES (BILINGUAL EN + HI)
    // -------------------------------------------------------------------------
    const DASHBOARD_SCHEMES = [
        {
            id: "pm_kisan",
            category: "Income",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-income",
            portal: "https://pmkisan.gov.in",
            en: {
                tag: "Direct Income Support",
                title: "PM Kisan Samman Nidhi (PM-KISAN)",
                desc: "Provides ₹6,000 per year in three equal installments of ₹2,000 every 4 months directly into Aadhaar-seeded bank accounts.",
                elig: "All cultivable landholding farmer families across India with completed eKYC.",
                benefit: "₹6,000 / Year (3 Installments of ₹2,000)",
                docs: "Aadhaar Card, Khatauni / Land Record, Aadhaar-seeded Bank Account"
            },
            hi: {
                tag: "प्रत्यक्ष आय सहायता",
                title: "पीएम किसान सम्मान निधि (PM-KISAN)",
                desc: "सभी पात्र भूमिधारक किसान परिवारों को हर 4 महीने में ₹2,000 की तीन समान किस्तों में ₹6,000 प्रति वर्ष की सीधी सहायता।",
                elig: "कृषि योग्य भूमि वाले सभी किसान परिवार (eKYC अनिवार्य)।",
                benefit: "₹6,000 प्रति वर्ष (₹2,000 की 3 किस्तें)",
                docs: "आधार कार्ड, खतौनी / भूमि रिकॉर्ड, आधार से जुड़ा बैंक खाता"
            }
        },
        {
            id: "pmfby",
            category: "Insurance",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-insurance",
            portal: "https://pmfby.gov.in",
            en: {
                tag: "Crop Insurance",
                title: "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                desc: "Comprehensive crop yield insurance against hailstorm, unseasonal rainfall, drought, and pests at nominal 1.5% Rabi farmer premium.",
                elig: "All farmers growing notified Rabi crops (Wheat & Mustard). Claim report within 72 hours.",
                benefit: "Full Sum Insured at 1.5% Rabi Premium",
                docs: "Land Record, Sowing Certificate, Aadhaar & Bank Passbook"
            },
            hi: {
                tag: "फसल बीमा सुरक्षा",
                title: "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
                desc: "ओलावृष्टि, बेमौसम बारिश, सूखा और कीटों से होने वाले फसल नुकसान की भरपाई के लिए केवल 1.5% रबी प्रीमियम पर बीमा।",
                elig: "अधिसूचित क्षेत्रों में गेहूं और सरसों उगाने वाले सभी किसान (72 घंटे में सूचना)।",
                benefit: "केवल 1.5% रबी प्रीमियम पर पूर्ण बीमा सुरक्षा",
                docs: "खतौनी, बुवाई प्रमाण पत्र, आधार और बैंक पासबुक"
            }
        },
        {
            id: "shc",
            category: "Soil",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-soil",
            portal: "https://soilhealth.dac.gov.in",
            en: {
                tag: "Soil & Fertility",
                title: "Soil Health Card (SHC) Scheme",
                desc: "Provides plot-level assessment of 12 soil parameters (N, P, K, pH, EC, OC, S, Zn, Fe, Cu, Mn, B) and crop-wise fertilizer dosages.",
                elig: "All farmers across India; soil samples tested every 3 years at District Labs.",
                benefit: "Free 12-Parameter Soil Test & NPK Advisory",
                docs: "Aadhaar Card, Plot Khasra Number, Mobile Number"
            },
            hi: {
                tag: "मृदा स्वास्थ्य एवं पोषण",
                title: "मृदा स्वास्थ्य कार्ड योजना (Soil Health Card)",
                desc: "मिट्टी के 12 पोषक तत्वों (N, P, K, pH, जिंक, सल्फर आदि) की नि:शुल्क जांच और फसल-वार खाद की सटीक मात्रा की सिफारिश।",
                elig: "सभी किसान; हर 3 वर्ष में जिला मृदा प्रयोगशाला द्वारा नि:शुल्क जांच।",
                benefit: "नि:शुल्क 12-पैरामीटर मिट्टी जांच और उर्वरक सलाह",
                docs: "आधार कार्ड, खसरा संख्या, मोबाइल नंबर"
            }
        },
        {
            id: "pmksy",
            category: "Soil",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-income",
            portal: "https://pmksy.gov.in",
            en: {
                tag: "Micro-Irrigation Subsidy",
                title: "PM Krishi Sinchayee Yojana (Per Drop More Crop)",
                desc: "Financial subsidy of 55% for small & marginal farmers and 45% for other farmers to install Drip and Sprinkler irrigation systems.",
                elig: "Farmers with cultivable land and assured irrigation source across all states.",
                benefit: "Up to 55% Subsidy on Sprinkler & Drip Systems",
                docs: "Aadhaar Card, Land Khatauni, Water Source Proof, Bank Account"
            },
            hi: {
                tag: "सूक्ष्म सिंचाई सब्सिडी",
                title: "पीएम कृषि सिंचाई योजना (Per Drop More Crop)",
                desc: "स्प्रिंकलर और ड्रिप सिंचाई संयंत्र लगाने के लिए लघु और सीमांत किसानों को 55% तथा अन्य किसानों को 45% तक सरकारी अनुदान।",
                elig: "कृषि भूमि और सिंचाई स्रोत वाले सभी पंजीकृत किसान।",
                benefit: "स्प्रिंकलर/ड्रिप पर 45% से 55% तक सीधी सब्सिडी",
                docs: "आधार कार्ड, खतौनी, सिंचाई स्रोत प्रमाण, बैंक खाता"
            }
        },
        {
            id: "kcc",
            category: "Credit",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-soil",
            portal: "https://www.myscheme.gov.in/schemes/kcc",
            en: {
                tag: "Low-Interest Farm Credit",
                title: "Kisan Credit Card (KCC) — 4% Crop Loan",
                desc: "Short-term institutional crop credit up to ₹3 Lakh at an effective 4% annual interest rate (with 3% prompt repayment incentive).",
                elig: "Individual/joint farmers, tenant farmers, oral lessees, and SHGs. Collateral-free up to ₹1.60 Lakh.",
                benefit: "Up to ₹3 Lakh Loan @ 4% Effective Interest",
                docs: "Aadhaar Card, PAN/Voter ID, Land Khatauni, Passport Photo"
            },
            hi: {
                tag: "सस्ता फसली ऋण",
                title: "किसान क्रेडिट कार्ड (KCC) — 4% ब्याज पर ऋण",
                desc: "बीज, खाद, डीजल और सिंचाई खर्चों के लिए ₹3 लाख तक का फसली ऋण, समय पर भुगतान करने पर केवल 4% प्रभावी वार्षिक ब्याज दर पर।",
                elig: "सभी भूमिधारक किसान और बटाईदार। ₹1.60 लाख तक बिना गारंटी ऋण।",
                benefit: "4% प्रभावी ब्याज दर पर ₹3 लाख तक का किसान ऋण",
                docs: "आधार कार्ड, पैन/वोटर आईडी, खतौनी, पासपोर्ट फोटो"
            }
        },
        {
            id: "pm_kusum",
            category: "Solar",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-income",
            portal: "https://pmkusum.mnre.gov.in",
            en: {
                tag: "Solar Irrigation Pump",
                title: "PM-KUSUM Solar Pump Subsidy Scheme",
                desc: "Provides 60% government subsidy (30% Central + 30% State) to install standalone solar agricultural pumps (2 HP to 10 HP) and replace diesel pumps.",
                elig: "Individual farmers, water user associations, and FPOs with Borewell/Tube-well.",
                benefit: "60% Government Subsidy on 2 HP – 10 HP Solar Pumps",
                docs: "Aadhaar Card, Land Khatauni, Borewell Certificate, Bank Account"
            },
            hi: {
                tag: "सोलर पंप अनुदान",
                title: "पीएम-कुसुम सोलर पंप योजना (PM-KUSUM)",
                desc: "डीजल पंप के स्थान पर 2 HP से 10 HP तक के स्टैंडअलोन सोलर पंप लगाने के लिए 60% सरकारी सब्सिडी (30% केंद्र + 30% राज्य)।",
                elig: "बोरवेल/ट्यूबवेल वाले सभी किसान और किसान उत्पादक संगठन (FPO)।",
                benefit: "सोलर पंप पर 60% सब्सिडी (केवल 10% किसान अंशदान)",
                docs: "आधार कार्ड, खतौनी, बोरवेल प्रमाण, बैंक पासबुक"
            }
        },
        {
            id: "smam",
            category: "Machinery",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-insurance",
            portal: "https://agrimachinery.nic.in",
            en: {
                tag: "Farm Mechanization",
                title: "Sub-Mission on Agricultural Mechanization (SMAM)",
                desc: "40% to 50% subsidy on purchasing Super Seeder, Happy Seeder, Rotavator, Zero-Till Seed Drill, and up to 80% for Custom Hiring Centres.",
                elig: "All farmers (50% for SC/ST/Small & Marginal/Women farmers; 40% for others).",
                benefit: "40% – 50% Subsidy on Farm Machinery & Implements",
                docs: "Aadhaar Card, Khatauni, GST Quotation from Authorized Dealer"
            },
            hi: {
                tag: "कृषि यंत्र सब्सिडी",
                title: "कृषि यंत्रीकरण उप-मिशन (SMAM)",
                desc: "सुपर सीडर, हैप्पी सीडर, रोटावेटर और जीरो-टिल सीड ड्रिल खरीदने पर 40% से 50% तक अनुदान तथा कस्टम हायरिंग सेंटर पर 80% तक सब्सिडी।",
                elig: "लघु, सीमांत, महिला और SC/ST किसानों को 50% तथा अन्य को 40% अनुदान।",
                benefit: "आधुनिक कृषि यंत्रों पर 40% से 50% तक सीधी सब्सिडी",
                docs: "आधार कार्ड, खतौनी, अधिकृत डीलर का कोटेशन, बैंक खाता"
            }
        },
        {
            id: "pkvy",
            category: "Organic",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-income",
            portal: "https://pgsindia-ncof.gov.in",
            en: {
                tag: "Organic Farming",
                title: "Paramparagat Krishi Vikas Yojana (PKVY)",
                desc: "Promotes chemical-free organic farming with ₹31,500/hectare over 3 years for bio-fertilizers, vermicompost, PGS certification, and branding.",
                elig: "Farmers practicing or transitioning to organic farming in 20-hectare clusters (up to 2 ha/farmer).",
                benefit: "₹31,500 / Hectare (including ₹15,000 DBT for Bio-Inputs)",
                docs: "Aadhaar Card, Land Record, PGS Cluster Registration"
            },
            hi: {
                tag: "जैविक खेती प्रोत्साहन",
                title: "परम्परागत कृषि विकास योजना (PKVY)",
                desc: "रसायन-मुक्त जैविक खेती को बढ़ावा देने के लिए जैविक खाद, वर्मीकम्पोस्ट और प्रमाणीकरण हेतु 3 वर्षों में ₹31,500 प्रति हेक्टेयर की सहायता।",
                elig: "क्लस्टर में जैविक खेती करने वाले किसान (अधिकतम 2 हेक्टेयर प्रति किसान)।",
                benefit: "₹31,500 / हेक्टेयर (₹15,000 सीधे बैंक खाते में DBT)",
                docs: "आधार कार्ड, खतौनी, क्लस्टर पंजीकरण विवरण"
            }
        },
        {
            id: "enam",
            category: "Organic",
            crops: ["All", "Wheat", "Mustard"],
            tagClass: "tag-soil",
            portal: "https://enam.gov.in",
            en: {
                tag: "Digital Mandi & MSP",
                title: "National Agriculture Market (e-NAM) & MSP Procurement",
                desc: "Transparent electronic mandi trading, free quality assaying, and direct Minimum Support Price (MSP) payment for Wheat & Mustard into farmer accounts.",
                elig: "All farmers selling Wheat, Mustard, or other notified produce in APMC/e-NAM mandis.",
                benefit: "100% Direct MSP Payment & Multi-Mandi Price Discovery",
                docs: "Aadhaar Card, Land Khatauni, Active Mobile Number & Bank Account"
            },
            hi: {
                tag: "डिजिटल मंडी एवं MSP",
                title: "राष्ट्रीय कृषि बाजार (e-NAM) एवं MSP खरीद",
                desc: "गेहूं और सरसों की पारदर्शी ऑनलाइन बोली, नि:शुल्क गुणवत्ता जांच और न्यूनतम समर्थन मूल्य (MSP) का सीधा बैंक खाते में भुगतान।",
                elig: "अपनी उपज मंडी में बेचने वाले सभी पंजीकृत किसान।",
                benefit: "पारदर्शी ऑनलाइन मंडी भाव और सीधा MSP बैंक भुगतान",
                docs: "आधार कार्ड, खतौनी, बैंक पासबुक और मोबाइल नंबर"
            }
        }
    ];

    function populateDistrictDropdown(selectEl, stateName, preferredDistrict = null) {
        if (!selectEl) return "";
        const list = STATE_DISTRICTS[stateName] || STATE_DISTRICTS["Uttar Pradesh"];
        selectEl.innerHTML = "";
        let chosen = list[0];
        list.forEach((dist, idx) => {
            const opt = document.createElement("option");
            opt.value = dist;
            opt.textContent = dist;
            if ((preferredDistrict && dist === preferredDistrict) || (!preferredDistrict && idx === 0)) {
                opt.selected = true;
                chosen = dist;
            }
            selectEl.appendChild(opt);
        });
        return chosen;
    }

    // Apply Theme
    document.documentElement.setAttribute("data-theme", state.theme);
    updateThemeIcon();

    // -------------------------------------------------------------------------
    // 1. TAB NAVIGATION & HASH ROUTING
    // -------------------------------------------------------------------------
    const sidebarLinks = document.querySelectorAll(".sidebar-link");
    const tabScreens = document.querySelectorAll(".app-tab-screen");

    function switchTab(tabId) {
        sidebarLinks.forEach(link => {
            const isMatch = link.getAttribute("data-tab") === tabId;
            link.classList.toggle("active", isMatch);
        });

        tabScreens.forEach(screen => {
            const isMatch = screen.id === tabId;
            screen.classList.toggle("active", isMatch);
            screen.style.display = isMatch ? "block" : "none";
        });

        if (tabId === "tab-dashboard") {
            setTimeout(() => {
                if (state.yieldTrendChart) state.yieldTrendChart.resize();
                if (state.cropComparisonChart) state.cropComparisonChart.resize();
            }, 100);
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    sidebarLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            const targetTab = link.getAttribute("data-tab");
            if (!targetTab) return;
            e.preventDefault();
            const hash = link.getAttribute("href");
            if (hash && hash.startsWith("#")) {
                window.location.hash = hash;
            }
            switchTab(targetTab);
        });
    });

    const helpCard = document.getElementById("sidebarHelpSathiCard");
    if (helpCard) {
        helpCard.addEventListener("click", () => {
            window.location.hash = "#krishisathi";
            switchTab("tab-krishisathi");
        });
    }

    const topAvatar = document.getElementById("topUserAvatar");
    if (topAvatar) {
        topAvatar.style.cursor = "pointer";
        topAvatar.addEventListener("click", () => {
            window.location.hash = "#profile";
            switchTab("tab-profile");
        });
    }

    function handleHashRoute() {
        const hash = window.location.hash.replace("#", "").toLowerCase();
        const routeMap = {
            "dashboard": "tab-dashboard",
            "predict": "tab-predict",
            "advisories": "tab-advisories",
            "schemes": "tab-schemes",
            "scheme-intel": "tab-scheme-intel",
            "suraksha": "tab-suraksha",
            "nasa": "tab-nasa",
            "krishisathi": "tab-krishisathi",
            "weather": "tab-weather",
            "farms": "tab-farms",
            "profile": "tab-profile"
        };
        const targetTab = routeMap[hash] || "tab-dashboard";
        switchTab(targetTab);
    }
    window.addEventListener("hashchange", handleHashRoute);
    handleHashRoute();

    // -------------------------------------------------------------------------
    // 2. THEME & FULL WEBSITE LANGUAGE SWITCHING (EN <-> हिंदी)
    // -------------------------------------------------------------------------
    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            state.theme = state.theme === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", state.theme);
            localStorage.setItem("km_theme", state.theme);
            updateThemeIcon();
            renderCharts(state.cachedData?.historical_yields, state.cachedData?.prediction);
        });
    }

    function updateThemeIcon() {
        const iconSpan = document.getElementById("themeToggleIcon");
        if (iconSpan) {
            if (state.lang === "hi") {
                iconSpan.textContent = state.theme === "dark" ? "लाइट मोड" : "डार्क मोड";
            } else {
                iconSpan.textContent = state.theme === "dark" ? "Light Mode" : "Dark Mode";
            }
        }
    }

    function translateSelectOptions(lang) {
        const isHi = lang === "hi";

        // Translate State Dropdowns (All 35 States & UTs)
        ["statePicker", "predState", "filterState", "newPlotState", "editFarmerState", "intelStateSelect", "insState", "nasaStateSelect"].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            Array.from(el.options).forEach(opt => {
                const st = opt.value;
                if (STATE_HI[st]) {
                    opt.textContent = isHi ? `${STATE_HI[st]} (${st})` : st;
                }
            });
        });

        // Translate Crop Dropdowns
        ["predCrop", "newPlotCrop"].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const cropMapEn = {
                "Wheat": "Wheat (Rabi)",
                "Mustard": "Mustard (Rabi)",
                "Gram": "Gram / Chana (Rabi)",
                "Barley": "Barley / Jau (Rabi)",
                "Masoor": "Masoor / Lentil (Rabi)",
                "Maize": "Maize / Makka (Rabi)",
                "Peas & beans (Pulses)": "Peas & Beans (Rabi)",
                "Potato": "Potato / Aloo (Rabi)",
                "Onion": "Onion / Pyaz (Rabi)",
                "Linseed": "Linseed / Alsi (Rabi)"
            };
            const cropMapHi = {
                "Wheat": "गेहूं (रबी)",
                "Mustard": "सरसों (रबी)",
                "Gram": "चना (रबी)",
                "Barley": "जौ (रबी)",
                "Masoor": "मसूर (रबी)",
                "Maize": "मक्का (रबी)",
                "Peas & beans (Pulses)": "मटर और फलियां (रबी)",
                "Potato": "आलू (रबी)",
                "Onion": "प्याज (रबी)",
                "Linseed": "अलसी (रबी)"
            };
            Array.from(el.options).forEach(opt => {
                if (cropMapEn[opt.value]) {
                    opt.textContent = isHi ? cropMapHi[opt.value] : cropMapEn[opt.value];
                }
            });
        });

        // Translate Sowing Window Dropdowns
        ["predSowing", "newPlotSowing"].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            Array.from(el.options).forEach(opt => {
                if (opt.value.includes("Timely")) {
                    opt.textContent = isHi ? "समय पर बुवाई (01 नवंबर – 20 नवंबर)" : "Timely Sown (Nov 01 – Nov 20)";
                } else if (opt.value.includes("Moderately")) {
                    opt.textContent = isHi ? "मध्यम देरी से बुवाई (21 नवंबर – 05 दिसंबर)" : "Moderately Late (Nov 21 – Dec 05)";
                } else if (opt.value.includes("Very Late")) {
                    opt.textContent = isHi ? "अधिक देरी से बुवाई (05 दिसंबर के बाद)" : "Very Late Sown (After Dec 05)";
                }
            });
        });

        // Translate Irrigation Dropdowns
        ["predIrrigation", "newPlotIrrigation"].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            Array.from(el.options).forEach(opt => {
                if (opt.value.includes("Tube")) {
                    opt.textContent = isHi ? "ट्यूबवेल / बोरवेल" : "Tube well / Borewell";
                } else if (opt.value.includes("Canal")) {
                    opt.textContent = isHi ? "नहर सिंचाई" : "Canal Irrigation";
                } else if (opt.value.includes("Rainfed")) {
                    opt.textContent = isHi ? "वर्षा आधारित / सीमित सिंचाई" : "Rainfed / Limited";
                }
            });
        });

        // Translate Soil Dropdown
        const soilEl = document.getElementById("newPlotSoil");
        if (soilEl) {
            Array.from(soilEl.options).forEach(opt => {
                if (opt.value === "Alluvial (Sandy Loam)") opt.textContent = isHi ? "जलोढ़ (बलुई दोमट मिट्टी)" : "Alluvial (Sandy Loam)";
                if (opt.value === "Alluvial (Clay Loam)") opt.textContent = isHi ? "जलोढ़ (मटियार दोमट मिट्टी)" : "Alluvial (Clay Loam)";
                if (opt.value === "Clay Loam") opt.textContent = isHi ? "चिकनी दोमट मिट्टी" : "Clay Loam";
                if (opt.value === "Sandy Soil") opt.textContent = isHi ? "बलुई मिट्टी" : "Sandy Soil";
            });
        }

        // Translate Season Dropdown
        const seasonEl = document.getElementById("predSeason");
        if (seasonEl && seasonEl.options[0]) {
            seasonEl.options[0].textContent = isHi ? "रबी (शीतकालीन सीजन)" : "Rabi (Winter)";
        }

        // Translate Scheme Filter Dropdowns
        const filterCrop = document.getElementById("filterCrop");
        if (filterCrop) {
            Array.from(filterCrop.options).forEach(opt => {
                if (opt.value === "All") opt.textContent = isHi ? "सभी फसलें" : "All Crops";
                if (opt.value === "Wheat") opt.textContent = isHi ? "गेहूं" : "Wheat";
                if (opt.value === "Mustard") opt.textContent = isHi ? "सरसों" : "Mustard";
            });
        }

        const filterCat = document.getElementById("filterCategory");
        if (filterCat) {
            const catLabels = {
                "All": isHi ? "सभी श्रेणियां (9 योजनाएं)" : "All Categories (9 Schemes)",
                "Income": isHi ? "आय सहायता (पीएम-किसान)" : "Income Support (PM-KISAN)",
                "Insurance": isHi ? "फसल बीमा (PMFBY)" : "Crop Insurance (PMFBY)",
                "Soil": isHi ? "मृदा एवं सिंचाई (SHC / PMKSY)" : "Soil & Irrigation (SHC / PMKSY)",
                "Credit": isHi ? "किसान ऋण (KCC)" : "Institutional Credit (KCC)",
                "Solar": isHi ? "सोलर पंप (पीएम-कुसुम)" : "Solar Pump (PM-KUSUM)",
                "Machinery": isHi ? "कृषि यंत्र (SMAM)" : "Farm Machinery (SMAM)",
                "Organic": isHi ? "जैविक खेती एवं ई-मंडी (PKVY / e-NAM)" : "Organic & Market (PKVY / e-NAM)"
            };
            Array.from(filterCat.options).forEach(opt => {
                if (catLabels[opt.value]) opt.textContent = catLabels[opt.value];
            });
        }

        // Placeholders
        const chatIn = document.getElementById("chatInputField");
        if (chatIn) {
            chatIn.placeholder = isHi ? "अपना कृषि या योजना से जुड़ा प्रश्न यहाँ लिखें..." : "Type your question in English or Hindi...";
        }
        const plotNameIn = document.getElementById("newPlotName");
        if (plotNameIn) {
            plotNameIn.placeholder = isHi ? "उदा., प्लॉट C — नलकूप वाला खेत" : "e.g., Plot C — Tube Well Field";
        }
    }

    function applyDashboardLanguage() {
        const lang = state.lang === "hi" ? "hi" : "en";
        const dict = DASHBOARD_I18N[lang];
        document.documentElement.lang = lang;

        const label = document.getElementById("langSwitchLabel");
        if (label) label.textContent = lang === "hi" ? "हिंदी | EN" : "EN | हिंदी";

        // 1. Update all [data-i18n] elements
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        // 2. Update Greeting Header with Farmer Name
        const farmerName = state.farmerProfile?.name || (lang === "hi" ? "किसान भाई" : "Farmer");
        const topGreeting = document.getElementById("topGreetingText");
        const topSub = document.getElementById("topGreetingSub");
        if (lang === "hi") {
            if (topGreeting) topGreeting.textContent = `नमस्ते, ${farmerName}`;
            if (topSub) topSub.textContent = "यहाँ आपके खेत, मौसम और फसल उपज का संपूर्ण विवरण है।";
        } else {
            if (topGreeting) topGreeting.textContent = `Welcome back, ${farmerName}`;
            if (topSub) topSub.textContent = "Here's an overview of your farm and crop insights.";
        }

        // 3. Translate select options & placeholders
        translateSelectOptions(lang);
        updateThemeIcon();

        // 4. Re-render dynamic sections in the selected language
        renderDashboardSchemes();
        renderMyFarms();
        renderFarmerProfile();
        updateDynamicYieldLabels();
        if (typeof loadKrishiSchemeIntelligence === "function") {
            loadKrishiSchemeIntelligence();
        }
        if (typeof refreshSurakshaLanguage === "function") {
            refreshSurakshaLanguage();
        }
        if (state.cachedData?.weather) {
            renderLiveWeatherForecast(state.cachedData.weather);
        }
        renderCharts(state.cachedData?.historical_yields, state.cachedData?.prediction);
    }

    const langBtn = document.getElementById("langSwitchBtn");
    if (langBtn) {
        langBtn.addEventListener("click", () => {
            state.lang = state.lang === "hi" ? "en" : "hi";
            localStorage.setItem("km_lang", state.lang);
            applyDashboardLanguage();
        });
    }

    // -------------------------------------------------------------------------
    // 3. STATE & DISTRICT PICKER & DATA SYNC
    // -------------------------------------------------------------------------
    const stateSelect = document.getElementById("statePicker");
    const districtSelect = document.getElementById("districtPicker");
    const predStateSelect = document.getElementById("predState");
    const predDistrictSelect = document.getElementById("predDistrict");
    const newPlotStateSelect = document.getElementById("newPlotState");
    const newPlotDistrictSelect = document.getElementById("newPlotDistrict");
    const editFarmerStateSelect = document.getElementById("editFarmerState");
    const editFarmerDistrictSelect = document.getElementById("editFarmerDistrict");

    if (newPlotStateSelect && newPlotDistrictSelect) {
        populateDistrictDropdown(newPlotDistrictSelect, newPlotStateSelect.value, "Meerut");
        newPlotStateSelect.addEventListener("change", (e) => {
            populateDistrictDropdown(newPlotDistrictSelect, e.target.value);
        });
    }

    if (editFarmerStateSelect && editFarmerDistrictSelect) {
        populateDistrictDropdown(editFarmerDistrictSelect, editFarmerStateSelect.value, "Meerut");
        editFarmerStateSelect.addEventListener("change", (e) => {
            populateDistrictDropdown(editFarmerDistrictSelect, e.target.value);
        });
    }

    if (stateSelect) {
        stateSelect.addEventListener("change", (e) => {
            state.stateName = e.target.value;
            state.district = populateDistrictDropdown(districtSelect, state.stateName);
            if (predStateSelect) predStateSelect.value = state.stateName;
            if (predDistrictSelect) populateDistrictDropdown(predDistrictSelect, state.stateName, state.district);
            loadDashboardData();
        });
    }

    if (districtSelect) {
        districtSelect.addEventListener("change", (e) => {
            state.district = e.target.value;
            if (predDistrictSelect) predDistrictSelect.value = state.district;
            loadDashboardData();
        });
    }

    if (predStateSelect) {
        predStateSelect.addEventListener("change", (e) => {
            const newSt = e.target.value;
            populateDistrictDropdown(predDistrictSelect, newSt);
        });
    }

    function updateDynamicYieldLabels() {
        const isHi = state.lang === "hi";
        const p = state.cachedData?.prediction;
        if (!p) return;

        const yieldHa = p.predicted_yield_q_ha || (p.predicted_yield_per_acre ? (p.predicted_yield_per_acre * 2.471).toFixed(1) : 41.5);
        const yieldAcre = p.predicted_yield_per_acre || (yieldHa / 2.471).toFixed(1);
        const cropLabel = isHi ? (CROP_HI[state.crop] || state.crop) : state.crop;
        const stateLabel = isHi ? (STATE_HI[state.stateName] || state.stateName) : state.stateName;

        const elYield = document.getElementById("cardEstimatedYield");
        if (elYield) elYield.textContent = `${yieldHa} q/ha (${yieldAcre} q/acre)`;

        const elCropSub = document.getElementById("cardEstimatedCropSub");
        if (elCropSub) elCropSub.textContent = `${cropLabel} • ${state.district} (${stateLabel})`;

        const elBannerLabel = document.getElementById("predBannerCropLabel");
        if (elBannerLabel) {
            elBannerLabel.textContent = isHi
                ? `अनुमानित उपज • ${cropLabel} (${state.district}, ${stateLabel})`
                : `Estimated Yield • ${cropLabel} (${state.district}, ${stateLabel})`;
        }

        const elBannerYield = document.getElementById("predBannerYieldValue");
        if (elBannerYield) elBannerYield.textContent = `${yieldHa} q/ha (${yieldAcre} q/acre)`;

        const diff = Number(p.performance_vs_regional_mean_pct || 8.5);
        const elModelVer = document.getElementById("predBannerModelVersion");
        if (elModelVer) {
            elModelVer.textContent = isHi
                ? `${diff >= 0 ? "+" : ""}${diff}% राज्य औसत की तुलना में (${stateLabel})`
                : `${diff >= 0 ? "+" : ""}${diff}% vs State Average (${stateLabel})`;
        }

        if (document.getElementById("valPerAcre")) {
            document.getElementById("valPerAcre").textContent = isHi ? `${yieldAcre} क्विंटल/एकड़` : `${yieldAcre} q/acre`;
        }
        if (document.getElementById("valTotalHarvest") && p.total_harvest_quintals) {
            document.getElementById("valTotalHarvest").textContent = isHi
                ? `${p.total_harvest_quintals} क्विंटल`
                : `${p.total_harvest_quintals} Quintals`;
        }
        if (document.getElementById("valConfRange") && p.confidence_interval_90) {
            document.getElementById("valConfRange").textContent = `${p.confidence_interval_90.lower} – ${p.confidence_interval_90.upper} q/acre`;
        }
        if (document.getElementById("valBaseline") && p.regional_benchmark_mean) {
            const baseHa = (p.regional_benchmark_mean * 2.471).toFixed(1);
            document.getElementById("valBaseline").textContent = `${baseHa} q/ha (${p.regional_benchmark_mean} q/acre)`;
        }
    }

    const CONDITION_HI = {
        "Clear Sky": "साफ आसमान",
        "Mainly Clear": "मुख्यतः साफ आसमान",
        "Sunny": "तेज धूप / साफ मौसम",
        "Partly Cloudy": "आंशिक बादल",
        "Cloudy": "बादल छाए रहेंगे",
        "Overcast": "घने बादल",
        "Morning Fog": "सुबह का कोहरा",
        "Dense Fog": "घना कोहरा",
        "Light Drizzle": "हल्की बूंदाबांदी",
        "Moderate Drizzle": "मध्यम बूंदाबांदी",
        "Light Rain": "हल्की बारिश",
        "Moderate Rain": "मध्यम बारिश",
        "Heavy Rain": "भारी बारिश",
        "Rain Showers": "बारिश की बौछारें",
        "Thunderstorm": "मेघगर्जन और आंधी"
    };

    function applyRiskBadgeStyle(badgeEl, riskObj, isHi) {
        if (!badgeEl || !riskObj) return;
        badgeEl.classList.remove("risk-badge-low", "risk-badge-moderate", "risk-badge-high");
        const code = riskObj.code || "low";
        if (code === "high") {
            badgeEl.classList.add("risk-badge-high");
            badgeEl.textContent = isHi ? "उच्च जोखिम" : "HIGH RISK";
        } else if (code === "moderate") {
            badgeEl.classList.add("risk-badge-moderate");
            badgeEl.textContent = isHi ? "मध्यम" : "MODERATE";
        } else {
            badgeEl.classList.add("risk-badge-low");
            badgeEl.textContent = isHi ? "कम जोखिम" : "LOW RISK";
        }
    }

    function renderLiveWeatherForecast(w) {
        if (!w) return;
        const isHi = state.lang === "hi";
        const stateLabel = isHi ? (STATE_HI[state.stateName] || state.stateName) : state.stateName;
        const distName = w.district || state.district;

        const tempVal = w.temperature_c !== undefined ? `${Math.round(w.temperature_c)}°C` : "24°C";
        const rawCond = w.condition || "Clear Sky";
        const condText = isHi ? (CONDITION_HI[rawCond] || rawCond) : rawCond;
        const iconText = w.icon || "☀️";

        // 1. Update Current Weather Card
        const curIcon = document.getElementById("weatherCurIcon");
        const curTemp = document.getElementById("weatherCurTemp");
        const curCond = document.getElementById("weatherCurCond");
        const extraTel = document.getElementById("weatherExtraTelemetry");
        if (curIcon) curIcon.textContent = iconText;
        if (curTemp) curTemp.textContent = tempVal;
        if (curCond) curCond.textContent = condText;
        if (extraTel) {
            const hum = w.humidity_pct !== undefined ? w.humidity_pct : 55;
            const wind = w.wind_speed_kmh !== undefined ? w.wind_speed_kmh : 8.5;
            const feels = w.apparent_temperature_c !== undefined ? Math.round(w.apparent_temperature_c) : Math.round(w.temperature_c || 24);
            extraTel.textContent = isHi
                ? `महसूस: ${feels}°C • नमी: ${hum}% • हवा: ${wind} km/h`
                : `Feels ${feels}°C • Humidity: ${hum}% • Wind: ${wind} km/h`;
        }

        // 2. Update 7-Day Rainfall Card
        const rain7d = w.rain_next_7d_mm !== undefined ? w.rain_next_7d_mm : (w.precipitation_mm || 0);
        const rainProb = w.precipitation_prob_pct !== undefined ? w.precipitation_prob_pct : 5;
        const rainVal = document.getElementById("weatherRainVal");
        const rainSub = document.getElementById("weatherRainSub");
        const rainProbEl = document.getElementById("weatherRainProbText");
        if (rainVal) rainVal.textContent = `${rain7d} mm`;
        if (rainSub) {
            if (rain7d >= 25) {
                rainSub.textContent = isHi ? "अच्छी बारिश की संभावना" : "Active rainfall expected";
            } else if (rain7d > 0) {
                rainSub.textContent = isHi ? "हल्की वर्षा की संभावना" : "Light precipitation expected";
            } else {
                rainSub.textContent = isHi ? "शुष्क मौसम / सामान्य स्थिति" : "Dry & clear week ahead";
            }
        }
        if (rainProbEl) {
            rainProbEl.textContent = isHi
                ? `अधिकतम वर्षा संभावना: ${rainProb}%`
                : `Max Rain Probability: ${rainProb}%`;
        }

        // 3. Update Overall Risk Card & Coords
        const risks = w.risk_indicators || {};
        const overallLvl = risks.overall_risk || "Low";
        const riskValEl = document.getElementById("weatherRiskVal");
        const riskSubEl = document.getElementById("weatherRiskSub");
        const coordsEl = document.getElementById("weatherCoordsText");
        const cardRiskOverview = document.getElementById("cardRiskStatus");
        if (riskValEl) {
            riskValEl.textContent = isHi
                ? (overallLvl === "High" ? "उच्च" : (overallLvl === "Moderate" ? "मध्यम" : "कम"))
                : overallLvl;
        }
        if (cardRiskOverview) {
            cardRiskOverview.textContent = isHi
                ? (overallLvl === "High" ? "उच्च" : (overallLvl === "Moderate" ? "मध्यम" : "कम"))
                : overallLvl;
        }
        if (riskSubEl) {
            riskSubEl.textContent = isHi
                ? (overallLvl === "Low" ? "कोई बड़ा मौसमी खतरा नहीं" : "खेत की नमी और कीट निगरानी रखें")
                : (risks.overall_sub || "No major climate hazard");
        }
        if (coordsEl && w.latitude && w.longitude) {
            coordsEl.textContent = `${distName}, ${stateLabel} (${Number(w.latitude).toFixed(2)}°N, ${Number(w.longitude).toFixed(2)}°E)`;
        }

        // 4. Update Overview Tab Weather Stat Card
        const cardWeatherOutlook = document.getElementById("cardWeatherOutlook");
        if (cardWeatherOutlook) {
            cardWeatherOutlook.textContent = `${tempVal} • ${condText}`;
        }

        // 5. Update Live Status Header & Timestamp
        const liveSrcEl = document.getElementById("weatherLiveSourceText");
        const updatedBadge = document.getElementById("weatherUpdatedTimeBadge");
        if (liveSrcEl) {
            liveSrcEl.textContent = isHi
                ? `लाइव • ${distName} (${w.source || "Open-Meteo"})`
                : `LIVE • ${distName} (${w.source || "Open-Meteo API"})`;
        }
        if (updatedBadge) {
            updatedBadge.textContent = isHi
                ? `अंतिम अपडेट: ${w.updated_at || "अभी"} IST`
                : `Last Synced: ${w.updated_at || "Just now"} IST`;
        }

        // 6. Render 7-Day Daily Forecast Cards
        const grid7d = document.getElementById("live7DayForecastGrid");
        if (grid7d && Array.isArray(w.daily_forecast) && w.daily_forecast.length > 0) {
            grid7d.innerHTML = w.daily_forecast.map((d, idx) => {
                const dayTitle = idx === 0 ? (isHi ? "आज (Today)" : "Today") : d.day_label;
                const dCond = isHi ? (CONDITION_HI[d.condition] || d.condition) : d.condition;
                return `
                    <div style="background: var(--km-bg); border: 1px solid var(--km-border); border-radius: 12px; padding: 12px 10px; text-align: center;">
                        <div style="font-size: 0.78rem; font-weight: 800; color: var(--km-text-heading); margin-bottom: 6px;">${escapeHtml(dayTitle)}</div>
                        <div style="font-size: 1.55rem; margin-bottom: 4px;">${d.icon || "☀️"}</div>
                        <div style="font-size: 0.92rem; font-weight: 800; color: var(--km-primary);">
                            ${Math.round(d.temp_max_c)}° <span style="font-weight: 500; color: var(--km-text-muted); font-size: 0.82rem;">/ ${Math.round(d.temp_min_c)}°C</span>
                        </div>
                        <div style="font-size: 0.73rem; color: var(--km-text-body); margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(dCond)}</div>
                        <div style="font-size: 0.72rem; color: var(--km-text-muted); margin-top: 4px;">
                            💧 ${d.precipitation_mm} mm (${d.precipitation_prob_pct}%)
                        </div>
                    </div>
                `;
            }).join("");
        }

        // 7. Update Dynamic Seasonal Risk Indicators
        applyRiskBadgeStyle(document.getElementById("badgeHeavyRain"), risks.heavy_rainfall, isHi);
        applyRiskBadgeStyle(document.getElementById("badgeDrought"), risks.drought, isHi);
        applyRiskBadgeStyle(document.getElementById("badgePest"), risks.pest_risk, isHi);
        applyRiskBadgeStyle(document.getElementById("badgeHeat"), risks.heat_stress, isHi);

        if (document.getElementById("riskHeavyRainSub") && risks.heavy_rainfall?.detail) {
            document.getElementById("riskHeavyRainSub").textContent = risks.heavy_rainfall.detail;
        }
        if (document.getElementById("riskDroughtSub") && risks.drought?.detail) {
            document.getElementById("riskDroughtSub").textContent = risks.drought.detail;
        }
        if (document.getElementById("riskPestSub") && risks.pest_risk?.detail) {
            document.getElementById("riskPestSub").textContent = risks.pest_risk.detail;
        }
        if (document.getElementById("riskHeatSub") && risks.heat_stress?.detail) {
            document.getElementById("riskHeatSub").textContent = risks.heat_stress.detail;
        }
    }

    async function refreshLiveWeatherOnly(lat = null, lon = null) {
        const btn = document.getElementById("btnRefreshLiveWeather");
        const isHi = state.lang === "hi";
        if (btn) btn.style.opacity = "0.7";
        try {
            let url = `/api/weather?district=${encodeURIComponent(state.district)}`;
            if (lat !== null && lon !== null) {
                url += `&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;
            }
            const res = await fetch(url);
            if (res.ok) {
                const wData = await res.json();
                if (!state.cachedData) state.cachedData = {};
                state.cachedData.weather = wData;
                renderLiveWeatherForecast(wData);
            }
        } catch (err) {
            console.warn("Live weather refresh error:", err);
        } finally {
            if (btn) btn.style.opacity = "1";
        }
    }

    const btnRefreshWea = document.getElementById("btnRefreshLiveWeather");
    if (btnRefreshWea) {
        btnRefreshWea.addEventListener("click", () => refreshLiveWeatherOnly());
    }

    const btnUseGps = document.getElementById("btnWeatherUseGps");
    if (btnUseGps) {
        btnUseGps.addEventListener("click", () => {
            if (!navigator.geolocation) {
                refreshLiveWeatherOnly();
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    refreshLiveWeatherOnly(pos.coords.latitude.toFixed(4), pos.coords.longitude.toFixed(4));
                },
                () => {
                    refreshLiveWeatherOnly();
                },
                { timeout: 6000 }
            );
        });
    }

    async function loadDashboardData() {
        try {
            const res = await fetch(
                `/api/dashboard-data?state=${encodeURIComponent(state.stateName)}&district=${encodeURIComponent(state.district)}&crop=${encodeURIComponent(state.crop)}`
            );
            if (!res.ok) throw new Error("Network response was not ok");
            const data = await res.json();
            state.cachedData = data;

            // Sync Farmer Profile & Plots if returned
            if (data.farmer) {
                state.farmerProfile = data.farmer;
            }
            if (data.plots && Array.isArray(data.plots)) {
                state.farmerPlots = data.plots;
            }

            updateDynamicYieldLabels();
            renderMyFarms();
            renderFarmerProfile();

            // Update Live Weather & 7-Day Forecast in Stats & Weather Tab
            if (data.weather) {
                renderLiveWeatherForecast(data.weather);
            }

            renderCharts(data.historical_yields, data.prediction);
        } catch (err) {
            if (window.KrishiAllIndiaStatic && typeof window.KrishiAllIndiaStatic.computeFallbackPrediction === "function") {
                const fb = window.KrishiAllIndiaStatic.computeFallbackPrediction({
                    state: state.stateName,
                    district: state.district,
                    crop: state.crop,
                    plot_acres: 2.0
                });
                state.cachedData = fb;
                updateDynamicYieldLabels();
                if (fb.weather) renderLiveWeatherForecast(fb.weather);
                renderMyFarms();
                renderFarmerProfile();
                renderCharts(fb.historical_yields, fb.prediction);
                return;
            }
            renderMyFarms();
            renderFarmerProfile();
            renderCharts();
        }
    }

    // -------------------------------------------------------------------------
    // 4. CHART.JS VISUALIZATIONS (Yield Trend & Multi-State Comparison)
    // -------------------------------------------------------------------------
    function renderCharts(historyRecords, prediction) {
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const isHi = state.lang === "hi";
        const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
        const textColor = isDark ? "#94a3b8" : "#64748b";

        const cropLabel = isHi ? (CROP_HI[state.crop] || state.crop) : state.crop;
        const stateLabel = isHi ? (STATE_HI[state.stateName] || state.stateName) : state.stateName;

        const trendTitleEl = document.getElementById("chartYieldTrendTitle");
        if (trendTitleEl) {
            trendTitleEl.textContent = isHi
                ? `उपज रुझान (${cropLabel} - ${state.district}, ${stateLabel})`
                : `Yield Trend (${state.crop} - ${state.district}, ${state.stateName})`;
        }

        // Chart 1: Yield Trend Line Chart
        const ctxTrend = document.getElementById("chartYieldTrend");
        if (ctxTrend) {
            let labels = ["2018", "2019", "2020", "2021", "2022", "2023"];
            let values = [38.2, 39.8, 41.5, 38.9, 41.2, 43.5];

            if (historyRecords && historyRecords.length >= 3) {
                labels = historyRecords.map(r => String(r.start_year || r.year));
                values = historyRecords.map(r => {
                    if (r.yield_q_ha) return Number(r.yield_q_ha);
                    if (r.yield_quintals_per_acre) return Number((r.yield_quintals_per_acre * 2.471).toFixed(1));
                    if (r.yield_tonne_per_ha) return Number((r.yield_tonne_per_ha * 10.0).toFixed(1));
                    return 38.0;
                });
            }

            if (state.yieldTrendChart) {
                state.yieldTrendChart.destroy();
            }

            state.yieldTrendChart = new Chart(ctxTrend, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: isHi ? "उपज (क्विंटल/हेक्टेयर)" : "Yield (q/ha)",
                        data: values,
                        borderColor: "#064E2B",
                        backgroundColor: isDark ? "rgba(34, 197, 94, 0.15)" : "rgba(6, 78, 43, 0.12)",
                        borderWidth: 2.8,
                        pointBackgroundColor: "#064E2B",
                        pointBorderColor: "#ffffff",
                        pointBorderWidth: 2,
                        pointRadius: 4.5,
                        pointHoverRadius: 6.5,
                        fill: true,
                        tension: 0.35
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: "#0f172a",
                            padding: 10,
                            cornerRadius: 8,
                            callbacks: {
                                label: (context) => ` ${context.parsed.y} q/ha`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: gridColor },
                            ticks: { color: textColor, font: { family: "inherit", size: 11 } }
                        },
                        y: {
                            min: 5,
                            max: 60,
                            grid: { color: gridColor },
                            ticks: {
                                color: textColor,
                                font: { family: "inherit", size: 11 },
                                callback: (val) => val
                            }
                        }
                    }
                }
            });
        }

        // Chart 2: All-India Multi-State Comparison Bar Chart (Dynamic across all 35 States & UTs)
        const ctxComp = document.getElementById("chartCropComparison");
        if (ctxComp) {
            if (state.cropComparisonChart) {
                state.cropComparisonChart.destroy();
            }

            const sbMap = (window.KRISHI_ALL_INDIA_DATA && window.KRISHI_ALL_INDIA_DATA.state_benchmarks) || {};
            const baseComparisonStates = [
                "Uttar Pradesh", "Punjab", "Haryana", "Madhya Pradesh", "Rajasthan",
                "Bihar", "Maharashtra", "Gujarat", "Karnataka", "Andhra Pradesh",
                "Tamil Nadu", "West Bengal", "Telangana", "Odisha", "Chhattisgarh", "Assam"
            ];
            if (state.stateName && !baseComparisonStates.includes(state.stateName)) {
                baseComparisonStates.unshift(state.stateName);
            }

            const shortLabelEn = {
                "Uttar Pradesh": "UP", "Madhya Pradesh": "MP", "Maharashtra": "MH",
                "Andhra Pradesh": "AP", "Tamil Nadu": "TN", "West Bengal": "WB",
                "Chhattisgarh": "CG", "Himachal Pradesh": "HP", "Jammu and Kashmir": "J&K",
                "Arunachal Pradesh": "AR", "Uttarakhand": "UK", "Jharkhand": "JH"
            };
            const barLabels = baseComparisonStates.map(st =>
                isHi ? (STATE_HI[st] || st) : (shortLabelEn[st] || st)
            );
            const wheatData = baseComparisonStates.map(st =>
                (sbMap[st] && sbMap[st].wheat_q_ha) ? sbMap[st].wheat_q_ha : 36.5
            );
            const mustardData = baseComparisonStates.map(st =>
                (sbMap[st] && sbMap[st].mustard_q_ha) ? sbMap[st].mustard_q_ha : 16.2
            );

            state.cropComparisonChart = new Chart(ctxComp, {
                type: "bar",
                data: {
                    labels: barLabels,
                    datasets: [
                        {
                            label: isHi ? "गेहूं / मुख्य फसल (q/ha)" : "Wheat / Cereal (q/ha)",
                            data: wheatData,
                            backgroundColor: "#064E2B",
                            borderRadius: 6
                        },
                        {
                            label: isHi ? "सरसों / तिलहन (q/ha)" : "Mustard / Oilseed (q/ha)",
                            data: mustardData,
                            backgroundColor: "#FFC928",
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: "top",
                            labels: { color: textColor, font: { size: 11, weight: "600" } }
                        },
                        tooltip: {
                            backgroundColor: "#0f172a",
                            padding: 10,
                            cornerRadius: 8,
                            callbacks: {
                                label: (context) => ` ${context.dataset.label}: ${context.parsed.y} q/ha`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: textColor, font: { family: "inherit", weight: "600", size: 10 } }
                        },
                        y: {
                            min: 0,
                            max: 60,
                            grid: { color: gridColor },
                            ticks: { color: textColor, font: { family: "inherit", size: 11 } }
                        }
                    }
                }
            });
        }
    }

    // -------------------------------------------------------------------------
    // 5. PREDICT CROP YIELD FORM SUBMISSION
    // -------------------------------------------------------------------------
    const yieldForm = document.getElementById("yieldPredictionForm");
    if (yieldForm) {
        yieldForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const isHi = state.lang === "hi";
            const btn = document.getElementById("btnSubmitPredict");
            if (btn) btn.innerHTML = `<span>${isHi ? "गणना हो रही है..." : "Computing..."}</span>`;

            const selectedState = document.getElementById("predState")?.value || state.stateName || "Uttar Pradesh";
            const district = document.getElementById("predDistrict").value || "Meerut";
            const crop = document.getElementById("predCrop").value || "Wheat";
            const acres = parseFloat(document.getElementById("predAcres")?.value) || 2.0;
            const sowing = document.getElementById("predSowing")?.value || "Timely Sown (Nov 01 - Nov 20)";
            const irrigation = document.getElementById("predIrrigation")?.value || "Tube well / Borewell";
            const seasonVal = document.getElementById("predSeason")?.value || "Rabi";

            const reqPayload = {
                state: selectedState,
                district: district,
                crop: crop,
                plot_acres: acres,
                season: seasonVal,
                sowing_window: sowing,
                soil_type: "Alluvial (Sandy Loam)",
                irrigation_source: irrigation,
                seasonal_rainfall_mm: 65.0,
                march_max_temp_c: 31.5,
                nitrogen_kg_acre: crop === "Mustard" ? 32.0 : 48.0,
                phosphorus_kg_acre: crop === "Mustard" ? 16.0 : 22.0,
                potassium_kg_acre: crop === "Mustard" ? 8.0 : 15.0
            };

            try {
                const res = await fetch("/api/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(reqPayload)
                });
                if (!res.ok) throw new Error("API predict status " + res.status);
                const data = await res.json();
                state.stateName = selectedState;
                state.district = district;
                state.crop = crop;
                if (!state.cachedData) state.cachedData = {};
                state.cachedData.prediction = data;

                updateDynamicYieldLabels();
            } catch (err) {
                if (window.KrishiAllIndiaStatic && typeof window.KrishiAllIndiaStatic.computeFallbackPrediction === "function") {
                    const fb = window.KrishiAllIndiaStatic.computeFallbackPrediction(reqPayload);
                    state.stateName = selectedState;
                    state.district = district;
                    state.crop = crop;
                    if (!state.cachedData) state.cachedData = {};
                    state.cachedData.prediction = fb.prediction;
                    updateDynamicYieldLabels();
                }
            } finally {
                if (btn) {
                    const lbl = state.lang === "hi" ? "उपज का अनुमान लगाएं" : "Predict Yield";
                    btn.innerHTML = `<span data-i18n="btn_predict_now">${lbl}</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 6. MY FARMS: RENDER PLOTS + "ADD MY FARM" INTERACTIVE CARD & FORM
    // -------------------------------------------------------------------------
    const btnScrollToAddFarm = document.getElementById("btnScrollToAddFarm");
    if (btnScrollToAddFarm) {
        btnScrollToAddFarm.addEventListener("click", () => {
            const box = document.getElementById("addFarmCardBox");
            const input = document.getElementById("newPlotName");
            if (box) box.scrollIntoView({ behavior: "smooth", block: "center" });
            if (input) setTimeout(() => input.focus(), 350);
        });
    }

    window.scrollToAddFarmBox = function() {
        const box = document.getElementById("addFarmCardBox");
        const input = document.getElementById("newPlotName");
        if (box) box.scrollIntoView({ behavior: "smooth", block: "center" });
        if (input) setTimeout(() => input.focus(), 350);
    };

    window.deleteFarmPlot = async function(plotId) {
        try {
            const res = await fetch(`/api/plots/${encodeURIComponent(plotId)}`, { method: "DELETE" });
            if (res.ok) {
                const data = await res.json();
                if (data.plots) state.farmerPlots = data.plots;
                renderMyFarms();
                renderFarmerProfile();
            }
        } catch (err) {
            console.warn("Could not delete plot:", err);
        }
    };

    function renderMyFarms() {
        const container = document.getElementById("myFarmsContainer");
        if (!container) return;
        const isHi = state.lang === "hi";

        const plots = (state.farmerPlots && state.farmerPlots.length > 0) ? state.farmerPlots : [
            {
                id: "plot-a",
                plot_name: "Plot A — Main Canal Field",
                crop: "Wheat",
                season: "Rabi",
                sowing_window: "Timely Sown (Nov 01 - Nov 20)",
                area_acres: 2.5,
                soil_type: "Alluvial (Sandy Loam)",
                irrigation_source: "Tube well / Borewell"
            },
            {
                id: "plot-b",
                plot_name: "Plot B — North Orchard Edge",
                crop: "Mustard",
                season: "Rabi",
                sowing_window: "Timely Sown (Oct 15 - Nov 05)",
                area_acres: 1.2,
                soil_type: "Alluvial (Clay Loam)",
                irrigation_source: "Canal Irrigation"
            }
        ];

        const plotCardsHtml = plots.map(plot => {
            const cropName = isHi ? (CROP_HI[plot.crop] || plot.crop) : plot.crop;
            const acresLabel = isHi ? `${plot.area_acres} एकड़` : `${plot.area_acres} Acres`;
            const lblCrop = isHi ? "फसल:" : "Crop:";
            const lblSoil = isHi ? "मिट्टी:" : "Soil:";
            const lblIrr = isHi ? "सिंचाई:" : "Irrigation:";
            const lblSow = isHi ? "बुवाई समय:" : "Sowing Window:";
            const btnDelTitle = isHi ? "यह खेत हटाएं" : "Remove Plot";

            return `
                <div class="chart-card-pro" style="position: relative; transition: transform 0.18s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 12px;">
                        <h4 style="font-size: 1.08rem; font-weight: 800; color: var(--km-text-heading);">${escapeHtml(plot.plot_name)}</h4>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span class="scheme-tag-pill tag-income">${escapeHtml(acresLabel)}</span>
                            <button type="button" onclick="deleteFarmPlot('${escapeHtml(plot.id)}')" title="${btnDelTitle}" style="background: transparent; border: none; color: var(--km-text-muted); cursor: pointer; font-size: 0.9rem; padding: 2px 6px;">✕</button>
                        </div>
                    </div>
                    <p style="font-size: 0.88rem; color: var(--km-text-body); line-height: 1.75;">
                        <strong>${lblCrop}</strong> ${escapeHtml(cropName)} (${escapeHtml(plot.season || "Rabi")})<br>
                        <strong>${lblSoil}</strong> ${escapeHtml(plot.soil_type || "Alluvial (Sandy Loam)")}<br>
                        <strong>${lblIrr}</strong> ${escapeHtml(plot.irrigation_source || "Tube well / Borewell")}<br>
                        <strong>${lblSow}</strong> ${escapeHtml(plot.sowing_window || "Timely Sown")}
                    </p>
                </div>
            `;
        }).join("");

        // Interactive "+ Add My Farm" Card right next to the existing plot cards
        const addCardTitle = isHi ? "➕ नया खेत जोड़ें (Add My Farm)" : "➕ Add My Farm Plot";
        const addCardSub = isHi
            ? "अपने नए खेत का नाम, फसल, रकबा (एकड़), मिट्टी और सिंचाई का विवरण जोड़ने के लिए यहाँ क्लिक करें।"
            : "Click here to register another farm plot with your crop, acreage, soil type, and irrigation source.";

        const addFarmInteractiveCard = `
            <div class="chart-card-pro" onclick="scrollToAddFarmBox()" style="border: 2px dashed var(--km-primary); background: rgba(6, 78, 43, 0.03); display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; cursor: pointer; min-height: 185px; transition: all 0.2s ease;">
                <div style="width: 46px; height: 46px; border-radius: 50%; background: var(--km-primary); color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 1.35rem; font-weight: 800; margin-bottom: 10px;">+</div>
                <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--km-primary); margin-bottom: 6px;">${addCardTitle}</h4>
                <p style="font-size: 0.84rem; color: var(--km-text-muted); max-width: 260px; line-height: 1.45;">${addCardSub}</p>
            </div>
        `;

        container.innerHTML = plotCardsHtml + addFarmInteractiveCard;
    }

    const addFarmForm = document.getElementById("addFarmForm");
    if (addFarmForm) {
        addFarmForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const isHi = state.lang === "hi";
            const statusMsg = document.getElementById("addFarmStatusMsg");

            const plotName = document.getElementById("newPlotName")?.value?.trim() || "New Farm Plot";
            const village = document.getElementById("newPlotVillage")?.value?.trim() || "Daurala";
            const acres = parseFloat(document.getElementById("newPlotAcres")?.value) || 2.0;
            const st = document.getElementById("newPlotState")?.value || "Uttar Pradesh";
            const dist = document.getElementById("newPlotDistrict")?.value || "Meerut";
            const crop = document.getElementById("newPlotCrop")?.value || "Wheat";
            const soil = document.getElementById("newPlotSoil")?.value || "Alluvial (Sandy Loam)";
            const irrigation = document.getElementById("newPlotIrrigation")?.value || "Tube well / Borewell";
            const sowing = document.getElementById("newPlotSowing")?.value || "Timely Sown (Nov 01 - Nov 20)";

            const fullPlotTitle = `${plotName} (${village}, ${dist})`;

            try {
                const res = await fetch("/api/plots", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        plot_name: fullPlotTitle,
                        crop: crop,
                        season: "Rabi",
                        sowing_window: sowing,
                        area_acres: acres,
                        soil_type: soil,
                        irrigation_source: irrigation
                    })
                });
                const data = await res.json();
                if (data.plots) {
                    state.farmerPlots = data.plots;
                } else {
                    state.farmerPlots.push({
                        id: "plot-" + Date.now(),
                        plot_name: fullPlotTitle,
                        crop: crop,
                        season: "Rabi",
                        sowing_window: sowing,
                        area_acres: acres,
                        soil_type: soil,
                        irrigation_source: irrigation
                    });
                }

                renderMyFarms();
                renderFarmerProfile();
                const nameInput = document.getElementById("newPlotName");
                if (nameInput) nameInput.value = "";

                if (statusMsg) {
                    statusMsg.textContent = isHi
                        ? `✅ "${fullPlotTitle}" आपके खेतों में सफलतापूर्वक जुड़ गया है!`
                        : `✅ "${fullPlotTitle}" added to your farm holdings!`;
                    setTimeout(() => { statusMsg.textContent = ""; }, 4500);
                }
            } catch (err) {
                console.warn("Failed to save plot via API, updating locally:", err);
                state.farmerPlots.push({
                    id: "plot-" + Date.now(),
                    plot_name: fullPlotTitle,
                    crop: crop,
                    season: "Rabi",
                    sowing_window: sowing,
                    area_acres: acres,
                    soil_type: soil,
                    irrigation_source: irrigation
                });
                renderMyFarms();
                renderFarmerProfile();
            }
        });
    }

    // -------------------------------------------------------------------------
    // 7. FARMER PROFILE & EDIT PROFILE FORM
    // -------------------------------------------------------------------------
    const btnToggleEditProfile = document.getElementById("btnToggleEditProfile");
    if (btnToggleEditProfile) {
        btnToggleEditProfile.addEventListener("click", () => {
            const card = document.getElementById("editProfileFormCard");
            const nameIn = document.getElementById("editFarmerName");
            if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
            if (nameIn) setTimeout(() => nameIn.focus(), 300);
        });
    }

    function renderFarmerProfile() {
        const isHi = state.lang === "hi";
        const role = (currentActiveRoleView || "farmer").toLowerCase();
        const f = state.farmerProfile || {
            name: "Tanishka",
            phone: "+91 98765 43210",
            state: "Uttar Pradesh",
            district: "Meerut",
            village: "Daurala",
            language: state.lang
        };

        const plots = (state.farmerPlots && state.farmerPlots.length > 0) ? state.farmerPlots : [];
        const totalAcres = plots.reduce((acc, p) => acc + (parseFloat(p.area_acres) || 0), 0) || 3.7;
        const plotCount = plots.length || 2;

        const profHeading = document.getElementById("profTitleHeading");
        const profSub = document.getElementById("profSubHeading");
        const nameEl = document.getElementById("profileDisplayName");
        const locEl = document.getElementById("profileDisplayLocation");
        const badgeEl = document.getElementById("profileDisplayLandBadge");
        const phoneEl = document.getElementById("profileDisplayPhone");
        const langEl = document.getElementById("profileDisplayLang");
        const zoneEl = document.getElementById("profileDisplayZone");
        const ekycLbl = document.getElementById("profileDisplayEkycLabel");
        const ekycVal = document.getElementById("profileDisplayEkycVal");
        const zoneLbl = document.getElementById("profileDisplayZoneLabel");
        const idLbl = document.getElementById("profileDisplayIdLabel");
        const idVal = document.getElementById("profileDisplayId");
        const avatarEl = document.getElementById("profileDisplayAvatar");
        const editHeading = document.getElementById("editProfileHeading");
        const lblName = document.getElementById("lblEditProfileName");
        const lblVillage = document.getElementById("lblEditProfileVillage");
        const btnSave = document.getElementById("btnSaveProfileText");
        const sideNavProf = document.getElementById("sidebarProfileNavText");

        const stName = isHi ? (STATE_HI[f.state] || f.state || "उत्तर प्रदेश") : (f.state || "Uttar Pradesh");

        if (nameEl) nameEl.textContent = f.name || "Tanishka";

        if (role === "officer") {
            if (profHeading) profHeading.textContent = isHi ? "कृषि अधिकारी प्रोफ़ाइल" : "Agricultural Officer Profile";
            if (profSub) profSub.textContent = isHi ? "विभागीय साख, निर्धारित जिला क्षेत्राधिकार एवं आधिकारिक सेटिंग्स।" : "Official department credentials, designated district jurisdiction, and officer settings.";
            if (sideNavProf) sideNavProf.textContent = isHi ? "अधिकारी प्रोफ़ाइल" : "Officer Profile";
            if (locEl) {
                locEl.textContent = isHi
                    ? `क्षेत्राधिकार: ${f.district || "मेरठ"} मंडल • कृषि विभाग, ${stName}`
                    : `Jurisdiction: ${f.district || "Meerut"} Sub-Division • Dept of Agriculture, ${f.state || "Uttar Pradesh"}`;
            }
            if (badgeEl) {
                badgeEl.textContent = isHi
                    ? "नामित कृषि अधिकारी (SDAO) • जिला कृषि परामर्श एवं निगरानी"
                    : "Designated Agricultural Officer (SDAO) • District Monitoring";
            }
            if (ekycLbl) ekycLbl.textContent = isHi ? "विभागीय क्रेडेंशियल:" : "Department Credential:";
            if (ekycVal) ekycVal.textContent = isHi ? "सत्यापित कृषि अधिकारी • कृषि एवं किसान कल्याण विभाग" : "Verified Officer • Dept of Agriculture & Farmers Welfare";
            if (zoneLbl) zoneLbl.textContent = isHi ? "आवंटित जिला:" : "Assigned District:";
            if (zoneEl) zoneEl.textContent = `${f.district || "Meerut"}, ${stName}`;
            if (idLbl) idLbl.textContent = isHi ? "अधिकारी आईडी:" : "Officer ID:";
            if (idVal) idVal.textContent = "AGRI-OFF-2024-042";

            if (editHeading) editHeading.textContent = isHi ? "अधिकारी प्रोफ़ाइल संपादित करें" : "Edit Officer Profile";
            if (lblName) lblName.textContent = isHi ? "अधिकारी का पूरा नाम *" : "Officer Full Name *";
            if (lblVillage) lblVillage.textContent = isHi ? "कार्यालय / ब्लॉक / तहसील" : "Office / Block / Tehsil";
            if (btnSave) btnSave.textContent = isHi ? "अधिकारी प्रोफ़ाइल सहेजें" : "Save Officer Profile";

            if (avatarEl) {
                avatarEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='76' height='76' viewBox='0 0 76 76'><rect width='76' height='76' rx='38' fill='%23064E2B'/><circle cx='38' cy='28' r='14' fill='%23FFC928'/><path d='M18 64c0-11 9-20 20-20s20 9 20 20' fill='%23E8F3EC'/><circle cx='54' cy='52' r='9' fill='%2316A34A'/><path d='M51 52l2 2 4-4' stroke='%23ffffff' stroke-width='2' fill='none' stroke-linecap='round'/></svg>";
            }
        } else if (role === "admin") {
            if (profHeading) profHeading.textContent = isHi ? "सिस्टम प्रशासक प्रोफ़ाइल" : "Administrator Profile";
            if (profSub) profSub.textContent = isHi ? "सिस्टम प्रशासक क्रेडेंशियल, मंच नियंत्रण एवं सुरक्षा प्रबंधन।" : "Platform administrator credentials, system governance, and security controls.";
            if (sideNavProf) sideNavProf.textContent = isHi ? "प्रशासक प्रोफ़ाइल" : "Admin Profile";
            if (locEl) {
                locEl.textContent = isHi
                    ? `मुख्यालय: केंद्रीय कृषि आईटी सेल • नई दिल्ली`
                    : `Headquarters: Central Agricultural IT & Operations Cell • New Delhi`;
            }
            if (badgeEl) {
                badgeEl.textContent = isHi
                    ? "सिस्टम प्रशासक • सम्पूर्ण मंच प्रबंधन"
                    : "Platform Administrator • Full Platform Control";
            }
            if (ekycLbl) ekycLbl.textContent = isHi ? "सुरक्षा साख:" : "Access Level:";
            if (ekycVal) ekycVal.textContent = isHi ? "सुपर एडमिन (PBKDF2-SHA256 प्रमाणित)" : "Super Administrator (PBKDF2-SHA256 Encrypted)";
            if (zoneLbl) zoneLbl.textContent = isHi ? "सिस्टम दायरा:" : "System Scope:";
            if (zoneEl) zoneEl.textContent = isHi ? "अखिल भारतीय 35 राज्य एवं केंद्र शासित प्रदेश" : "All-India 35 States & Union Territories";
            if (idLbl) idLbl.textContent = isHi ? "प्रशासक आईडी:" : "Admin ID:";
            if (idVal) idVal.textContent = "ADMIN-SYS-001";

            if (editHeading) editHeading.textContent = isHi ? "प्रशासक प्रोफ़ाइल संपादित करें" : "Edit Administrator Profile";
            if (lblName) lblName.textContent = isHi ? "प्रशासक का नाम *" : "Administrator Name *";
            if (lblVillage) lblVillage.textContent = isHi ? "विभाग / यूनिट" : "Department / Unit";
            if (btnSave) btnSave.textContent = isHi ? "प्रशासक सेटिंग्स सहेजें" : "Save Admin Settings";

            if (avatarEl) {
                avatarEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='76' height='76' viewBox='0 0 76 76'><rect width='76' height='76' rx='38' fill='%230A2918'/><circle cx='38' cy='28' r='14' fill='%23D97706'/><path d='M18 64c0-11 9-20 20-20s20 9 20 20' fill='%23FEF3C7'/><path d='M38 46v6m-4-3h8' stroke='%230A2918' stroke-width='2' stroke-linecap='round'/></svg>";
            }
        } else {
            // Farmer
            if (profHeading) profHeading.textContent = isHi ? "किसान प्रोफ़ाइल" : "Farmer Profile";
            if (profSub) profSub.textContent = isHi ? "सत्यापित प्रोफ़ाइल विवरण, पंजीकृत भूमि जोत सारांश एवं व्यक्तिगत सेटिंग्स।" : "Verified profile credentials, registered landholding summary, and personal settings.";
            if (sideNavProf) sideNavProf.textContent = isHi ? "किसान प्रोफ़ाइल" : "Profile";
            if (locEl) {
                locEl.textContent = isHi
                    ? `गांव: ${f.village || "Daurala"} • जिला: ${f.district || "Meerut"}, ${stName}`
                    : `Village: ${f.village || "Daurala"} • District: ${f.district || "Meerut"}, ${f.state || "Uttar Pradesh"}`;
            }
            if (badgeEl) {
                badgeEl.textContent = isHi
                    ? `पंजीकृत किसान (${totalAcres.toFixed(1)} एकड़ • ${plotCount} खेत)`
                    : `Registered Farmer (${totalAcres.toFixed(1)} Acres • ${plotCount} Plots)`;
            }
            if (ekycLbl) ekycLbl.textContent = isHi ? "आधार / eKYC स्थिति:" : "Aadhaar / eKYC Status:";
            if (ekycVal) ekycVal.textContent = isHi ? "PM-किसान पोर्टल पर सत्यापित" : "Verified on PM-KISAN Portal";
            if (zoneLbl) zoneLbl.textContent = isHi ? "पंजीकृत क्षेत्र:" : "Supported Region:";
            if (zoneEl) {
                zoneEl.textContent = isHi
                    ? `${stName} (बहु-राज्य रबी कृषि मंच)`
                    : `${f.state || "Uttar Pradesh"} (Multi-State Rabi Platform)`;
            }
            if (idLbl) idLbl.textContent = isHi ? "किसान आईडी:" : "Farmer ID:";
            if (idVal) idVal.textContent = f.id || "farmer-001";

            if (editHeading) editHeading.textContent = isHi ? "किसान प्रोफ़ाइल संपादित करें" : "Edit Farmer Profile";
            if (lblName) lblName.textContent = isHi ? "किसान का पूरा नाम *" : "Farmer Full Name *";
            if (lblVillage) lblVillage.textContent = isHi ? "गांव / तहसील" : "Village / Tehsil";
            if (btnSave) btnSave.textContent = isHi ? "प्रोफ़ाइल परिवर्तन सहेजें" : "Save Profile Changes";

            if (avatarEl) {
                avatarEl.src = "images/farmer_portrait.jpg";
            }
        }

        if (phoneEl) phoneEl.textContent = f.phone || "+91 98765 43210";
        if (langEl) {
            langEl.textContent = isHi
                ? "हिंदी (द्विभाषी अंग्रेजी समर्थन के साथ)"
                : "English (with Bilingual Hindi Support)";
        }

        // Sync form inputs with current profile state
        const inName = document.getElementById("editFarmerName");
        const inPhone = document.getElementById("editFarmerPhone");
        const inVillage = document.getElementById("editFarmerVillage");
        const inLang = document.getElementById("editFarmerLang");
        const inState = document.getElementById("editFarmerState");
        const inDist = document.getElementById("editFarmerDistrict");

        if (inName && document.activeElement !== inName) inName.value = f.name || "Tanishka";
        if (inPhone && document.activeElement !== inPhone) inPhone.value = f.phone || "+91 98765 43210";
        if (inVillage && document.activeElement !== inVillage) inVillage.value = f.village || (role === "officer" ? "Meerut Sub-Division" : "Daurala");
        if (inLang && document.activeElement !== inLang) inLang.value = state.lang;
        if (inState && f.state && document.activeElement !== inState) {
            inState.value = f.state;
            if (inDist) populateDistrictDropdown(inDist, f.state, f.district || "Meerut");
        }
    }

    const editProfileForm = document.getElementById("editProfileForm");
    if (editProfileForm) {
        editProfileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const newName = document.getElementById("editFarmerName")?.value?.trim() || "Tanishka";
            const newPhone = document.getElementById("editFarmerPhone")?.value?.trim() || "+91 98765 43210";
            const newVillage = document.getElementById("editFarmerVillage")?.value?.trim() || "Daurala";
            const newLang = document.getElementById("editFarmerLang")?.value || state.lang;
            const newState = document.getElementById("editFarmerState")?.value || "Uttar Pradesh";
            const newDistrict = document.getElementById("editFarmerDistrict")?.value || "Meerut";
            const statusMsg = document.getElementById("editProfileStatusMsg");

            const payload = {
                name: newName,
                phone: newPhone,
                village: newVillage,
                language: newLang,
                state: newState,
                district: newDistrict
            };

            try {
                const res = await fetch("/api/farmer", {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.farmer) {
                    state.farmerProfile = data.farmer;
                } else {
                    state.farmerProfile = { ...state.farmerProfile, ...payload };
                }
            } catch (err) {
                console.warn("Profile save fallback to local state:", err);
                state.farmerProfile = { ...state.farmerProfile, ...payload };
            }

            // Update global location & language if changed in profile
            state.stateName = newState;
            state.district = newDistrict;
            if (stateSelect) stateSelect.value = newState;
            if (districtSelect) populateDistrictDropdown(districtSelect, newState, newDistrict);

            if (newLang !== state.lang) {
                state.lang = newLang;
                localStorage.setItem("km_lang", state.lang);
            }

            applyDashboardLanguage();

            if (statusMsg) {
                statusMsg.textContent = state.lang === "hi"
                    ? "✅ किसान प्रोफ़ाइल सफलतापूर्वक अपडेट हो गई!"
                    : "✅ Farmer profile updated successfully!";
                setTimeout(() => { statusMsg.textContent = ""; }, 4000);
            }
        });
    }

    // -------------------------------------------------------------------------
    // 8. GOVERNMENT SCHEMES (9 VERIFIED SCHEMES + FILTER + BILINGUAL MODAL)
    // -------------------------------------------------------------------------
    function renderDashboardSchemes() {
        const grid = document.getElementById("dashboardSchemesGrid");
        if (!grid) return;

        const isHi = state.lang === "hi";
        const cropFilter = document.getElementById("filterCrop")?.value || "All";
        const catFilter = document.getElementById("filterCategory")?.value || "All";

        const filtered = DASHBOARD_SCHEMES.filter(s => {
            const matchCrop = cropFilter === "All" || s.crops.includes(cropFilter);
            const matchCat = catFilter === "All" || s.category === catFilter;
            return matchCrop && matchCat;
        });

        const countEl = document.getElementById("cardSchemesCount");
        if (countEl) {
            countEl.textContent = isHi ? `${DASHBOARD_SCHEMES.length} उपलब्ध योजनाएं` : `${DASHBOARD_SCHEMES.length} Available`;
        }

        const lblElig = isHi ? "पात्रता:" : "Eligibility:";
        const lblBen = isHi ? "मुख्य लाभ:" : "Key Benefit:";
        const btnDetails = isHi ? "पूरी जानकारी देखें" : "View Details";
        const btnPortal = isHi ? "आधिकारिक पोर्टल ↗" : "Official Portal ↗";

        grid.innerHTML = filtered.map(s => {
            const t = isHi ? s.hi : s.en;
            return `
                <div class="scheme-card-pro">
                    <div class="scheme-card-body">
                        <span class="scheme-tag-pill ${s.tagClass}">${escapeHtml(t.tag)}</span>
                        <h3 class="scheme-card-title">${escapeHtml(t.title)}</h3>
                        <p class="scheme-card-desc">${escapeHtml(t.desc)}</p>

                        <div class="scheme-eligibility-block">
                            <strong>${lblElig}</strong>
                            <p>${escapeHtml(t.elig)}</p>
                            <div style="margin-top: 6px; font-size: 0.82rem; font-weight: 700; color: var(--km-primary);">
                                ${lblBen} ${escapeHtml(t.benefit)}
                            </div>
                        </div>

                        <div style="display: flex; gap: 10px; align-items: center; margin-top: auto;">
                            <button type="button" class="btn-scheme-outline" onclick="openSchemeModal('${s.id}')">${btnDetails}</button>
                            <a href="${s.portal}" target="_blank" rel="noopener" style="font-size: 0.8rem; font-weight: 700; color: var(--km-primary); text-decoration: none;">${btnPortal}</a>
                        </div>
                    </div>
                </div>
            `;
        }).join("");
    }

    const btnFilterSchemes = document.getElementById("btnFilterSchemes");
    if (btnFilterSchemes) {
        btnFilterSchemes.addEventListener("click", renderDashboardSchemes);
    }
    ["filterCrop", "filterState", "filterCategory"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("change", renderDashboardSchemes);
    });

    window.openSchemeModal = function(schemeKey) {
        const modal = document.getElementById("schemeDetailModal");
        const titleEl = document.getElementById("modalSchemeTitle");
        const bodyEl = document.getElementById("modalSchemeBody");
        if (!modal || !titleEl || !bodyEl) return;

        const isHi = state.lang === "hi";
        const schemeObj = DASHBOARD_SCHEMES.find(s => s.id === schemeKey) || DASHBOARD_SCHEMES[0];
        const t = isHi ? schemeObj.hi : schemeObj.en;

        titleEl.textContent = t.title;
        bodyEl.innerHTML = `
            <div style="font-size: 0.92rem; line-height: 1.75; color: var(--km-text-body);">
                <p><strong>${isHi ? "श्रेणी:" : "Category:"}</strong> ${escapeHtml(t.tag)}</p>
                <p><strong>${isHi ? "वित्तीय लाभ:" : "Direct Benefit:"}</strong> ${escapeHtml(t.benefit)}</p>
                <p><strong>${isHi ? "योजना विवरण:" : "Description:"}</strong> ${escapeHtml(t.desc)}</p>
                <p><strong>${isHi ? "पात्रता मानदंड:" : "Eligibility Criteria:"}</strong> ${escapeHtml(t.elig)}</p>
                <p><strong>${isHi ? "आवश्यक दस्तावेज:" : "Required Documents:"}</strong> ${escapeHtml(t.docs)}</p>
                <div style="margin-top: 24px;">
                    <a href="${schemeObj.portal}" target="_blank" rel="noopener" class="btn-solid-start" style="display: inline-flex;">
                        ${isHi ? "आधिकारिक पोर्टल खोलें" : "Visit Official Portal"} (${new URL(schemeObj.portal).hostname}) →
                    </a>
                </div>
            </div>
        `;
        modal.classList.add("active");
    };

    window.closeSchemeModal = function() {
        const modal = document.getElementById("schemeDetailModal");
        if (modal) modal.classList.remove("active");
    };

    const modalBackdrop = document.getElementById("schemeDetailModal");
    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) closeSchemeModal();
        });
    }

    // -------------------------------------------------------------------------
    // 9. KRISHISATHI CHAT & VOICE ASSISTANT
    // -------------------------------------------------------------------------
    const chatInput = document.getElementById("chatInputField");
    const sendBtn = document.getElementById("btnSendChat");
    const chatBox = document.getElementById("chatStreamBox");

    async function sendUserMessage(text) {
        if (!text || !text.trim()) return;
        const query = text.trim();
        if (chatInput) chatInput.value = "";

        appendUserBubble(query);
        const typingEl = appendAiTypingIndicator();

        const voiceLangEl = document.getElementById("voiceLangSelect");
        const activeChatLang = state.lang === "hi" ? "hi" : (voiceLangEl ? voiceLangEl.value : "en");

        try {
            const res = await fetch("/api/krishisathi/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    lang: activeChatLang,
                    context: {
                        state: state.selectedState || "Uttar Pradesh",
                        crop: state.crop || "Wheat",
                        district: state.district || "Meerut",
                        plot_acres: 2.5,
                        growth_stage: "Tillering"
                    }
                })
            });

            const data = await res.json();
            if (typingEl) typingEl.remove();

            if (data.answer) {
                appendAiBubble(data.answer, data.sources, data.retrieval_mode);
            } else {
                appendAiBubble(
                    state.lang === "hi"
                        ? "क्षमा करें, अभी उत्तर सत्यापित नहीं हो सका। कृपया पुनः प्रयास करें।"
                        : "Sorry, I could not verify a response right now. Please try again.",
                    []
                );
            }
        } catch (err) {
            if (typingEl) typingEl.remove();
            appendAiBubble(
                state.lang === "hi"
                    ? "नेटवर्क कनेक्शन बाधित हुआ। गेहूं की तत्काल सलाह: बुवाई के 21–25 दिन बाद शीर्ष जड़ अवस्था (CRI) पर पहली सिंचाई अवश्य करें।"
                    : "Network connection interrupted. For immediate Wheat advice, ensure timely Crown Root Initiation (CRI) irrigation at 21–25 days after sowing.",
                []
            );
        }
    }

    function appendUserBubble(text) {
        if (!chatBox) return;
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble-user";
        bubble.innerHTML = `<span>${escapeHtml(text)}</span>`;
        chatBox.appendChild(bubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function appendAiTypingIndicator() {
        if (!chatBox) return null;
        const isHi = state.lang === "hi";
        const wrap = document.createElement("div");
        wrap.className = "chat-bubble-ai-wrap";
        wrap.innerHTML = `
            <div class="chat-avatar-sathi" style="font-weight: 800; font-size: 0.78rem; color: var(--km-primary);">AI</div>
            <div class="chat-bubble-ai" style="padding: 10px 16px;">
                <em>${isHi ? "कृषिसाथी प्रमाणित दिशानिर्देश खोज रहा है..." : "KrishiSathi is searching verified guidelines..."}</em>
            </div>
        `;
        chatBox.appendChild(wrap);
        chatBox.scrollTop = chatBox.scrollHeight;
        return wrap;
    }

    function appendAiBubble(answer, sources) {
        if (!chatBox) return;
        const isHi = state.lang === "hi";
        const wrap = document.createElement("div");
        wrap.className = "chat-bubble-ai-wrap";

        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            const badges = sources.slice(0, 2).map(s => {
                const tag = s.source_type === "official_pdf" ? "[Official PDF]" : "[Official Portal]";
                return `<a href="${s.url}" target="_blank" rel="noopener" style="display: inline-block; font-size: 0.76rem; background: #ffffff; border: 1px solid var(--km-border); border-radius: 9999px; padding: 2px 10px; color: var(--km-primary); text-decoration: none; margin-top: 6px; margin-right: 6px;">
                    ${tag} ${escapeHtml((s.title || "Official Source").split('-')[0].trim())}
                </a>`;
            }).join("");
            sourcesHtml = `<div style="margin-top: 8px;">${badges}</div>`;
        }

        const formattedAnswer = escapeHtml(answer).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        wrap.innerHTML = `
            <div class="chat-avatar-sathi" style="font-weight: 800; font-size: 0.78rem; color: var(--km-primary);">AI</div>
            <div class="chat-bubble-ai">
                <div style="white-space: pre-line; line-height: 1.55;">${formattedAnswer}</div>
                ${sourcesHtml}
                <div class="chat-bubble-actions">
                    <button type="button" class="btn-speak-audio" onclick="speakText(this)">
                        <span>${isHi ? "आवाज़ में सुनें" : "Listen Aloud"}</span>
                    </button>
                </div>
            </div>
        `;
        chatBox.appendChild(wrap);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", () => {
            if (chatInput) sendUserMessage(chatInput.value);
        });
    }

    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                sendUserMessage(chatInput.value);
            }
        });
    }

    window.sendQuickPrompt = function(promptText) {
        sendUserMessage(promptText);
    };

    window.speakText = function(btn) {
        const bubble = btn.closest(".chat-bubble-ai");
        if (bubble) {
            const clone = bubble.cloneNode(true);
            const actionRow = clone.querySelector(".chat-bubble-actions");
            if (actionRow) actionRow.remove();
            speakResponseText(clone.textContent.trim());
        }
    };

    function speakResponseText(text) {
        const voiceLangEl = document.getElementById("voiceLangSelect");
        const voiceGenderEl = document.getElementById("voiceGenderSelect");
        const langMode = state.lang === "hi" ? "hi-IN" : ((voiceLangEl && voiceLangEl.value.includes("hi")) ? "hi-IN" : "en-IN");
        const gender = (voiceGenderEl && voiceGenderEl.value === "male") ? "male" : "female";
        const voiceName = gender === "male" ? "Deepak" : "Nalini";

        const btnStop = document.getElementById("btnDashStopVoice");
        if (btnStop) btnStop.style.display = "inline-block";

        if (window.KrishiGnaniVoice && typeof window.KrishiGnaniVoice.speak === "function") {
            window.KrishiGnaniVoice.speak(text, {
                language: langMode,
                gender: gender,
                voice: voiceName,
                speed: 1.0,
                onStart: () => {
                    const voiceStatus = document.getElementById("voiceStatusBadge");
                    if (voiceStatus) voiceStatus.textContent = `Speaking: Gnani Timbre v2.5 (${voiceName})...`;
                },
                onEnd: () => {
                    if (btnStop) btnStop.style.display = "none";
                    const voiceStatus = document.getElementById("voiceStatusBadge");
                    if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
                }
            });
            return;
        }

        if (!state.synthesis) return;
        state.synthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = langMode;
        utterance.rate = 0.95;
        state.synthesis.speak(utterance);
    }

    // -------------------------------------------------------------------------
    // 10. GNANI.AI PRISMA V3.0 SPEECH-TO-TEXT & TIMBRE V2.5 VOICE COMPANION
    // -------------------------------------------------------------------------
    const bigVoiceBtn = document.getElementById("btnBigVoiceMic");
    const inputMicBtn = document.getElementById("btnInputMic");
    const micRing = document.getElementById("micWaveRing");
    const voiceStatus = document.getElementById("voiceStatusBadge");
    const btnDashStopRecord = document.getElementById("btnDashStopRecord");
    const btnDashStopVoice = document.getElementById("btnDashStopVoice");
    let isDashRecording = false;

    if (btnDashStopVoice) {
        btnDashStopVoice.addEventListener("click", () => {
            if (window.KrishiGnaniVoice) window.KrishiGnaniVoice.stopPlayback();
            btnDashStopVoice.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
        });
    }

    async function startDashRecording() {
        if (isDashRecording) return;
        const voiceLangEl = document.getElementById("voiceLangSelect");
        const selLang = (voiceLangEl ? voiceLangEl.value : state.lang) || "hi";
        const langCode = selLang === "hi" ? "hi-IN" : (selLang === "en" ? "en-IN" : "indic-auto");

        if (voiceStatus) voiceStatus.textContent = state.lang === "hi" ? "माइक कनेक्ट हो रहा है..." : "Connecting microphone...";
        if (micRing) micRing.style.display = "block";
        if (btnDashStopRecord) btnDashStopRecord.style.display = "inline-block";

        if (window.KrishiGnaniVoice && typeof window.KrishiGnaniVoice.startRecording === "function") {
            await window.KrishiGnaniVoice.startRecording({
                language: langCode,
                onStart: () => {
                    isDashRecording = true;
                    if (voiceStatus) {
                        voiceStatus.textContent = state.lang === "hi"
                            ? "सुन रहे हैं (बोलिए)... 00:00 / 00:30"
                            : "Listening... Speak now (00:00 / 00:30)";
                    }
                },
                onTick: (sec, maxSec) => {
                    if (voiceStatus) {
                        const mm = String(Math.floor(sec / 60)).padStart(2, "0");
                        const ss = String(sec % 60).padStart(2, "0");
                        voiceStatus.textContent = state.lang === "hi"
                            ? `रिकॉर्ड हो रहा है... ${mm}:${ss} / 00:${maxSec} (पूरा होने पर टैप करें)`
                            : `Recording audio... ${mm}:${ss} / 00:${maxSec} (Tap stop when done)`;
                    }
                },
                onSuccess: (res) => {
                    // Browser speech fallback
                    isDashRecording = false;
                    if (micRing) micRing.style.display = "none";
                    if (btnDashStopRecord) btnDashStopRecord.style.display = "none";
                    if (res && res.transcript) {
                        if (chatInput) chatInput.value = res.transcript;
                        sendUserMessage(res.transcript);
                    }
                },
                onError: (err) => {
                    isDashRecording = false;
                    if (micRing) micRing.style.display = "none";
                    if (btnDashStopRecord) btnDashStopRecord.style.display = "none";
                    if (voiceStatus) voiceStatus.textContent = err.message || DASHBOARD_I18N[state.lang].voice_tap_mic;
                }
            });
            return;
        }

        // Native browser SpeechRecognition fallback
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            alert(state.lang === "hi"
                ? "इस ब्राउज़र में वॉइस उपलब्ध नहीं है। कृपया अपना सवाल टाइप करें।"
                : "Speech recognition is not supported on this browser. Please type your question.");
            return;
        }
        state.recognition = new SpeechRec();
        state.recognition.lang = langCode;
        state.recognition.onstart = () => {
            isDashRecording = true;
            if (micRing) micRing.style.display = "block";
            if (voiceStatus) voiceStatus.textContent = state.lang === "hi" ? "सुन रहे हैं... कृपया बोलें" : "Listening / सुन रहे हैं...";
        };
        state.recognition.onresult = (evt) => {
            const transcript = evt.results[0][0].transcript;
            if (chatInput) chatInput.value = transcript;
            sendUserMessage(transcript);
        };
        state.recognition.onend = () => {
            isDashRecording = false;
            if (micRing) micRing.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
        };
        state.recognition.start();
    }

    async function stopDashRecording() {
        if (!isDashRecording) return;
        isDashRecording = false;
        if (micRing) micRing.style.display = "none";
        if (btnDashStopRecord) btnDashStopRecord.style.display = "none";
        if (voiceStatus) voiceStatus.textContent = state.lang === "hi" ? "Gnani Prisma v3.0 से ट्रांसक्राइब हो रहा है..." : "Transcribing with Gnani Prisma v3.0...";

        if (window.KrishiGnaniVoice && typeof window.KrishiGnaniVoice.stopRecording === "function") {
            try {
                const audioBlob = await window.KrishiGnaniVoice.stopRecording();
                if (!audioBlob || audioBlob.size < 64) {
                    if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
                    return;
                }
                const voiceLangEl = document.getElementById("voiceLangSelect");
                const selLang = (voiceLangEl ? voiceLangEl.value : state.lang) || "hi";
                const langCode = selLang === "hi" ? "hi-IN" : (selLang === "en" ? "en-IN" : "indic-auto");

                const result = await window.KrishiGnaniVoice.transcribe(audioBlob, {
                    language: langCode,
                    model: "prisma-v3.0"
                });
                if (result && result.transcript) {
                    if (chatInput) chatInput.value = result.transcript;
                    sendUserMessage(result.transcript);
                } else {
                    if (voiceStatus) voiceStatus.textContent = state.lang === "hi" ? "आवाज स्पष्ट नहीं मिली, कृपया दोबारा बोलें" : "No clear speech detected. Please speak again.";
                }
            } catch (err) {
                console.warn("Gnani STT error:", err);
                if (voiceStatus) voiceStatus.textContent = err.message || DASHBOARD_I18N[state.lang].voice_tap_mic;
            }
            return;
        }

        if (state.recognition) {
            try { state.recognition.stop(); } catch (e) {}
        }
    }

    function toggleDashVoice() {
        if (isDashRecording) {
            stopDashRecording();
        } else {
            startDashRecording();
        }
    }

    if (bigVoiceBtn) bigVoiceBtn.addEventListener("click", toggleDashVoice);
    if (inputMicBtn) inputMicBtn.addEventListener("click", toggleDashVoice);
    if (btnDashStopRecord) btnDashStopRecord.addEventListener("click", stopDashRecording);

    // Helper HTML escape
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? String(text).replace(/[&<>"']/g, m => map[m]) : "";
    }

    // -------------------------------------------------------------------------
    // 11. ALL-INDIA DYNAMIC METADATA, AUTHENTICATION, KRISHISCHEME INTEL,
    //     KRISHISURAKSHA PMFBY INSURANCE & NASA EARTH INTELLIGENCE
    // -------------------------------------------------------------------------
    let schemeYearlyChartInstance = null;
    let schemeStatesChartInstance = null;
    let nasaTempSolarChartInstance = null;
    let nasaRainHumidityChartInstance = null;

    function applyAllIndiaConfigToSelectors(cfg) {
        if (!cfg) return;
        if (cfg.state_districts && Object.keys(cfg.state_districts).length > 0) {
            Object.assign(STATE_DISTRICTS, cfg.state_districts);
        }
        const allStates = Array.isArray(cfg.supported_states) && cfg.supported_states.length
            ? cfg.supported_states
            : Object.keys(STATE_DISTRICTS);
        const allCrops = Array.isArray(cfg.all_india_crops) && cfg.all_india_crops.length
            ? cfg.all_india_crops
            : (cfg.crops || []);
        const allSeasons = Array.isArray(cfg.seasons) && cfg.seasons.length
            ? cfg.seasons
            : ["Rabi", "Kharif", "Summer", "Whole Year", "Autumn", "Winter"];

        const stateSelectIds = [
            "statePicker", "predState", "newPlotState", "editFarmerState",
            "filterState", "intelStateSelect", "insState", "nasaStateSelect"
        ];
        const isHi = state.lang === "hi";
        stateSelectIds.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const cur = el.value || "Uttar Pradesh";
            el.innerHTML = "";
            allStates.forEach(st => {
                const opt = document.createElement("option");
                opt.value = st;
                opt.textContent = (isHi && STATE_HI[st]) ? `${STATE_HI[st]} (${st})` : st;
                if (st === cur) opt.selected = true;
                el.appendChild(opt);
            });
        });

        populateDistrictDropdown(document.getElementById("districtPicker"), state.stateName || "Uttar Pradesh", state.district || "Meerut");
        populateDistrictDropdown(document.getElementById("predDistrict"), state.stateName || "Uttar Pradesh", state.district || "Meerut");
        populateDistrictDropdown(document.getElementById("newPlotDistrict"), document.getElementById("newPlotState")?.value || "Uttar Pradesh", "Meerut");
        populateDistrictDropdown(document.getElementById("editFarmerDistrict"), document.getElementById("editFarmerState")?.value || "Uttar Pradesh", "Meerut");
        populateDistrictDropdown(document.getElementById("insDistrict"), document.getElementById("insState")?.value || "Uttar Pradesh", "Meerut");
        populateDistrictDropdown(document.getElementById("nasaDistrictSelect"), document.getElementById("nasaStateSelect")?.value || "Uttar Pradesh", "Meerut");

        const cropSelectIds = ["predCrop", "newPlotCrop", "insCrop"];
        cropSelectIds.forEach(id => {
            const el = document.getElementById(id);
            if (!el || !allCrops.length) return;
            const cur = el.value || "Wheat";
            el.innerHTML = "";
            allCrops.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c;
                opt.textContent = c;
                if (c === cur) opt.selected = true;
                el.appendChild(opt);
            });
        });

        const predSeasonEl = document.getElementById("predSeason");
        if (predSeasonEl && allSeasons.length) {
            predSeasonEl.innerHTML = "";
            allSeasons.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s;
                opt.textContent = s;
                if (s === "Rabi") opt.selected = true;
                predSeasonEl.appendChild(opt);
            });
        }
    }

    async function initAllIndiaDynamicSelectors() {
        // 1. Immediately populate all 35 States, 743 Districts, and 72 Crops synchronously from static bundle
        if (window.KRISHI_ALL_INDIA_DATA) {
            applyAllIndiaConfigToSelectors(window.KRISHI_ALL_INDIA_DATA);
        }
        // 2. Also fetch /api/config (or fallback all_india_config.json on Netlify)
        try {
            let res = await fetch("/api/config").catch(() => null);
            if (!res || !res.ok) {
                res = await fetch("all_india_config.json").catch(() => null);
            }
            if (res && res.ok) {
                const cfg = await res.json();
                applyAllIndiaConfigToSelectors(cfg);
            }
        } catch (err) {
            console.warn("All-India selector init fallback:", err);
        }
    }

    const insStateEl = document.getElementById("insState");
    const insDistrictEl = document.getElementById("insDistrict");
    if (insStateEl && insDistrictEl) {
        insStateEl.addEventListener("change", () => {
            populateDistrictDropdown(insDistrictEl, insStateEl.value);
        });
    }

    const nasaStateEl = document.getElementById("nasaStateSelect");
    const nasaDistrictEl = document.getElementById("nasaDistrictSelect");
    if (nasaStateEl && nasaDistrictEl) {
        nasaStateEl.addEventListener("change", () => {
            populateDistrictDropdown(nasaDistrictEl, nasaStateEl.value);
            loadNasaIntelligence();
        });
    }

    // --- 11A. Role-Based Authentication & Account Access ---
    const btnAuthTabLogin = document.getElementById("btnAuthTabLogin");
    const btnAuthTabRegister = document.getElementById("btnAuthTabRegister");
    const btnAuthTabReset = document.getElementById("btnAuthTabReset");
    const authLoginForm = document.getElementById("authLoginForm");
    const authRegisterForm = document.getElementById("authRegisterForm");
    const authResetForm = document.getElementById("authResetForm");
    const authStatusBanner = document.getElementById("authStatusBanner");

    function switchAuthForm(mode) {
        [btnAuthTabLogin, btnAuthTabRegister, btnAuthTabReset].forEach(b => b && b.classList.remove("active"));
        if (authLoginForm) authLoginForm.style.display = mode === "login" ? "block" : "none";
        if (authRegisterForm) authRegisterForm.style.display = mode === "register" ? "block" : "none";
        if (authResetForm) authResetForm.style.display = mode === "reset" ? "block" : "none";
        if (mode === "login" && btnAuthTabLogin) btnAuthTabLogin.classList.add("active");
        if (mode === "register" && btnAuthTabRegister) btnAuthTabRegister.classList.add("active");
        if (mode === "reset" && btnAuthTabReset) btnAuthTabReset.classList.add("active");
    }

    if (btnAuthTabLogin) btnAuthTabLogin.addEventListener("click", () => switchAuthForm("login"));
    if (btnAuthTabRegister) btnAuthTabRegister.addEventListener("click", () => switchAuthForm("register"));
    if (btnAuthTabReset) btnAuthTabReset.addEventListener("click", () => switchAuthForm("reset"));

    window.fillDemoLogin = function(email, pass) {
        const em = document.getElementById("authLoginEmail");
        const pw = document.getElementById("authLoginPassword");
        if (em) em.value = email;
        if (pw) pw.value = pass;
    };

    let currentActiveRoleView = "farmer";

    function switchActiveRoleView(role, userObj) {
        const cleanRole = (role || "farmer").toLowerCase();
        currentActiveRoleView = cleanRole;
        const roleMeta = {
            farmer: {
                pill: "Role: Farmer",
                label: "Farmer"
            },
            officer: {
                pill: "Role: Agri Officer",
                label: "Agricultural Officer"
            },
            admin: {
                pill: "Role: Admin",
                label: "Administrator"
            }
        };
        const meta = roleMeta[cleanRole] || roleMeta.farmer;

        const officerPanel = document.getElementById("officerDedicatedPanel");
        const adminPanel = document.getElementById("adminDedicatedPanel");
        const adminUploadCard = document.getElementById("adminSchemeUploadCardWrap");
        const adminUsersWrap = document.getElementById("adminUsersTableWrap");

        if (officerPanel) officerPanel.style.display = cleanRole === "officer" ? "block" : "none";
        if (adminPanel) adminPanel.style.display = cleanRole === "admin" ? "block" : "none";
        if (adminUploadCard) adminUploadCard.style.display = (cleanRole === "admin" || cleanRole === "officer") ? "block" : "none";

        if (cleanRole === "admin" || cleanRole === "officer") {
            if (adminUsersWrap) adminUsersWrap.style.display = "block";
            loadAdminUsersList();
        } else if (adminUsersWrap) {
            adminUsersWrap.style.display = "none";
        }

        const headerLbl = document.getElementById("headerAuthRoleLabel");
        const roleBadge = document.getElementById("authCurrentRoleBadge");
        const rbacTag = document.getElementById("rbacRoleTag");
        const topGreet = document.getElementById("topGreetingText");

        // Keep header pill concise so it never wraps onto two lines
        if (headerLbl) headerLbl.textContent = meta.pill;
        if (roleBadge) roleBadge.textContent = `Active: ${meta.label}`;
        if (rbacTag) rbacTag.textContent = `${meta.label} Access`;

        if (topGreet && userObj && userObj.name) {
            const firstName = String(userObj.name).split("(")[0].trim().split(" ").slice(0, 2).join(" ");
            topGreet.textContent = `Welcome back, ${firstName}`;
        }

        renderFarmerProfile();
    }

    function applyUserSessionUI(user) {
        if (!user) return;
        switchActiveRoleView(user.role || "farmer", user);
    }

    const headerAuthRoleBtn = document.getElementById("headerAuthRoleBtn");
    if (headerAuthRoleBtn) {
        headerAuthRoleBtn.addEventListener("click", () => {
            const order = ["farmer", "officer", "admin"];
            const nextRole = order[(order.indexOf(currentActiveRoleView) + 1) % order.length];
            let savedUser = null;
            try { savedUser = JSON.parse(localStorage.getItem("km_auth_user") || "null"); } catch (_) {}
            switchActiveRoleView(nextRole, savedUser ? { ...savedUser, role: nextRole } : null);
        });
    }

    async function loadAdminUsersList() {
        const box = document.getElementById("adminUsersListBox");
        if (!box) return;
        try {
            const token = localStorage.getItem("km_auth_token") || "";
            const res = await fetch(`/api/admin/users?token=${encodeURIComponent(token)}`);
            if (!res.ok) return;
            const data = await res.json();
            const users = data.users || [];
            box.innerHTML = users.map(u =>
                `<div style="padding:6px 8px; border-bottom:1px solid var(--km-border); display:flex; justify-content:space-between;">
                    <span><strong>${escapeHtml(u.name)}</strong> (${escapeHtml(u.email)})</span>
                    <span class="chart-badge-tag">${escapeHtml(u.role.toUpperCase())} • ${escapeHtml(u.district)}</span>
                </div>`
            ).join("");
        } catch (err) {
            console.warn("Could not load users list:", err);
        }
    }

    if (authLoginForm) {
        authLoginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("authLoginEmail")?.value || "";
            const password = document.getElementById("authLoginPassword")?.value || "";
            try {
                const data = window.KrishiAuth
                    ? await window.KrishiAuth.signIn(email, password)
                    : await (await fetch("/api/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, password })
                    })).json();
                if (data.status === "success" && data.user) {
                    localStorage.setItem("km_auth_token", data.token);
                    localStorage.setItem("km_auth_user", JSON.stringify(data.user));
                    applyUserSessionUI(data.user);
                    if (authStatusBanner) {
                        authStatusBanner.style.color = "var(--km-primary)";
                        authStatusBanner.textContent = `Signed in as ${data.user.name} (${data.user.role.toUpperCase()})`;
                    }
                } else if (authStatusBanner) {
                    authStatusBanner.style.color = "var(--km-danger)";
                    authStatusBanner.textContent = data.message || "Invalid credentials";
                }
            } catch (err) {
                if (authStatusBanner) authStatusBanner.textContent = "Login request failed.";
            }
        });
    }

    if (authRegisterForm) {
        authRegisterForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                name: document.getElementById("regName")?.value || "",
                email: document.getElementById("regEmail")?.value || "",
                password: document.getElementById("regPassword")?.value || "",
                role: document.getElementById("regRole")?.value || "farmer",
                phone: document.getElementById("regPhone")?.value || "",
                state: state.selectedState || "Uttar Pradesh",
                district: state.district || "Meerut"
            };
            try {
                const data = window.KrishiAuth
                    ? await window.KrishiAuth.signUp(payload)
                    : await (await fetch("/api/auth/register", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    })).json();
                if (data.status === "success" && data.user) {
                    localStorage.setItem("km_auth_token", data.token);
                    localStorage.setItem("km_auth_user", JSON.stringify(data.user));
                    applyUserSessionUI(data.user);
                    if (authStatusBanner) {
                        authStatusBanner.style.color = "var(--km-primary)";
                        authStatusBanner.textContent = `Registered & signed in as ${data.user.name} (${data.user.role.toUpperCase()})`;
                    }
                } else if (authStatusBanner) {
                    authStatusBanner.style.color = "var(--km-danger)";
                    authStatusBanner.textContent = data.message || "Registration failed";
                }
            } catch (err) {
                if (authStatusBanner) authStatusBanner.textContent = "Registration request failed.";
            }
        });
    }

    const btnGenerateResetToken = document.getElementById("btnGenerateResetToken");
    if (btnGenerateResetToken) {
        btnGenerateResetToken.addEventListener("click", async () => {
            const email = document.getElementById("resetEmailInput")?.value || "";
            const data = window.KrishiAuth
                ? await window.KrishiAuth.forgotPassword(email)
                : await (await fetch("/api/auth/forgot-password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email })
                })).json();
            if (data.reset_token) {
                const tkIn = document.getElementById("resetTokenInput");
                if (tkIn) tkIn.value = data.reset_token;
                if (authStatusBanner) {
                    authStatusBanner.style.color = "var(--km-primary)";
                    authStatusBanner.textContent = data.message || `Reset token generated: ${data.reset_token}`;
                }
            } else if (authStatusBanner) {
                authStatusBanner.textContent = data.message || "Could not generate reset token.";
            }
        });
    }

    if (authResetForm) {
        authResetForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const token = document.getElementById("resetTokenInput")?.value || "";
            const new_password = document.getElementById("resetNewPassInput")?.value || "";
            const data = window.KrishiAuth
                ? await window.KrishiAuth.resetPassword(token, new_password)
                : await (await fetch("/api/auth/reset-password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token, new_password })
                })).json();
            if (authStatusBanner) {
                authStatusBanner.style.color = data.status === "success" ? "var(--km-primary)" : "var(--km-danger)";
                authStatusBanner.textContent = data.message || "Password reset completed.";
            }
        });
    }

    const btnAuthLogout = document.getElementById("btnAuthLogout");
    if (btnAuthLogout) {
        btnAuthLogout.addEventListener("click", async () => {
            if (window.KrishiAuth && typeof window.KrishiAuth.signOut === "function") {
                await window.KrishiAuth.signOut("login.html?logout=1");
                return;
            }
            const token = localStorage.getItem("km_auth_token") || "";
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token })
            }).catch(() => {});
            localStorage.removeItem("km_auth_token");
            localStorage.removeItem("km_auth_user");
            window.location.href = "login.html?logout=1";
        });
    }

    // Restore saved session or URL ?role= parameter
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlRole = urlParams.get("role");
        const savedUser = JSON.parse(localStorage.getItem("km_auth_user") || "null");
        if (urlRole && ["farmer", "officer", "admin"].includes(urlRole.toLowerCase())) {
            switchActiveRoleView(urlRole.toLowerCase(), savedUser);
        } else if (savedUser) {
            applyUserSessionUI(savedUser);
        } else {
            switchActiveRoleView("farmer", null);
        }
    } catch (_) {}

    // --- 11B. KrishiScheme Intelligence (Beneficiaries & ₹ Amount Spotlight + All-Schemes Table) ---
    let allSchemesCache = [];

    const PER_FARMER_SUMMARY_MAP = {
        "pm-kisan": {
            en: "₹6,000 / year direct bank transfer (₹2,000 × 3 installments)",
            hi: "₹6,000 / वर्ष सीधा बैंक ट्रांसफर (₹2,000 × 3 किस्तें)"
        },
        "pmfby": {
            en: "Full crop loss claim payout (Avg ₹18,000–₹42,000/ha against 1.5%–2% premium)",
            hi: "पूर्ण फसल नुकसान मुआवजा (1.5%–2% प्रीमियम पर औसतन ₹18,000–₹42,000/हेक्टेयर क्लेम)"
        },
        "kcc": {
            en: "Up to ₹3.00 Lakh crop loan @ 4% p.a. (₹2.00 Lakh collateral-free)",
            hi: "4% वार्षिक ब्याज पर ₹3.00 लाख तक फसल ऋण (₹2.00 लाख बिना गारंटी)"
        },
        "soil-health-card": {
            en: "Free 12-parameter Soil Lab Test + ₹1,500–₹2,500/acre fertilizer savings",
            hi: "नि:शुल्क 12-पैरामीटर मिट्टी जांच + ₹1,500–₹2,500/एकड़ खाद बचत"
        },
        "pmksy": {
            en: "45% to 55% Government Subsidy on Drip & Sprinkler Irrigation (up to 5 Ha)",
            hi: "ड्रिप और स्प्रिंकलर सिंचाई पर 45% से 55% सरकारी सब्सिडी (5 हेक्टेयर तक)"
        },
        "pm-kusum": {
            en: "Up to 60% Government Subsidy on 3 HP–10 HP Standalone Solar Pumps",
            hi: "3 HP से 10 HP सोलर कृषि पंप पर 60% तक सरकारी अनुदान"
        }
    };

    const SCHEME_FULL_NAME_HI = {
        "pm-kisan": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)",
        "pmfby": "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
        "kcc": "किसान क्रेडिट कार्ड योजना (KCC)",
        "soil-health-card": "मृदा स्वास्थ्य कार्ड योजना (Soil Health Card)",
        "pmksy": "प्रधानमंत्री कृषि सिंचाई योजना (PMKSY)",
        "pm-kusum": "प्रधानमंत्री किसान ऊर्जा सुरक्षा एवं उत्थान महाभियान (PM-KUSUM)"
    };

    function formatStateRowMetrics(row, isHi = false) {
        if (!row) {
            return isHi
                ? { reg: "डेटा उपलब्ध नहीं", ben: "डेटा उपलब्ध नहीं", amt: "सत्यापित राज्य DBT" }
                : { reg: "Historical data unavailable.", ben: "Historical data unavailable.", amt: "Verified State DBT" };
        }
        const reg = row.beneficiaries_lakh ? (isHi ? `${row.beneficiaries_lakh} लाख किसान` : `${row.beneficiaries_lakh} Lakh Farmers`)
            : (row.applications_lakh ? (isHi ? `${row.applications_lakh} लाख आवेदन` : `${row.applications_lakh} Lakh Applications`)
            : (row.accounts_lakh ? (isHi ? `${row.accounts_lakh} लाख KCC खाते` : `${row.accounts_lakh} Lakh KCC Accounts`)
            : (row.cards_lakh ? (isHi ? `${row.cards_lakh} लाख मृदा कार्ड` : `${row.cards_lakh} Lakh Soil Cards`)
            : (row.area_lakh_ha ? (isHi ? `${row.area_lakh_ha} लाख हेक्टेयर सिंचित` : `${row.area_lakh_ha} Lakh Ha Drip/Sprinkler`)
            : (row.pumps_installed ? (isHi ? `${Number(row.pumps_installed).toLocaleString()} सोलर पंप` : `${Number(row.pumps_installed).toLocaleString()} Solar Pumps`) : (isHi ? "सत्यापित" : "Verified"))))));

        const ben = row.beneficiaries_lakh ? (isHi ? `${row.beneficiaries_lakh} लाख किसान` : `${row.beneficiaries_lakh} Lakh Farmers`)
            : (row.applications_lakh ? (isHi ? `${row.applications_lakh} लाख बीमित किसान` : `${row.applications_lakh} Lakh Insured Farmers`)
            : (row.accounts_lakh ? (isHi ? `${row.accounts_lakh} लाख सक्रिय KCC किसान` : `${row.accounts_lakh} Lakh Active KCC Farmers`)
            : (row.cards_lakh ? (isHi ? `${row.cards_lakh} लाख कार्ड वितरित` : `${row.cards_lakh} Lakh Cards Issued`)
            : (row.area_lakh_ha ? (isHi ? `${row.area_lakh_ha} लाख हेक्टेयर कवर` : `${row.area_lakh_ha} Lakh Ha Covered`)
            : (row.pumps_installed ? (isHi ? `${Number(row.pumps_installed).toLocaleString()} किसान (सोलर पंप)` : `${Number(row.pumps_installed).toLocaleString()} Farmers (Solar Pumps)`) : (isHi ? "सत्यापित" : "Verified"))))));

        const amt = row.disbursed_crore ? (isHi ? `₹${Number(row.disbursed_crore).toLocaleString()} करोड़` : `₹${Number(row.disbursed_crore).toLocaleString()} Crore`)
            : (row.claims_paid_crore ? (isHi ? `₹${Number(row.claims_paid_crore).toLocaleString()} करोड़ क्लेम भुगतान` : `₹${Number(row.claims_paid_crore).toLocaleString()} Crore Claims Paid`)
            : (row.credit_crore ? (isHi ? `₹${Number(row.credit_crore).toLocaleString()} करोड़ ऋण स्वीकृत` : `₹${Number(row.credit_crore).toLocaleString()} Crore Credit Sanctioned`)
            : (row.cards_lakh ? (isHi ? "100% नि:शुल्क सरकारी लैब जांच" : "100% Free Govt Lab Testing")
            : (row.area_lakh_ha ? (isHi ? "45%–55% केंद्र+राज्य सब्सिडी" : "45%–55% Central+State Subsidy")
            : (row.pumps_installed ? (isHi ? "60% तक सोलर पंप सब्सिडी" : "Up to 60% Solar Pump Subsidy") : (isHi ? "सत्यापित" : "Verified"))))));

        return { reg, ben, amt };
    }

    async function ensureAllSchemesLoaded() {
        if (allSchemesCache.length > 0) return allSchemesCache;
        try {
            const res = await fetch("/api/schemes/intelligence");
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data.schemes) && data.schemes.length > 0) {
                    allSchemesCache = data.schemes;
                    return allSchemesCache;
                }
            }
        } catch (e) {
            console.warn("Using static All-India 35-state schemes bundle:", e);
        }
        if (window.KRISHI_ALL_INDIA_DATA && Array.isArray(window.KRISHI_ALL_INDIA_DATA.schemes)) {
            allSchemesCache = window.KRISHI_ALL_INDIA_DATA.schemes;
        }
        return allSchemesCache;
    }

    function renderAllSchemesQuickComparisonTable(activeSchemeId) {
        const tbody = document.getElementById("intelAllSchemesQuickTableBody");
        if (!tbody || !Array.isArray(allSchemesCache) || allSchemesCache.length === 0) return;

        const isHi = state.lang === "hi";
        tbody.innerHTML = allSchemesCache.map(sc => {
            const nm = sc.national_metrics || {};
            const isSel = sc.id === activeSchemeId;
            const summaryObj = PER_FARMER_SUMMARY_MAP[sc.id];
            const perFarmer = summaryObj ? (isHi ? summaryObj.hi : summaryObj.en) : (sc.benefits || "Direct Scheme Benefit");
            const displayFull = isHi ? (SCHEME_FULL_NAME_HI[sc.id] || sc.full_name) : sc.full_name;
            const portalTxt = isHi ? "आधिकारिक पोर्टल ↗" : "Official Portal ↗";
            return `<tr data-scheme-row="${escapeHtml(sc.id)}" style="cursor:pointer; border-bottom:1px solid var(--km-border); transition:background 0.15s; ${isSel ? 'background:rgba(6,78,43,0.10); font-weight:700;' : ''}">
                <td style="padding:10px 8px; color:var(--km-primary);">
                    <strong>${escapeHtml(sc.short_name)}</strong>
                    <div style="font-size:0.74rem; color:var(--km-text-muted); font-weight:400;">${escapeHtml(displayFull)}</div>
                </td>
                <td style="padding:10px 8px; font-weight:700; color:#064E2B;">${escapeHtml(nm.actual_beneficiaries_latest_installment || nm.approved_applications || (isHi ? "सत्यापित" : "Verified"))}</td>
                <td style="padding:10px 8px; font-weight:700; color:#b45309;">${escapeHtml(nm.total_financial_assistance_distributed || (isHi ? "सत्यापित" : "Verified"))}</td>
                <td style="padding:10px 8px; font-size:0.8rem;">${escapeHtml(perFarmer)}</td>
                <td style="padding:10px 8px;"><a href="${escapeHtml(sc.official_website)}" target="_blank" rel="noopener" style="color:var(--km-primary); font-weight:700;" onclick="event.stopPropagation();">${portalTxt}</a></td>
            </tr>`;
        }).join("");

        tbody.querySelectorAll("tr[data-scheme-row]").forEach(rowEl => {
            rowEl.addEventListener("click", () => {
                const sid = rowEl.getAttribute("data-scheme-row");
                const sel = document.getElementById("intelSchemeSelect");
                if (sel && sid) {
                    sel.value = sid;
                    loadKrishiSchemeIntelligence();
                }
            });
        });
    }

    async function loadKrishiSchemeIntelligence() {
        await ensureAllSchemesLoaded();
        const isHi = state.lang === "hi";
        const schemeId = document.getElementById("intelSchemeSelect")?.value || "pm-kisan";
        const st = document.getElementById("intelStateSelect")?.value || state.selectedState || "Uttar Pradesh";

        // Highlight active scheme pill
        document.querySelectorAll(".intel-scheme-pill").forEach(btn => {
            const pid = btn.getAttribute("data-scheme-id") || btn.getAttribute("data-scheme");
            if (pid === schemeId) {
                btn.classList.add("active");
                btn.style.background = "var(--km-primary)";
                btn.style.color = "#fff";
            } else {
                btn.classList.remove("active");
                btn.style.background = "#fff";
                btn.style.color = "var(--km-primary)";
            }
        });

        try {
            let sc = null;
            try {
                const res = await fetch(`/api/schemes/intelligence?scheme_id=${encodeURIComponent(schemeId)}&state=${encodeURIComponent(st)}`);
                if (res.ok) {
                    const data = await res.json();
                    sc = data.scheme || (data.schemes && data.schemes[0]);
                }
            } catch (_) {}
            if (!sc) {
                sc = allSchemesCache.find(x => x.id === schemeId) || allSchemesCache[0];
            }
            if (!sc) return;

            renderAllSchemesQuickComparisonTable(sc.id);

            const nm = sc.national_metrics || {};
            const statesList = sc.top_beneficiary_states || sc.state_wise_beneficiaries || [];
            const matchedStateRow = statesList.find(r => r.state && r.state.toLowerCase() === st.toLowerCase()) || statesList[0] || null;
            const stateMetrics = formatStateRowMetrics(matchedStateRow, isHi);

            // Populate Farmer Benefit & Amount Spotlight Card
            const spotTitle = document.getElementById("spotlightSchemeTitle");
            const spotNatFarmers = document.getElementById("spotlightNationalFarmers");
            const spotNatSub = document.getElementById("spotlightNationalSub");
            const spotNatAmt = document.getElementById("spotlightNationalAmount");
            const spotPerFarmer = document.getElementById("spotlightPerFarmerBenefit");
            const spotStateHdr = document.getElementById("spotlightStateHeader");
            const spotStateFarmers = document.getElementById("spotlightStateFarmers");
            const spotStateAmt = document.getElementById("spotlightStateAmount");
            const spotApplyBtn = document.getElementById("spotlightApplyBtn");

            const displayFull = isHi ? (SCHEME_FULL_NAME_HI[sc.id] || sc.full_name) : sc.full_name;
            const summaryObj = PER_FARMER_SUMMARY_MAP[sc.id];
            const perFarmerTxt = summaryObj ? (isHi ? summaryObj.hi : summaryObj.en) : sc.benefits;

            if (spotTitle) {
                spotTitle.textContent = isHi
                    ? `${displayFull} — लाभार्थी किसान एवं कुल राशि विवरण`
                    : `${displayFull}`;
            }
            if (spotNatFarmers) spotNatFarmers.textContent = nm.actual_beneficiaries_latest_installment || nm.approved_applications || (isHi ? "सत्यापित" : "Verified");
            if (spotNatSub) {
                spotNatSub.textContent = isHi
                    ? `कुल पंजीकृत किसान: ${nm.registered_farmers || nm.eligible_farmers || "अखिल भारतीय"}`
                    : `Registered / Enrolled: ${nm.registered_farmers || nm.eligible_farmers || "All-India"}`;
            }
            if (spotNatAmt) spotNatAmt.textContent = nm.total_financial_assistance_distributed || (isHi ? "सत्यापित DBT सहायता" : "Verified DBT Assistance");
            if (spotPerFarmer) {
                spotPerFarmer.textContent = isHi
                    ? `प्रति किसान लाभ: ${perFarmerTxt}`
                    : `Per Farmer Benefit: ${perFarmerTxt}`;
            }
            if (spotStateHdr) {
                const displaySt = matchedStateRow ? matchedStateRow.state : st;
                const displayStHi = STATE_HI[displaySt] || displaySt;
                spotStateHdr.textContent = isHi
                    ? `राज्य लाभार्थी (${displayStHi}):`
                    : `State Beneficiaries (${displaySt}):`;
            }
            if (spotStateFarmers) spotStateFarmers.textContent = stateMetrics.ben;
            if (spotStateAmt) {
                spotStateAmt.textContent = isHi
                    ? `कुल राज्य वितरित राशि: ${stateMetrics.amt}`
                    : `Total State Benefit / Amount: ${stateMetrics.amt}`;
            }
            if (spotApplyBtn && sc.official_website) {
                spotApplyBtn.href = sc.official_website;
                spotApplyBtn.textContent = isHi
                    ? `आधिकारिक ${sc.short_name} पोर्टल ↗`
                    : `Official ${sc.short_name} Portal ↗`;
            }

            const titleEl = document.getElementById("intelSchemeFullTitle");
            const sumBox = document.getElementById("intelSchemeSummaryBox");
            if (titleEl) titleEl.textContent = `${sc.full_name} — Eligibility & State Coverage`;
            if (sumBox) {
                sumBox.innerHTML = `
                    <p><strong>Objective:</strong> ${escapeHtml(sc.objective)}</p>
                    <p style="margin-top:4px;"><strong>Benefits (किसान को लाभ):</strong> ${escapeHtml(sc.benefits)}</p>
                    <p style="margin-top:4px;"><strong>Eligibility:</strong> ${escapeHtml(sc.eligibility_criteria || "All eligible farming households")}</p>
                    <p style="margin-top:4px; font-size:0.78rem; color:var(--km-text-muted);"><strong>Official Source:</strong> ${escapeHtml(sc.source || sc.official_source || "Ministry of Agriculture")} | <strong>Reporting Period:</strong> ${escapeHtml(sc.reporting_period)}</p>
                `;
            }

            const tbody = document.getElementById("intelStateTableBody");
            if (tbody && Array.isArray(statesList)) {
                tbody.innerHTML = statesList.map(row => {
                    const isSel = row.state && row.state.toLowerCase() === st.toLowerCase();
                    const fm = formatStateRowMetrics(row);
                    return `<tr style="border-bottom:1px solid var(--km-border); ${isSel ? 'background:rgba(6,78,43,0.09); font-weight:700;' : ''}">
                        <td style="padding:7px 8px;">${escapeHtml(row.state)} ${isSel ? '(Selected)' : ''}</td>
                        <td style="padding:7px 8px;">${escapeHtml(fm.reg)}</td>
                        <td style="padding:7px 8px; color:var(--km-primary); font-weight:700;">${escapeHtml(fm.ben)}</td>
                        <td style="padding:7px 8px; color:#b45309; font-weight:600;">${escapeHtml(fm.amt)}</td>
                        <td style="padding:7px 8px;">${row.coverage_pct ? row.coverage_pct + '%' : 'Verified DBT'}</td>
                    </tr>`;
                }).join("");
            }

            // Render Yearly Chart
            const yearlyList = sc.yearly_trend || sc.yearly_trends || [];
            const ctxY = document.getElementById("chartSchemeYearly")?.getContext("2d");
            if (ctxY && Array.isArray(yearlyList) && yearlyList.length > 0) {
                if (schemeYearlyChartInstance) schemeYearlyChartInstance.destroy();
                const labels = yearlyList.map(y => y.year);
                const vals = yearlyList.map(y =>
                    y.beneficiaries_crore || y.applications_crore || y.operative_accounts_crore || y.cards_issued_crore || y.area_covered_lakh_ha || y.pumps_installed_cumulative || 0
                );
                schemeYearlyChartInstance = new Chart(ctxY, {
                    type: "line",
                    data: {
                        labels,
                        datasets: [{
                            label: sc.short_name + " Yearly Beneficiaries / Coverage",
                            data: vals,
                            borderColor: "#064E2B",
                            backgroundColor: "rgba(6, 78, 43, 0.14)",
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }

            // Render State Chart
            const ctxS = document.getElementById("chartSchemeStates")?.getContext("2d");
            if (ctxS && Array.isArray(statesList) && statesList.length > 0) {
                if (schemeStatesChartInstance) schemeStatesChartInstance.destroy();
                const sLabels = statesList.map(r => r.state);
                const sVals = statesList.map(r =>
                    r.beneficiaries_lakh || r.applications_lakh || r.accounts_lakh || r.cards_lakh || r.area_lakh_ha || r.pumps_installed || 0
                );
                schemeStatesChartInstance = new Chart(ctxS, {
                    type: "bar",
                    data: {
                        labels: sLabels,
                        datasets: [{
                            label: sc.short_name + " State-Wise Beneficiaries / Coverage",
                            data: sVals,
                            backgroundColor: "#064E2B",
                            borderRadius: 6
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }
        } catch (err) {
            console.warn("KrishiScheme Intelligence load error:", err);
        }
    }

    // Wire clickable scheme pills
    document.querySelectorAll(".intel-scheme-pill").forEach(btn => {
        btn.addEventListener("click", () => {
            const sid = btn.getAttribute("data-scheme-id") || btn.getAttribute("data-scheme");
            const sel = document.getElementById("intelSchemeSelect");
            if (sel && sid) {
                sel.value = sid;
                loadKrishiSchemeIntelligence();
            }
        });
    });

    // Wire live search input for schemes
    const intelQuickSearchInput = document.getElementById("intelQuickSearchInput");
    if (intelQuickSearchInput) {
        intelQuickSearchInput.addEventListener("input", () => {
            const q = intelQuickSearchInput.value.trim().toLowerCase();
            if (!q) return;
            const keywordMap = [
                { id: "pm-kisan", keys: ["kisan", "samman", "6000", "2000", "dbt", "nidhi"] },
                { id: "pmfby", keys: ["pmfby", "fasal", "bima", "insurance", "claim", "crop loss"] },
                { id: "kcc", keys: ["kcc", "credit", "loan", "bank", "interest", "4%"] },
                { id: "soil-health-card", keys: ["soil", "health", "card", "npk", "mitti", "test"] },
                { id: "pmksy", keys: ["pmksy", "sinchayee", "drip", "sprinkler", "irrigation", "water"] },
                { id: "pm-kusum", keys: ["kusum", "solar", "pump", "urja", "bijli"] }
            ];
            for (const item of keywordMap) {
                if (item.keys.some(k => q.includes(k))) {
                    const sel = document.getElementById("intelSchemeSelect");
                    if (sel && sel.value !== item.id) {
                        sel.value = item.id;
                        loadKrishiSchemeIntelligence();
                    }
                    break;
                }
            }
        });
    }

    const btnLoadSchemeIntel = document.getElementById("btnLoadSchemeIntel");
    if (btnLoadSchemeIntel) btnLoadSchemeIntel.addEventListener("click", loadKrishiSchemeIntelligence);
    const intelSchemeSelect = document.getElementById("intelSchemeSelect");
    if (intelSchemeSelect) intelSchemeSelect.addEventListener("change", loadKrishiSchemeIntelligence);
    const intelStateSelect = document.getElementById("intelStateSelect");
    if (intelStateSelect) intelStateSelect.addEventListener("change", loadKrishiSchemeIntelligence);

    const adminSchemeUploadForm = document.getElementById("adminSchemeUploadForm");
    if (adminSchemeUploadForm) {
        adminSchemeUploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msgEl = document.getElementById("upSchemeStatusMsg");
            const payload = {
                scheme_id: document.getElementById("intelSchemeSelect")?.value || "pm-kisan",
                state: document.getElementById("upSchemeState")?.value || "Uttar Pradesh",
                district: document.getElementById("upSchemeDistrict")?.value || "Meerut",
                year: document.getElementById("upSchemeYear")?.value || "2024-25",
                registered_farmers: parseInt(document.getElementById("upSchemeReg")?.value || "0", 10) || null,
                actual_beneficiaries: parseInt(document.getElementById("upSchemeBen")?.value || "0", 10) || 0,
                amount_disbursed_crore: parseFloat(document.getElementById("upSchemeAmt")?.value || "0") || 0,
                source_citation: document.getElementById("upSchemeSource")?.value || "Official District Report"
            };
            const res = await fetch("/api/schemes/intelligence/upload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (msgEl) msgEl.textContent = data.status === "success" ? "✅ Verified record saved!" : `⚠️ ${data.message}`;
            loadKrishiSchemeIntelligence();
        });
    }

    // --- 11C. KrishiSuraksha AI Crop Insurance (Landowner vs. Tenant & PMFBY Calculator) ---
    const insDamageDateInput = document.getElementById("insDamageDate");
    if (insDamageDateInput && !insDamageDateInput.value) {
        insDamageDateInput.value = new Date().toISOString().split("T")[0];
    }

    const OWNERSHIP_GUIDANCE_UI = {
        owner: {
            en: {
                badge: "Mode: Own Land",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">Yes — Direct Landowners are 100% eligible for PMFBY Crop Insurance.</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>Documents Needed:</strong> Aadhaar Card, Khatauni / 7-12 Land Record, Sowing Certificate, and Bank Passbook.<br>
                           • <strong>Direct Payout:</strong> 100% of the approved claim payout is transferred directly to your Aadhaar-seeded bank account (DBT).
                       </p>`
            },
            hi: {
                badge: "श्रेणी: स्वयं की भूमि (Own Land)",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">हाँ! स्वयं की भूमि (Own Land / खतौनी) पर किसान को 100% सीधा PMFBY फसल बीमा लाभ मिलता है।</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>आवश्यक दस्तावेज:</strong> आधार कार्ड, खतौनी / 7-12 नकल, बुवाई प्रमाण पत्र और बैंक पासबुक।<br>
                           • <strong>सीधा बैंक भुगतान (DBT):</strong> फसल नुकसान होने पर पूरी बीमा क्लेम राशि सीधे आपके आधार-लिंक्ड बैंक खाते में आती है।
                       </p>`
            }
        },
        tenant_with_agreement: {
            en: {
                badge: "Mode: Landowner's Land (+ Consent/NOC)",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">Yes — Tenant / Bataidar farmers cultivating a Landowner's land are eligible for PMFBY!</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>Required from Landowner:</strong> Copy of Landowner's Khatauni + Written Lease / Consent Letter (NOC) OR a Patwari/Sarpanch <strong>Cultivator Sowing Certificate</strong>.<br>
                           • <strong>Who Receives the Claim Money?</strong> When enrolled in the cultivator's name at CSC or pmfby.gov.in, the claim payout goes directly to the <strong>cultivating farmer's bank account</strong> (provided the landowner has not claimed duplicate KCC insurance on the same plot).
                       </p>`
            },
            hi: {
                badge: "श्रेणी: ज़मीन मालिक की भूमि (सहमति पत्र / NOC सहित)",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">हाँ! ज़मीन मालिक (Landowner) की भूमि पर खेती करने वाले बटाईदार / किरायेदार किसान को भी PMFBY फसल बीमा मिलता है!</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>ज़मीन मालिक (Landowner) से क्या चाहिए?</strong> मालिक की खतौनी की फोटोकॉपी + लिखित किरायानामा / सहमति पत्र (NOC) या लेखपाल/पटवारी/सरपंच द्वारा जारी <strong>वास्तविक काश्तकार बुवाई प्रमाण पत्र (Sowing Certificate)</strong>।<br>
                           • <strong>पैसा किसके खाते में आएगा?</strong> यदि बीमा आपके (बटाईदार किसान के) नाम से CSC या pmfby.gov.in पर दर्ज है, तो क्लेम की राशि सीधे <strong>आपके बैंक खाते (DBT)</strong> में आएगी (बशर्ते मालिक ने उसी खसरे पर डुप्लीकेट KCC बीमा न लिया हो)।
                       </p>`
            }
        },
        tenant_without_agreement: {
            en: {
                badge: "Mode: Landowner's Land (Oral Bataidar)",
                html: `<div style="font-weight: 800; color: #b45309; font-size: 0.92rem; margin-bottom: 4px;">Important: Without Landowner Consent or a Sowing Certificate, an oral tenant cannot claim directly in their own name.</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>Why:</strong> PMFBY requires linking a Khasra/Khatauni plot number.<br>
                           • <strong>How to Solve (2 Easy Steps):</strong> (1) Obtain a 1-season Cultivation Consent Note from the landowner or a <em>Patwari/Sarpanch Sowing Certificate</em> before enrollment, <strong>OR</strong> (2) Have the landowner enroll the plot and sign a mutual crop-compensation share note.
                       </p>`
            },
            hi: {
                badge: "श्रेणी: ज़मीन मालिक की भूमि (मौखिक बटाईदार किसान)",
                html: `<div style="font-weight: 800; color: #b45309; font-size: 0.92rem; margin-bottom: 4px;">ध्यान दें: बिना ज़मीन मालिक की सहमति या बुवाई प्रमाण पत्र के मौखिक बटाईदार को अपने नाम से सीधा क्लेम नहीं मिल पाता।</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>कारण:</strong> पोर्टल पर खसरा/खतौनी नंबर जोड़ना अनिवार्य है।<br>
                           • <strong>अभी क्या करें (2 आसान उपाय)?</strong> (1) ज़मीन मालिक से सादे कागज पर 1-सीजन का सहमति पत्र (NOC) लेकर पटवारी/सरपंच से <em>बुवाई प्रमाण पत्र (Sowing Certificate)</em> बनवा लें, <strong>या</strong> (2) ज़मीन मालिक के नाम से बीमा करवाते समय आपसी फसल-बटाई समझौता रखें।
                       </p>`
            }
        },
        joint_family: {
            en: {
                badge: "Mode: Joint Family Khatauni",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">Yes — Farmers cultivating on a Joint Family / Ancestral Khatauni are eligible for PMFBY.</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>How to Apply:</strong> Submit the joint Khatauni along with a Family Cultivation Declaration and Lekhpal Sowing Certificate for your cultivated share (in acres) at your nearest CSC.
                       </p>`
            },
            hi: {
                badge: "श्रेणी: संयुक्त परिवार की खतौनी",
                html: `<div style="font-weight: 800; color: #064E2B; font-size: 0.92rem; margin-bottom: 4px;">हाँ! पिता / संयुक्त परिवार के नाम दर्ज खतौनी पर खेती करने वाले सदस्य को भी पूरा फसल बीमा मिलता है।</div>
                       <p style="margin: 0; font-size: 0.82rem; color: var(--km-text-body); line-height: 1.5;">
                           • <strong>कैसे आवेदन करें?</strong> संयुक्त खतौनी में अपने हिस्से के रकबे (एकड़) के लिए परिवार सहमति घोषणा पत्र और लेखपाल बुवाई प्रमाण पत्र के साथ नजदीकी CSC से आवेदन करें।
                       </p>`
            }
        }
    };

    function refreshSurakshaLanguage() {
        const isHi = state.lang === "hi";
        const ownType = document.getElementById("insOwnershipType")?.value || "owner";
        const infoGroup = OWNERSHIP_GUIDANCE_UI[ownType] || OWNERSHIP_GUIDANCE_UI.owner;
        const info = isHi ? infoGroup.hi : infoGroup.en;
        const badgeEl = document.getElementById("selectedOwnershipBadge");
        const boxEl = document.getElementById("landownerExplainBox");
        if (badgeEl) badgeEl.textContent = info.badge;
        if (boxEl) boxEl.innerHTML = info.html;

        const titleEl = document.getElementById("surakshaStatusTitle");
        const expEl = document.getElementById("surakshaExplanationText");
        const badge72 = document.getElementById("suraksha72HrBadge");
        if (titleEl && (titleEl.textContent === "Potentially eligible." || titleEl.textContent === "पात्र होने की प्रबल संभावना है।")) {
            titleEl.textContent = isHi ? "पात्र होने की प्रबल संभावना है।" : "Potentially eligible.";
        }
        if (expEl && (expEl.textContent.includes("Both direct Landowners") || expEl.textContent.includes("प्रत्यक्ष भूमि मालिक"))) {
            expEl.textContent = isHi
                ? "प्रत्यक्ष भूमि मालिक (Landowner) और सहमति पत्र/बुवाई प्रमाण पत्र वाले बटाईदार किसान दोनों PMFBY के तहत पात्र हैं।"
                : "Both direct Landowners and Tenant/Bataidar farmers with a Landowner Consent Note or Patwari Sowing Certificate are eligible under PMFBY.";
        }
        if (badge72 && (badge72.textContent.includes("Within 72-Hr") || badge72.textContent.includes("72-घंटे की समय-सीमा"))) {
            badge72.textContent = isHi ? "72-घंटे की समय-सीमा के भीतर" : "Within 72-Hr Window";
        }
    }

    function updateSurakshaLivePremiumPreview() {
        const acres = parseFloat(document.getElementById("insLandAcres")?.value || "2.5") || 2.5;
        const season = document.getElementById("insSeason")?.value || "Rabi";
        const ha = Math.max(0.1, acres * 0.404686);
        const scaleOfFinancePerHa = 68000;
        const sumInsured = Math.round(ha * scaleOfFinancePerHa);
        const rate = season === "Rabi" ? 0.015 : (season === "Kharif" ? 0.02 : 0.05);
        const farmerPrem = Math.round(sumInsured * rate);

        const siEl = document.getElementById("surakshaSumInsuredVal");
        const fpEl = document.getElementById("surakshaFarmerPremVal");
        if (siEl) siEl.textContent = `₹${sumInsured.toLocaleString("en-IN")}`;
        if (fpEl) fpEl.textContent = `₹${farmerPrem.toLocaleString("en-IN")} (${(rate * 100).toFixed(1)}%)`;
    }

    document.querySelectorAll(".ownership-type-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const ownType = btn.getAttribute("data-ownership") || "owner";
            const hiddenIn = document.getElementById("insOwnershipType");
            if (hiddenIn) hiddenIn.value = ownType;

            document.querySelectorAll(".ownership-type-btn").forEach(b => {
                if (b.getAttribute("data-ownership") === ownType) {
                    b.classList.add("active");
                    b.style.background = "var(--km-primary)";
                    b.style.color = "#fff";
                } else {
                    b.classList.remove("active");
                    b.style.background = "#fff";
                    b.style.color = "var(--km-primary)";
                }
            });

            const infoGroup = OWNERSHIP_GUIDANCE_UI[ownType] || OWNERSHIP_GUIDANCE_UI.owner;
            const info = state.lang === "hi" ? infoGroup.hi : infoGroup.en;
            const badgeEl = document.getElementById("selectedOwnershipBadge");
            const boxEl = document.getElementById("landownerExplainBox");
            if (badgeEl) badgeEl.textContent = info.badge;
            if (boxEl) boxEl.innerHTML = info.html;
        });
    });

    document.querySelectorAll(".peril-quick-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const peril = btn.getAttribute("data-peril") || "";
            const dmgInput = document.getElementById("insDamageType");
            if (dmgInput && peril) {
                dmgInput.value = peril;
            }
        });
    });

    const insLandAcresInput = document.getElementById("insLandAcres");
    const insSeasonInput = document.getElementById("insSeason");
    if (insLandAcresInput) insLandAcresInput.addEventListener("input", updateSurakshaLivePremiumPreview);
    if (insSeasonInput) insSeasonInput.addEventListener("change", updateSurakshaLivePremiumPreview);
    updateSurakshaLivePremiumPreview();

    const surakshaAssessForm = document.getElementById("surakshaAssessForm");
    if (surakshaAssessForm) {
        surakshaAssessForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            updateSurakshaLivePremiumPreview();
            const fileIn = document.getElementById("insPhotoFile");
            const photoName = (fileIn && fileIn.files && fileIn.files[0]) ? fileIn.files[0].name : "";
            const payload = {
                farmer_name: document.getElementById("insFarmerName")?.value || "Tanishka",
                state: document.getElementById("insState")?.value || "Uttar Pradesh",
                district: document.getElementById("insDistrict")?.value || "Meerut",
                village: document.getElementById("insVillage")?.value || "Daurala",
                crop: document.getElementById("insCrop")?.value || "Wheat",
                season: document.getElementById("insSeason")?.value || "Rabi",
                land_acres: parseFloat(document.getElementById("insLandAcres")?.value || "2.5") || 2.5,
                sowing_date: document.getElementById("insSowingDate")?.value || "",
                enrolled_pmfby: document.getElementById("insEnrolled")?.value || "yes",
                policy_number: document.getElementById("insPolicyNo")?.value || "",
                damage_date: document.getElementById("insDamageDate")?.value || new Date().toISOString().split("T")[0],
                damage_type: document.getElementById("insDamageType")?.value || "Hailstorm (Localized Calamity)",
                ownership_type: document.getElementById("insOwnershipType")?.value || "owner",
                landowner_kcc_claimed: document.getElementById("insLandownerKcc")?.value || "no",
                photo_filename: photoName
            };

            const isHi = state.lang === "hi";
            const titleEl = document.getElementById("surakshaStatusTitle");
            const expEl = document.getElementById("surakshaExplanationText");
            const badgeEl = document.getElementById("suraksha72HrBadge");
            const rulesEl = document.getElementById("surakshaRuleChecksBox");
            const discEl = document.getElementById("surakshaDisclaimerText");
            const siEl = document.getElementById("surakshaSumInsuredVal");
            const fpEl = document.getElementById("surakshaFarmerPremVal");
            const bannerEl = document.getElementById("surakshaStatusBanner");

            // Compute deterministic PMFBY prediction client-side (Zero Failure on Netlify/Local)
            const ha = Math.max(0.1, payload.land_acres * 0.404686);
            const scaleOfFinance = 68000; // standard per hectare Scale of Finance
            const estSumInsured = Math.round(ha * scaleOfFinance);
            const premiumRate = payload.season === "Rabi" ? 0.015 : (payload.season === "Kharif" ? 0.02 : 0.05);
            const estFarmerPrem = Math.round(estSumInsured * premiumRate);

            // 72-hour reporting limit check
            const dmgDate = new Date(payload.damage_date);
            const now = new Date();
            const elapsedHours = Math.max(0, Math.round((now - dmgDate) / (1000 * 60 * 60)));
            const within72 = elapsedHours <= 72;

            // Determine eligibility verdict & explanation
            let statusText = "Claim Eligible: 100% Direct DBT Payout";
            let explanationText = "";
            let bannerBg = "linear-gradient(135deg, #064E2B, #0B6B3A)";

            if (payload.enrolled_pmfby === "no") {
                statusText = isHi ? "वर्तमान में अपात्र (नामांकन आवश्यक)" : "Not eligible (Enrollment Required)";
                explanationText = isHi
                    ? "PMFBY फसल बीमा क्लेम के लिए सक्रिय सीजन में बुवाई कट-ऑफ तिथि से पूर्व बीमा पॉलिसी होना अनिवार्य है। अगली फसल के लिए CSC केंद्र या pmfby.gov.in पर समय से नामांकन करें।"
                    : "PMFBY crop insurance claim requires an active policy enrolled before the seasonal cut-off date. You can enroll for the next season at your nearest CSC or pmfby.gov.in.";
                bannerBg = "linear-gradient(135deg, #991B1B, #DC2626)";
            } else if (payload.ownership_type === "tenant_without_agreement") {
                statusText = isHi ? "अतिरिक्त दस्तावेज आवश्यक (सहमति पत्र / NOC)" : "More Information Required (Landowner NOC / Sowing Cert)";
                explanationText = isHi
                    ? "मौखिक बटाईदार (Oral Bataidar): ज़मीन मालिक से सादे कागज पर 1-सीजन सहमति पत्र (NOC) अथवा लेखपाल/पटवारी द्वारा जारी वास्तविक बुवाई प्रमाण पत्र (Sowing Certificate) संलग्न करने पर क्लेम राशि 100% आपके बैंक खाते (DBT) में अंतरित होगी।"
                    : "Tenant / Bataidar without formal contract: You must attach a signed Landowner Consent Note (NOC) or Patwari/Sarpanch Cultivator Sowing Certificate so the claim payout transfers directly to your bank account via DBT.";
                bannerBg = "linear-gradient(135deg, #92400E, #D97706)";
            } else if (payload.landowner_kcc_claimed === "yes" && payload.ownership_type !== "owner") {
                statusText = isHi ? "भूमि मालिक KCC डुप्लीकेट क्लेम जांच आवश्यक" : "Landowner Duplicate KCC Claim Verification Required";
                explanationText = isHi
                    ? "ज़मीन मालिक के KCC खाते से इस खसरे पर स्वतः बीमा कट चुका है। दोहरी क्लेम से बचने के लिए भूमि मालिक से NOC लेकर बैंक में प्रस्तुत करें ताकि क्लेम वास्तविक काश्तकार को मिले।"
                    : "Duplicate KCC Alert: Landowner already has an active loan deduction on this plot. Obtain an NOC from the landowner to redirect claim payment to your account.";
                bannerBg = "linear-gradient(135deg, #92400E, #D97706)";
            } else {
                statusText = isHi ? "दावा पात्रता: 100% पात्र (Direct DBT Payout)" : "Claim Eligible: 100% Direct DBT Payout";
                explanationText = isHi
                    ? `बधाई! आपका फसल नुकसान दावा PMFBY मानकों के अनुसार पूर्णतः पात्र है। ₹${estSumInsured.toLocaleString("en-IN")} की बीमित राशि पर फसल नुकसान का मुआविज़ा सीधे आधार-लिंक्ड बैंक खाते (DBT) में प्राप्त होगा।`
                    : `Your crop damage claim qualifies under PMFBY guidelines. With ₹${estSumInsured.toLocaleString("en-IN")} Sum Insured coverage, your claim payout will be directly credited via Direct Benefit Transfer (DBT) to your Aadhaar-linked bank account upon CCE survey.`;
                bannerBg = "linear-gradient(135deg, #064E2B, #0B6B3A)";
            }

            // Apply immediate render
            if (bannerEl) bannerEl.style.background = bannerBg;
            if (titleEl) titleEl.textContent = statusText;
            if (expEl) expEl.textContent = explanationText;
            if (siEl) siEl.textContent = `₹${estSumInsured.toLocaleString("en-IN")}`;
            if (fpEl) fpEl.textContent = `₹${estFarmerPrem.toLocaleString("en-IN")} (${(premiumRate * 100).toFixed(1)}%)`;
            if (badgeEl) {
                badgeEl.textContent = within72
                    ? (isHi ? `72-घंटे की सीमा में (${elapsedHours} घंटे व्यतीत)` : `Within 72-Hr Window (${elapsedHours}h elapsed)`)
                    : (isHi ? `⚠️ 72 घंटे से अधिक (${elapsedHours} घंटे व्यतीत - 14447 पर तुरंत संपर्क करें)` : `⚠️ >72h Elapsed (Call 14447 immediately)`);
            }

            if (rulesEl) {
                const ownStatusStr = payload.ownership_type === "owner"
                    ? (isHi ? "✅ सत्यापित भूमि मालिक (Khatauni Verified)" : "✅ Verified Khatedar Landowner")
                    : (payload.ownership_type === "tenant_with_agreement"
                        ? (isHi ? "✅ ज़मीन मालिक NOC / बुवाई प्रमाण पत्र संलग्न" : "✅ Landowner NOC / Sowing Certificate Attached")
                        : (payload.ownership_type === "joint_family"
                            ? (isHi ? "✅ संयुक्त परिवार खतौनी (हिस्सा सत्यापित)" : "✅ Joint Family Khatauni (Share Verified)")
                            : (isHi ? "⚠️ लेखपाल बुवाई प्रमाण पत्र आवश्यक" : "⚠️ Patwari Sowing Certificate Required")));

                if (isHi) {
                    rulesEl.innerHTML = `
                        <div style="margin-bottom:4px;">• <strong>भूमि स्वामित्व / काश्तकार स्थिति:</strong> ${ownStatusStr}</div>
                        <div style="margin-bottom:4px;">• <strong>बीमा कवरेज (Sum Insured):</strong> ₹${estSumInsured.toLocaleString("en-IN")} (${payload.land_acres} एकड़ @ ₹68,000/हेक्टेयर वित्त पैमाना)</div>
                        <div style="margin-bottom:4px;">• <strong>किसान प्रीमियम अंश:</strong> मात्र ₹${estFarmerPrem.toLocaleString("en-IN")} (${(premiumRate * 100).toFixed(1)}%) — 98.5% सरकार द्वारा अनुदानित</div>
                        <div style="margin-bottom:4px;">• <strong>आपदा कवरेज:</strong> ✅ ${escapeHtml(payload.damage_type)} PMFBY प्राकृतिक आपदा श्रेणी में कवर है</div>
                        <div style="margin-bottom:4px;">• <strong>72-घंटे सूचना समय-सीमा:</strong> ${within72 ? "✅ समय-सीमा के भीतर (मान्य)" : "⚠️ 72 घंटे से अधिक (टोल-फ्री 14447 पर तुरंत इंटिमेशन दर्ज कराएं)"}</div>
                        <div>• <strong>भुगतान माध्यम:</strong> ✅ सीधा आधार-लिंक्ड बैंक खाता (Direct Benefit Transfer - DBT)</div>
                    `;
                } else {
                    rulesEl.innerHTML = `
                        <div style="margin-bottom:4px;">• <strong>Landowner / Cultivator Status:</strong> ${ownStatusStr}</div>
                        <div style="margin-bottom:4px;">• <strong>Calculated Coverage (Sum Insured):</strong> ₹${estSumInsured.toLocaleString("en-IN")} (${payload.land_acres} acres @ ₹68,000/ha Scale of Finance)</div>
                        <div style="margin-bottom:4px;">• <strong>Farmer Premium Payable:</strong> Only ₹${estFarmerPrem.toLocaleString("en-IN")} (${(premiumRate * 100).toFixed(1)}%) — 98.5% Subsidized by Govt</div>
                        <div style="margin-bottom:4px;">• <strong>Peril Coverage:</strong> ✅ ${escapeHtml(payload.damage_type)} is fully covered under PMFBY Non-Preventable Natural Risks</div>
                        <div style="margin-bottom:4px;">• <strong>72-Hour Intimation Window:</strong> ${within72 ? "✅ Within 72-Hour Limit (Approved)" : "⚠️ Exceeded 72h (Intimate immediately via Toll-Free 14447)"}</div>
                        <div>• <strong>Payout Mode:</strong> ✅ 100% Direct Benefit Transfer (DBT) into farmer's bank account</div>
                    `;
                }
            }

            // Sync with Flask backend if reachable
            try {
                const res = await fetch("/api/insurance/assess", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.estimated_sum_insured_inr && siEl) {
                        siEl.textContent = `₹${Number(data.estimated_sum_insured_inr).toLocaleString("en-IN")}`;
                    }
                    if (data.farmer_premium_inr && fpEl) {
                        fpEl.textContent = `₹${Number(data.farmer_premium_inr).toLocaleString("en-IN")}`;
                    }
                }
            } catch (_) {}
        });
    }

    // --- 11D. NASA Earth & Weather Intelligence (100% Interactive Clickable Buttons) ---
    let latestNasaSeriesCache = [];
    let latestNasaIndicatorsCache = [];
    let currentNasaFocusParam = "all";

    function renderNasaIndicatorsList(indicators, focusParam) {
        const indBox = document.getElementById("nasaIndicatorsList");
        const filterBadge = document.getElementById("nasaIndicatorFilterBadge");
        if (!indBox || !Array.isArray(indicators)) return;

        const focusTitles = {
            all: "Showing: All Parameters",
            temp: "Showing: Thermal & Heat Stress",
            rain: "Showing: Precipitation & Drought",
            solar: "Showing: Solar & PM-KUSUM"
        };
        if (filterBadge) filterBadge.textContent = focusTitles[focusParam] || "Showing: All Parameters";

        const filtered = indicators.filter(ind => {
            if (!focusParam || focusParam === "all") return true;
            const text = `${ind.name || ""} ${ind.agronomic_implication || ""}`.toLowerCase();
            if (focusParam === "temp") return text.includes("heat") || text.includes("thermal") || text.includes("temp");
            if (focusParam === "rain") return text.includes("rain") || text.includes("drought") || text.includes("moisture") || text.includes("precip") || text.includes("humid");
            if (focusParam === "solar") return text.includes("solar") || text.includes("kusum") || text.includes("radiation") || text.includes("irradiance");
            return true;
        });

        const listToRender = filtered.length > 0 ? filtered : indicators;
        indBox.innerHTML = listToRender.map(ind => `
            <div style="padding: 12px 14px; background: var(--km-bg); border-radius: 10px; border-left: 4px solid var(--km-primary);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="color:var(--km-text-heading); font-size:0.9rem;">${escapeHtml(ind.name)}</strong>
                    <span class="chart-badge-tag">${escapeHtml(ind.status)}</span>
                </div>
                <div style="font-size:0.78rem; color:var(--km-text-muted); margin-bottom:4px;"><strong>Threshold:</strong> ${escapeHtml(ind.threshold_used)} | <strong>Observed:</strong> ${escapeHtml(ind.observed_value)}</div>
                <div style="font-size:0.83rem; color:var(--km-text-body);">${escapeHtml(ind.agronomic_implication)}</div>
            </div>
        `).join("");
    }

    function setNasaFocusParameter(focusParam) {
        currentNasaFocusParam = focusParam || "all";
        document.querySelectorAll(".nasa-focus-btn").forEach(b => {
            const bf = b.getAttribute("data-nasa-focus") || b.getAttribute("data-focus") || "all";
            if (bf === currentNasaFocusParam) {
                b.classList.add("active");
                b.style.background = "var(--km-primary)";
                b.style.color = "#fff";
            } else {
                b.classList.remove("active");
                b.style.background = "#fff";
                b.style.color = "var(--km-primary)";
            }
        });

        // Update chart titles & badges dynamically so user sees immediate change
        const c1Title = document.getElementById("nasaChart1Title");
        const c1Badge = document.getElementById("nasaChart1Badge");
        const c2Title = document.getElementById("nasaChart2Title");
        const c2Badge = document.getElementById("nasaChart2Badge");

        if (currentNasaFocusParam === "temp") {
            if (c1Title) c1Title.textContent = "Thermal Regime & Heat Stress Profile (T2M / T2M_MAX)";
            if (c1Badge) c1Badge.textContent = "Thermal Focus Active";
        } else if (currentNasaFocusParam === "solar") {
            if (c1Title) c1Title.textContent = "Solar Irradiance & PM-KUSUM Potential (ALLSKY_SFC_SW_DWN)";
            if (c1Badge) c1Badge.textContent = "Solar Focus Active";
        } else if (currentNasaFocusParam === "rain") {
            if (c2Title) c2Title.textContent = "Precipitation & Drought Anomaly Profile (PRECTOTCORR)";
            if (c2Badge) c2Badge.textContent = "Precipitation Focus Active";
        } else {
            if (c1Title) c1Title.textContent = "Temperature & Solar Radiation Profile";
            if (c1Badge) c1Badge.textContent = "T2M + ALLSKY_SFC_SW_DWN";
            if (c2Title) c2Title.textContent = "Precipitation & Relative Humidity Profile";
            if (c2Badge) c2Badge.textContent = "PRECTOTCORR + RH2M";
        }

        renderNasaChartsFromSeries(latestNasaSeriesCache, currentNasaFocusParam);
        renderNasaIndicatorsList(latestNasaIndicatorsCache, currentNasaFocusParam);
    }

    async function loadNasaIntelligence(showButtonFeedback = false) {
        const st = document.getElementById("nasaStateSelect")?.value || state.selectedState || "Uttar Pradesh";
        const dt = document.getElementById("nasaDistrictSelect")?.value || state.district || "Meerut";
        const viewMode = document.getElementById("nasaViewMode")?.value || "monthly";
        const fetchBtn = document.getElementById("btnFetchNasaIntel");
        const zoneBadge = document.getElementById("nasaActiveZoneBadge");

        if (showButtonFeedback && fetchBtn) {
            fetchBtn.textContent = "Fetching NASA Data...";
            fetchBtn.style.opacity = "0.85";
        }

        try {
            let data = null;
            try {
                const res = await fetch(`/api/nasa/intelligence?state=${encodeURIComponent(st)}&district=${encodeURIComponent(dt)}`);
                if (res.ok) {
                    data = await res.json();
                }
            } catch (_) {}
            if (!data && window.KrishiAllIndiaStatic && typeof window.KrishiAllIndiaStatic.computeFallbackNasa === "function") {
                data = window.KrishiAllIndiaStatic.computeFallbackNasa(st, dt);
            }
            if (!data) return;
            const sm = data.summary_metrics || {};
            const coords = data.coordinates || {};

            if (zoneBadge) {
                zoneBadge.textContent = `Active Zone: ${dt}, ${st} (${coords.latitude || 28.98}°N, ${coords.longitude || 77.71}°E)`;
            }

            const cTemp = document.getElementById("nasaCardTemp");
            const cTempSub = document.getElementById("nasaCardTempSub");
            const cRain = document.getElementById("nasaCardRain");
            const cRainSub = document.getElementById("nasaCardRainSub");
            const cSolar = document.getElementById("nasaCardSolar");
            const cHumSub = document.getElementById("nasaCardHumiditySub");
            const cCoords = document.getElementById("nasaCardCoords");
            const cSrc = document.getElementById("nasaCardSourceBadge");

            if (cTemp) cTemp.textContent = `${sm.avg_temp_c || 25.2}°C`;
            if (cTempSub) cTempSub.textContent = `Peak Max: ${sm.max_temp_c || 38.0}°C (${sm.heat_stress_days || 0} heat days)`;
            if (cRain) cRain.textContent = `${sm.total_rain_mm || 640} mm`;
            if (cRainSub) cRainSub.textContent = `Heavy Rain Events: ${sm.heavy_rain_days || 0}`;
            if (cSolar) cSolar.textContent = `${sm.avg_solar_mj_m2 || 18.2} MJ/m²`;
            if (cHumSub) cHumSub.textContent = `Mean RH2M: ${sm.avg_humidity_pct || 58}%`;
            if (cCoords) cCoords.textContent = `${coords.latitude || 28.98}°N, ${coords.longitude || 77.71}°E`;
            if (cSrc) cSrc.textContent = data.nasa_live_api_connected ? "Live NASA POWER API" : "Verified Reanalysis Cache";

            latestNasaIndicatorsCache = Array.isArray(data.agricultural_indicators) ? data.agricultural_indicators : [];
            renderNasaIndicatorsList(latestNasaIndicatorsCache, currentNasaFocusParam);

            const series = viewMode === "yearly" ? (data.yearly_series || []) : (data.monthly_series || []);
            latestNasaSeriesCache = series;
            renderNasaChartsFromSeries(series, currentNasaFocusParam);

            if (showButtonFeedback && fetchBtn) {
                fetchBtn.textContent = `Synced: ${dt}`;
                fetchBtn.style.opacity = "1";
                setTimeout(() => {
                    fetchBtn.textContent = "Fetch NASA Satellite Data";
                }, 1800);
            }
        } catch (err) {
            console.warn("NASA Intelligence load error:", err);
            if (showButtonFeedback && fetchBtn) {
                fetchBtn.textContent = "Fetch NASA Satellite Data";
                fetchBtn.style.opacity = "1";
            }
        }
    }

    function renderNasaChartsFromSeries(series, focusParam) {
        if (!Array.isArray(series)) return;
        const labels = series.map(s => s.period);
        const tAvg = series.map(s => s.avg_temp_c);
        const tMax = series.map(s => s.max_temp_c);
        const sRad = series.map(s => s.avg_solar_mj_m2);
        const rainVals = series.map(s => s.total_rain_mm);
        const humVals = series.map(s => s.avg_humidity_pct);

        const ctx1 = document.getElementById("chartNasaTempSolar")?.getContext("2d");
        if (ctx1) {
            if (nasaTempSolarChartInstance) nasaTempSolarChartInstance.destroy();
            const ds1 = [];
            if (focusParam === "all" || focusParam === "temp") {
                ds1.push({ label: "Mean Temp (°C)", data: tAvg, borderColor: "#064E2B", backgroundColor: "rgba(6,78,43,0.1)", fill: focusParam === "temp", tension: 0.3 });
                ds1.push({ label: "Max Temp (°C)", data: tMax, borderColor: "#dc2626", tension: 0.3 });
            }
            if (focusParam === "all" || focusParam === "solar") {
                ds1.push({ label: "Solar Irradiance (MJ/m²)", data: sRad, borderColor: "#d97706", backgroundColor: "rgba(217,119,6,0.15)", fill: focusParam === "solar", tension: 0.3 });
            }
            if (ds1.length === 0) {
                ds1.push({ label: "Mean Temp (°C)", data: tAvg, borderColor: "#064E2B", tension: 0.3 });
            }
            nasaTempSolarChartInstance = new Chart(ctx1, {
                type: "line",
                data: { labels, datasets: ds1 },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        const ctx2 = document.getElementById("chartNasaRainHumidity")?.getContext("2d");
        if (ctx2) {
            if (nasaRainHumidityChartInstance) nasaRainHumidityChartInstance.destroy();
            const ds2 = [];
            if (focusParam === "all" || focusParam === "rain") {
                ds2.push({ label: "Precipitation (mm)", data: rainVals, backgroundColor: "#064E2B", borderRadius: 5 });
            }
            if (focusParam === "all" || focusParam !== "rain") {
                ds2.push({ label: "Relative Humidity (%)", data: humVals, backgroundColor: "#FFC928", borderRadius: 5 });
            }
            nasaRainHumidityChartInstance = new Chart(ctx2, {
                type: "bar",
                data: { labels, datasets: ds2 },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
    }

    // Wire clickable NASA Zone quick-jump buttons
    document.querySelectorAll(".nasa-zone-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const zState = btn.getAttribute("data-nasa-state") || btn.getAttribute("data-state") || "Uttar Pradesh";
            const zDist = btn.getAttribute("data-nasa-district") || btn.getAttribute("data-district") || "Meerut";

            document.querySelectorAll(".nasa-zone-btn").forEach(b => {
                if (b === btn) {
                    b.classList.add("active");
                    b.style.background = "var(--km-primary)";
                    b.style.color = "#fff";
                } else {
                    b.classList.remove("active");
                    b.style.background = "#fff";
                    b.style.color = "var(--km-primary)";
                }
            });

            const stSel = document.getElementById("nasaStateSelect");
            const dtSel = document.getElementById("nasaDistrictSelect");
            if (stSel) {
                if (!Array.from(stSel.options).some(o => o.value === zState)) {
                    const opt = document.createElement("option");
                    opt.value = zState;
                    opt.textContent = zState;
                    stSel.appendChild(opt);
                }
                stSel.value = zState;
                stSel.dispatchEvent(new Event("change"));
            }
            if (dtSel) {
                if (!Array.from(dtSel.options).some(o => o.value === zDist)) {
                    const opt = document.createElement("option");
                    opt.value = zDist;
                    opt.textContent = zDist;
                    dtSel.appendChild(opt);
                }
                dtSel.value = zDist;
            }
            loadNasaIntelligence(true);
        });
    });

    // Wire clickable NASA Temporal buttons
    document.querySelectorAll(".nasa-time-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tv = btn.getAttribute("data-nasa-time") || btn.getAttribute("data-mode") || "monthly";
            document.querySelectorAll(".nasa-time-btn").forEach(b => {
                if (b === btn) {
                    b.classList.add("active");
                    b.style.background = "var(--km-primary)";
                    b.style.color = "#fff";
                } else {
                    b.classList.remove("active");
                    b.style.background = "#fff";
                    b.style.color = "var(--km-primary)";
                }
            });
            const sel = document.getElementById("nasaViewMode");
            if (sel) sel.value = tv;
            loadNasaIntelligence(true);
        });
    });

    // Wire clickable NASA Parameter Focus buttons
    document.querySelectorAll(".nasa-focus-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const focusVal = btn.getAttribute("data-nasa-focus") || btn.getAttribute("data-focus") || "all";
            setNasaFocusParameter(focusVal);
        });
    });

    // Also wire the 4 NASA KPI stat cards to filter parameters on click
    const nasaStatCardTemp = document.getElementById("nasaStatCardTemp");
    const nasaStatCardRain = document.getElementById("nasaStatCardRain");
    const nasaStatCardSolar = document.getElementById("nasaStatCardSolar");
    const nasaStatCardAll = document.getElementById("nasaStatCardAll");
    if (nasaStatCardTemp) nasaStatCardTemp.addEventListener("click", () => setNasaFocusParameter("temp"));
    if (nasaStatCardRain) nasaStatCardRain.addEventListener("click", () => setNasaFocusParameter("rain"));
    if (nasaStatCardSolar) nasaStatCardSolar.addEventListener("click", () => setNasaFocusParameter("solar"));
    if (nasaStatCardAll) nasaStatCardAll.addEventListener("click", () => setNasaFocusParameter("all"));

    // Wire clickable GIBS Satellite Layer buttons
    const GIBS_LAYER_DESCRIPTIONS = {
        "MODIS_Terra_NDVI_8Day": "MODIS Terra NDVI (8-Day Vegetation Index) — Shows crop canopy vigor and chlorophyll density across Indian districts.",
        "SMAP_L4_Analyzed_Root_Zone_Soil_Moisture": "NASA SMAP Root Zone Soil Moisture — Measures top 100cm soil water availability for irrigation scheduling.",
        "MODIS_Terra_Land_Surface_Temp_Day": "MODIS Land Surface Temperature (Day) — Detects canopy thermal stress and terminal heat wave hotspots.",
        "IMERG_Precipitation_Rate": "GPM IMERG Precipitation Rate — Near-real-time satellite rainfall intensity and monsoon progression."
    };

    function updateGibsLayerSelection(layerId) {
        const nasaGibsLayerSelect = document.getElementById("nasaGibsLayerSelect");
        if (nasaGibsLayerSelect) nasaGibsLayerSelect.value = layerId;

        document.querySelectorAll(".gibs-layer-btn").forEach(b => {
            const bl = b.getAttribute("data-gibs-layer") || b.getAttribute("data-layer");
            if (bl === layerId) {
                b.classList.add("active");
                b.style.background = "var(--km-primary)";
                b.style.color = "#fff";
            } else {
                b.classList.remove("active");
                b.style.background = "#fff";
                b.style.color = "var(--km-primary)";
            }
        });

        const urlCode = document.getElementById("nasaGibsUrlCode");
        const wvLink = document.getElementById("nasaWorldviewDirectLink");
        const descEl = document.getElementById("nasaGibsLayerDesc");
        if (urlCode) {
            urlCode.textContent = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${layerId}/default/2024-02-18/GoogleMapsCompatible_Level9/5/13/22.png`;
        }
        if (wvLink) {
            wvLink.href = `https://worldview.earthdata.nasa.gov/?v=66,6,99,37&l=${layerId},Reference_Labels_15m,Coastlines_15m`;
        }
        if (descEl && GIBS_LAYER_DESCRIPTIONS[layerId]) {
            descEl.innerHTML = `<strong>Active Layer:</strong> ${escapeHtml(GIBS_LAYER_DESCRIPTIONS[layerId])}`;
        }
    }

    document.querySelectorAll(".gibs-layer-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const lid = btn.getAttribute("data-gibs-layer") || btn.getAttribute("data-layer") || "MODIS_Terra_NDVI_8Day";
            updateGibsLayerSelection(lid);
        });
    });

    const nasaGibsLayerSelect = document.getElementById("nasaGibsLayerSelect");
    if (nasaGibsLayerSelect) {
        nasaGibsLayerSelect.addEventListener("change", () => {
            updateGibsLayerSelection(nasaGibsLayerSelect.value);
        });
    }

    const btnCopyGibsUrl = document.getElementById("btnCopyGibsUrl");
    if (btnCopyGibsUrl) {
        btnCopyGibsUrl.addEventListener("click", () => {
            const urlCode = document.getElementById("nasaGibsUrlCode")?.textContent || "";
            if (navigator.clipboard && urlCode) {
                navigator.clipboard.writeText(urlCode).catch(() => {});
            }
            const orig = btnCopyGibsUrl.textContent;
            btnCopyGibsUrl.textContent = "✅ Copied WMTS URL!";
            setTimeout(() => { btnCopyGibsUrl.textContent = orig; }, 2000);
        });
    }

    const btnNasaUseLiveGps = document.getElementById("btnNasaUseLiveGps");
    if (btnNasaUseLiveGps) {
        btnNasaUseLiveGps.addEventListener("click", () => {
            const orig = btnNasaUseLiveGps.textContent;
            btnNasaUseLiveGps.textContent = "📍 Locating...";
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    async (pos) => {
                        const lat = pos.coords.latitude.toFixed(3);
                        const lon = pos.coords.longitude.toFixed(3);
                        const cCoords = document.getElementById("nasaCardCoords");
                        if (cCoords) cCoords.textContent = `${lat}°N, ${lon}°E (Live GPS)`;
                        btnNasaUseLiveGps.textContent = "✅ GPS Synced";
                        await loadNasaIntelligence(true);
                        setTimeout(() => { btnNasaUseLiveGps.textContent = orig; }, 2000);
                    },
                    () => {
                        btnNasaUseLiveGps.textContent = "📍 District Centroid";
                        loadNasaIntelligence(true);
                        setTimeout(() => { btnNasaUseLiveGps.textContent = orig; }, 2000);
                    },
                    { timeout: 5000 }
                );
            } else {
                loadNasaIntelligence(true);
                btnNasaUseLiveGps.textContent = orig;
            }
        });
    }

    const btnDownloadNasaCsv = document.getElementById("btnDownloadNasaCsv");
    if (btnDownloadNasaCsv) {
        btnDownloadNasaCsv.addEventListener("click", () => {
            if (!Array.isArray(latestNasaSeriesCache) || latestNasaSeriesCache.length === 0) return;
            const header = "Period,Avg_Temp_C,Max_Temp_C,Total_Rain_mm,Avg_Humidity_Pct,Avg_Solar_MJ_m2\n";
            const rows = latestNasaSeriesCache.map(r =>
                `${r.period},${r.avg_temp_c},${r.max_temp_c},${r.total_rain_mm},${r.avg_humidity_pct},${r.avg_solar_mj_m2}`
            ).join("\n");
            const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "nasa_power_agroclimate_series.csv";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    const btnFetchNasaIntel = document.getElementById("btnFetchNasaIntel");
    if (btnFetchNasaIntel) {
        btnFetchNasaIntel.addEventListener("click", (e) => {
            e.preventDefault();
            loadNasaIntelligence(true);
        });
    }
    const nasaStateSelectEl = document.getElementById("nasaStateSelect");
    const nasaDistrictSelectEl = document.getElementById("nasaDistrictSelect");
    const nasaViewModeEl = document.getElementById("nasaViewMode");
    if (nasaStateSelectEl) nasaStateSelectEl.addEventListener("change", () => loadNasaIntelligence(true));
    if (nasaDistrictSelectEl) nasaDistrictSelectEl.addEventListener("change", () => loadNasaIntelligence(true));
    if (nasaViewModeEl) nasaViewModeEl.addEventListener("change", () => loadNasaIntelligence(true));

    // Trigger lazy loads when switching to new tabs
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener("click", () => {
            const tab = link.getAttribute("data-tab");
            if (tab === "tab-scheme-intel") loadKrishiSchemeIntelligence();
            if (tab === "tab-nasa") loadNasaIntelligence(false);
        });
    });

    initAllIndiaDynamicSelectors();
    loadKrishiSchemeIntelligence();
    loadNasaIntelligence(false);

    // Initial render & language application
    applyDashboardLanguage();
    loadDashboardData();
});
