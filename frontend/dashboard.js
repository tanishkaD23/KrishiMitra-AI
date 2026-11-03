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

    const STATE_DISTRICTS = {
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
    };

    const STATE_HI = {
        "Uttar Pradesh": "उत्तर प्रदेश",
        "Madhya Pradesh": "मध्य प्रदेश",
        "Bihar": "बिहार",
        "Rajasthan": "राजस्थान",
        "Punjab": "पंजाब",
        "Haryana": "हरियाणा"
    };

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
            badge_6_states: "6 States • Rabi Benchmark",
            dash_banner_title: "🌾 Active Crop Phase: Tillering Stage (20–35 Days After Sowing)",
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
            notes_title: "ℹ️ Agronomic Guidance & Units",
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
            sathi_sub: "Ask your farming and government scheme questions in English or Hindi (हिंदी), anytime. 🌾",
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
            wea_7d_title: "📅 Live 7-Day District Weather Forecast",
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
            btn_add_my_farm: "Add My Farm",
            add_farm_box_title: "🌾 Add My Farm Details",
            add_farm_box_sub: "Enter your plot name, village, crop, land size in acres, soil type, and irrigation source.",
            badge_instant_save: "Saves to Your Profile",
            lbl_farm_name: "Farm / Plot Name *",
            lbl_village: "Village / Tehsil *",
            lbl_soil_type: "Soil Type",
            btn_save_farm: "Add Farm to My Holdings",
            prof_title: "Farmer Profile",
            prof_sub: "Verified profile credentials, registered landholding summary, and personal settings.",
            btn_edit_profile: "Edit Profile",
            prof_lbl_phone: "Mobile Number:",
            prof_lbl_lang: "Preferred Language:",
            prof_lbl_ekyc: "Aadhaar / eKYC Status:",
            prof_val_verified: "✅ Verified on PM-KISAN Portal",
            prof_lbl_zone: "Supported Region:",
            edit_prof_heading: "✏️ Edit Farmer Profile",
            badge_sqlite_sync: "Live Database Sync",
            lbl_farmer_name: "Farmer Full Name *",
            btn_save_profile: "Save Profile Changes"
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
            badge_6_states: "6 राज्य • रबी बेंचमार्क",
            dash_banner_title: "🌾 सक्रिय फसल अवस्था: कल्ले निकलने की अवस्था (बुवाई के 20–35 दिन बाद)",
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
            notes_title: "ℹ️ कृषि मार्गदर्शन और इकाइयां",
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
            sathi_sub: "खेती और सरकारी योजनाओं से जुड़े अपने सवाल हिंदी या अंग्रेजी में कभी भी पूछें। 🌾",
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
            wea_7d_title: "📅 आगामी 7-दिन का लाइव मौसम पूर्वानुमान",
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
            btn_add_my_farm: "नया खेत जोड़ें",
            add_farm_box_title: "🌾 नया खेत जोड़ें (Add My Farm Details)",
            add_farm_box_sub: "अपने खेत का नाम, गांव, फसल, भूमि का आकार (एकड़ में), मिट्टी का प्रकार और सिंचाई का साधन दर्ज करें।",
            badge_instant_save: "प्रोफ़ाइल में सुरक्षित",
            lbl_farm_name: "खेत / प्लॉट का नाम *",
            lbl_village: "गांव / तहसील *",
            lbl_soil_type: "मिट्टी का प्रकार",
            btn_save_farm: "मेरे खेतों में जोड़ें",
            prof_title: "किसान प्रोफ़ाइल",
            prof_sub: "प्रमाणित किसान विवरण, कुल पंजीकृत भूमि और व्यक्तिगत सेटिंग्स।",
            btn_edit_profile: "प्रोफ़ाइल संपादित करें",
            prof_lbl_phone: "मोबाइल नंबर:",
            prof_lbl_lang: "पसंदीदा भाषा:",
            prof_lbl_ekyc: "आधार / eKYC स्थिति:",
            prof_val_verified: "✅ पीएम-किसान पोर्टल पर सत्यापित",
            prof_lbl_zone: "पंजीकृत क्षेत्र:",
            edit_prof_heading: "✏️ किसान प्रोफ़ाइल संपादित करें",
            badge_sqlite_sync: "लाइव डेटाबेस सिंक",
            lbl_farmer_name: "किसान का पूरा नाम *",
            btn_save_profile: "प्रोफ़ाइल परिवर्तन सहेजें"
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
                iconSpan.textContent = state.theme === "dark" ? "☀️ लाइट" : "🌙 डार्क";
            } else {
                iconSpan.textContent = state.theme === "dark" ? "☀️ Light" : "🌙 Dark";
            }
        }
    }

    function translateSelectOptions(lang) {
        const isHi = lang === "hi";

        // Translate State Dropdowns
        ["statePicker", "predState", "filterState", "newPlotState", "editFarmerState"].forEach(id => {
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
            if (topGreeting) topGreeting.textContent = `नमस्ते, ${farmerName}! 🌾`;
            if (topSub) topSub.textContent = "यहाँ आपके खेत, मौसम और फसल उपज का संपूर्ण विवरण है।";
        } else {
            if (topGreeting) topGreeting.textContent = `Welcome back, ${farmerName}! 🌾`;
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
            console.warn("Could not fetch live dashboard data; using local benchmark values.", err);
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
                labels = historyRecords.map(r => String(r.start_year));
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
                            min: 10,
                            max: 55,
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

        // Chart 2: Multi-State Comparison Bar Chart
        const ctxComp = document.getElementById("chartCropComparison");
        if (ctxComp) {
            if (state.cropComparisonChart) {
                state.cropComparisonChart.destroy();
            }

            const barLabels = isHi
                ? ["उ.प्र.", "म.प्र.", "बिहार", "राजस्थान", "पंजाब", "हरियाणा"]
                : ["UP", "MP", "Bihar", "Rajasthan", "Punjab", "Haryana"];

            state.cropComparisonChart = new Chart(ctxComp, {
                type: "bar",
                data: {
                    labels: barLabels,
                    datasets: [
                        {
                            label: isHi ? "गेहूं (q/ha)" : "Wheat (q/ha)",
                            data: [41.5, 38.0, 33.6, 40.0, 50.4, 48.4],
                            backgroundColor: "#064E2B",
                            borderRadius: 6
                        },
                        {
                            label: isHi ? "सरसों (q/ha)" : "Mustard (q/ha)",
                            data: [18.5, 16.8, 14.6, 20.0, 19.5, 20.8],
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
                            ticks: { color: textColor, font: { family: "inherit", weight: "600", size: 11 } }
                        },
                        y: {
                            min: 0,
                            max: 55,
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

            try {
                const res = await fetch("/api/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        state: selectedState,
                        district: district,
                        crop: crop,
                        plot_acres: acres,
                        season: "Rabi",
                        sowing_window: sowing,
                        soil_type: "Alluvial (Sandy Loam)",
                        irrigation_source: irrigation,
                        seasonal_rainfall_mm: 65.0,
                        march_max_temp_c: 31.5,
                        nitrogen_kg_acre: crop === "Mustard" ? 32.0 : 48.0,
                        phosphorus_kg_acre: crop === "Mustard" ? 16.0 : 22.0,
                        potassium_kg_acre: crop === "Mustard" ? 8.0 : 15.0
                    })
                });

                const data = await res.json();
                state.stateName = selectedState;
                state.district = district;
                state.crop = crop;
                if (!state.cachedData) state.cachedData = {};
                state.cachedData.prediction = data;

                updateDynamicYieldLabels();
            } catch (err) {
                console.warn("Prediction call failed, using offline model output.", err);
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

        const nameEl = document.getElementById("profileDisplayName");
        const locEl = document.getElementById("profileDisplayLocation");
        const badgeEl = document.getElementById("profileDisplayLandBadge");
        const phoneEl = document.getElementById("profileDisplayPhone");
        const langEl = document.getElementById("profileDisplayLang");
        const zoneEl = document.getElementById("profileDisplayZone");

        const stName = isHi ? (STATE_HI[f.state] || f.state || "उत्तर प्रदेश") : (f.state || "Uttar Pradesh");

        if (nameEl) nameEl.textContent = f.name || "Tanishka";
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
        if (phoneEl) phoneEl.textContent = f.phone || "+91 98765 43210";
        if (langEl) {
            langEl.textContent = isHi
                ? "हिंदी (द्विभाषी अंग्रेजी समर्थन के साथ)"
                : "English (with Bilingual Hindi Support)";
        }
        if (zoneEl) {
            zoneEl.textContent = isHi
                ? `${stName} (बहु-राज्य रबी कृषि मंच)`
                : `${f.state || "Uttar Pradesh"} (Multi-State Rabi Platform)`;
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
        if (inVillage && document.activeElement !== inVillage) inVillage.value = f.village || "Daurala";
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
        bubble.innerHTML = `<span>${escapeHtml(text)}</span><span>👨‍🌾</span>`;
        chatBox.appendChild(bubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function appendAiTypingIndicator() {
        if (!chatBox) return null;
        const isHi = state.lang === "hi";
        const wrap = document.createElement("div");
        wrap.className = "chat-bubble-ai-wrap";
        wrap.innerHTML = `
            <div class="chat-avatar-sathi">🌾</div>
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
            <div class="chat-avatar-sathi">🌾</div>
            <div class="chat-bubble-ai">
                <div style="white-space: pre-line; line-height: 1.55;">${formattedAnswer}</div>
                ${sourcesHtml}
                <div class="chat-bubble-actions">
                    <button type="button" class="btn-speak-audio" onclick="speakText(this)">
                        <span>🔊</span>
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
        if (!state.synthesis) return;
        state.synthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = state.lang === "en" ? "en-IN" : "hi-IN";
        utterance.rate = 0.95;
        state.synthesis.speak(utterance);
    }

    // -------------------------------------------------------------------------
    // 10. SPEECH RECOGNITION (VOICE MODE)
    // -------------------------------------------------------------------------
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    const bigVoiceBtn = document.getElementById("btnBigVoiceMic");
    const inputMicBtn = document.getElementById("btnInputMic");
    const micRing = document.getElementById("micWaveRing");
    const voiceStatus = document.getElementById("voiceStatusBadge");

    if (SpeechRecognition) {
        state.recognition = new SpeechRecognition();
        state.recognition.continuous = false;
        state.recognition.interimResults = false;

        state.recognition.onstart = () => {
            state.isListening = true;
            if (micRing) micRing.style.display = "block";
            if (voiceStatus) voiceStatus.textContent = state.lang === "hi" ? "सुन रहे हैं... कृपया बोलें" : "Listening / सुन रहे हैं...";
        };

        state.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (chatInput) chatInput.value = transcript;
            sendUserMessage(transcript);
        };

        state.recognition.onerror = () => {
            state.isListening = false;
            if (micRing) micRing.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
        };

        state.recognition.onend = () => {
            state.isListening = false;
            if (micRing) micRing.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = DASHBOARD_I18N[state.lang].voice_tap_mic;
        };
    }

    function toggleMic() {
        if (!state.recognition) {
            alert(state.lang === "hi"
                ? "इस ब्राउज़र में वॉइस रिकग्निशन उपलब्ध नहीं है। कृपया अपना सवाल टाइप करें।"
                : "Speech recognition is not supported on this browser. Please type your query in the box.");
            return;
        }
        if (state.isListening) {
            state.recognition.stop();
        } else {
            const voiceLangEl = document.getElementById("voiceLangSelect");
            const activeLang = state.lang === "hi" ? "hi" : (voiceLangEl ? voiceLangEl.value : "en");
            state.recognition.lang = activeLang === "hi" ? "hi-IN" : "en-IN";
            state.recognition.start();
        }
    }

    if (bigVoiceBtn) bigVoiceBtn.addEventListener("click", toggleMic);
    if (inputMicBtn) inputMicBtn.addEventListener("click", toggleMic);

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

    // Initial render & language application
    applyDashboardLanguage();
    loadDashboardData();
});
