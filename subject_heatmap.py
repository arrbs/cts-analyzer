
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calplot
import streamlit as st
from datetime import datetime, timedelta
from utils import parse_date

def plot_subject_heatmap(completed, window_years=2):
    # Collect all dates and subjects
    date_subjects = []
    for subject, (status, score, base_month, date_str) in completed.items():
        dt = parse_date(date_str)
        if dt:
            date_subjects.append((dt.date(), subject))
    if not date_subjects:
        st.info("No subject dates to plot.")
        return
    # Build a DataFrame with counts per day
    df = pd.DataFrame(date_subjects, columns=["date", "subject"])
    df["count"] = 1
    df = df.groupby(["date"]).agg({"count": "sum", "subject": lambda x: ', '.join(x)}).reset_index()
    # Only last N years
    today = datetime.now().date()
    start_date = today - timedelta(days=window_years*365)
    df = df[df["date"] >= start_date]
    # Build a Series for calplot
    if df.empty:
        st.info("No subject dates to plot in the selected window.")
        return
    s = pd.Series(df["count"].values, index=pd.to_datetime(df["date"]))
    # Tooltip mapping
    tooltips = df.set_index("date")["subject"].to_dict()
    # Plot with error handling
    try:
        fig = calplot.calplot(s, how="sum", cmap="YlOrRd", colorbar=False, figsize=(10, 2))
        plt.tight_layout()
        st.pyplot(fig)
        # Show hover info as a table below
        st.markdown("**Hover over a date in the heatmap to see subject(s) written that day.**")
        st.dataframe(df[["date", "subject"]].sort_values("date", ascending=False).reset_index(drop=True))
    except Exception as e:
        st.error(f"Could not render heatmap: {e}")
