import html

import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1500px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            min-width: 255px;
            max-width: 255px;
        }

        .app-header {
            padding: 1.35rem 1.6rem;
            border-radius: 14px;
            background: linear-gradient(
                135deg,
                #0b3d91 0%,
                #1769aa 100%
            );
            color: white;
            margin-bottom: 1.25rem;
            box-shadow:
                0 5px 16px
                rgba(0, 0, 0, 0.12);
        }

        .app-header h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.2;
        }

        .app-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.92;
            font-size: 1rem;
        }

        .subtle-card {
            border: 1px solid
                rgba(49, 51, 63, 0.17);
            border-radius: 12px;
            padding: 1rem;
            background:
                rgba(128, 128, 128, 0.04);
        }

        .source-quote {
            border-left: 5px solid #1769aa;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            background:
                rgba(23, 105, 170, 0.06);
            margin-bottom: 1rem;
        }

        .source-quote p {
            margin: 0;
            font-size: 1.03rem;
            line-height: 1.55;
        }

        .breadcrumb {
            opacity: 0.7;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }

        .small-muted {
            opacity: 0.72;
            font-size: 0.88rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    subtitle: str,
) -> None:
    safe_title = html.escape(
        str(title)
    )

    safe_subtitle = html.escape(
        str(subtitle)
    )

    st.markdown(
        f"""
        <div class="app-header">
            <h1>{safe_title}</h1>
            <p>{safe_subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def breadcrumb(text: str) -> None:
    st.markdown(
        f'<div class="breadcrumb">'
        f'{html.escape(text)}'
        f'</div>',
        unsafe_allow_html=True,
    )
