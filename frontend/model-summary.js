/**
 * KrishiMitra AI - Model Performance & Benchmark Summary Dashboard Controller
 * Handles interactive sorting, unit conversions, SVG chart generation, and data exports.
 */

(function () {
    // Standard agricultural unit conversion: 1 Tonne / Hectare = 4.04686 Quintals / Acre
    const T_HA_TO_Q_ACRE = 4.04686;

    // Default Fallback Data (grounded in user-provided audit)
    const MODEL_DATA = {
        models: [
            {
                name: "Previous-Year Baseline",
                mae: 0.18919999999999995,
                rmse: 0.24393441741582916,
                r2: 0.736409384081083,
                rank: 1,
                status: "Champion",
                notes: "Strong annual temporal autocorrelation in district yields (Yield_t ≈ Yield_t-1). Outperforms complex models without overfitting."
            },
            {
                name: "Extra Trees",
                mae: 0.47292871538865183,
                rmse: 0.5297952483604351,
                r2: -0.24336861748394223,
                rank: 2,
                status: "Contender",
                notes: "Extreme randomized trees offer lower variance than Random Forest, but suffer from out-of-distribution shifts between 2014-2020 and 2021-2022."
            },
            {
                name: "Random Forest",
                mae: 0.5512276740276019,
                rmse: 0.6404497015638098,
                r2: -0.8169954472020209,
                rank: 3,
                status: "Underperforming",
                notes: "Standard decision trees struggle to interpolate outside training distributions during anomalous dry or early-heat seasons without lag features."
            },
            {
                name: "Ridge Regression",
                mae: 0.81476206868874,
                rmse: 1.0312469421034522,
                r2: -3.710956905156819,
                rank: 4,
                status: "Poor Fit",
                notes: "Linear regularized baseline fails to model nonlinear agronomic interactions (e.g. fertilizer plateau & March heat threshold) across split years."
            }
        ],
        dataset_summary: {
            training_records: 180,
            testing_records: 50,
            total_records: 230,
            train_ratio_percent: 78.26,
            test_ratio_percent: 21.74,
            training_years: [2014, 2015, 2016, 2017, 2018, 2019, 2020],
            testing_years: [2021, 2022],
            best_method_by_MAE: "Previous-Year Baseline",
            best_MAE: 0.18919999999999995,
            best_RMSE: 0.24393441741582916,
            best_R2: 0.736409384081083,
            target_variable: "Yield (Tonne / Hectare)",
            crop: "Wheat (Rabi)",
            state: "Uttar Pradesh"
        }
    };

    let state = {
        models: [...MODEL_DATA.models],
        summary: { ...MODEL_DATA.dataset_summary },
        unit: "t_ha", // 't_ha' or 'q_acre'
        sortKey: "rank",
        sortDir: "asc"
    };

    // Formatters
    function formatYield(val, unit) {
        if (unit === "q_acre") {
            return (val * T_HA_TO_Q_ACRE).toFixed(3);
        }
        return Number(val).toFixed(4);
    }

    function getUnitLabel(unit) {
        return unit === "q_acre" ? "Q / Acre" : "t / ha";
    }

    // 1. Fetch live API data or fall back seamlessly
    async function loadModelSummaryData() {
        try {
            const res = await fetch("/api/model-summary");
            if (res.ok) {
                const data = await res.json();
                if (data && data.models && data.models.length > 0) {
                    state.models = data.models;
                    state.summary = data.dataset_summary || state.summary;
                }
            }
        } catch (e) {
            console.log("Using static validated benchmark summary data.");
        }
        renderAll();
    }

    // 2. Render Top 4 KPI Cards
    function renderKPIs() {
        const bestModel = state.models.find(m => m.name === state.summary.best_method_by_MAE) || state.models[0];
        const unitLbl = getUnitLabel(state.unit);

        const valMAE = document.getElementById("kpiBestMAE");
        const valRMSE = document.getElementById("kpiBestRMSE");
        const valR2 = document.getElementById("kpiBestR2");
        const valSplit = document.getElementById("kpiDataSplit");

        const unitMAE = document.getElementById("kpiUnitMAE");
        const unitRMSE = document.getElementById("kpiUnitRMSE");

        if (valMAE) valMAE.textContent = formatYield(bestModel.mae, state.unit);
        if (unitMAE) unitMAE.textContent = unitLbl;

        if (valRMSE) valRMSE.textContent = formatYield(bestModel.rmse, state.unit);
        if (unitRMSE) unitRMSE.textContent = unitLbl;

        if (valR2) valR2.textContent = (bestModel.r2 * 100).toFixed(1) + "%";
        if (valSplit) valSplit.textContent = `${state.summary.training_records} / ${state.summary.testing_records}`;
    }

    // 3. Render Leaderboard Table
    function renderLeaderboard() {
        const tbody = document.getElementById("modelTableBody");
        if (!tbody) return;

        // Sort models
        const sorted = [...state.models].sort((a, b) => {
            let vA = a[state.sortKey];
            let vB = b[state.sortKey];
            if (typeof vA === "string") {
                return state.sortDir === "asc" ? vA.localeCompare(vB) : vB.localeCompare(vA);
            }
            return state.sortDir === "asc" ? vA - vB : vB - vA;
        });

        tbody.innerHTML = "";
        const maxMAE = Math.max(...sorted.map(m => m.mae));
        const unitLbl = getUnitLabel(state.unit);

        sorted.forEach(m => {
            const tr = document.createElement("tr");
            if (m.rank === 1) tr.className = "champion-row";

            let statusClass = "ms-status-champion";
            if (m.status === "Contender") statusClass = "ms-status-contender";
            if (m.status === "Underperforming") statusClass = "ms-status-underperforming";
            if (m.status === "Poor Fit") statusClass = "ms-status-poor";

            const barPct = Math.min(100, Math.round((m.mae / maxMAE) * 100));
            const barColor = m.rank === 1 ? "var(--ms-accent-emerald)" : m.rank === 2 ? "var(--ms-accent-blue)" : m.rank === 3 ? "var(--ms-accent-amber)" : "var(--ms-accent-red)";

            tr.innerHTML = `
                <td>
                    <span class="ms-rank-badge ${m.rank === 1 ? 'rank-1' : ''}">${m.rank}</span>
                </td>
                <td>
                    <div class="ms-model-name-cell">
                        <span>${m.name}</span>
                        ${m.rank === 1 ? '<span class="ms-status-chip ms-status-champion">Champion</span>' : ''}
                    </div>
                    <div style="font-size:0.78rem; color:var(--ms-text-muted); margin-top:3px; max-width:380px;">${m.notes}</div>
                </td>
                <td>
                    <div class="ms-mini-bar-wrap">
                        <strong style="font-size:0.95rem;">${formatYield(m.mae, state.unit)}</strong>
                        <span style="font-size:0.75rem; color:var(--ms-text-light);">${unitLbl}</span>
                        <div class="ms-mini-bar">
                            <div class="ms-mini-bar-fill" style="width: ${barPct}%; background: ${barColor};"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <strong>${formatYield(m.rmse, state.unit)}</strong>
                    <span style="font-size:0.75rem; color:var(--ms-text-light);">${unitLbl}</span>
                </td>
                <td>
                    <strong style="color: ${m.r2 > 0 ? 'var(--ms-accent-emerald)' : 'var(--ms-accent-red)'}; font-size:0.95rem;">
                        ${m.r2.toFixed(4)}
                    </strong>
                </td>
                <td>
                    <span class="ms-status-chip ${statusClass}">${m.status}</span>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Update table header sorting classes
        document.querySelectorAll(".ms-table th.sortable").forEach(th => {
            const key = th.getAttribute("data-sort");
            th.classList.remove("sorted-asc", "sorted-desc");
            if (key === state.sortKey) {
                th.classList.add(state.sortDir === "asc" ? "sorted-asc" : "sorted-desc");
            }
        });
    }

    // 4. Render Error Comparison Bar Chart (MAE vs RMSE)
    function renderErrorBarChart() {
        const svgContainer = document.getElementById("chartErrorsSvg");
        if (!svgContainer) return;

        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const gridColor = isDark ? "rgba(255,255,255,0.08)" : "#e5e7eb";
        const textColor = isDark ? "#94a3b8" : "#64748b";

        const width = 580;
        const height = 280;
        const margin = { top: 30, right: 25, bottom: 50, left: 55 };
        const chartW = width - margin.left - margin.right;
        const chartH = height - margin.top - margin.bottom;

        // Data conversion
        const models = state.models;
        const maxVal = Math.max(...models.map(m => Math.max(m.mae, m.rmse))) * 1.15;
        const factor = state.unit === "q_acre" ? T_HA_TO_Q_ACRE : 1.0;
        const scaledMax = maxVal * factor;

        const groupWidth = chartW / models.length;
        const barWidth = 22;

        let svg = `
            <svg viewBox="0 0 ${width} ${height}" class="ms-chart-svg" xmlns="http://www.w3.org/2000/svg">
                <!-- Grid Lines -->
                <line x1="${margin.left}" y1="${margin.top}" x2="${width - margin.right}" y2="${margin.top}" stroke="${gridColor}" stroke-dasharray="3 3"/>
                <line x1="${margin.left}" y1="${margin.top + chartH * 0.5}" x2="${width - margin.right}" y2="${margin.top + chartH * 0.5}" stroke="${gridColor}" stroke-dasharray="3 3"/>
                <line x1="${margin.left}" y1="${margin.top + chartH}" x2="${width - margin.right}" y2="${margin.top + chartH}" stroke="${gridColor}"/>

                <!-- Y Axis Labels -->
                <text x="${margin.left - 10}" y="${margin.top + 4}" class="ms-axis-text" text-anchor="end">${scaledMax.toFixed(2)}</text>
                <text x="${margin.left - 10}" y="${margin.top + chartH * 0.5 + 4}" class="ms-axis-text" text-anchor="end">${(scaledMax * 0.5).toFixed(2)}</text>
                <text x="${margin.left - 10}" y="${margin.top + chartH + 4}" class="ms-axis-text" text-anchor="end">0.00</text>
        `;

        models.forEach((m, idx) => {
            const centerX = margin.left + idx * groupWidth + groupWidth / 2;
            const maeVal = m.mae * factor;
            const rmseVal = m.rmse * factor;

            const maeH = (maeVal / scaledMax) * chartH;
            const rmseH = (rmseVal / scaledMax) * chartH;

            const xMAE = centerX - barWidth - 3;
            const yMAE = margin.top + chartH - maeH;

            const xRMSE = centerX + 3;
            const yRMSE = margin.top + chartH - rmseH;

            // Short label
            let label = m.name.replace(" Regression", "").replace(" Baseline", "");
            if (label.length > 12) label = label.slice(0, 11) + "…";

            svg += `
                <!-- Group for ${m.name} -->
                <rect x="${xMAE}" y="${yMAE}" width="${barWidth}" height="${maeH}" rx="4" fill="var(--ms-primary)" class="ms-bar-rect">
                    <title>${m.name} MAE: ${maeVal.toFixed(3)} ${getUnitLabel(state.unit)}</title>
                </rect>
                <text x="${xMAE + barWidth / 2}" y="${yMAE - 5}" font-size="10" font-weight="700" fill="${textColor}" text-anchor="middle">
                    ${maeVal.toFixed(2)}
                </text>

                <rect x="${xRMSE}" y="${yRMSE}" width="${barWidth}" height="${rmseH}" rx="4" fill="var(--ms-accent-amber)" class="ms-bar-rect">
                    <title>${m.name} RMSE: ${rmseVal.toFixed(3)} ${getUnitLabel(state.unit)}</title>
                </rect>
                <text x="${xRMSE + barWidth / 2}" y="${yRMSE - 5}" font-size="10" font-weight="700" fill="${textColor}" text-anchor="middle">
                    ${rmseVal.toFixed(2)}
                </text>

                <!-- Model X Axis Label -->
                <text x="${centerX}" y="${margin.top + chartH + 20}" font-size="11" font-weight="700" fill="${textColor}" text-anchor="middle">
                    ${label}
                </text>
            `;
        });

        svg += `</svg>`;
        svgContainer.innerHTML = svg;
    }

    // 5. Render R² Score Spectrum Diverging Chart
    function renderR2Chart() {
        const svgContainer = document.getElementById("chartR2Svg");
        if (!svgContainer) return;

        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const gridColor = isDark ? "rgba(255,255,255,0.08)" : "#e5e7eb";
        const textColor = isDark ? "#94a3b8" : "#64748b";

        const width = 580;
        const height = 280;
        const margin = { top: 25, right: 40, bottom: 25, left: 160 };
        const chartW = width - margin.left - margin.right;
        const chartH = height - margin.top - margin.bottom;

        // R² range from -4.0 to +1.0
        const minR2 = -4.0;
        const maxR2 = 1.0;
        const zeroX = margin.left + ((0 - minR2) / (maxR2 - minR2)) * chartW;

        const models = state.models;
        const rowH = chartH / models.length;
        const barH = 20;

        let svg = `
            <svg viewBox="0 0 ${width} ${height}" class="ms-chart-svg" xmlns="http://www.w3.org/2000/svg">
                <!-- Zero Line Reference -->
                <line x1="${zeroX}" y1="${margin.top}" x2="${zeroX}" y2="${margin.top + chartH}" stroke="var(--ms-text)" stroke-width="1.8" stroke-dasharray="2 2"/>
                <text x="${zeroX}" y="${margin.top - 8}" font-size="11" font-weight="800" fill="${textColor}" text-anchor="middle">0.0 (Baseline)</text>

                <!-- Scale Bounds -->
                <text x="${margin.left}" y="${margin.top - 8}" font-size="10" font-weight="600" fill="${textColor}" text-anchor="start">-4.0</text>
                <text x="${width - margin.right}" y="${margin.top - 8}" font-size="10" font-weight="600" fill="${textColor}" text-anchor="end">+1.0</text>
        `;

        models.forEach((m, idx) => {
            const y = margin.top + idx * rowH + rowH / 2 - barH / 2;
            const r2 = m.r2;
            const xPos = margin.left + ((r2 - minR2) / (maxR2 - minR2)) * chartW;

            let barX = zeroX;
            let barW = 0;
            let barColor = "var(--ms-accent-emerald)";

            if (r2 >= 0) {
                barX = zeroX;
                barW = xPos - zeroX;
                barColor = "var(--ms-accent-emerald)";
            } else {
                barX = xPos;
                barW = zeroX - xPos;
                barColor = r2 > -1.0 ? "var(--ms-accent-amber)" : "var(--ms-accent-red)";
            }

            const textAnchor = r2 >= 0 ? "start" : "end";
            const textX = r2 >= 0 ? zeroX + barW + 8 : xPos - 8;

            svg += `
                <!-- Model Name Label -->
                <text x="${margin.left - 14}" y="${y + barH * 0.7}" font-size="11" font-weight="700" fill="${textColor}" text-anchor="end">
                    ${m.name}
                </text>

                <!-- Bar -->
                <rect x="${barX}" y="${y}" width="${Math.max(2, barW)}" height="${barH}" rx="4" fill="${barColor}" class="ms-bar-rect">
                    <title>${m.name} R²: ${r2.toFixed(4)}</title>
                </rect>

                <!-- Value text -->
                <text x="${textX}" y="${y + barH * 0.7}" font-size="11" font-weight="800" fill="${barColor}" text-anchor="${textAnchor}">
                    ${r2 > 0 ? "+" : ""}${r2.toFixed(3)}
                </text>
            `;
        });

        svg += `</svg>`;
        svgContainer.innerHTML = svg;
    }

    // 6. CSV & JSON Export Handlers
    function exportCSV() {
        const factor = state.unit === "q_acre" ? T_HA_TO_Q_ACRE : 1.0;
        const unitLbl = getUnitLabel(state.unit);

        let csv = `Model,Rank,Status,MAE (${unitLbl}),RMSE (${unitLbl}),R2 Score,Notes\n`;
        state.models.forEach(m => {
            csv += `"${m.name}",${m.rank},"${m.status}",${(m.mae * factor).toFixed(4)},${(m.rmse * factor).toFixed(4)},${m.r2.toFixed(4)},"${m.notes}"\n`;
        });

        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `krishimitra_model_summary_${state.unit}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    function exportJSON() {
        const fullPayload = {
            models: state.models,
            dataset_summary: state.summary,
            exported_at: new Date().toISOString(),
            active_unit: state.unit
        };

        const blob = new Blob([JSON.stringify(fullPayload, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "krishimitra_model_summary.json";
        a.click();
        URL.revokeObjectURL(url);
    }

    // 7. Render All Components
    function renderAll() {
        renderKPIs();
        renderLeaderboard();
        renderErrorBarChart();
        renderR2Chart();
    }

    // 8. Event Listeners & Binding
    document.addEventListener("DOMContentLoaded", () => {
        loadModelSummaryData();

        // Unit switcher buttons
        const btnUnitTHa = document.getElementById("btnUnitTHa");
        const btnUnitQAcre = document.getElementById("btnUnitQAcre");

        if (btnUnitTHa) {
            btnUnitTHa.addEventListener("click", () => {
                state.unit = "t_ha";
                btnUnitTHa.classList.add("active");
                if (btnUnitQAcre) btnUnitQAcre.classList.remove("active");
                renderAll();
            });
        }

        if (btnUnitQAcre) {
            btnUnitQAcre.addEventListener("click", () => {
                state.unit = "q_acre";
                btnUnitQAcre.classList.add("active");
                if (btnUnitTHa) btnUnitTHa.classList.remove("active");
                renderAll();
            });
        }

        // Table column sorting
        document.querySelectorAll(".ms-table th.sortable").forEach(th => {
            th.addEventListener("click", () => {
                const key = th.getAttribute("data-sort");
                if (state.sortKey === key) {
                    state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
                } else {
                    state.sortKey = key;
                    state.sortDir = (key === "mae" || key === "rmse" || key === "rank") ? "asc" : "desc";
                }
                renderLeaderboard();
            });
        });

        // Export buttons
        const btnCsv = document.getElementById("btnExportCsv");
        if (btnCsv) btnCsv.addEventListener("click", (e) => { e.preventDefault(); exportCSV(); });

        const btnJson = document.getElementById("btnExportJson");
        if (btnJson) btnJson.addEventListener("click", (e) => { e.preventDefault(); exportJSON(); });

        // Global Theme Change Listener
        window.addEventListener("krishimitra:themeChanged", () => {
            renderErrorBarChart();
            renderR2Chart();
        });

        // Window resize debounced re-render
        let resizeTimer;
        window.addEventListener("resize", () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                renderErrorBarChart();
                renderR2Chart();
            }, 150);
        });
    });
})();
