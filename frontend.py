import os
import streamlit as st

from main import run_travel_planner


def _require_env(var_name: str) -> str | None:
    val = os.getenv(var_name)
    if not val:
        return None
    return val


st.set_page_config(
    page_title="Multi-Agent Travel Planner",
    page_icon="🧳",
    layout="wide",
)

# ---- Styling (team-like, classy) ----
st.markdown(
    """
<style>
    .brand {
        font-size: 54px;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }
    .subbrand {
        color: rgba(255,255,255,0.75);
        font-size: 15px;
        margin-bottom: 1.5rem;
    }
    .header-wrap {
        padding: 18px 22px;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(16,185,129,0.18));
        border: 1px solid rgba(255,255,255,0.12);
    }
    .card {
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.10);
    }
    .muted { color: rgba(255,255,255,0.7); }
    div[data-testid="stExpander"] section {
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 10px 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)


st.markdown('<div class="brand">🧳 Multi-Agent Travel Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="subbrand">Flights + Hotels + Itinerary in one smooth run</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


st.write("---")

# ---- Sidebar controls ----
with st.sidebar:
    st.header("Run settings")

    thread_id = st.text_input("thread_id (for checkpoints)", value="1")

    st.caption("Uses your existing multi-agent graph from main.py.")

# ---- Env check (non-blocking) ----
env_issues = []
if not _require_env("DATABASE_URL"):
    env_issues.append("DATABASE_URL")
if not _require_env("TAVILY_API_KEY"):
    env_issues.append("TAVILY_API_KEY")
if not _require_env("AVIATIONSTACK_API_KEY"):
    env_issues.append("AVIATIONSTACK_API_KEY")

if env_issues:
    st.sidebar.warning(
        "Missing env vars: " + ", ".join(env_issues)
        + ". Some features may fail until you set them in .env."
    )


# ---- Main input ----
st.markdown("### Describe your trip")
user_query = st.text_area(
    "What are you looking for?",
    placeholder="e.g., 5-day trip to Paris for a family, prefer central areas and good cafes",
    height=120,
)

run = st.button("✨ Generate my travel plan", type="primary", use_container_width=True)

# ---- Results ----
if run:
    if not user_query.strip():
        st.error("Enter a travel request to begin.")
        st.stop()

    try:
        with st.spinner("Coordinating agents: flights → hotels → itinerary → final response..."):
            result = run_travel_planner(user_input=user_query, thread_id=thread_id)

        # Parse outputs
        flight_info = result.get("flight_info", "")
        hotel_info = result.get("hotel_info", "")
        itinerary_info = result.get("itinerary_info", "")

        messages = result.get("messages", [])
        final_text = ""
        if messages:
            try:
                final_text = messages[-1].content
            except Exception:
                final_text = str(messages[-1])

        llm_calls = result.get("llm_calls", None)

        # Cards + expanders
        st.markdown("## Your plan")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Flights")
                st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Hotels")
                st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Itinerary")
                st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("✈️ Flights (agent output)", expanded=True):
            st.write(flight_info or "No flight information returned.")

        with st.expander("🏨 Hotels (agent output)", expanded=True):
            st.write(hotel_info or "No hotel information returned.")

        with st.expander("🗺️ Itinerary (LLM output)", expanded=True):
            st.write(itinerary_info or "No itinerary returned.")

        with st.expander("✅ Final response", expanded=True):
            st.write(final_text or "No final message returned.")

        with st.expander("🔎 Run metadata", expanded=False):
            meta = {
                "thread_id": thread_id,
                "llm_calls": llm_calls,
            }
            st.json(meta)

    except Exception as e:
        st.exception(e)
        st.error(
            "Run failed. If you recently added env vars, restart the Streamlit app. "
            "Common issues: missing DATABASE_URL / API keys, or network/API timeouts."
        )

