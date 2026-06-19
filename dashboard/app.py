import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "backend" / "data" / "calls.db"
ENV_PATH = ROOT_DIR / "backend" / ".env"
ENV_VALUES = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

DEFAULT_API_URL = os.getenv(
    "API_BASE_URL",
    "https://past-claudie-happyrobot-take-home-challenge-9a010a0d.koyeb.app",
)
DEFAULT_API_KEY = ENV_VALUES.get("API_KEY", "")

st.set_page_config(
    page_title="Carrier Sales Console",
    page_icon=":truck:",
    layout="wide",
)


def get_theme_palette(theme_mode: str) -> dict[str, str]:

    if theme_mode == "Light":
        return {
            "app_bg": """
                radial-gradient(circle at top left, rgba(44, 110, 129, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(214, 151, 83, 0.12), transparent 24%),
                linear-gradient(180deg, #f7f4ef 0%, #efe7dd 100%)
            """,
            "text": "#1a232c",
            "sidebar_bg": "linear-gradient(180deg, #22404c 0%, #1a313a 100%)",
            "hero_bg": "linear-gradient(135deg, #23414b 0%, #2f5f6b 56%, #cf8a43 100%)",
            "hero_text": "#fff9f1",
            "card_bg": "rgba(255, 252, 248, 0.92)",
            "card_border": "rgba(24, 35, 33, 0.08)",
            "card_shadow": "0 16px 38px rgba(25, 35, 33, 0.07)",
            "kpi_bg": "linear-gradient(180deg, #fffdf9 0%, #f6eee3 100%)",
            "muted": "#5f6b76",
            "strong": "#1b2d38",
            "pill_bg": "#e7f0f5",
            "pill_text": "#23414b",
            "control_bg": "linear-gradient(180deg, #fff9f0 0%, #f6efe6 100%)",
            "tip_bg": "rgba(215, 153, 83, 0.12)",
            "tip_text": "#714b1c",
            "response_bg": "#eef4f7",
            "response_text": "#1b2d38",
            "chip_bg": "#fff1db",
            "chip_text": "#86551a",
            "button_bg": "#fffaf4",
            "button_text": "#23414b",
            "button_border": "rgba(35, 65, 75, 0.12)",
            "button_hover_bg": "#f3eee7",
            "button_hover_border": "rgba(35, 65, 75, 0.24)",
            "button_primary_bg": "linear-gradient(135deg, #cf8a43 0%, #ba7232 100%)",
            "tab_bg": "rgba(255, 250, 244, 0.82)",
            "tab_text": "#51616d",
            "tab_active_bg": "#23414b",
            "tab_active_text": "#fffaf2",
            "chat_assistant_bg": "rgba(236, 244, 248, 0.95)",
            "chat_user_bg": "rgba(227, 229, 233, 0.95)",
            "chat_text": "#18232d",
            "chat_input_bg": "#ffffff",
            "metric_text": "#1b2d38",
            "dataframe_bg": "rgba(255, 252, 248, 0.92)",
        }

    return {
        "app_bg": """
            radial-gradient(circle at top left, rgba(54, 136, 156, 0.18), transparent 30%),
            radial-gradient(circle at top right, rgba(214, 151, 83, 0.12), transparent 24%),
            linear-gradient(180deg, #0f1419 0%, #171f27 100%)
        """,
        "text": "#ecf1f7",
        "sidebar_bg": "linear-gradient(180deg, #203640 0%, #182a32 100%)",
        "hero_bg": "linear-gradient(135deg, #1c2c35 0%, #24505c 56%, #c9853c 100%)",
        "hero_text": "#fff9f1",
        "card_bg": "rgba(23, 31, 39, 0.92)",
        "card_border": "rgba(124, 146, 164, 0.14)",
        "card_shadow": "0 16px 38px rgba(0, 0, 0, 0.22)",
        "kpi_bg": "linear-gradient(180deg, #1b2630 0%, #141c23 100%)",
        "muted": "#9ca9b5",
        "strong": "#f6f8fb",
        "pill_bg": "#243746",
        "pill_text": "#eff5fb",
        "control_bg": "linear-gradient(180deg, #1a242c 0%, #141d24 100%)",
        "tip_bg": "rgba(215, 153, 83, 0.12)",
        "tip_text": "#f2d3a9",
        "response_bg": "#1b2833",
        "response_text": "#eff4fa",
        "chip_bg": "#2d3944",
        "chip_text": "#ffd39c",
        "button_bg": "#202b35",
        "button_text": "#eff4fa",
        "button_border": "rgba(124, 146, 164, 0.18)",
        "button_hover_bg": "#263540",
        "button_hover_border": "rgba(190, 214, 232, 0.34)",
        "button_primary_bg": "linear-gradient(135deg, #d18a42 0%, #bb7130 100%)",
        "tab_bg": "rgba(25, 35, 44, 0.85)",
        "tab_text": "#cdd8e3",
        "tab_active_bg": "#d18a42",
        "tab_active_text": "#fffaf2",
        "chat_assistant_bg": "rgba(31, 44, 56, 0.72)",
        "chat_user_bg": "rgba(48, 54, 61, 0.9)",
        "chat_text": "#f4f7fb",
        "chat_input_bg": "#1a242d",
        "metric_text": "#eef4fa",
        "dataframe_bg": "rgba(23, 31, 39, 0.92)",
    }


def inject_styles(theme_mode: str):

    palette = get_theme_palette(theme_mode)

    css = """
        <style>
        .stApp {
            background: __APP_BG__;
            color: __TEXT__;
        }
        .block-container {
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            background: __SIDEBAR_BG__;
        }
        [data-testid="stSidebar"] * {
            color: #f7f4ef !important;
        }
        [data-testid="stSidebar"] input {
            background: rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
        }
        .hero {
            padding: 1.5rem 1.7rem;
            border-radius: 28px;
            background: __HERO_BG__;
            color: __HERO_TEXT__;
            box-shadow: 0 24px 52px rgba(23, 40, 47, 0.18);
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.5rem;
            line-height: 1.05;
        }
        .hero p {
            margin: 0.55rem 0 0;
            max-width: 58rem;
            font-size: 1rem;
            color: rgba(255, 248, 239, 0.9);
        }
        .section-card {
            border-radius: 24px;
            padding: 1.1rem 1.15rem;
            background: __CARD_BG__;
            border: 1px solid __CARD_BORDER__;
            box-shadow: __CARD_SHADOW__;
        }
        .kpi-card {
            position: relative;
            border-radius: 20px;
            padding: 1.35rem 1.25rem 1.2rem 1.5rem;
            background: __KPI_BG__;
            border: 1px solid __CARD_BORDER__;
            min-height: 156px;
            overflow: hidden;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }
        .kpi-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 5px;
            background: var(--kpi-accent, #d79953);
        }
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: __CARD_SHADOW__;
        }
        .kpi-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 700;
            color: __MUTED__;
        }
        .kpi-value {
            font-size: 2.55rem;
            font-weight: 800;
            line-height: 1.04;
            letter-spacing: -0.02em;
            color: __STRONG__;
            margin-top: 0.55rem;
        }
        .kpi-sub {
            color: __MUTED__;
            font-size: 0.82rem;
            margin-top: 0.4rem;
        }
        .status-pill {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: __PILL_BG__;
            color: __PILL_TEXT__;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }
        .control-card {
            padding: 0.85rem 1rem;
            border-radius: 18px;
            background: __CONTROL_BG__;
            border: 1px solid __CARD_BORDER__;
            margin-bottom: 0.9rem;
        }
        .control-card h4 {
            margin: 0;
            color: __STRONG__;
            font-size: 1rem;
        }
        .control-card p {
            margin: 0.35rem 0 0;
            color: __MUTED__;
            font-size: 0.9rem;
        }
        .bot-tip {
            border-left: 4px solid #d79953;
            padding: 0.8rem 0.9rem;
            background: __TIP_BG__;
            border-radius: 0 16px 16px 0;
            color: __TIP_TEXT__;
            margin-bottom: 0.9rem;
        }
        .agent-response {
            background: __RESPONSE_BG__;
            border: 1px solid __CARD_BORDER__;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-top: 0.5rem;
            color: __RESPONSE_TEXT__;
        }
        .scenario-chip {
            display: inline-block;
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: __CHIP_BG__;
            color: __CHIP_TEXT__;
            font-size: 0.78rem;
            font-weight: 700;
            margin: 0 0.35rem 0.35rem 0;
        }
        .stButton > button {
            height: 2.85rem;
            border-radius: 14px;
            border: 1px solid __BUTTON_BORDER__;
            background: __BUTTON_BG__;
            color: __BUTTON_TEXT__;
            font-weight: 700;
            transition: all 0.18s ease;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
        }
        .stButton > button:hover {
            border-color: __BUTTON_HOVER_BORDER__;
            background: __BUTTON_HOVER_BG__;
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: __BUTTON_PRIMARY_BG__;
            color: #fffaf2;
            border: 1px solid rgba(209, 138, 66, 0.2);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: __TAB_BG__;
            border-radius: 999px;
            padding: 0.35rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            height: 2.6rem;
            padding: 0 1rem;
            font-weight: 700;
            color: __TAB_TEXT__;
        }
        .stTabs [aria-selected="true"] {
            background: __TAB_ACTIVE_BG__ !important;
            color: __TAB_ACTIVE_TEXT__ !important;
        }
        [data-testid="stChatMessage"] {
            background: transparent !important;
        }
        [data-testid="stChatMessageContent"] {
            color: __CHAT_TEXT__ !important;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
            color: __CHAT_TEXT__ !important;
            font-size: 1.02rem;
            line-height: 1.55;
        }
        [data-testid="stChatMessage"]:has([aria-label="assistant message"]) {
            background: __CHAT_ASSISTANT_BG__ !important;
            border: 1px solid __CARD_BORDER__;
            border-radius: 20px;
            padding: 0.35rem 0.55rem;
            margin-bottom: 0.75rem;
        }
        [data-testid="stChatMessage"]:has([aria-label="user message"]) {
            background: __CHAT_USER_BG__ !important;
            border: 1px solid __CARD_BORDER__;
            border-radius: 20px;
            padding: 0.35rem 0.55rem;
            margin-bottom: 0.75rem;
        }
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {
            background: __CHAT_INPUT_BG__ !important;
            color: __CHAT_TEXT__ !important;
        }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: __METRIC_TEXT__ !important;
        }
        [data-testid="stDataFrame"] {
            background: __DATAFRAME_BG__;
        }
        </style>
        """

    replacements = {
        "__APP_BG__": palette["app_bg"],
        "__TEXT__": palette["text"],
        "__SIDEBAR_BG__": palette["sidebar_bg"],
        "__HERO_BG__": palette["hero_bg"],
        "__HERO_TEXT__": palette["hero_text"],
        "__CARD_BG__": palette["card_bg"],
        "__CARD_BORDER__": palette["card_border"],
        "__CARD_SHADOW__": palette["card_shadow"],
        "__KPI_BG__": palette["kpi_bg"],
        "__MUTED__": palette["muted"],
        "__STRONG__": palette["strong"],
        "__PILL_BG__": palette["pill_bg"],
        "__PILL_TEXT__": palette["pill_text"],
        "__CONTROL_BG__": palette["control_bg"],
        "__TIP_BG__": palette["tip_bg"],
        "__TIP_TEXT__": palette["tip_text"],
        "__RESPONSE_BG__": palette["response_bg"],
        "__RESPONSE_TEXT__": palette["response_text"],
        "__CHIP_BG__": palette["chip_bg"],
        "__CHIP_TEXT__": palette["chip_text"],
        "__BUTTON_BG__": palette["button_bg"],
        "__BUTTON_TEXT__": palette["button_text"],
        "__BUTTON_BORDER__": palette["button_border"],
        "__BUTTON_HOVER_BG__": palette["button_hover_bg"],
        "__BUTTON_HOVER_BORDER__": palette["button_hover_border"],
        "__BUTTON_PRIMARY_BG__": palette["button_primary_bg"],
        "__TAB_BG__": palette["tab_bg"],
        "__TAB_TEXT__": palette["tab_text"],
        "__TAB_ACTIVE_BG__": palette["tab_active_bg"],
        "__TAB_ACTIVE_TEXT__": palette["tab_active_text"],
        "__CHAT_ASSISTANT_BG__": palette["chat_assistant_bg"],
        "__CHAT_USER_BG__": palette["chat_user_bg"],
        "__CHAT_TEXT__": palette["chat_text"],
        "__CHAT_INPUT_BG__": palette["chat_input_bg"],
        "__METRIC_TEXT__": palette["metric_text"],
        "__DATAFRAME_BG__": palette["dataframe_bg"],
    }

    for token, value in replacements.items():
        css = css.replace(token, value)

    st.markdown(css, unsafe_allow_html=True)


def load_calls_dataframe(api_url: str | None = None, api_key: str | None = None) -> pd.DataFrame:

    columns = [
        "id",
        "mc_number",
        "load_id",
        "outcome",
        "sentiment",
        "final_rate",
        "carrier_approved",
        "negotiation_rounds",
        "carrier_offer",
        "counter_offer",
        "transcript",
        "carrier_name",
        "data_source",
        "created_at",
    ]

    df = None

    # Preferred path: read over HTTP via GET /calls so the dashboard can run as a
    # fully separate service/container from the API (no shared database volume).
    if api_url and api_key:
        try:
            payload = safe_get(api_url, api_key, "/calls?limit=500")
            records = payload.get("records", []) if isinstance(payload, dict) else []
            df = pd.DataFrame(records)
        except Exception:
            df = None

    # Fallback: read the local SQLite file directly (single-host / local dev).
    if df is None:
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql("SELECT * FROM calls", conn)
        except Exception:
            df = pd.DataFrame(columns=columns)
        finally:
            conn.close()

    if df is None or df.empty:
        df = pd.DataFrame(columns=columns)

    df = df.drop(columns=[c for c in ("summary", "extracted_data") if c in df.columns])

    if "created_at" in df.columns and not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    if "carrier_approved" in df.columns and not df.empty:
        df["carrier_approved"] = df["carrier_approved"].fillna(0).astype(int)

    return df


def initialize_state():

    st.session_state.setdefault("agent_session_id", None)
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("agent_stage", "not_started")
    st.session_state.setdefault("agent_result", None)
    st.session_state.setdefault("agent_context", {})
    st.session_state.setdefault("theme_mode", "Dark")


def api_headers(api_key: str) -> dict[str, str]:

    return {"x-api-key": api_key}


def safe_post(api_url: str, api_key: str, path: str, payload: dict | None = None) -> dict:

    response = requests.post(
        f"{api_url}{path}",
        headers=api_headers(api_key),
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def safe_get(api_url: str, api_key: str, path: str) -> dict:

    response = requests.get(
        f"{api_url}{path}",
        headers=api_headers(api_key),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def start_new_call(api_url: str, api_key: str):

    data = safe_post(api_url, api_key, "/agent/session")
    st.session_state.agent_session_id = data["session_id"]
    st.session_state.agent_stage = data["stage"]
    st.session_state.agent_result = None
    st.session_state.agent_context = {}
    st.session_state.chat_messages = [
        {"role": "assistant", "content": data["response"]}
    ]


def continue_call(api_url: str, api_key: str, utterance: str):

    data = safe_post(
        api_url,
        api_key,
        "/agent/respond",
        {
            "session_id": st.session_state.agent_session_id,
            "utterance": utterance,
        },
    )

    st.session_state.chat_messages.append({"role": "user", "content": utterance})
    st.session_state.chat_messages.append(
        {"role": "assistant", "content": data["response"]}
    )
    st.session_state.agent_stage = data.get("stage", st.session_state.agent_stage)
    st.session_state.agent_result = data.get("result")
    st.session_state.agent_context = {
        key: value
        for key, value in data.items()
        if key not in {"session_id", "stage", "response", "result"}
    }


def render_hero():

    st.markdown(
        """
        <div class="hero">
            <h1>Inbound Carrier Sales</h1>
            <p>
                Inbound carrier sales automation metrics and call outcomes
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, subtext: str, accent: str = "#d79953"):

    st.markdown(
        f"""
        <div class="kpi-card" style="--kpi-accent: {accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_playground(api_url: str, api_key: str):

    left_col, right_col = st.columns([1.45, 1], gap="large")

    with left_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Bot Playground")
        st.markdown(
            """
            <div class="bot-tip">
                Start a new call, then speak like a carrier. Try an MC number first,
                then a lane like "Dallas to Atlanta dry van", then your rate.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div>
                <span class="scenario-chip">1. Verify MC</span>
                <span class="scenario-chip">2. Match lane</span>
                <span class="scenario-chip">3. Negotiate rate</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="control-card">
                <h4>Call Controls</h4>
                <p>Use one primary action to start the workflow, then use the chat box below for the carrier side.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_col1, action_col2, action_col3 = st.columns([1, 1, 1.1])

        with action_col1:
            if st.button("Start New Call", type="primary", width="stretch"):
                try:
                    start_new_call(api_url, api_key)
                except requests.RequestException as exc:
                    st.error(f"Could not start session: {exc}")

        with action_col2:
            if st.button("Run Booked Demo", width="stretch"):
                try:
                    start_new_call(api_url, api_key)
                    continue_call(api_url, api_key, "My MC is 123456")
                    continue_call(api_url, api_key, "Dallas to Atlanta dry van")
                    continue_call(api_url, api_key, "I can do it for 1850")
                except requests.RequestException as exc:
                    st.error(f"Demo failed: {exc}")

        with action_col3:
            if st.button("Clear Session", width="stretch"):
                st.session_state.agent_session_id = None
                st.session_state.chat_messages = []
                st.session_state.agent_stage = "not_started"
                st.session_state.agent_result = None
                st.session_state.agent_context = {}

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input(
            "Type what the carrier says...",
            disabled=st.session_state.agent_session_id is None
            or st.session_state.agent_stage == "closed",
        )

        if prompt:
            try:
                continue_call(api_url, api_key, prompt)
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Could not reach bot: {exc}")

        if st.session_state.agent_session_id is None:
            st.info("Start a new call to begin testing the bot.")
        elif st.session_state.agent_stage == "closed":
            st.success("Call complete. Start a new call to test another scenario.")
            if st.session_state.agent_result:
                st.caption(
                    f"Saved to call records as record #{st.session_state.agent_result['record_id']}."
                )

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Live Call State")
        stage = st.session_state.agent_stage.replace("_", " ").title()
        st.markdown(
            f'<span class="status-pill">Stage: {stage}</span>',
            unsafe_allow_html=True,
        )
        if st.session_state.agent_result:
            st.markdown(
                f'<span class="status-pill">Outcome: {st.session_state.agent_result["outcome"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="status-pill">Final Rate: ${st.session_state.agent_result["final_rate"]}</span>',
                unsafe_allow_html=True,
            )

        context = st.session_state.agent_context

        if context.get("matched_load"):
            st.markdown("**Matched Load**")
            st.json(context["matched_load"], expanded=False)

        if context.get("negotiation"):
            st.markdown("**Negotiation Snapshot**")
            st.json(context["negotiation"], expanded=False)

        if st.session_state.agent_result:
            st.markdown("**Final Result**")
            st.json(st.session_state.agent_result, expanded=False)

        if not context and not st.session_state.agent_result:
            st.markdown(
                '<div class="agent-response">The bot context will appear here as the conversation advances.</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def prettify_label(value: str) -> str:
    """Turn database codes like NEGOTIATION_FAILED into plain text: 'Negotiation Failed'."""

    return str(value).replace("_", " ").title()


def style_chart(fig, palette: dict[str, str], *, integer_y: bool = False):
    """Apply clean, readable styling so non-technical viewers can read charts at a glance."""

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=palette["text"], size=14),
        margin=dict(t=24, r=16, b=8, l=8),
        hoverlabel=dict(font_size=13),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    fig.update_xaxes(showgrid=False, title_font=dict(size=13))
    fig.update_yaxes(gridcolor="rgba(140,150,160,0.18)", zeroline=False, title_font=dict(size=13))
    if integer_y:
        fig.update_yaxes(dtick=1, rangemode="tozero")
    return fig


def render_ops_dashboard(df: pd.DataFrame):

    palette = get_theme_palette(st.session_state.get("theme_mode", "Dark"))

    with st.sidebar:
        st.header("Ops Filters")
        outcome_filter = st.multiselect(
            "Outcome",
            options=sorted(df["outcome"].dropna().unique()) if "outcome" in df.columns else [],
        )
        sentiment_filter = st.multiselect(
            "Sentiment",
            options=sorted(df["sentiment"].dropna().unique()) if "sentiment" in df.columns else [],
        )
        load_filter = st.multiselect(
            "Load ID",
            options=sorted(df["load_id"].dropna().unique()) if "load_id" in df.columns else [],
        )

    filtered_df = df.copy()

    if outcome_filter:
        filtered_df = filtered_df[filtered_df["outcome"].isin(outcome_filter)]

    if sentiment_filter:
        filtered_df = filtered_df[filtered_df["sentiment"].isin(sentiment_filter)]

    if load_filter:
        filtered_df = filtered_df[filtered_df["load_id"].isin(load_filter)]

    total_calls = len(filtered_df)
    booked_calls = len(filtered_df[filtered_df["outcome"] == "BOOKED"])
    failed_calls = len(filtered_df[filtered_df["outcome"] == "NEGOTIATION_FAILED"])
    ineligible_calls = len(filtered_df[filtered_df["outcome"] == "CARRIER_NOT_ELIGIBLE"])
    avg_rate = round(filtered_df["final_rate"].fillna(0).mean(), 2) if total_calls > 0 else 0
    avg_rounds = (
        round(filtered_df["negotiation_rounds"].fillna(0).mean(), 2)
        if total_calls > 0 and "negotiation_rounds" in filtered_df.columns
        else 0
    )
    failed_total = failed_calls + ineligible_calls
    success_rate = round((booked_calls / total_calls) * 100, 1) if total_calls > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_kpi_card(
            "Total Calls", str(total_calls), "All logged inbound interactions", accent="#3a7d8c"
        )
    with kpi2:
        render_kpi_card(
            "Booked Loads", str(booked_calls), "Calls that reached handoff", accent="#2e8b6f"
        )
    with kpi3:
        render_kpi_card(
            "Failed Negotiations",
            str(failed_total),
            "Negotiation failures and ineligible carriers",
            accent="#c0563f",
        )
    with kpi4:
        render_kpi_card(
            "Booking Success Rate",
            f"{success_rate}%",
            "Share of calls that booked",
            accent="#7a5cc0",
        )
    with kpi5:
        render_kpi_card(
            "Average Final Rate", f"${avg_rate}", f"{avg_rounds} avg rounds", accent="#d79953"
        )

    st.markdown("")
    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Call Outcomes")
        st.caption("What happened on each call — how many were booked, declined, or failed.")
        if total_calls > 0:
            outcome_counts = filtered_df["outcome"].value_counts().reset_index()
            outcome_counts.columns = ["Outcome", "Count"]
            outcome_counts["Outcome"] = outcome_counts["Outcome"].map(prettify_label)
            outcome_fig = px.pie(
                outcome_counts,
                names="Outcome",
                values="Count",
                hole=0.45,
                color_discrete_sequence=["#2e8b6f", "#d89f5c", "#7a8f86", "#c0563f", "#48616f"],
            )
            outcome_fig.update_traces(
                textposition="inside",
                texttemplate="%{value} (%{percent})",
                hovertemplate="%{label}: %{value} calls (%{percent})<extra></extra>",
                insidetextfont=dict(color="#ffffff", size=15),
            )
            style_chart(outcome_fig, palette)
            st.plotly_chart(outcome_fig, width="stretch")
        else:
            st.info("No calls available for the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Sentiment Analysis")
        st.caption("The mood of the carrier during the call. A taller bar means more calls.")
        if total_calls > 0:
            sentiment_counts = filtered_df["sentiment"].value_counts().reset_index()
            sentiment_counts.columns = ["Sentiment", "Calls"]
            sentiment_counts["Sentiment"] = sentiment_counts["Sentiment"].map(prettify_label)
            sentiment_fig = px.bar(
                sentiment_counts,
                x="Sentiment",
                y="Calls",
                color="Sentiment",
                text="Calls",
                color_discrete_map={
                    "Positive": "#2e8b6f",
                    "Neutral": "#d89f5c",
                    "Negative": "#c0563f",
                },
            )
            sentiment_fig.update_traces(
                textposition="outside",
                hovertemplate="%{x}: %{y} calls<extra></extra>",
            )
            sentiment_fig.update_layout(showlegend=False)
            sentiment_fig.update_xaxes(title_text="")
            sentiment_fig.update_yaxes(title_text="Number of Calls")
            style_chart(sentiment_fig, palette, integer_y=True)
            st.plotly_chart(sentiment_fig, width="stretch")
        else:
            st.info("No calls available for the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    chart_col3, chart_col4 = st.columns(2, gap="large")

    with chart_col3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Calls per Load")
        st.caption("How many calls each load received. The number on each bar is the call count.")
        if total_calls > 0:
            load_stats = (
                filtered_df.groupby("load_id")["final_rate"]
                .agg(["count", "mean"])
                .reset_index()
            )
            load_stats.columns = ["Load", "Calls", "Average Final Rate"]
            load_stats["Average Final Rate"] = load_stats["Average Final Rate"].fillna(0).round(0)
            load_fig = px.bar(
                load_stats,
                x="Load",
                y="Calls",
                text="Calls",
                custom_data=["Average Final Rate"],
            )
            load_fig.update_traces(
                marker_color="#3a7d8c",
                textposition="outside",
                hovertemplate="Load %{x}<br>%{y} calls<br>Avg final rate: $%{customdata[0]:,.0f}<extra></extra>",
            )
            load_fig.update_xaxes(title_text="Load")
            load_fig.update_yaxes(title_text="Number of Calls")
            style_chart(load_fig, palette, integer_y=True)
            st.plotly_chart(load_fig, width="stretch")
        else:
            st.info("No calls available for the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Carriers Approved vs Rejected")
        st.caption("How many carriers passed the eligibility check versus how many did not.")
        if total_calls > 0 and "carrier_approved" in filtered_df.columns:
            approval_stats = pd.DataFrame(
                {
                    "Status": ["Approved", "Rejected"],
                    "Calls": [
                        int(filtered_df["carrier_approved"].sum()),
                        int(total_calls - filtered_df["carrier_approved"].sum()),
                    ],
                }
            )
            approval_fig = px.bar(
                approval_stats,
                x="Status",
                y="Calls",
                color="Status",
                text="Calls",
                color_discrete_map={
                    "Approved": "#2e8b6f",
                    "Rejected": "#c0563f",
                },
            )
            approval_fig.update_traces(
                textposition="outside",
                hovertemplate="%{x}: %{y} carriers<extra></extra>",
            )
            approval_fig.update_layout(showlegend=False)
            approval_fig.update_xaxes(title_text="")
            approval_fig.update_yaxes(title_text="Number of Carriers")
            style_chart(approval_fig, palette, integer_y=True)
            st.plotly_chart(approval_fig, width="stretch")
        else:
            st.info("No approval data available for the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Call Records")
    st.caption("Newest completed calls appear at the top of the table.")
    st.dataframe(filtered_df.sort_values("id", ascending=False), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Booking Success Rate")
    if total_calls > 0:
        st.progress(min(int(success_rate), 100))
        st.write(f"Booking Rate: {success_rate}%")
    else:
        st.info("No call data available yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar_connection(api_url: str, api_key: str):

    with st.sidebar:
        st.header("Control Panel")
        st.caption("Connection settings for the playground.")
        theme_mode = st.segmented_control(
            "Appearance",
            options=["Dark", "Light"],
            default=st.session_state.get("theme_mode", "Dark"),
        )
        st.session_state["theme_mode"] = theme_mode or "Dark"
        with st.expander("API Connection", expanded=True):
            api_url = st.text_input("API Base URL", value=api_url)
            api_key = st.text_input("API Key", value=api_key, type="password")
        st.session_state["api_url"] = api_url
        st.session_state["api_key"] = api_key
        connection_ok = False
        error_message = None

        try:
            response = safe_get(api_url, api_key, "/health")
            connection_ok = response.get("status") == "running"
        except requests.RequestException as exc:
            error_message = str(exc)

        if connection_ok:
            st.success(f"API connected: {api_url}")
        else:
            st.error("API not reachable")
            if error_message:
                st.caption(error_message)

        st.caption("HappyRobot should point to the same API base URL when you deploy it.")

    return api_url, api_key, st.session_state["theme_mode"]


def main():

    initialize_state()
    inject_styles(st.session_state.get("theme_mode", "Dark"))
    render_hero()

    api_url = st.session_state.get("api_url", DEFAULT_API_URL)
    api_key = st.session_state.get("api_key", DEFAULT_API_KEY)
    st.session_state["api_url"] = api_url
    st.session_state["api_key"] = api_key

    api_url, api_key, theme_mode = render_sidebar_connection(api_url, api_key)
    inject_styles(theme_mode)

    playground_tab, dashboard_tab = st.tabs(["Bot Playground", "Ops Dashboard"])

    with playground_tab:
        render_agent_playground(api_url, api_key)

    with dashboard_tab:
        df = load_calls_dataframe(api_url, api_key)
        render_ops_dashboard(df)


if __name__ == "__main__":
    main()
