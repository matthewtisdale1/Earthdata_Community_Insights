import streamlit as st

import api_client as api
from navigation import goto_tool
from styles import page_header


def render() -> None:
    page_header(
        "Earthdata Tools",
        "Explore the first Earthdata applications and services being connected to community needs and implementation artifacts.",
    )

    tools = api.get("/tools")

    if not tools:
        st.info("No Earthdata tools are currently registered.")
        return

    totals = st.columns(4)
    totals[0].metric("Tools", len(tools))
    totals[1].metric("Repositories and sources", sum(int(tool.get("source_count") or 0) for tool in tools))
    totals[2].metric("Implementation artifacts", sum(int(tool.get("artifact_count") or 0) for tool in tools))
    totals[3].metric("Releases", sum(int(tool.get("release_count") or 0) for tool in tools))

    st.caption(
        "Artifact totals will remain zero until the GitHub synchronization worker is added and run."
    )

    st.divider()

    for tool in tools:
        with st.container(border=True):
            heading, action = st.columns([5, 1.2])

            with heading:
                st.subheader(tool["tool_name"])
                st.caption(tool.get("tool_type") or "Earthdata tool or service")
                st.write(tool.get("description") or "No description recorded.")

            with action:
                if st.button(
                    "Open tool",
                    key=f'open_tool_{tool["tool_code"]}',
                    use_container_width=True,
                ):
                    goto_tool(tool["tool_code"])

            metrics = st.columns(5)
            metrics[0].metric("Sources", int(tool.get("source_count") or 0))
            metrics[1].metric("Artifacts", int(tool.get("artifact_count") or 0))
            metrics[2].metric("Issues", int(tool.get("issue_count") or 0))
            metrics[3].metric("Pull requests", int(tool.get("pull_request_count") or 0))
            metrics[4].metric("Releases", int(tool.get("release_count") or 0))
