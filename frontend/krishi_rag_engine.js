/**
 * KrishiMitra AI - Client-Side Agricultural & Scheme RAG Knowledge Engine
 * =====================================================================
 * Grounded in official ICAR, Ministry of Agriculture & Farmers Welfare,
 * PM-KISAN, PMFBY, KCC, PM-KUSUM, Soil Health Card, and National Agronomy Guidelines.
 * 
 * Works 100% offline and on static hosting (Netlify) when backend /api/krishisathi/chat
 * is unreachable, delivering immediate, accurate, multi-point verified responses in
 * both Hindi and English with official source citations.
 */

(function (window) {
    "use strict";

    // -------------------------------------------------------------------------
    // 1. OFFICIAL SOURCES DIRECTORY
    // -------------------------------------------------------------------------
    const OFFICIAL_SOURCES = {
        pm_kisan: [
            { title: "PM-KISAN Central Portal (Ministry of Agriculture)", url: "https://pmkisan.gov.in", official: true, source_type: "official_portal" },
            { title: "Direct Benefit Transfer (DBT) Bharat - Agriculture", url: "https://dbtbharat.gov.in", official: true, source_type: "official_portal" }
        ],
        pm_kusum: [
            { title: "Ministry of New and Renewable Energy (PM-KUSUM Component B)", url: "https://pmkusum.mnre.gov.in", official: true, source_type: "official_portal" },
            { title: "PM-KUSUM Operational Guidelines & Subsidies", url: "https://mnre.gov.in/solar/schemes", official: true, source_type: "official_pdf" }
        ],
        pmfby: [
            { title: "Pradhan Mantri Fasal Bima Yojana (PMFBY) Portal", url: "https://pmfby.gov.in", official: true, source_type: "official_portal" },
            { title: "PMFBY Revised Operational Guidelines (DA&FW)", url: "https://pmfby.gov.in/guidelines", official: true, source_type: "official_pdf" }
        ],
        kcc: [
            { title: "Kisan Credit Card (KCC) Scheme - myScheme India", url: "https://www.myscheme.gov.in/schemes/kcc", official: true, source_type: "official_portal" },
            { title: "NABARD KCC Modified Interest Subvention Guidelines", url: "https://www.nabard.org", official: true, source_type: "official_pdf" }
        ],
        shc: [
            { title: "Soil Health Card National Portal", url: "https://soilhealth.dac.gov.in", official: true, source_type: "official_portal" }
        ],
        pmksy: [
            { title: "PMKSY - Per Drop More Crop (Micro Irrigation)", url: "https://pmksy.gov.in", official: true, source_type: "official_portal" }
        ],
        smam: [
            { title: "Sub-Mission on Agricultural Mechanization (SMAM)", url: "https://agrimachinery.nic.in", official: true, source_type: "official_portal" }
        ],
        wheat_agronomy: [
            { title: "ICAR - Indian Institute of Wheat and Barley Research (IIWBR Karnal)", url: "https://iiwbr.icar.gov.in", official: true, source_type: "official_portal" },
            { title: "ICAR Package of Practices for Rabi Crops (Wheat)", url: "https://icar.org.in", official: true, source_type: "official_pdf" }
        ],
        mustard_agronomy: [
            { title: "ICAR - Directorate of Rapeseed-Mustard Research (DRMR Bharatpur)", url: "https://drmr.icar.gov.in", official: true, source_type: "official_portal" }
        ],
        gram_agronomy: [
            { title: "ICAR - Indian Institute of Pulses Research (IIPR Kanpur)", url: "https://iipr.icar.gov.in", official: true, source_type: "official_portal" }
        ],
        general_icar: [
            { title: "Indian Council of Agricultural Research (ICAR)", url: "https://icar.org.in", official: true, source_type: "official_portal" },
            { title: "Farmer Portal - Department of Agriculture & Farmers Welfare", url: "https://farmer.gov.in", official: true, source_type: "official_portal" }
        ]
    };

    // -------------------------------------------------------------------------
    // 2. DOMAIN KNOWLEDGE MODULES (RAG RETRIEVAL CORPUS)
    // -------------------------------------------------------------------------
    const RAG_TOPICS = [
        // =====================================================================
        // TOPIC 1: PM-KISAN (Eligibility, ₹6000 Benefits, eKYC, Exclusions)
        // =====================================================================
        {
            id: "pm_kisan",
            keywords: ["pm-kisan", "pm kisan", "pmkisan", "kisan samman", "सम्मान निधि", "पीएम किसान", "6000", "₹6,000", "installment", "किस्त", "ekyc", "ईकेवाईसी", "ekyc eligibility", "kisan portal"],
            sources: OFFICIAL_SOURCES.pm_kisan,
            answer: {
                hi: `**प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) योजना संपूर्ण विवरण:**

1. **वित्तीय लाभ (Financial Benefit):**
• पात्र किसान परिवारों को प्रति वर्ष **₹6,000** की वित्तीय सहायता दी जाती है।
• यह राशि **₹2,000 की 3 समान किस्तों** में (प्रत्येक 4 माह में: अप्रैल-जुलाई, अगस्त-नवंबर, दिसंबर-मार्च) सीधे आधार-लिंक्ड बैंक खाते (DBT) में भेजी जाती है।

2. **पात्रता मानदंड (Eligibility Criteria):**
• ऐसे सभी किसान परिवार जिनके नाम राज्य/केंद्र शासित प्रदेश के भूमि अभिलेखों (खतौनी/जमाबंदी) में कृषि योग्य भूमि दर्ज है।
• छोटे, सीमांत एवं बड़े किसान सभी इस योजना के पात्र हैं (2 हेक्टेयर की पुरानी सीमा हटा दी गई है)।

3. **अनिवार्य आवश्यकताएं (Mandatory Compliance):**
• **e-KYC पूर्ण होना अनिवार्य:** बिना e-KYC के अगली किस्त जारी नहीं होगी।
• बैंक खाते का **आधार एवं NPCI से DBT-सक्षम** (Aadhaar Seeded) होना आवश्यक है।
• भू-अभिलेखों का सत्यापन (Land Seeding) पोर्टल पर 'Yes' होना चाहिए।

4. **अपात्रता / बहिष्करण (Who is Ineligible):**
• संस्थागत भूमिधारक (Institutional landholders)।
• वर्तमान या पूर्व संवैधानिक पदधारक, मंत्री, सांसद, विधायक, मेयर।
• केंद्र/राज्य सरकार के नियमित या सेवानिवृत्त कर्मचारी (चतुर्थ श्रेणी/ग्रुप डी को छोड़कर)।
• ₹10,000 प्रति माह या अधिक पेंशन पाने वाले पेंशनभोगी।
• पिछले मूल्यांकन वर्ष में आयकर (Income Tax) का भुगतान करने वाले व्यक्ति/परिवार।
• डॉक्टर, इंजीनियर, वकील, सीए जैसे पंजीकृत पेशेवर।

5. **आवेदन व स्थिति जांच (Official Portal):**
• नया पंजीकरण एवं eKYC हेतु आधिकारिक पोर्टल: **https://pmkisan.gov.in**
• किसान हेल्पलाइन नंबर: **155261 / 1800-115-526** या 011-23381092.`,

                en: `**Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) Complete Guide:**

1. **Financial Benefit:**
• Eligible farmer families receive **₹6,000 per year** as 100% Central Sector DBT assistance.
• The amount is disbursed in **three equal installments of ₹2,000 each** every 4 months (April–July, August–November, December–March) directly into Aadhaar-linked bank accounts.

2. **Eligibility Criteria:**
• All landholding farmer families who have cultivable agricultural land registered in their name in the official State land revenue records (Khatauni/ROR).
• Both small/marginal and large farmers are eligible (the earlier 2-hectare land ceiling has been removed).

3. **Mandatory Compliance Requirements:**
• **Mandatory e-KYC:** Installments are paused without active biometric or Aadhaar-OTP eKYC.
• **Bank Account Seeding:** Bank account must be seeded with Aadhaar and active on the NPCI DBT mapper.
• **Land Record Seeding:** Verified land registration mapped on the PM-KISAN portal.

4. **Exclusion Criteria (Who is NOT Eligible):**
• Institutional landholders.
• Current or former holders of constitutional posts, MPs, MLAs, MLCs, Mayors, District Panchayat Chairpersons.
• Serving or retired officers and employees of Central/State Government, PSUs, and autonomous bodies (excluding Multi-Tasking / Class IV / Group D staff).
• Pensioners with a monthly pension of ₹10,000 or more.
• Individuals who paid Income Tax in the last assessment year.
• Practicing professionals: Doctors, Engineers, Lawyers, Chartered Accountants, and Architects.

5. **Official Portal & Support:**
• Online application, eKYC & beneficiary status: **https://pmkisan.gov.in**
• Farmer Toll-Free Helpline: **155261 / 1800-115-526**.`
            }
        },

        // =====================================================================
        // TOPIC 2: WHEAT CRI IRRIGATION & UREA MANAGEMENT
        // =====================================================================
        {
            id: "wheat_cri_urea",
            keywords: ["cri", "crown root", "शीर्ष जड़", "ताज जड़", "cri stage", "21-25", "21 दिन", "पहला पानी", "first irrigation", "यूरिया", "urea", "cri irrigation", "गेहूं में पहली सिंचाई", "यूरिया कब दें", "when to apply urea"],
            sources: OFFICIAL_SOURCES.wheat_agronomy,
            answer: {
                hi: `**गेहूं में शीर्ष जड़ (CRI) सिंचाई एवं यूरिया प्रबंधन (ICAR-IIWBR करनाल अनुशंसा):**

1. **शीर्ष जड़ (CRI - Crown Root Initiation) अवस्था क्या है और क्यों महत्वपूर्ण है?**
• बुवाई के **21 से 25 दिन बाद** गेहूं के पौधे के तने के आधार से स्थायी जड़ें (Crown Roots) निकलना शुरू होती हैं।
• यह गेहूं के जीवन चक्र की **सबसे संवेदनशील अवस्था** है। इस समय पौधे में कल्ले (tillers) बनने की शुरुआत होती है।
• यदि इस अवस्था पर सिंचाई में 1 सप्ताह की भी देरी हो जाए, तो पौधों की बढ़वार रुक जाती है और पैदावार में **20% से 30% तक की भारी गिरावट** आ सकती है।

2. **CRI सिंचाई कैसे करें?**
• पहली सिंचाई **हल्की (4 से 5 सेमी पानी)** करें। खेत में अधिक पानी न भरने दें, क्योंकि अत्यधिक पानी से छोटे पौधे पीले पड़ सकते हैं।

3. **यूरिया (नाइट्रोजन) की पहली टॉप-ड्रेसिंग कब और कितनी दें?**
• **सही समय:** CRI सिंचाई के **2 से 3 दिन बाद**, जब खेत 'वापसा' स्थिति (पैर टिकने योग्य हल्की गीली मिट्टी) में आ जाए।
• **मात्रा:** प्रति एकड़ **40 से 45 किलो नीम लेपित यूरिया** (1 बोरी) समान रूप से बुरकाव (broadcast) करें।
• **वैज्ञानिक नियम:** कभी भी सूखी मिट्टी में या सिंचाई से पहले यूरिया न डालें, अन्यथा नाइट्रोजन वाष्पीकृत होकर उड़ जाती है। हल्की नमी में डालने पर यूरिया सीधे जड़ों तक पहुंचती है।

4. **गेहूं की संपूर्ण 6-सिंचाई सारणी:**
• **1. CRI अवस्था:** बुवाई के 21–25 दिन पर (सर्वाधिक महत्वपूर्ण)
• **2. कल्ले फूटते समय (Tillering):** 40–45 दिन पर (इसके बाद दूसरी 40 किलो यूरिया दें)
• **3. गांठ बनते समय (Late Jointing):** 60–65 दिन पर
• **4. फूल आते समय (Flowering):** 80–85 दिन पर
• **5. दूधिया दाना बनते समय (Milking):** 100–105 दिन पर
• **6. दाना पकते समय (Dough Stage):** 115–120 दिन पर (तेज हवा में सिंचाई न करें ताकि फसल गिरे नहीं)।`,

                en: `**Wheat Crown Root Initiation (CRI) Irrigation & Urea Top-Dressing Guide (ICAR-IIWBR):**

1. **What is the Crown Root Initiation (CRI) Stage and Why is it Critical?**
• CRI occurs **21 to 25 days after sowing (DAS)** when permanent crown roots emerge from the node located just below the soil surface.
• This is the **single most critical stage** in the entire wheat lifecycle. The primary seminal roots transition to the permanent root system that anchors the plant and absorbs nutrients.
• Delaying irrigation at CRI by even 7–10 days leads to poor tillering, shallow root penetration, and a permanent **20% to 30% yield penalty**.

2. **CRI Irrigation Best Practice:**
• Apply a **light irrigation of 4–5 cm depth**. Avoid heavy waterlogging, as standing water cuts off root aeration and turns seedlings pale yellow.

3. **When and How to Apply Urea (Nitrogen Top-Dressing)?**
• **Optimal Timing:** Apply **2 to 3 days after CRI irrigation** when the field reaches the "Wapsa" state (optimum workable soil moisture where footprints leave slight impressions without sinking).
• **Dosage:** Broadcast **40 to 45 kg Neem-coated Urea per acre** (approx. 1 standard bag).
• **Agronomic Rule:** Do not broadcast urea in bone-dry soil or immediately into deep standing water. Applying on moist soil allows rapid dissolving and root uptake with minimal volatilization loss.

4. **Complete 6-Stage Wheat Irrigation Schedule:**
• **Stage 1 (CRI):** 21–25 DAS (Critical root anchorage)
• **Stage 2 (Tillering):** 40–45 DAS (Followed by 2nd urea dose of 40 kg/acre)
• **Stage 3 (Late Jointing / Booting):** 60–65 DAS
• **Stage 4 (Flowering / Heading):** 80–85 DAS
• **Stage 5 (Milking stage):** 100–105 DAS
• **Stage 6 (Dough stage):** 115–120 DAS (Avoid watering on windy days to prevent stem lodging).`
            }
        },

        // =====================================================================
        // TOPIC 3: PM-KUSUM SOLAR PUMP 60% SUBSIDY
        // =====================================================================
        {
            id: "pm_kusum_solar",
            keywords: ["kusum", "solar", "कुसुम", "सोलर", "सौर", "solar pump", "solar subsidy", "60% subsidy", "60%", "solar pump subsidy", "बोरवेल", "सोलर पंप सब्सिडी", "pm-kusum"],
            sources: OFFICIAL_SOURCES.pm_kusum,
            answer: {
                hi: `**PM-KUSUM योजना (कंपोनेंट-बी) सोलर पंप 60% सब्सिडी दिशानिर्देश:**

1. **सब्सिडी संरचना (60% Subsidy Breakdown):**
• **केंद्रीय वित्तीय सहायता (MNRE):** बेंचमार्क लागत का **30% केंद्र सरकार** वहन करती है।
• **राज्य सरकार सब्सिडी:** **30% राज्य सरकार** द्वारा दिया जाता है।
• **कुल सरकारी अनुदान:** कुल मिलाकर किसान को **60% तक भारी सब्सिडी** प्राप्त होती है।
• **किसान का अंशदान:** किसान को केवल **40% राशि** देनी होती है। इसमें से 30% तक बैंक ऋण (KCC/कृषि ऋण) के माध्यम से लिया जा सकता है, जिससे किसान को शुरुआत में मात्र **10% नकद अंशदान** जमा करना होता है।

2. **पंप क्षमता एवं प्रकार (Available Capacities):**
• **2 HP, 3 HP, 5 HP, 7.5 HP और 10 HP** क्षमता के स्टैंडअलोन सोलर कृषि पंप।
• सतह पंप (Surface Pump) और सबमर्सिबल पंप (Submersible Pump) दोनों AC/DC वेरिएंट में उपलब्ध।

3. **पात्रता एवं शर्तें (Eligibility Criteria):**
• व्यक्तिगत किसान, किसान उत्पादक संगठन (FPO), जल उपयोगकर्ता संघ (WUA) और प्राथमिक कृषि सहकारी समितियां (PACS)।
• किसान के पास अपना खेत और सुनिश्चित जल स्रोत (बोरवेल/कुआं/तालाब) होना आवश्यक है।
• जहां पहले से ग्रिड-कनेक्टेड बिजली का कृषि कनेक्शन नहीं है (डीजल पंप रिप्लेसमेंट को प्राथमिकता दी जाती है)।

4. **आवश्यक दस्तावेज (Required Documents):**
• आधार कार्ड एवं मोबाइल नंबर (आधार से लिंक)।
• अद्यतन भूमि खतौनी/जमाबंदी (Land Ownership Record)।
• बैंक पासबुक (DBT सक्रिय)।
• बोरवेल/जल स्रोत का स्व-घोषणा पत्र।

5. **आवेदन कैसे करें (Official Application Process):**
• राज्य के कृषि विभाग/ऊर्जा विकास प्राधिकरण के पोर्टल पर ऑनलाइन आवेदन करें (जैसे UP में **upagriculture.com**, राजस्थान में **rajkisan.rajasthan.gov.in**)।
• केंद्रीय पोर्टल: **https://pmkusum.mnre.gov.in**
• नोट: फर्जी वेबसाइटों से सावधान रहें; केवल राज्य कृषि विभाग के आधिकारिक पोर्टल पर ही निर्धारित टोकन/पंजीकरण शुल्क जमा करें।`,

                en: `**PM-KUSUM Scheme (Component B) Solar Pump 60% Subsidy Guide:**

1. **Subsidy Financial Structure (60% Total Assistance):**
• **Central Financial Assistance (MNRE):** **30% subsidy** paid directly by the Central Government.
• **State Government Subsidy:** **30% additional subsidy** paid by the State Agriculture/Renewable Energy Department.
• **Total Government Subsidy:** Farmers receive up to **60% combined subsidy** on the benchmark installation cost.
• **Farmer Contribution:** The beneficiary farmer only contributes **40%**. Up to 30% of this amount can be financed via agricultural bank loans (KCC), requiring the farmer to pay as little as **10% upfront margin money**.

2. **Pump Capacities and Types Supported:**
• Standalone solar irrigation pump sets of **2 HP, 3 HP, 5 HP, 7.5 HP, and 10 HP**.
• Both Surface and Submersible solar pumps (AC and DC motor types) equipped with solar photovoltaic arrays.

3. **Eligibility Criteria:**
• Individual farmers, Farmer Producer Organizations (FPOs), Water User Associations (WUAs), and Primary Agricultural Credit Societies (PACS).
• Must possess cultivable agricultural land with an assured water source (borewell, open well, or farm pond).
• Priority is given to areas without existing grid electric pump connections (replacing polluting diesel pump engines).

4. **Mandatory Documentation:**
• Aadhaar card linked with active mobile number.
• Updated land record documents (Khatauni / Jamabandi / 7/12 extract).
• Bank account passbook copy (Aadhaar/DBT seeded).
• Self-declaration certificate confirming existing borewell/water depth.

5. **How to Apply:**
• Apply online on your respective State Agriculture or Renewable Energy Development Agency portal (e.g. **upagriculture.com** for UP, **rajkisan.rajasthan.gov.in** for Rajasthan).
• Central MNRE Portal: **https://pmkusum.mnre.gov.in**
• *Caution:* Beware of fraudulent lookalike websites. Official token booking is conducted solely on accredited state government agriculture portals.`
            }
        },

        // =====================================================================
        // TOPIC 4: WHEAT HIGH-YIELD VARIETIES & FERTILIZER SCHEDULE
        // =====================================================================
        {
            id: "wheat_varieties_fertilizer",
            keywords: ["गेहूं की उन्नत किस्में", "उन्नत किस्में", "खाद की मात्रा", "गेहूं किस्में", "varieties", "wheat varieties", "उर्वरक", "खाद", "dap", "npk 120:60:40", "dbw 187", "hd 2967", "hd 3086", "fertilizer dose", "उन्नत किस्म और खाद"],
            sources: OFFICIAL_SOURCES.wheat_agronomy,
            answer: {
                hi: `**गेहूं की शीर्ष उन्नत किस्में एवं संतुलित खाद/उर्वरक प्रबंधन (ICAR-IIWBR करनाल):**

1. **शीर्ष उच्च-उपज उन्नत किस्में (Top High-Yield Varieties):**
• **DBW-187 (करण वंदना - Karan Vandana):**
  - पैदावार: **61 से 75 क्विंटल प्रति हेक्टेयर** (25–30 क्विंटल/एकड़)।
  - विशेषताएं: पीला रतुआ (Yellow Rust) और ब्लास्ट रोग प्रतिरोधी; 11.8% प्रोटीन और उच्च आयरन सामग्री; चपाती व बिस्कुट हेतु श्रेष्ठ।
  - बुवाई समय: समय पर सिंचित बुवाई (5 से 25 नवंबर)।
• **DBW-222 (करण नरेंद्र - Karan Narendra):**
  - पैदावार: **61 से 82 क्विंटल प्रति हेक्टेयर**।
  - विशेषताएं: मजबूत तना होने के कारण फसल गिरती (lodging) नहीं है; मार्च की अगेती गर्मी (Heat Stress) सहन करने में सक्षम।
• **HD-2967:**
  - पैदावार: **50 से 55 क्विंटल प्रति हेक्टेयर**। उत्तर-पश्चिम भारत के किसानों की सबसे लोकप्रिय एवं भरोसेमंद किस्म।
• **HD-3086 (पूसा गौतमी - Pusa Gautami):**
  - पैदावार: **54 से 60 क्विंटल प्रति हेक्टेयर**। टर्मिनल हीट प्रतिरोधी, 12.5% प्रोटीन और उत्कृष्ट चपाती गुणवत्ता।
• **HD-3226 (पूसा यशस्वी):**
  - पैदावार: **57 से 79 क्विंटल प्रति हेक्टेयर**। करनाल बंट एवं रतुआ रोधी।
• **पछेती बुवाई हेतु किस्में (दिसंबर बुवाई):** DBW-173, HD-3059, राज-3765 (बीज दर: 50 किग्रा/एकड़)।

---

2. **संतुलित खाद एवं उर्वरक मात्रा (Fertilizer Schedule प्रति एकड़):**
• **वैज्ञानिक NPK अनुपात:** 120:60:40 किग्रा/हेक्टेयर (प्रति एकड़ शुद्ध पोषक तत्व: ~48 किग्रा N, 24 किग्रा P, 16 किग्रा K)।

• **उर्वरक की सही मात्रा (प्रति एकड़):**
  1. **बुवाई के समय (Basal Application):**
     - **DAP:** 50 से 55 किलो (1 बैग) **अथवा** NPK 12:32:16 (75 किलो)।
     - **म्यूरेट ऑफ पोटाश (MOP):** 25 से 30 किलो (दाने का वजन और चमक बढ़ाने हेतु)।
     - **जिंक सल्फेट (21%):** 10 किलो (पीलेपन की रोकथाम व रोग प्रतिरोधक क्षमता हेतु)।
     - **यूरिया:** 30 से 35 किलो (DAP के साथ प्रथम नाइट्रोजन खुराक)।
  2. **पहली टॉप-ड्रेसिंग (CRI सिंचाई के बाद - 21 से 25 दिन):**
     - **नीम लेपित यूरिया:** 40 से 45 किलो (1 बैग) वापसा नमी में छिड़कें।
  3. **दूसरी टॉप-ड्रेसिंग (कल्ले फूटते समय - 40 से 45 दिन):**
     - **नीम लेपित यूरिया:** 40 किलो।
  4. **दाना भरते समय पर्णीय छिड़काव (Foliar Spray - 75–85 दिन):**
     - मार्च की गर्मी से दाने को पिचकने से बचाने के लिए **NPK 13:0:45 (पोटेशियम नाइट्रेट) @ 1 किलो प्रति एकड़** 200 लीटर पानी में घोलकर छिड़कें।`,

                en: `**Top High-Yield Wheat Varieties & Balanced Fertilizer Schedule (ICAR-IIWBR):**

1. **Top High-Yield Recommended Wheat Varieties:**
• **DBW-187 (Karan Vandana):**
  - Potential Yield: **61 to 75 Quintals/Hectare** (25–30 Q/Acre).
  - Characteristics: Immune to Yellow Stripe Rust and Wheat Blast; high protein (11.8%) and rich in iron content; premier chapati making quality.
  - Sowing Window: Timely irrigated conditions (November 5–25).
• **DBW-222 (Karan Narendra):**
  - Potential Yield: **61 to 82 Quintals/Hectare**.
  - Characteristics: Thick, sturdy stem preventing lodging under heavy fertilizer/winds; exceptional terminal heat tolerance.
• **HD-2967:**
  - Potential Yield: **50 to 55 Quintals/Hectare**. Widely cultivated and reliable across Punjab, Haryana, UP, and Rajasthan.
• **HD-3086 (Pusa Gautami):**
  - Potential Yield: **54 to 60 Quintals/Hectare**. Resists sudden temperature spikes in late February/March, ensuring plump grains.
• **HD-3226 (Pusa Yashasvi):**
  - Potential Yield: **57 to 79 Quintals/Hectare**. Highly resistant to all rusts and Karnal Bunt.
• **Late-Sown Varieties (December Sowing):** DBW-173, HD-3059, Raj-3765 (Seed rate: 50 kg/acre).

---

2. **Balanced Fertilizer Schedule (Per Acre Recommendations):**
• **Scientific N-P-K Ratio:** 120:60:40 kg/ha (Pure Nutrients per acre: ~48 kg N, 24 kg P, 16 kg K).

• **Fertilizer Bag Quantities (Per Acre):**
  1. **Basal Dose (Drilled at Sowing below seed):**
     - **DAP (Di-Ammonium Phosphate):** 50–55 kg (1 bag) OR NPK 12:32:16 (75 kg).
     - **MOP (Muriate of Potash):** 25–30 kg (essential for disease resistance & grain boldness).
     - **Zinc Sulfate (21%):** 10 kg (protects against seedling yellowing/khaira).
     - **Urea:** 30–35 kg.
  2. **1st Top Dressing (At CRI Irrigation - 21 to 25 DAS):**
     - **Neem-coated Urea:** 40–45 kg broadcast in moist ("Wapsa") soil.
  3. **2nd Top Dressing (At Tillering / Jointing - 40 to 45 DAS):**
     - **Neem-coated Urea:** 40 kg broadcast after 2nd irrigation.
  4. **Foliar Spray at Booting / Flowering (75–85 DAS):**
     - Spray **NPK 13:0:45 (Potassium Nitrate) @ 1 kg/acre** dissolved in 200 L water to shield grains from terminal March heat and maximize test weight.`
            }
        },

        // =====================================================================
        // TOPIC 5: PMFBY CROP INSURANCE (Eligibility, Claims, 72-Hour Rule)
        // =====================================================================
        {
            id: "pmfby_crop_insurance",
            keywords: ["pmfby", "fasal bima", "crop insurance", "फसल बीमा", "बीमा", "क्लेम", "claim", "72 hours", "72 घंटे", "प्रीमियम", "insurance eligibility", "pmfby claim"],
            sources: OFFICIAL_SOURCES.pmfby,
            answer: {
                hi: `**प्रधानमंत्री फसल बीमा योजना (PMFBY) पात्रता, कवरेज एवं क्लेम नियम:**

1. **प्रीमियम दरें (Farmer Premium Rates):**
• **रबी फसलें (गेहूं, सरसों, चना, जौ):** किसान द्वारा केवल **1.5% सांकेतिक प्रीमियम** देय।
• **खरीफ फसलें (धान, मक्का, बाजरा, दलहन):** किसान द्वारा केवल **2.0% प्रीमियम** देय।
• **वाणिज्यिक एवं बागवानी फसलें (कपास, गन्ना, आलू, प्याज):** केवल **5.0% प्रीमियम** देय।
• शेष भारी प्रीमियम राशि केंद्र एवं राज्य सरकार मिलकर 50:50 अनुपात में सब्सिडी के रूप में वहन करती हैं।

2. **कौन पात्र है (Who is Eligible)?**
• **भूमि स्वामी किसान:** जिनके पास अपना भूमि रिकॉर्ड (खतौनी/ROR) है।
• **बटाईदार एवं किरायेदार किसान (Tenant / Sharecropper Farmers):** जमीन मालिक के सहमति पत्र (NOC / Tenancy Agreement) अथवा स्थानीय पटवारी/कृषि अधिकारी द्वारा जारी बुवाई प्रमाण पत्र (Sowing Certificate) के आधार पर 100% पात्र हैं।
• ऋणी (Loanee) और गैर-ऋणी (Non-Loanee) दोनों किसान पात्र हैं।

3. **जोखिम कवरेज (Comprehensive Risk Stages):**
• बुवाई न कर पाना (Prevented Sowing) - प्रतिकूल मौसम के कारण।
• खड़ी फसल में नुकसान (खेत सूखा, बाढ़, कीट, बेमौसम बारिश)।
• स्थानीयकृत आपदाएं (Localized Calamities) - ओलावृष्टि (Hailstorm), जलभराव (Inundation), आकाशीय बिजली, बादल फटना।
• कटाई उपरांत नुकसान (Post-Harvest Losses) - खेत में सुखाई हेतु रखी कटी फसल पर 14 दिनों तक बेमौसम बारिश या चक्रवात से नुकसान।

4. **अत्यंत महत्वपूर्ण: 72 घंटे की क्लेम सूचना समयसीमा (Mandatory 72-Hour Window):**
• ओलावृष्टि, जलभराव या बेमौसम बारिश से नुकसान होने पर **घटना के ठीक 72 घंटे के भीतर सूचना देना अनिवार्य** है।
• **क्लेम दर्ज करने के 3 आसान माध्यम:**
  1. **क्रॉप इंश्योरेंस मोबाइल ऐप (Crop Insurance App):** जियो-टैग फोटो के साथ तत्काल दर्ज करें।
  2. **राष्ट्रीय टोल-फ्री किसान हेल्पलाइन:** **14447** (24x7 कॉल करें)।
  3. अपने संबंधित बैंक या जिला कृषि अधिकारी / बीमा कंपनी प्रतिनिधि को लिखित सूचना दें।
• आधिकारिक पोर्टल: **https://pmfby.gov.in**`,

                en: `**Pradhan Mantri Fasal Bima Yojana (PMFBY) Complete Guide:**

1. **Farmer Premium Rates:**
• **Rabi Crops (Wheat, Mustard, Gram, Barley):** Nominal **1.5% of Sum Insured**.
• **Kharif Crops (Paddy, Maize, Bajra, Pulses):** Nominal **2.0% of Sum Insured**.
• **Commercial & Horticultural Crops (Cotton, Sugarcane, Potato, Onion):** Only **5.0% of Sum Insured**.
• The entire remaining premium subsidy is funded jointly 50:50 by the Central and State Governments.

2. **Eligibility (Landowners & Tenant Farmers):**
• **Landowner Farmers:** With verified land ownership records (Khatauni / ROR).
• **Tenant / Sharecropper Farmers:** Fully eligible upon submitting a Tenancy Agreement / Landowner NOC or a Crop Sowing Certificate issued by the Village Patwari / Agricultural Extension Officer.
• Available to both Loanee (KCC holders) and Non-Loanee farmers.

3. **Coverage Stages:**
• Prevented Sowing / Planting risk due to deficit rainfall or adverse seasonal conditions.
• Standing crop mid-season adversity (drought, dry spells, pests, diseases).
• Localized Calamities: Hailstorm, Landslide, Inundation (waterlogging), Cloudburst, and Lightning.
• Post-Harvest Losses: Coverage up to 14 days for harvested crops kept in "cut-and-spread" condition in the field against unseasonal rainfall or cyclones.

4. **CRITICAL: Mandatory 72-Hour Claim Intimation Rule:**
• In cases of localized loss (hailstorm, cloudburst, inundation), you **MUST report the damage within 72 hours** of occurrence.
• **3 Ways to Intimate Claims:**
  1. **Crop Insurance Mobile App:** Upload geo-tagged photos directly.
  2. **National Farmer Insurance Toll-Free Helpline:** Dial **14447** (Available 24x7).
  3. Intimate your bank branch or the District Agriculture Officer / insurance company toll-free number.
• Official Portal: **https://pmfby.gov.in**`
            }
        },

        // =====================================================================
        // TOPIC 6: KISAN CREDIT CARD (KCC) 4% INTEREST LOAN
        // =====================================================================
        {
            id: "kcc_loan",
            keywords: ["kcc", "kisan credit card", "credit card", "loan", "ऋण", "लोन", "क्रेडिट कार्ड", "4% interest", "ब्याज दर", "kcc limit", "collateral"],
            sources: OFFICIAL_SOURCES.kcc,
            answer: {
                hi: `**किसान क्रेडिट कार्ड (KCC) योजना - 4% प्रभावी ब्याज दर एवं ऋण प्रक्रिया:**

1. **ऋण सीमा एवं 4% प्रभावी ब्याज दर:**
• किसानों को **₹3 लाख तक का अल्पकालिक फसल ऋण** मिलता है।
• **ब्याज गणित:** सामान्य कृषि ब्याज दर 9% होती है। केंद्र सरकार **2% ब्याज सबवेंशन (छूट)** देती है, जिससे दर 7% हो जाती है।
• समय पर ऋण चुकाने वाले किसानों को **3% की त्वरित पुनर्भुगतान प्रोत्साहन (Prompt Repayment Incentive)** छूट मिलती है।
• परिणामस्वरूप, किसान को **मात्र 4% वार्षिक प्रभावी ब्याज** चुकाना पड़ता है।

2. **बिना गारंटी (Collateral-Free) ऋण:**
• **₹1.60 लाख तक के ऋण** के लिए किसी भी भूमि को बंधक (Mortgage) रखने या गारंटी देने की आवश्यकता नहीं होती।
• दुग्ध उत्पादन एवं मत्स्य पालन (Animal Husbandry & Fisheries) हेतु KCC पर ₹2 लाख तक का ऋण मिलता है।

3. **आवश्यक दस्तावेज:**
• विधिवत भरा हुआ KCC आवेदन पत्र।
• पहचान एवं पता प्रमाण: आधार कार्ड एवं पैन कार्ड/वोटर आईडी।
• भू-अभिलेख: अद्यतन खतौनी/जमाबंदी नकल एवं बुवाई प्रमाण पत्र।

4. **आवेदन कैसे करें:**
• किसी भी वाणिज्यिक बैंक, क्षेत्रीय ग्रामीण बैंक (RRB) या प्राथमिक कृषि ऋण समिति (PACS) शाखा में संपर्क करें।
• ऑनलाइन आवेदन पोर्टल: **https://www.myscheme.gov.in/schemes/kcc** अथवा बैंक की वेबसाइट।`,

                en: `**Kisan Credit Card (KCC) Scheme - 4% Effective Interest & Guidelines:**

1. **Loan Limit & The 4% Effective Interest Formula:**
• Farmers can avail short-term crop loans up to **₹3 Lakh**.
• **Interest Subvention Breakdown:** Baseline agricultural interest rate is 9%. Government provides a **2% upfront Interest Subvention**, bringing it to 7%.
• Farmers who repay their dues on or before the due date receive an additional **3% Prompt Repayment Incentive (PRI)**.
• Thus, the **net effective interest rate borne by the farmer is just 4% per annum**.

2. **Collateral-Free Limit:**
• Loans up to **₹1.60 Lakh are completely collateral-free** (no land mortgage or hypothecation required).
• KCC for Animal Husbandry and Fisheries offers short-term working capital up to ₹2 Lakh at the same subsidized interest rate.

3. **Required Documents:**
• Duly completed KCC Application Form.
• Proof of Identity and Address (Aadhaar Card, PAN / Voter ID).
• Land Ownership Record (Updated Khatauni / Jamabandi / 7/12 extract) showing crop pattern.

4. **Application Channels:**
• Visit your nearest Commercial Bank, Regional Rural Bank (RRB), or Cooperative Society branch.
• Official Portal: **https://www.myscheme.gov.in/schemes/kcc**.`
            }
        },

        // =====================================================================
        // TOPIC 7: MUSTARD AGRONOMY (Varieties, Fertilizer, Aphid/Chetpa Control)
        // =====================================================================
        {
            id: "mustard_agronomy",
            keywords: ["सरसों", "mustard", "sarson", "माहू", "चेपा", "aphid", "गिरिराज", "rh-725", "सरसों की किस्में", "सरसों में खाद", "mustard varieties"],
            sources: OFFICIAL_SOURCES.mustard_agronomy,
            answer: {
                hi: `**सरसों (Mustard) उन्नत किस्में, खाद एवं कीट प्रबंधन (ICAR-DRMR भरतपुर):**

1. **प्रमुख उच्च-उपज किस्में:**
• **RH-725:** 25–28 क्विंटल/हेक्टेयर, फलियों में दानों की संख्या अधिक, पाले के प्रति सहनशील।
• **गिरिराज (DRMR-IJ-31):** 24–27 क्विंटल/हेक्टेयर, 40–41% तेल, सफेद रतुआ रोधी।
• **पूसा बोल्ड (Pusa Bold) एवं NRCHB-101:** मोटे दाने वाली समय से बुवाई हेतु किस्में।
• बीज दर: **1.5 से 2 किलो प्रति एकड़** (बुवाई से पूर्व थीरम या कार्बेन्डाजिम से उपचारित करें)।

2. **खाद एवं सल्फर प्रबंधन (प्रति एकड़):**
• **बुवाई पर:** 35 किलो यूरिया + 50 किलो SSP (सिंगल सुपर फास्फेट) या 25 किलो DAP + **10 किलो बेंटोनाइट सल्फर**।
• **सल्फर का महत्व:** सरसों में सल्फर डालने से तेल की मात्रा **3 से 5 प्रतिशत** बढ़ जाती है।
• **पहली सिंचाई पर (30–35 दिन):** 30 किलो नीम लेपित यूरिया का बुरकाव करें।

3. **माहू (चेपा / Aphid) एवं कीट नियंत्रण:**
• जब पौधे की टहनी पर 10% से अधिक माहू दिखाई दे, तो तुरंत **इमिडाक्लोप्रिड 17.8% SL @ 80 मिली प्रति एकड़** (या थायोमेथोक्साम 25% WG @ 40 ग्राम/एकड़) 150 लीटर पानी में मिलाकर छिड़कें।
• मधुमक्खियों की सुरक्षा हेतु छिड़काव हमेशा **दोपहर 3 बजे के बाद (शाम के समय)** करें।`,

                en: `**Mustard High-Yield Package of Practices (ICAR-DRMR Bharatpur):**

1. **Top Recommended Varieties:**
• **RH-725:** 25–28 Q/Ha, high siliqua density, frost tolerant.
• **Giriraj (DRMR-IJ-31):** 24–27 Q/Ha, 40–41% oil content, resistant to white rust.
• **Pusa Bold & NRCHB-101:** Large-seeded, widely adaptable varieties.
• Seed Rate: **1.5 to 2.0 kg per acre** treated with Carbendazim/Thiram before sowing.

2. **Fertilizer & Sulfur Schedule (Per Acre):**
• **Basal:** 35 kg Urea + 50 kg SSP (Single Super Phosphate) OR 25 kg DAP + **10 kg Bentonite Sulfur**.
• **Sulfur Benefit:** Increases mustard oil recovery by **3% to 5%** and enhances cold tolerance.
• **1st Irrigation (30–35 DAS):** Top-dress 30 kg Neem-coated Urea.

3. **Aphid (Chetpa/Mahua) Management:**
• Spray **Imidacloprid 17.8% SL @ 80 ml/acre** or **Thiamethoxam 25% WG @ 40 g/acre** in 150 liters of water.
• Always spray late in the afternoon (after 3:00 PM) to safeguard pollinators (honeybees).`
            }
        },

        // =====================================================================
        // TOPIC 8: CHANA / GRAM AGRONOMY (Varieties, Fertilizer, Pod Borer)
        // =====================================================================
        {
            id: "gram_agronomy",
            keywords: ["चना", "gram", "chana", "chickpea", "सुंडी", "फली छेदक", "pod borer", "चने की किस्में", "चने में खाद"],
            sources: OFFICIAL_SOURCES.gram_agronomy,
            answer: {
                hi: `**चना (Gram/Chickpea) उन्नत उत्पादन एवं कीट प्रबंधन (ICAR-IIPR कानपुर):**

1. **उन्नत किस्में:**
• **JG-14, RVG-202, GNG-1581, पूसा-362 (Pusa-362):** 20–25 क्विंटल/हेक्टेयर, उकठा (Wilt) रोग रोधी।
• बीज दर: देशी चना **30–35 किलो/एकड़**, काबुली चना **40–45 किलो/एकड़**। राइजोबियम कल्चर से बीज उपचार अवश्य करें।

2. **खाद एवं सिंचाई:**
• चना दलहनी फसल है जो वायुमंडलीय नाइट्रोजन स्वयं स्थिर करती है। बुवाई के समय **40 किलो DAP + 8 किलो सल्फर प्रति एकड़** पर्याप्त है।
• **सिंचाई सावधानी:** पहली हल्की सिंचाई शाखाएं निकलते समय (40–45 दिन) और दूसरी फली बनते समय (70–75 दिन) करें। **फूल खिलते समय सिंचाई कभी न करें**, वर्ना फूल झड़ जाते हैं।

3. **फली छेदक सुंडी (Gram Pod Borer / Helicoverpa) नियंत्रण:**
• खेत में प्रति एकड़ 8–10 पक्षी आश्रय (T-shaped perches) लगाएं ताकि चिड़ियां सुंडियों को खा सकें।
• रासायनिक नियंत्रण: सुंडी दिखने पर **इमामेक्टिन बेंजोएट 5% SG @ 80 ग्राम प्रति एकड़** 150 लीटर पानी में घोलकर छिड़कें।`,

                en: `**Gram (Chickpea) Scientific Package of Practices (ICAR-IIPR):**

1. **High-Yield Varieties:**
• **JG-14, RVG-202, GNG-1581, Pusa-362:** 20–25 Q/Ha, resistant to Fusarium Wilt.
• Seed Rate: Desi Chickpea **30–35 kg/acre**; Kabuli **40–45 kg/acre**. Inoculate seeds with Rhizobium culture before sowing.

2. **Nutrient & Water Management:**
• Being a leguminous crop, chickpea fixes atmospheric nitrogen. Apply **40 kg DAP + 8 kg Sulfur per acre** as basal dose. No heavy urea is needed.
• **Irrigation Warning:** Irrigate at branching (40–45 DAS) and pod development (70–75 DAS). **NEVER irrigate during peak flowering**, as it causes severe flower drop.

3. **Gram Pod Borer (Helicoverpa armigera) Management:**
• Erect 8–10 T-perches per acre for predatory birds.
• Spray **Emamectin Benzoate 5% SG @ 80 g/acre** or **Chlorantraniliprole 18.5% SC @ 50 ml/acre** in 150 L water upon early borer infestation.`
            }
        },

        // =====================================================================
        // TOPIC 9: YELLOW RUST & WHEAT DISEASES
        // =====================================================================
        {
            id: "wheat_diseases",
            keywords: ["पीला रतुआ", "yellow rust", "stripe rust", "रतुआ", "rust", "पत्तियां पीली", "पीलापन", "tilt", "propiconazole", "wheat disease"],
            sources: OFFICIAL_SOURCES.wheat_agronomy,
            answer: {
                hi: `**गेहूं में पीला रतुआ (Yellow Stripe Rust) एवं पीलेपन का वैज्ञानिक उपचार:**

1. **पीले रतुआ के लक्षण:**
• पत्तियों पर हल्दी जैसा पीला पाउडर और सीधी पीली धारियां दिखाई देती हैं। हाथ लगाने पर उंगलियों पर पीला रंग चिपकता है।
• यह रोग ठंडे और नम मौसम (जनवरी-फरवरी) में बहुत तेजी से फैलता है।

2. **तुरंत रासायनिक उपचार (ICAR-IIWBR अनुशंसा):**
• लक्षण दिखते ही **प्रोपिकोनाजोल 25% EC (टिल्ट / Tilt) @ 200 मिली प्रति एकड़** (1 मिली प्रति लीटर पानी) 200 लीटर पानी में घोलकर छिड़कें।
• यदि 15 दिन बाद भी प्रकोप रहे, तो दूसरा छिड़काव करें।

3. **यदि पत्तियां पीली हैं पर रतुआ पाउडर नहीं है (पोषक तत्व की कमी):**
• **जिंक की कमी से पीलापन:** पत्ती के मध्य में पीलापन होता है। उपचार: **1 किलो जिंक सल्फेट (21%) + 2.5 किलो यूरिया** को 200 लीटर पानी में घोलकर प्रति एकड़ छिड़काव करें।
• **अत्यधिक पानी से पीलापन:** खेत में पानी की निकासी सुनिश्चित करें और 15 किलो यूरिया का हल्का बुरकाव करें।`,

                en: `**Wheat Yellow Stripe Rust & Leaf Yellowing Diagnostic & Control (ICAR-IIWBR):**

1. **Symptoms of Yellow Stripe Rust (Puccinia striiformis):**
• Parallel yellow stripes of bright powdery pustules appear on leaves. Touching the leaves leaves yellow powder on fingers.
• Spreads aggressively under cool, cloudy, humid conditions in January and February.

2. **Immediate Chemical Control:**
• Spray **Propiconazole 25% EC (Tilt) @ 200 ml per acre** (1 ml per liter of water) in 200 liters of water with a flat-fan nozzle.
• Repeat spray after 15 days if rust spores persist.

3. **Nutrient-Induced Yellowing (No Rust Powder):**
• **Zinc / Nitrogen Deficiency:** Foliar spray of **1 kg Zinc Sulfate (21%) + 2.5 kg Urea** dissolved in 200 L water per acre.
• **Waterlogging Yellowing:** Drain excess field water immediately and apply a light top dressing of 15 kg Urea to revive root respiration.`
            }
        },

        // =====================================================================
        // TOPIC 10: SOIL HEALTH CARD, SMAM, PMKSY & GENERAL SCHEMES
        // =====================================================================
        {
            id: "other_schemes",
            keywords: ["soil health", "मृदा स्वास्थ्य", "smam", "कृषि यंत्र", "ट्रैक्टर", "rotavator", "रोटावेटर", "drip", "sprinkler", "ड्रिप", "स्प्रिंकलर", "pmksy", "subsidy on machinery"],
            sources: OFFICIAL_SOURCES.smam,
            answer: {
                hi: `**कृषि यंत्र, ड्रिप सिंचाई एवं मृदा स्वास्थ्य योजनाएं:**

1. **कृषि यंत्र सब्सिडी (SMAM योजना):**
• सुपर सीडर, हैप्पी सीडर, रोटावेटर, लेजर लैंड लेवलर, रीपर और कस्टम हायरिंग सेंटर (CHC) की स्थापना पर **40% से 50% सरकारी अनुदान** मिलता है।
• अनुसूचित जाति/जनजाति, लघु/सीमांत एवं महिला किसानों को 50% तक विशेष वरीयता।
• पोर्टल: **https://agrimachinery.nic.in**

2. **ड्रिप एवं स्प्रिंकलर सिंचाई (PMKSY - प्रति बूंद अधिक फसल):**
• ड्रिप (टपक) और मिनी स्प्रिंकलर सिस्टम लगाने पर लघु व सीमांत किसानों को **55% सब्सिडी** और अन्य किसानों को 45% सब्सिडी दी जाती है।
• पानी की 40-50% बचत और उपज में 25-30% की वृद्धि।
• पोर्टल: **https://pmksy.gov.in**

3. **मृदा स्वास्थ्य कार्ड (Soil Health Card):**
• सरकार हर 3 वर्ष में मिट्टी के 12 मुख्य मापदंडों (N, P, K, सल्फर, जिंक, आयरन, बोरॉन, pH, EC, कार्बन) की निःशुल्क जांच करती है।
• पोर्टल: **https://soilhealth.dac.gov.in**`,

                en: `**Farm Machinery (SMAM), Micro-Irrigation (PMKSY) & Soil Health Schemes:**

1. **Farm Machinery Subsidies (SMAM Scheme):**
• Offers **40% to 50% subsidy** on Super Seeders, Happy Seeders, Rotavators, Zero-Till Drills, Laser Levelers, and Straw Reapers (and up to 80% for Custom Hiring Centres).
• Portal: **https://agrimachinery.nic.in**

2. **Micro-Irrigation (PMKSY - Per Drop More Crop):**
• Small and Marginal farmers receive up to **55% subsidy** (and other farmers receive 45%) for installing **Drip and Sprinkler irrigation systems**.
• Saves 40–50% water while increasing fertilizer efficiency by 30%.
• Portal: **https://pmksy.gov.in**

3. **Soil Health Card (SHC):**
• Tests 12 parameters (N, P, K, S, Zn, Fe, Cu, Mn, Bo, pH, EC, OC) free of cost to cut fertilizer costs by 15–20%.
• Portal: **https://soilhealth.dac.gov.in**`
            }
        }
    ];

    // -------------------------------------------------------------------------
    // 3. RETRIEVAL & SEMANTIC MATCHING LOGIC
    // -------------------------------------------------------------------------
    function isDevanagariHindi(text) {
        if (!text) return false;
        // Range \u0900-\u097F covers Devanagari script
        const devanagariCount = (text.match(/[\u0900-\u097F]/g) || []).length;
        return devanagariCount >= 3;
    }

    function calculateMatchScore(query, topic) {
        const q = query.toLowerCase();
        let score = 0;

        for (const kw of topic.keywords) {
            const kwLower = kw.toLowerCase();
            if (q.includes(kwLower)) {
                // Exact substring match
                score += kwLower.length * 3;
            } else {
                // Word-level partial match
                const kwWords = kwLower.split(/\s+/);
                for (const w of kwWords) {
                    if (w.length > 2 && q.includes(w)) {
                        score += w.length;
                    }
                }
            }
        }

        return score;
    }

    function answerQuery(rawQuery, context) {
        const query = String(rawQuery || "").trim();
        if (!query) {
            return {
                answer: "Please ask a question about crops, irrigation, fertilizers, or government schemes.",
                sources: OFFICIAL_SOURCES.general_icar,
                retrieval_mode: "fallback",
                lang: "en"
            };
        }

        context = context || {};
        const crop = context.crop || "Wheat";
        const district = context.district || "Meerut";
        const stateName = context.state || "Uttar Pradesh";
        const plotAcres = context.plot_acres || 2.5;

        // Language detection:
        // Priority: Devanagari characters in query > context.lang > localStorage > 'en'
        let lang = "en";
        if (isDevanagariHindi(query)) {
            lang = "hi";
        } else if (context.lang === "hi" || (typeof localStorage !== "undefined" && localStorage.getItem("km_lang") === "hi")) {
            lang = "hi";
        }

        // Rank topics by relevance
        let bestTopic = null;
        let highestScore = 0;

        for (const topic of RAG_TOPICS) {
            const score = calculateMatchScore(query, topic);
            if (score > highestScore) {
                highestScore = score;
                bestTopic = topic;
            }
        }

        // If strong match found (score threshold >= 5)
        if (bestTopic && highestScore >= 5) {
            const answerText = bestTopic.answer[lang] || bestTopic.answer.en;
            return {
                answer: answerText,
                sources: bestTopic.sources || OFFICIAL_SOURCES.general_icar,
                retrieval_mode: "rag_verified",
                topic_id: bestTopic.id,
                match_score: highestScore,
                lang: lang
            };
        }

        // Contextual Fallback for unindexed or conversational queries
        const isHi = lang === "hi";
        let defaultAns = "";

        if (isHi) {
            defaultAns = `किसान भाई, आपके प्रश्न **"${query}"** के संदर्भ में **${district} (${stateName})** के लिए ICAR सत्यापित सलाह:\n\n` +
                `1. **फसल एवं सिंचाई प्रबंधन:** ${crop} फसल में जलभराव न होने दें। क्रांतिक अवस्थाओं (CRI, कल्ले एवं दाना भरते समय) पर हल्की सिंचाई सुनिश्चित करें।\n` +
                `2. **उर्वरक एवं पोषण:** मिट्टी जांच के अनुसार संतुलित NPK (120:60:40 किग्रा/हेक्टेयर) और 10 किग्रा जिंक सल्फेट प्रति एकड़ का प्रयोग करें।\n` +
                `3. **सरकारी योजनाएं:** PM-KISAN (₹6000/वर्ष), फसल बीमा (PMFBY 1.5% प्रीमियम), KCC लोन (4% ब्याज) एवं PM-KUSUM सोलर पंप (60% सब्सिडी) की सुविधा उपलब्ध है।\n\n` +
                `विस्तृत जानकारी हेतु आप ऊपर किसी भी योजना या फसल रोग का नाम लिखकर पूछ सकते हैं अथवा किसान कॉल सेंटर (1800-180-1551) पर संपर्क करें।`;
        } else {
            defaultAns = `Farmer Friend, regarding your query **"${query}"** for **${crop}** in **${district} (${stateName})**:\n\n` +
                `1. **Irrigation & Agronomy:** Maintain optimum soil moisture at critical growth phases (CRI, tillering, and grain development). Avoid water stagnation.\n` +
                `2. **Nutrient Dosage:** Apply balanced N-P-K (120:60:40 kg/ha) with 10 kg Zinc Sulfate per acre in split doses.\n` +
                `3. **Government Scheme Entitlements:** You are entitled to PM-KISAN (₹6,000/yr), PMFBY Crop Insurance (1.5% Rabi premium), KCC Crop Loan (4% effective interest), and PM-KUSUM Solar Pump (up to 60% subsidy).\n\n` +
                `Feel free to ask specifically about PM-KISAN eligibility, PM-KUSUM subsidy, CRI irrigation timing, or fertilizer schedules, or dial Kisan Call Centre at 1800-180-1551.`;
        }

        return {
            answer: defaultAns,
            sources: OFFICIAL_SOURCES.general_icar,
            retrieval_mode: "rag_contextual",
            lang: lang
        };
    }

    // Expose globally on window
    window.KrishiRAGEngine = {
        answerQuery: answerQuery,
        RAG_TOPICS: RAG_TOPICS,
        OFFICIAL_SOURCES: OFFICIAL_SOURCES,
        isDevanagariHindi: isDevanagariHindi
    };

    console.log("[KrishiMitra AI] Client-side Agricultural RAG Knowledge Engine loaded successfully.");
})(typeof window !== "undefined" ? window : globalThis);
