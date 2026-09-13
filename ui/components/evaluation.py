import streamlit as st


def render_evaluation(scores):
    """
    Render response evaluation in a minimal GPT-like style.

    Evaluation appears as lightweight metadata below the assistant
    response instead of a separate card.

    نکته‌ی مهم: مسیرهایی مثل greeting/calculator/summarize/compare
    اصلاً از ResponseValidator رد نمی‌شن، پس validation_result براشون
    خالیه ({}) و مقدار هر معیار می‌شه None - این تابع باید بدون کرش
    این حالت رو مدیریت کنه (و چیزی نمایش نده).

    همچنین هر معیار از ResponseValidator به‌صورت دیکشنری برمی‌گرده
    (مثل {"score": 7, "reason": "..."}) با نمره‌ی ۰ تا ۱۰، نه یک عدد
    خام بین ۰ و ۱ - پس هم باید مقدار "score" رو از دلش دربیاریم، هم
    مقیاسش رو درست به درصد تبدیل کنیم.
    """

    if not scores:
        return

    def extract_score(value):
        """از dict یا عدد خام، نمره‌ی خام (۰ تا ۱۰) رو استخراج می‌کنه."""
        if value is None:
            return None
        if isinstance(value, dict):
            value = value.get("score")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def to_percent(value):
        """نمره‌ی خام (۰ تا ۱۰) رو به درصد تبدیل می‌کنه؛ اگه معتبر نبود None برمی‌گردونه."""
        score = extract_score(value)
        if score is None:
            return None
        return max(0, min(100, int(round(score * 10))))

    relevance = to_percent(scores.get("relevance"))
    completeness = to_percent(scores.get("completeness"))
    faithfulness = to_percent(scores.get("faithfulness"))

    # اگه هیچ معیار معتبری نبود (مثلاً مسیر greeting/calculator بوده)،
    # اصلاً چیزی نمایش نده - به‌جای نمایش گمراه‌کننده‌ی "0%"
    if relevance is None and completeness is None and faithfulness is None:
        return

    def render_row(label, value):
        display = f"{value}%" if value is not None else "—"
        return f"""
            <div class="evaluation-item">
                <span>{label}</span>
                <strong>{display}</strong>
            </div>
        """

    html = f"""
    <div class="evaluation-section">

        <div class="evaluation-title">
            ارزیابی پاسخ
        </div>

        <div class="evaluation-items">
            {render_row("ارتباط", relevance)}
            {render_row("کامل بودن", completeness)}
            {render_row("صحت", faithfulness)}
        </div>

    </div>
    """

    st.html(html)