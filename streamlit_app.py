import streamlit as st

st.set_page_config(
    page_title="Sleeper",
    page_icon="https://sleeper.com/favicon.ico",
)

draft_assistant = st.Page(
"draft/draft_assistant.py", title="Draft Assistant", icon=":material/dashboard:", default=True
)

draft_reviewer = st.Page(
    "draft/draft_reviewer.py", title="Draft Reviewer", icon=":material/dashboard:", default=True
)

guillotine = st.Page(
    "in-season/guillotine.py", title="Guillotine", icon=":material/dashboard:", default=True
)

pg = st.navigation(
    {
        "Draft": [draft_assistant, draft_reviewer],
        "In-Season": [guillotine]
    }
)

pg.run()