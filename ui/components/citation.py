import html
import streamlit as st


def render_citations(sources):
    """
    Render sources in a minimal GPT-like style.

    Sources appear as part of the assistant response
    without a large surrounding card.
    """

    if not sources:
        return

    items = []

    for source in sources:

        name = html.escape(
            str(source.get("name", "بدون عنوان"))
        )

        page = html.escape(
            str(source.get("page", "-"))
        )

        items.append(
            f"""
            <div class="citation-item">

                <span class="citation-icon">
                    📄
                </span>

                <span class="citation-name">
                    {name}
                </span>

                <span class="citation-page">
                    صفحه {page}
                </span>

            </div>
            """
        )

    html_content = f"""
    <div class="citations-section">

        <div class="citations-title">
            <span>منابع</span>
        </div>

        <div class="citations-list">
            {''.join(items)}
        </div>

    </div>
    """

    st.html(html_content)