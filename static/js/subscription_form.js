document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#subscription-form");
    if (!form) return;

    const cyclePresets = {
        weekly: [1, "week"], monthly: [1, "month"], quarterly: [3, "month"],
        half_yearly: [6, "month"], yearly: [1, "year"],
    };
    const trialPresets = {3: 3, 7: 7, 14: 14, 30: 30};
    const modeInputs = [...form.querySelectorAll("[name='service_mode']")];
    const trialStatus = form.querySelector("#id_trial_status");
    const trialPanel = form.querySelector("#trial-mode-fields");
    const paidPanel = form.querySelector("#paid-mode-fields");
    const paidInputs = [...paidPanel.querySelectorAll("input, select")];
    const trialInputs = [...trialPanel.querySelectorAll("input, select")];
    const cyclePreset = form.querySelector("#id_billing_cycle_preset");
    const cycleValue = form.querySelector("#id_sub_cycle_value");
    const cycleUnit = form.querySelector("#id_sub_cycle_unit");
    const subPrice = form.querySelector("#id_sub_price");
    const payMethod = form.querySelector("#id_pay_method");
    const paymentMethodPreset = form.querySelector("#id_payment_method_preset");
    const paymentMethodCustom = form.querySelector("#id_payment_method_custom");
    const paymentMethodCustomGroup = form.querySelector("#payment-method-custom-group");
    const customCycleFields = form.querySelector("#custom-cycle-fields");
    const startDate = form.querySelector("#id_sub_start");
    const nextDate = form.querySelector("#id_sub_next");
    const calculateNextButton = form.querySelector("#calculate-next-date");
    const categoryPreset = form.querySelector("#id_category_preset");
    const categoryCustom = form.querySelector("#id_category_custom");
    const categoryCustomGroup = form.querySelector("#category-custom-group");
    const categoryValue = form.querySelector("#id_sub_category");
    const platformPreset = form.querySelector("#id_platform_preset");
    const platformCustom = form.querySelector("#id_platform_custom");
    const platformCustomGroup = form.querySelector("#platform-custom-group");
    const platformValue = form.querySelector("#id_sub_platform");
    const websiteUrlGroup = form.querySelector("#website-url-group");
    const websiteUrl = form.querySelector("#id_sub_url");
    const trialPreset = form.querySelector("#id_trial_duration_preset");
    const trialCustomDays = form.querySelector("#id_trial_custom_days");
    const trialCustomDaysGroup = form.querySelector("#trial-custom-days-group");
    const trialEnd = form.querySelector("#id_trial_end");
    const calculateTrialButton = form.querySelector("#calculate-trial-end");
    let nextDateWasEdited = Boolean(nextDate.value);
    let trialEndWasEdited = Boolean(trialEnd.value);

    function setRequired(input, required) {
        if (!input) return;
        input.required = required;
        if (required) input.setAttribute("aria-required", "true");
        else input.removeAttribute("aria-required");
    }
    function selectedMode() {
        return modeInputs.find((input) => input.checked)?.value || modeInputs[0]?.value || "trial";
    }
    function parseDate(value) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
        const [year, month, day] = value.split("-").map(Number);
        return {year, month, day};
    }
    function formatDate({year, month, day}) {
        return [year, String(month).padStart(2, "0"), String(day).padStart(2, "0")].join("-");
    }
    function addDays(value, days) {
        const parsed = parseDate(value);
        if (!parsed || !Number.isInteger(days) || days < 1) return "";
        const result = new Date(parsed.year, parsed.month - 1, parsed.day + days);
        return formatDate({year: result.getFullYear(), month: result.getMonth() + 1, day: result.getDate()});
    }
    function addCalendarCycle(value, amount, unit) {
        const parsed = parseDate(value);
        if (!parsed || !Number.isInteger(amount) || amount < 1) return "";
        if (unit === "day") return addDays(value, amount);
        if (unit === "week") return addDays(value, amount * 7);
        if (unit !== "month" && unit !== "year") return "";
        const monthIndex = parsed.month - 1 + (unit === "month" ? amount : amount * 12);
        const targetYear = parsed.year + Math.floor(monthIndex / 12);
        const targetMonthIndex = ((monthIndex % 12) + 12) % 12;
        const lastDay = new Date(targetYear, targetMonthIndex + 1, 0).getDate();
        return formatDate({year: targetYear, month: targetMonthIndex + 1, day: Math.min(parsed.day, lastDay)});
    }
    function syncCyclePreset() {
        const isCustom = cyclePreset.value === "custom";
        const paidMode = selectedMode() === "paid";
        customCycleFields.hidden = !isCustom;
        cycleValue.disabled = !isCustom || !paidMode;
        cycleUnit.disabled = !isCustom || !paidMode;
        setRequired(cyclePreset, paidMode);
        setRequired(cycleValue, paidMode && isCustom);
        setRequired(cycleUnit, paidMode && isCustom);
        if (!isCustom && cyclePresets[cyclePreset.value]) {
            [cycleValue.value, cycleUnit.value] = cyclePresets[cyclePreset.value];
        }
    }
    function syncCategory() {
        const isCustom = categoryPreset.value === "other";
        categoryCustomGroup.hidden = !isCustom;
        categoryCustom.disabled = !isCustom;
        setRequired(categoryCustom, isCustom);
        categoryValue.value = isCustom ? categoryCustom.value.trim() : categoryPreset.value;
    }
    function syncPlatform() {
        const platformValues = {
            apple_app_store: "Apple App Store",
            google_play_store: "Google Play Store",
            website: "เว็บไซต์",
        };
        const isCustom = platformPreset.value === "other";
        const isWebsite = platformPreset.value === "website";
        platformCustomGroup.hidden = !isCustom;
        platformCustom.disabled = !isCustom;
        setRequired(platformCustom, isCustom);
        websiteUrlGroup.hidden = !isWebsite;
        websiteUrl.disabled = !isWebsite;
        platformValue.value = isCustom
            ? platformCustom.value.trim()
            : (platformValues[platformPreset.value] || "");
        if (!isWebsite) websiteUrl.value = "";
    }
    function syncPaymentMethod() {
        const paymentValues = {
            credit_debit_card: "บัตรเครดิต / เดบิต",
            bank_debit: "หักบัญชีธนาคารอัตโนมัติ",
            mobile_banking: "โมบายแบงก์กิ้ง / โอนธนาคาร",
            promptpay: "พร้อมเพย์ / QR Code",
            truemoney: "TrueMoney Wallet",
            paypal: "PayPal",
            mobile_carrier: "เรียกเก็บผ่านเครือข่ายมือถือ",
        };
        const paidMode = selectedMode() === "paid";
        const isCustom = paymentMethodPreset.value === "other";
        paymentMethodCustomGroup.hidden = !isCustom;
        paymentMethodCustom.disabled = !paidMode || !isCustom;
        setRequired(paymentMethodPreset, paidMode);
        setRequired(paymentMethodCustom, paidMode && isCustom);
        payMethod.value = isCustom
            ? paymentMethodCustom.value.trim()
            : (paymentValues[paymentMethodPreset.value] || "");
    }
    function selectedTrialDays() {
        if (trialPreset.value === "custom") {
            const days = Number.parseInt(trialCustomDays.value, 10);
            return Number.isInteger(days) && days >= 1 ? days : null;
        }
        return trialPresets[trialPreset.value] || null;
    }
    function syncTrialDuration() {
        const isCustom = trialPreset.value === "custom";
        trialCustomDaysGroup.hidden = !isCustom;
        trialCustomDays.disabled = selectedMode() !== "trial" || !isCustom;
        setRequired(trialCustomDays, selectedMode() === "trial" && isCustom);
    }
    function calculateTrialEnd(force = false) {
        if (selectedMode() !== "trial" || (!force && trialEndWasEdited)) return;
        const calculated = addDays(startDate.value, selectedTrialDays());
        if (calculated) trialEnd.value = calculated;
    }
    function calculateNextDate(force = false) {
        if (selectedMode() !== "paid" || (!force && nextDateWasEdited)) return;
        const amount = Number.parseInt(cycleValue.value, 10);
        const calculated = addCalendarCycle(startDate.value, amount, cycleUnit.value);
        if (calculated) nextDate.value = calculated;
    }
    function syncMode() {
        const trialMode = selectedMode() === "trial";
        trialPanel.hidden = !trialMode;
        paidPanel.hidden = trialMode;
        trialStatus.value = trialMode ? "True" : "False";
        trialInputs.forEach((input) => { input.disabled = !trialMode; });
        paidInputs.forEach((input) => { input.disabled = trialMode; });
        setRequired(trialPreset, trialMode);
        setRequired(trialEnd, trialMode);
        setRequired(subPrice, !trialMode);
        setRequired(nextDate, !trialMode);
        syncTrialDuration();
        syncCyclePreset();
        syncPaymentMethod();
        if (trialMode) calculateTrialEnd();
        else calculateNextDate();
    }

    modeInputs.forEach((input) => input.addEventListener("change", syncMode));
    cyclePreset.addEventListener("change", () => { syncCyclePreset(); calculateNextDate(); });
    cycleValue.addEventListener("input", () => calculateNextDate());
    cycleUnit.addEventListener("change", () => calculateNextDate());
    categoryPreset.addEventListener("change", syncCategory);
    categoryCustom.addEventListener("input", syncCategory);
    platformPreset.addEventListener("change", syncPlatform);
    platformCustom.addEventListener("input", syncPlatform);
    paymentMethodPreset.addEventListener("change", syncPaymentMethod);
    paymentMethodCustom.addEventListener("input", syncPaymentMethod);
    startDate.addEventListener("change", () => { calculateTrialEnd(); calculateNextDate(); });
    nextDate.addEventListener("input", () => { nextDateWasEdited = true; });
    calculateNextButton.addEventListener("click", () => { nextDateWasEdited = false; calculateNextDate(true); });
    trialPreset.addEventListener("change", () => { syncTrialDuration(); trialEndWasEdited = false; calculateTrialEnd(true); });
    trialCustomDays.addEventListener("input", () => { trialEndWasEdited = false; calculateTrialEnd(true); });
    trialEnd.addEventListener("input", () => { trialEndWasEdited = true; });
    calculateTrialButton.addEventListener("click", () => { trialEndWasEdited = false; calculateTrialEnd(true); });
    form.addEventListener("submit", () => { syncCategory(); syncPlatform(); syncPaymentMethod(); syncCyclePreset(); });

    syncCategory();
    syncPlatform();
    syncPaymentMethod();
    syncMode();
});
