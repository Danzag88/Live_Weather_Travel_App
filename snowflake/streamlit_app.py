"""
Snowflake Streamlit app: manage who receives the Live Weather Travel dashboard.

Reads and writes SHARED_DB.PUBLIC.EMAIL_RECIPIENTS. The primary key is
(EMAIL_ADDRESS, INTEGRATION_SCOPE, ENVIRONMENT, STATUS_SCOPE).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

RECIPIENTS_TABLE = "SHARED_DB.PUBLIC.EMAIL_RECIPIENTS"

INTEGRATION_SCOPES = ("ALL", "DAILY_APP")
RECIPIENT_TYPES = ("TO", "CC", "BCC")
ENVIRONMENTS = ("Live", "Test")
STATUS_SCOPES = ("All", "Amber/Red")
SEND_DAYS = ("All", "Weekdays", "Weekends")

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PK_COLS = ("EMAIL_ADDRESS", "INTEGRATION_SCOPE", "ENVIRONMENT", "STATUS_SCOPE")


def session():
    return get_active_session()


def ensure_table() -> None:
    session().sql(
        f"""
        CREATE TABLE IF NOT EXISTS {RECIPIENTS_TABLE} (
            EMAIL_ADDRESS VARCHAR(320) NOT NULL,
            RECIPIENT_NAME VARCHAR(256),
            INTEGRATION_SCOPE VARCHAR(50) NOT NULL DEFAULT 'ALL',
            RECIPIENT_TYPE VARCHAR(20) NOT NULL DEFAULT 'TO',
            IS_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,
            CREATED_TIMESTAMP TIMESTAMP_NTZ(9) NOT NULL DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT TIMESTAMP_NTZ(9),
            NOTES VARCHAR(16777216),
            ENVIRONMENT VARCHAR(50) NOT NULL DEFAULT 'Live',
            STATUS_SCOPE VARCHAR(50) NOT NULL DEFAULT 'All',
            SEND_DAYS VARCHAR(50) NOT NULL DEFAULT 'All',
            PRIMARY KEY (EMAIL_ADDRESS, INTEGRATION_SCOPE, ENVIRONMENT, STATUS_SCOPE)
        )
        """
    ).collect()


def load_recipients() -> pd.DataFrame:
    df = session().sql(
        f"""
        SELECT
            EMAIL_ADDRESS,
            RECIPIENT_NAME,
            INTEGRATION_SCOPE,
            RECIPIENT_TYPE,
            IS_ACTIVE,
            CREATED_TIMESTAMP,
            UPDATED_AT,
            NOTES,
            ENVIRONMENT,
            STATUS_SCOPE,
            SEND_DAYS
        FROM {RECIPIENTS_TABLE}
        ORDER BY IS_ACTIVE DESC, EMAIL_ADDRESS, INTEGRATION_SCOPE, ENVIRONMENT, STATUS_SCOPE
        """
    ).to_pandas()
    if df.empty:
        return df
    df.columns = [c.upper() for c in df.columns]
    return df


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def pk_tuple(row: pd.Series) -> tuple[str, str, str, str]:
    return (
        str(row["EMAIL_ADDRESS"]),
        str(row["INTEGRATION_SCOPE"]),
        str(row["ENVIRONMENT"]),
        str(row["STATUS_SCOPE"]),
    )


def add_recipient(
    email: str,
    name: str,
    integration_scope: str,
    recipient_type: str,
    environment: str,
    status_scope: str,
    send_days: str,
    notes: str,
) -> str:
    email = normalize_email(email)
    if not valid_email(email):
        return "Enter a valid email address."

    existing = session().sql(
        f"""
        SELECT 1 AS FOUND
        FROM {RECIPIENTS_TABLE}
        WHERE EMAIL_ADDRESS = ?
          AND INTEGRATION_SCOPE = ?
          AND ENVIRONMENT = ?
          AND STATUS_SCOPE = ?
        """,
        params=[email, integration_scope, environment, status_scope],
    ).collect()
    if existing:
        return (
            f"{email} already exists for {integration_scope} / {environment} / {status_scope}."
        )

    session().sql(
        f"""
        INSERT INTO {RECIPIENTS_TABLE} (
            EMAIL_ADDRESS,
            RECIPIENT_NAME,
            INTEGRATION_SCOPE,
            RECIPIENT_TYPE,
            IS_ACTIVE,
            NOTES,
            ENVIRONMENT,
            STATUS_SCOPE,
            SEND_DAYS
        )
        VALUES (?, ?, ?, ?, TRUE, ?, ?, ?, ?)
        """,
        params=[
            email,
            name.strip() or None,
            integration_scope,
            recipient_type,
            notes.strip() or None,
            environment,
            status_scope,
            send_days,
        ],
    ).collect()
    return f"Added {email} to {RECIPIENTS_TABLE}."


def update_recipient(
    pk: tuple[str, str, str, str],
    name: str,
    recipient_type: str,
    send_days: str,
    notes: str,
    active: bool,
) -> None:
    session().sql(
        f"""
        UPDATE {RECIPIENTS_TABLE}
        SET
            RECIPIENT_NAME = ?,
            RECIPIENT_TYPE = ?,
            SEND_DAYS = ?,
            NOTES = ?,
            IS_ACTIVE = ?,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EMAIL_ADDRESS = ?
          AND INTEGRATION_SCOPE = ?
          AND ENVIRONMENT = ?
          AND STATUS_SCOPE = ?
        """,
        params=[
            name.strip() or None,
            recipient_type,
            send_days,
            notes.strip() or None,
            active,
            *pk,
        ],
    ).collect()


def set_active(pk: tuple[str, str, str, str], active: bool) -> None:
    session().sql(
        f"""
        UPDATE {RECIPIENTS_TABLE}
        SET IS_ACTIVE = ?, UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EMAIL_ADDRESS = ?
          AND INTEGRATION_SCOPE = ?
          AND ENVIRONMENT = ?
          AND STATUS_SCOPE = ?
        """,
        params=[active, *pk],
    ).collect()


def delete_recipient(pk: tuple[str, str, str, str]) -> None:
    session().sql(
        f"""
        DELETE FROM {RECIPIENTS_TABLE}
        WHERE EMAIL_ADDRESS = ?
          AND INTEGRATION_SCOPE = ?
          AND ENVIRONMENT = ?
          AND STATUS_SCOPE = ?
        """,
        params=list(pk),
    ).collect()


def active_email_list(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    return sorted(
        df.loc[df["IS_ACTIVE"] == True, "EMAIL_ADDRESS"].astype(str).unique().tolist()
    )


def option_index(options: tuple[str, ...], value: object, default: str) -> int:
    text = default if pd.isna(value) else str(value)
    if text in options:
        return options.index(text)
    return options.index(default)


def main() -> None:
    st.set_page_config(
        page_title="Dashboard recipients",
        page_icon="✉️",
        layout="wide",
    )
    st.title("Live Weather Travel — email recipients")
    st.caption(
        f"This app populates {RECIPIENTS_TABLE}. Active rows are emailed. "
        "The same address can appear more than once if scope, environment, or status differs."
    )

    ensure_table()
    recipients = load_recipients()

    active_count = int(recipients["IS_ACTIVE"].sum()) if not recipients.empty else 0
    total = len(recipients)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Rows in table", total)
    col_b.metric("Active (will be emailed)", active_count)
    col_c.metric("Paused", total - active_count)

    with st.expander("Active addresses (copy for an email job)", expanded=False):
        emails = active_email_list(recipients)
        if emails:
            st.code(", ".join(emails))
            st.caption(f"{len(emails)} active address{'es' if len(emails) != 1 else ''}.")
        else:
            st.info("No active recipients yet.")

    st.subheader("Add a recipient")
    with st.form("add_recipient", clear_on_submit=True):
        row1 = st.columns((2, 2, 1, 1))
        email = row1[0].text_input("Email address", placeholder="name@example.com")
        name = row1[1].text_input("Recipient name", placeholder="Optional")
        recipient_type = row1[2].selectbox("Type", RECIPIENT_TYPES, index=0)
        environment = row1[3].selectbox("Environment", ENVIRONMENTS, index=0)
        row2 = st.columns(3)
        integration_scope = row2[0].selectbox("Integration scope", INTEGRATION_SCOPES, index=0)
        status_scope = row2[1].selectbox("Status scope", STATUS_SCOPES, index=0)
        send_days = row2[2].selectbox("Send days", SEND_DAYS, index=0)
        notes = st.text_input("Notes", placeholder="Optional")
        submitted = st.form_submit_button("Add to EMAIL_RECIPIENTS")
        if submitted:
            message = add_recipient(
                email,
                name,
                integration_scope,
                recipient_type,
                environment,
                status_scope,
                send_days,
                notes,
            )
            if message.startswith("Added"):
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.subheader("Manage the list")
    if recipients.empty:
        st.info("EMAIL_RECIPIENTS is empty. Add the first address above.")
        return

    filter_cols = st.columns((2, 1, 1))
    search = filter_cols[0].text_input("Search", placeholder="Email or name")
    status_filter = filter_cols[1].selectbox("Show", ("All", "Active only", "Paused only"))
    env_filter = filter_cols[2].selectbox("Environment", ("All",) + ENVIRONMENTS)

    view = recipients.copy()
    if search.strip():
        needle = search.strip().lower()
        name_col = view["RECIPIENT_NAME"].fillna("").astype(str).str.lower()
        view = view[
            view["EMAIL_ADDRESS"].astype(str).str.lower().str.contains(needle, regex=False)
            | name_col.str.contains(needle, regex=False)
        ]
    if status_filter == "Active only":
        view = view[view["IS_ACTIVE"] == True]
    elif status_filter == "Paused only":
        view = view[view["IS_ACTIVE"] == False]
    if env_filter != "All":
        view = view[view["ENVIRONMENT"].astype(str) == env_filter]

    display = view[
        [
            "EMAIL_ADDRESS",
            "RECIPIENT_NAME",
            "RECIPIENT_TYPE",
            "INTEGRATION_SCOPE",
            "ENVIRONMENT",
            "STATUS_SCOPE",
            "SEND_DAYS",
            "IS_ACTIVE",
            "NOTES",
            "UPDATED_AT",
        ]
    ].rename(
        columns={
            "EMAIL_ADDRESS": "Email",
            "RECIPIENT_NAME": "Name",
            "RECIPIENT_TYPE": "Type",
            "INTEGRATION_SCOPE": "Scope",
            "ENVIRONMENT": "Environment",
            "STATUS_SCOPE": "Status",
            "SEND_DAYS": "Days",
            "IS_ACTIVE": "Active",
            "NOTES": "Notes",
            "UPDATED_AT": "Updated",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    if view.empty:
        st.warning("No rows match that search.")
        return

    labels = {}
    for row in view.itertuples():
        key = (
            str(row.EMAIL_ADDRESS),
            str(row.INTEGRATION_SCOPE),
            str(row.ENVIRONMENT),
            str(row.STATUS_SCOPE),
        )
        labels[key] = (
            f"{row.EMAIL_ADDRESS} · {row.INTEGRATION_SCOPE} · "
            f"{row.ENVIRONMENT} · {row.STATUS_SCOPE}"
        )

    selected_pk = st.selectbox(
        "Select a row to edit",
        options=list(labels.keys()),
        format_func=lambda key: labels[key],
    )
    match = recipients
    for col, value in zip(PK_COLS, selected_pk):
        match = match[match[col].astype(str) == value]
    selected = match.iloc[0]

    with st.form("edit_recipient"):
        edit1 = st.columns((2, 2, 1))
        edit1[0].text_input("Email address (key)", value=selected["EMAIL_ADDRESS"], disabled=True)
        new_name = edit1[1].text_input(
            "Recipient name",
            value="" if pd.isna(selected["RECIPIENT_NAME"]) else str(selected["RECIPIENT_NAME"]),
        )
        new_type = edit1[2].selectbox(
            "Type",
            RECIPIENT_TYPES,
            index=option_index(RECIPIENT_TYPES, selected["RECIPIENT_TYPE"], "TO"),
        )
        edit2 = st.columns(3)
        edit2[0].text_input("Integration scope (key)", value=selected["INTEGRATION_SCOPE"], disabled=True)
        edit2[1].text_input("Environment (key)", value=selected["ENVIRONMENT"], disabled=True)
        edit2[2].text_input("Status scope (key)", value=selected["STATUS_SCOPE"], disabled=True)
        new_days = st.selectbox(
            "Send days",
            SEND_DAYS,
            index=option_index(SEND_DAYS, selected["SEND_DAYS"], "All"),
        )
        new_notes = st.text_area(
            "Notes",
            value="" if pd.isna(selected["NOTES"]) else str(selected["NOTES"]),
        )
        new_active = st.checkbox(
            "Active — include on the next dashboard email",
            value=bool(selected["IS_ACTIVE"]),
        )
        save = st.form_submit_button("Save changes to EMAIL_RECIPIENTS")
        if save:
            update_recipient(selected_pk, new_name, new_type, new_days, new_notes, new_active)
            st.success(f"Updated {selected['EMAIL_ADDRESS']}.")
            st.rerun()

    action_cols = st.columns(3)
    if selected["IS_ACTIVE"]:
        if action_cols[0].button("Pause emails"):
            set_active(selected_pk, False)
            st.rerun()
    else:
        if action_cols[0].button("Resume emails"):
            set_active(selected_pk, True)
            st.rerun()

    confirm = action_cols[1].checkbox("Confirm delete")
    if action_cols[2].button("Delete permanently", disabled=not confirm, type="primary"):
        delete_recipient(selected_pk)
        st.rerun()

    st.caption(
        f"Writes to {RECIPIENTS_TABLE}. Email jobs should SELECT EMAIL_ADDRESS "
        f"WHERE IS_ACTIVE = TRUE. {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC."
    )


main()
