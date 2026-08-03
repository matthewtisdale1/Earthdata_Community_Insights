import pandas as pd
import streamlit as st

import api_client as api
from navigation import tools_link
from styles import breadcrumb, page_header


def render() -> None:
    tool_code = st.session_state.get("selected_tool_code")

    if not tool_code:
        st.warning("No Earthdata tool was selected.")
        tools_link(label="Return to Earthdata Tools")
        return

    detail = api.get(f"/tools/{tool_code}")
    tool = detail["tool"]
    sources = detail["sources"]
    artifact_counts = detail["artifact_counts"]
    recent_artifacts = detail["recent_artifacts"]

    breadcrumb("Earthdata Tools › Tool Details")
    page_header(tool["tool_name"], tool.get("description") or "Earthdata tool or service")

    metrics = st.columns(5)
    metrics[0].metric("Sources", int(tool.get("source_count") or 0))
    metrics[1].metric("Artifacts", int(tool.get("artifact_count") or 0))
    metrics[2].metric("Issues", int(tool.get("issue_count") or 0))
    metrics[3].metric("Pull requests", int(tool.get("pull_request_count") or 0))
    metrics[4].metric("Releases", int(tool.get("release_count") or 0))

    overview_tab, sources_tab, artifacts_tab = st.tabs(
        ["Overview", f"Sources ({len(sources)})", f"Artifacts ({len(recent_artifacts)})"]
    )

    with overview_tab:
        left, right = st.columns([2, 1], gap="large")

        with left:
            st.subheader("About this tool")
            st.write(tool.get("description") or "No description has been recorded.")

        with right:
            with st.container(border=True):
                st.markdown("#### Catalog details")
                st.write(f'**Tool code:** {tool["tool_code"]}')
                st.write(f'**Type:** {tool.get("tool_type") or "Not classified"}')
                st.write(f'**Active:** {"Yes" if tool.get("active") else "No"}')
                if tool.get("homepage_url"):
                    st.link_button("Open official website", tool["homepage_url"], use_container_width=True)
                if tool.get("last_synced_at"):
                    st.write(f'**Last synchronized:** {tool["last_synced_at"]}')
                else:
                    st.write("**Last synchronized:** Not yet synchronized")

    with sources_tab:
        if not sources:
            st.info("No repositories or external sources are registered for this tool.")
        else:
            for source in sources:
                with st.container(border=True):
                    st.markdown(f'### {source.get("owner_name")}/{source.get("repository_name")}')
                    st.caption(source.get("source_kind") or "External source")
                    cols = st.columns(3)
                    cols[0].write(f'**Sync enabled:** {"Yes" if source.get("sync_enabled") else "No"}')
                    cols[1].write(f'**Status:** {source.get("sync_status") or "Not run"}')
                    cols[2].write(f'**Last sync:** {source.get("last_synced_at") or "Never"}')
                    if source.get("base_url"):
                        st.link_button("Open source", source["base_url"])
                    if source.get("sync_error"):
                        st.error(source["sync_error"])

    with artifacts_tab:
        if artifact_counts:
            st.subheader("Artifact totals")
            st.dataframe(pd.DataFrame(artifact_counts), hide_index=True, use_container_width=True)

        if not recent_artifacts:
            st.info(
                "No implementation artifacts have been imported yet. This section will populate after the GitHub synchronizer is added and run."
            )
        else:
            st.subheader("Recent artifacts")
            st.dataframe(pd.DataFrame(recent_artifacts), hide_index=True, use_container_width=True)

    st.divider()
    tools_link()
