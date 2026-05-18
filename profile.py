from __future__ import annotations
import json, os
import streamlit as st

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
T = {
    "en": {
        "title": "Investor Risk Profiling",
        "subtitle": "Answer 15 questions so we can personalise your P1 Asset Allocation targets.",
        "s1": "Section 1 — About You",
        "s2": "Section 2 — Investment Goals",
        "s3": "Section 3 — Risk Tolerance",
        "s4": "Section 4 — Portfolio Preferences",
        "submit": "Generate My Investor Profile",
        "apply": "Apply Profile to P1 Analysis",
        "applied_ok": "P1 sliders have been updated. Switch to the Stock Evaluator tab.",
        "generating": "Analysing your profile with Claude AI…",
        "fallback": "Claude API not configured — using rule-based profile.",
        "profile_label": "Your Risk Profile",
        "alloc_label": "Recommended Asset Allocation",
        "p1_label": "P1 Target Values (auto-filled)",
        "commentary_label": "Personalised Advice",
        "mode_label": "Recommended Market Mode",
        "unanswered": "Please answer all questions before submitting.",
        "lang_toggle": "Language / ภาษา",
    },
    "th": {
        "title": "ประเมินโปรไฟล์นักลงทุน",
        "subtitle": "ตอบ 15 คำถามเพื่อกำหนดเป้าหมาย P1 การจัดสรรสินทรัพย์ที่เหมาะกับคุณ",
        "s1": "ส่วนที่ 1 — ข้อมูลส่วนตัว",
        "s2": "ส่วนที่ 2 — เป้าหมายการลงทุน",
        "s3": "ส่วนที่ 3 — ความเสี่ยงที่ยอมรับได้",
        "s4": "ส่วนที่ 4 — ความชอบด้านพอร์ตโฟลิโอ",
        "submit": "สร้างโปรไฟล์นักลงทุนของฉัน",
        "apply": "นำโปรไฟล์ไปใช้กับการวิเคราะห์ P1",
        "applied_ok": "อัปเดตสไลเดอร์ P1 แล้ว กรุณาสลับไปแท็บ Stock Evaluator",
        "generating": "กำลังวิเคราะห์โปรไฟล์ด้วย Claude AI…",
        "fallback": "ไม่ได้ตั้งค่า Claude API — ใช้ระบบคำนวณอัตโนมัติแทน",
        "profile_label": "โปรไฟล์ความเสี่ยงของคุณ",
        "alloc_label": "การจัดสรรสินทรัพย์ที่แนะนำ",
        "p1_label": "ค่าเป้าหมาย P1 (กรอกอัตโนมัติ)",
        "commentary_label": "คำแนะนำส่วนบุคคล",
        "mode_label": "Market Mode ที่แนะนำ",
        "unanswered": "กรุณาตอบคำถามทุกข้อก่อนกด Submit",
        "lang_toggle": "Language / ภาษา",
    },
}

# ---------------------------------------------------------------------------
# Questions  (id, section, en_text, th_text, options_en, options_th, scores)
# scores[i] = risk score for option i  (higher = more aggressive)
# ---------------------------------------------------------------------------
QUESTIONS = [
    # --- Section 1 ---
    {
        "id": "q_age", "section": 1, "type": "radio",
        "en": "What is your age range?",
        "th": "คุณอยู่ในช่วงอายุใด?",
        "opts_en": ["20–30", "31–40", "41–50", "51–60", "60+"],
        "opts_th": ["20–30 ปี", "31–40 ปี", "41–50 ปี", "51–60 ปี", "60 ปีขึ้นไป"],
        "scores":  [3, 3, 2, 1, 0],
    },
    {
        "id": "q_dep", "section": 1, "type": "radio",
        "en": "How many financial dependents do you have?",
        "th": "คุณมีผู้ที่ต้องดูแลทางการเงินกี่คน?",
        "opts_en": ["None", "1–2", "3–4", "5+"],
        "opts_th": ["ไม่มี", "1–2 คน", "3–4 คน", "5 คนขึ้นไป"],
        "scores":  [3, 2, 1, 0],
    },
    {
        "id": "q_job", "section": 1, "type": "radio",
        "en": "What is your employment situation?",
        "th": "สถานการณ์การทำงานของคุณเป็นอย่างไร?",
        "opts_en": ["Stable salary / employee", "Business owner", "Freelance / self-employed", "Retired / semi-retired"],
        "opts_th": ["พนักงานประจำ / เงินเดือนมั่นคง", "เจ้าของธุรกิจ", "ฟรีแลนซ์ / ประกอบอาชีพอิสระ", "เกษียณแล้ว / กึ่งเกษียณ"],
        "scores":  [3, 2, 1, 1],
    },
    {
        "id": "q_save", "section": 1, "type": "radio",
        "en": "What % of monthly income do you save / invest?",
        "th": "คุณออมหรือลงทุนกี่เปอร์เซ็นต์ของรายได้รายเดือน?",
        "opts_en": ["Less than 10%", "10–20%", "20–30%", "More than 30%"],
        "opts_th": ["น้อยกว่า 10%", "10–20%", "20–30%", "มากกว่า 30%"],
        "scores":  [0, 1, 2, 3],
    },
    # --- Section 2 ---
    {
        "id": "q_goal", "section": 2, "type": "radio",
        "en": "What is your primary investment goal?",
        "th": "เป้าหมายหลักในการลงทุนของคุณคืออะไร?",
        "opts_en": ["Build passive income stream", "Secure retirement", "Children's education fund", "Maximum wealth accumulation"],
        "opts_th": ["สร้างรายได้ Passive Income", "ความมั่นคงในการเกษียณ", "ทุนการศึกษาบุตร", "สะสมความมั่งคั่งสูงสุด"],
        "scores":  [1, 1, 1, 3],
    },
    {
        "id": "q_horizon", "section": 2, "type": "radio",
        "en": "When do you expect to need this money?",
        "th": "คุณคาดว่าจะต้องใช้เงินนี้เมื่อใด?",
        "opts_en": ["Less than 3 years", "3–7 years", "7–15 years", "More than 15 years"],
        "opts_th": ["น้อยกว่า 3 ปี", "3–7 ปี", "7–15 ปี", "มากกว่า 15 ปี"],
        "scores":  [0, 1, 2, 3],
    },
    {
        "id": "q_return", "section": 2, "type": "radio",
        "en": "What annual return do you realistically target?",
        "th": "คุณตั้งเป้าผลตอบแทนต่อปีเท่าใด?",
        "opts_en": ["5–7%  (conservative)", "8–12%  (moderate)", "13–18%  (aggressive)", "19%+  (very aggressive)"],
        "opts_th": ["5–7%  (อนุรักษ์นิยม)", "8–12%  (ปานกลาง)", "13–18%  (เชิงรุก)", "19%+  (เชิงรุกมาก)"],
        "scores":  [0, 1, 2, 3],
    },
    # --- Section 3 ---
    {
        "id": "q_drop", "section": 3, "type": "radio",
        "en": "If your portfolio dropped 25% in 3 months, you would…",
        "th": "ถ้าพอร์ตของคุณลดลง 25% ใน 3 เดือน คุณจะ…",
        "opts_en": ["Sell everything immediately", "Hold and wait it out", "Hold and review the strategy", "Buy more at the lower price"],
        "opts_th": ["ขายทุกอย่างทันที", "ถือไว้และรอ", "ถือไว้และทบทวนกลยุทธ์", "ซื้อเพิ่มในราคาที่ต่ำกว่า"],
        "scores":  [0, 1, 2, 3],
    },
    {
        "id": "q_pref", "section": 3, "type": "radio",
        "en": "Which scenario do you prefer?",
        "th": "คุณชอบสถานการณ์ใดมากกว่า?",
        "opts_en": ["Guaranteed 6% per year", "Possible 15% or –3%", "Possible 25% or –10%", "Possible 40% or –20%"],
        "opts_th": ["ได้ผลตอบแทน 6% ต่อปีแน่นอน", "อาจได้ 15% หรือ -3%", "อาจได้ 25% หรือ -10%", "อาจได้ 40% หรือ -20%"],
        "scores":  [0, 1, 2, 3],
    },
    {
        "id": "q_loss", "section": 3, "type": "radio",
        "en": "Maximum portfolio loss you can emotionally handle",
        "th": "ขาดทุนสูงสุดที่คุณรับได้ทางจิตใจ",
        "opts_en": ["Up to 5%", "Up to 10%", "Up to 20%", "30% or more"],
        "opts_th": ["ไม่เกิน 5%", "ไม่เกิน 10%", "ไม่เกิน 20%", "30% ขึ้นไป"],
        "scores":  [0, 1, 2, 3],
    },
    {
        "id": "q_panic", "section": 3, "type": "radio",
        "en": "Have you ever panic-sold investments at a loss?",
        "th": "คุณเคย panic-sell ลงทุนขาดทุนหรือไม่?",
        "opts_en": ["Never invested before", "No — I stayed disciplined", "Yes — once or twice", "Yes — multiple times"],
        "opts_th": ["ยังไม่เคยลงทุนมาก่อน", "ไม่เคย — ฉันมีวินัย", "เคย — หนึ่งหรือสองครั้ง", "เคย — หลายครั้ง"],
        "scores":  [1, 3, 1, 0],
    },
    # --- Section 4 ---
    {
        "id": "q_assets", "section": 4, "type": "multiselect",
        "en": "Which asset classes are you comfortable investing in?",
        "th": "ประเภทสินทรัพย์ใดที่คุณสบายใจลงทุน?",
        "opts_en": ["Thai / Global Stocks", "Government / Corporate Bonds", "REITs / Property Funds", "Gold / Commodities", "Cash / Money Market", "Cryptocurrency"],
        "opts_th": ["หุ้นไทย / หุ้นต่างประเทศ", "พันธบัตร / หุ้นกู้", "REITs / กองทุนอสังหาฯ", "ทองคำ / สินค้าโภคภัณฑ์", "เงินสด / กองทุนตลาดเงิน", "สกุลเงินดิจิทัล"],
        "scores":  None,  # handled separately
    },
    {
        "id": "q_income", "section": 4, "type": "radio",
        "en": "Do you need regular income from your portfolio?",
        "th": "คุณต้องการรายได้สม่ำเสมอจากพอร์ตหรือไม่?",
        "opts_en": ["Yes — need monthly income", "Yes — quarterly is fine", "No — reinvest everything", "Flexible"],
        "opts_th": ["ต้องการรายได้รายเดือน", "รายไตรมาสก็ได้", "ไม่ต้องการ — reinvest ทั้งหมด", "ยืดหยุ่นได้"],
        "scores":  [0, 1, 3, 2],
    },
    {
        "id": "q_rebal", "section": 4, "type": "radio",
        "en": "How disciplined are you about rebalancing your portfolio?",
        "th": "คุณมีวินัยในการปรับสมดุลพอร์ตมากแค่ไหน?",
        "opts_en": ["Rebalance regularly (quarterly / annually)", "Rebalance when I remember", "Rarely or never", "Don't know what rebalancing is"],
        "opts_th": ["ปรับสมดุลเป็นประจำ (รายไตรมาส / รายปี)", "ปรับสมดุลเมื่อนึกได้", "ไม่ค่อยปรับหรือไม่เคยปรับ", "ไม่รู้ว่า rebalancing คืออะไร"],
        "scores":  [3, 2, 1, 0],
    },
    {
        "id": "q_exp", "section": 4, "type": "radio",
        "en": "Your investment experience level",
        "th": "ระดับประสบการณ์การลงทุนของคุณ",
        "opts_en": ["Complete beginner (< 1 year)", "Some experience (1–3 years)", "Experienced (3–10 years)", "Expert (10+ years)"],
        "opts_th": ["มือใหม่ (น้อยกว่า 1 ปี)", "มีประสบการณ์บ้าง (1–3 ปี)", "มีประสบการณ์ (3–10 ปี)", "ผู้เชี่ยวชาญ (10 ปีขึ้นไป)"],
        "scores":  [0, 1, 2, 3],
    },
]

# ---------------------------------------------------------------------------
# Risk profiles — P1 target values and asset allocations
# ---------------------------------------------------------------------------
PROFILES = {
    "Conservative": {
        "color": "#3498db",
        "en": "Conservative (Capital Preservation)",
        "th": "อนุรักษ์นิยม (รักษาเงินต้น)",
        "p1": {
            "P1-01": 5.5, "P1-02": 7.0,  "P1-03": 0.55,
            "P1-04": 8.0, "P1-05": 0.55, "P1-06": 0.25,
            "P1-07": 7.0, "P1-08": 4.0,
        },
        "alloc": {"Thai Bonds": 35, "Global Bonds": 15, "Thai Stocks": 15,
                  "Global Stocks": 15, "REITs": 10, "Gold": 5, "Cash": 5},
        "mode": "Bear",
    },
    "Moderate": {
        "color": "#27ae60",
        "en": "Moderate Growth (Balanced)",
        "th": "การเติบโตระดับปานกลาง (สมดุล)",
        "p1": {
            "P1-01": 8.5,  "P1-02": 13.0, "P1-03": 0.70,
            "P1-04": 15.0, "P1-05": 0.90, "P1-06": 0.40,
            "P1-07": 5.0,  "P1-08": 7.0,
        },
        "alloc": {"Thai Stocks": 25, "Global Stocks": 30, "Bonds": 25,
                  "REITs": 10, "Gold": 5, "Cash": 5},
        "mode": "Base",
    },
    "Aggressive": {
        "color": "#e67e22",
        "en": "Aggressive Growth",
        "th": "การเติบโตเชิงรุก",
        "p1": {
            "P1-01": 13.0, "P1-02": 19.0, "P1-03": 0.80,
            "P1-04": 25.0, "P1-05": 1.10, "P1-06": 0.55,
            "P1-07": 4.0,  "P1-08": 11.0,
        },
        "alloc": {"Thai Stocks": 30, "Global Stocks": 45, "REITs": 10,
                  "Gold": 5, "Bonds": 10},
        "mode": "Bull",
    },
    "Very Aggressive": {
        "color": "#c0392b",
        "en": "Very Aggressive (Maximum Growth)",
        "th": "เชิงรุกมาก (เติบโตสูงสุด)",
        "p1": {
            "P1-01": 18.0, "P1-02": 26.0, "P1-03": 0.90,
            "P1-04": 35.0, "P1-05": 1.35, "P1-06": 0.65,
            "P1-07": 3.0,  "P1-08": 14.0,
        },
        "alloc": {"Thai Stocks": 20, "Global Stocks": 60, "REITs": 5,
                  "Gold": 5, "Crypto": 10},
        "mode": "Bull",
    },
}

P1_LABELS = {
    "P1-01": ("Expected Return",      "ผลตอบแทนที่คาดหวัง",       "%"),
    "P1-02": ("Portfolio Volatility", "ความผันผวนของพอร์ต",        "%"),
    "P1-03": ("Target Sharpe Ratio",  "Sharpe Ratio เป้าหมาย",    ""),
    "P1-04": ("Max Drawdown",         "การขาดทุนสูงสุดที่ยอมรับ", "%"),
    "P1-05": ("Beta to Market",       "Beta ต่อตลาด",              "x"),
    "P1-06": ("Avg Correlation",      "ค่าสหสัมพันธ์เฉลี่ย",       ""),
    "P1-07": ("# Asset Classes",      "จำนวนประเภทสินทรัพย์",     ""),
    "P1-08": ("Portfolio Drift",      "การเบี่ยงเบนพอร์ต",         "%"),
}

# ---------------------------------------------------------------------------
# Rule-based scoring
# ---------------------------------------------------------------------------
def _rule_score(answers: dict) -> int:
    total = 0
    for q in QUESTIONS:
        qid = q["id"]
        if qid not in answers:
            continue
        if q["type"] == "multiselect":
            # more diverse asset classes = slightly more aggressive
            total += min(3, len(answers[qid]))
        else:
            opts = q["opts_en"]
            val = answers[qid]
            if val in opts:
                idx = opts.index(val)
                total += q["scores"][idx]
    return total


def rule_based_profile(answers: dict) -> dict:
    score = _rule_score(answers)
    if score <= 12:
        key = "Conservative"
    elif score <= 24:
        key = "Moderate"
    elif score <= 33:
        key = "Aggressive"
    else:
        key = "Very Aggressive"

    p = PROFILES[key]
    return {
        "risk_profile_en":  p["en"],
        "risk_profile_th":  p["th"],
        "profile_key":      key,
        "color":            p["color"],
        "p1_values":        dict(p["p1"]),
        "asset_allocation": dict(p["alloc"]),
        "recommended_mode": p["mode"],
        "commentary_en": (
            f"Based on your answers, you are a {p['en']} investor. "
            "Your P1 targets have been calibrated to match your risk tolerance, "
            "time horizon, and income needs."
        ),
        "commentary_th": (
            f"จากคำตอบของคุณ คุณเป็นนักลงทุนประเภท {p['th']} "
            "ค่าเป้าหมาย P1 ถูกปรับให้เหมาะสมกับระดับความเสี่ยง ระยะเวลา และความต้องการรายได้ของคุณ"
        ),
        "source": "rule-based",
    }


# ---------------------------------------------------------------------------
# Claude API interpretation
# ---------------------------------------------------------------------------
def _get_api_key() -> str:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")


def claude_profile(answers: dict, lang: str) -> dict | None:
    api_key = _get_api_key()
    if not api_key or api_key.startswith("sk-ant-api03-YOUR"):
        return None

    answers_text = "\n".join(
        f"- {q['en']}: {answers.get(q['id'], 'Not answered')}"
        for q in QUESTIONS
    )

    prompt = f"""You are a senior financial advisor specialising in Thai and international investment markets.
An investor completed a risk profiling questionnaire. Analyse their answers and return a JSON profile.

ANSWERS:
{answers_text}

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "risk_profile_en": "one of: Conservative, Moderate Growth, Aggressive Growth, Very Aggressive",
  "risk_profile_th": "Thai translation of the profile name",
  "profile_key": "one of: Conservative, Moderate, Aggressive, Very Aggressive",
  "color": "hex color: #3498db / #27ae60 / #e67e22 / #c0392b",
  "p1_values": {{
    "P1-01": <expected annual return % — float>,
    "P1-02": <portfolio volatility % — float>,
    "P1-03": <sharpe ratio target — float>,
    "P1-04": <max drawdown % — float>,
    "P1-05": <beta to market — float>,
    "P1-06": <avg pairwise correlation — float>,
    "P1-07": <number of asset classes — integer as float>,
    "P1-08": <portfolio drift % — float>
  }},
  "asset_allocation": {{"Asset Class": <integer %>}},
  "recommended_mode": "Base or Bull or Bear",
  "commentary_en": "2-3 sentences personalised advice in English",
  "commentary_th": "2-3 sentences personalised advice in Thai",
  "source": "claude"
}}

P1 ranges: P1-01: 4-22 | P1-02: 5-30 | P1-03: 0.3-1.2 | P1-04: 5-40
           P1-05: 0.3-1.6 | P1-06: 0.1-0.8 | P1-07: 2-9 | P1-08: 3-20
Asset allocation must sum to 100.
Be specific, practical, and consider the investor's age, dependents, goals, and behavioural risk tolerance together."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        data.setdefault("source", "claude")
        return data
    except Exception as e:
        st.warning(f"Claude API error: {e}. Falling back to rule-based profile.")
        return None


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def _section_header(text: str):
    st.markdown(
        f"<div style='background:#f0f4ff;border-left:4px solid #4a6cf7;"
        f"padding:8px 14px;border-radius:4px;font-weight:700;margin:18px 0 10px'>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )


def _profile_badge(label: str, color: str):
    st.markdown(
        f"<div style='display:inline-block;background:{color}22;border:2px solid {color};"
        f"border-radius:20px;padding:6px 20px;font-size:1.1rem;font-weight:800;color:{color}'>"
        f"{label}</div>",
        unsafe_allow_html=True,
    )


def _alloc_bars(alloc: dict):
    total = sum(alloc.values()) or 1
    colors = ["#4a6cf7", "#27ae60", "#e67e22", "#c0392b", "#8e44ad", "#16a085", "#f39c12"]
    html = "<div style='margin:10px 0'>"
    for i, (asset, pct) in enumerate(alloc.items()):
        w = pct / total * 100
        c = colors[i % len(colors)]
        html += (
            f"<div style='display:flex;align-items:center;margin:4px 0'>"
            f"<div style='width:140px;font-size:0.82rem;color:#555'>{asset}</div>"
            f"<div style='flex:1;background:#eee;border-radius:4px;height:18px'>"
            f"<div style='width:{w:.0f}%;background:{c};height:18px;border-radius:4px'></div></div>"
            f"<div style='width:40px;text-align:right;font-size:0.82rem;font-weight:600;color:{c}'>"
            f"{pct}%</div></div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _p1_table(p1_values: dict, lang: str):
    rows = []
    for iid, val in p1_values.items():
        lbl_en, lbl_th, unit = P1_LABELS.get(iid, (iid, iid, ""))
        label = lbl_th if lang == "th" else lbl_en
        rows.append(f"<tr><td style='padding:5px 10px;color:#555'>{iid}</td>"
                    f"<td style='padding:5px 10px'>{label}</td>"
                    f"<td style='padding:5px 10px;font-weight:700;text-align:right'>"
                    f"{val:.2f}{(' ' + unit) if unit else ''}</td></tr>")
    st.markdown(
        "<table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        "<thead><tr style='background:#f5f5f5'>"
        "<th style='padding:6px 10px;text-align:left'>ID</th>"
        "<th style='padding:6px 10px;text-align:left'>Indicator</th>"
        "<th style='padding:6px 10px;text-align:right'>Target</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main render function — called from app.py
# ---------------------------------------------------------------------------
def render_profile_tab():
    # Language toggle
    lang = st.radio(
        T["en"]["lang_toggle"],
        ["English", "ภาษาไทย"],
        horizontal=True,
        key="profile_lang",
        label_visibility="collapsed",
    )
    lang = "th" if lang == "ภาษาไทย" else "en"
    tx = T[lang]

    st.markdown(f"### {tx['title']}")
    st.caption(tx["subtitle"])
    st.markdown("---")

    answers: dict = {}
    all_answered = True

    prev_section = 0
    for q in QUESTIONS:
        if q["section"] != prev_section:
            _section_header(tx[f"s{q['section']}"])
            prev_section = q["section"]

        opts = q["opts_th"] if lang == "th" else q["opts_en"]
        label = q["th"] if lang == "th" else q["en"]

        if q["type"] == "multiselect":
            val = st.multiselect(label, opts, key=f"pq_{q['id']}")
            answers[q["id"]] = val
        else:
            val = st.radio(label, opts, index=None, key=f"pq_{q['id']}", horizontal=False)
            answers[q["id"]] = val
            if val is None:
                all_answered = False

    st.markdown("---")

    if st.button(tx["submit"], type="primary", use_container_width=True):
        if not all_answered:
            st.warning(tx["unanswered"])
            return

        # Convert multiselect Thai options back to English for Claude
        answers_en = {}
        for q in QUESTIONS:
            raw = answers[q["id"]]
            if q["type"] == "multiselect":
                if lang == "th" and raw:
                    answers_en[q["id"]] = [
                        q["opts_en"][q["opts_th"].index(v)]
                        for v in raw if v in q["opts_th"]
                    ]
                else:
                    answers_en[q["id"]] = raw
            else:
                if lang == "th" and raw and raw in q["opts_th"]:
                    answers_en[q["id"]] = q["opts_en"][q["opts_th"].index(raw)]
                else:
                    answers_en[q["id"]] = raw

        with st.spinner(tx["generating"]):
            result = claude_profile(answers_en, lang)
            if result is None:
                st.info(tx["fallback"])
                result = rule_based_profile(answers_en)

        st.session_state["investor_profile"] = result

    # ---- Display result if available ----
    result = st.session_state.get("investor_profile")
    if not result:
        return

    st.markdown("---")
    color = result.get("color", "#27ae60")

    # Profile badge
    st.markdown(f"#### {tx['profile_label']}")
    _profile_badge(
        result.get("risk_profile_th" if lang == "th" else "risk_profile_en", ""),
        color,
    )
    src = result.get("source", "")
    st.caption(f"{'Claude AI' if src == 'claude' else 'Rule-based'} · "
               f"{tx['mode_label']}: **{result.get('recommended_mode','Base')}**")

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{tx['alloc_label']}**")
        _alloc_bars(result.get("asset_allocation", {}))

    with col2:
        st.markdown(f"**{tx['p1_label']}**")
        _p1_table(result.get("p1_values", {}), lang)

    st.markdown(f"**{tx['commentary_label']}**")
    commentary = result.get("commentary_th" if lang == "th" else "commentary_en", "")
    st.markdown(
        f"<div style='background:#f9f9f9;border-left:4px solid {color};"
        f"padding:12px 16px;border-radius:6px;font-size:0.92rem;line-height:1.6'>"
        f"{commentary}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    if st.button(tx["apply"], type="primary", use_container_width=True):
        p1_vals = result.get("p1_values", {})
        for iid, val in p1_vals.items():
            st.session_state[f"slider_{iid}"] = float(val)
        st.session_state["profile_applied"] = True
        st.success(tx["applied_ok"])
        st.rerun()
