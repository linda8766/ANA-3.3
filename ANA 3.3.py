import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")

st.title("MIP 3.3 Contemporaneous As-Is Analysis (Longest Path with Total Float)")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your project schedule Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Normalize column headers
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.title()

    required_columns = [
        'Activity_Id', 'Activity_Name', 'Update_Id', 'Planned_Start', 'Planned_Finish',
        'Actual_Start', 'Actual_Finish', 'Longest_Path', 'Total_Float'
    ]

    # Check for missing columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Missing columns in uploaded file: {', '.join(missing_cols)}")
        st.stop()

    # Convert date columns
    date_columns = ['Planned_Start', 'Planned_Finish', 'Actual_Start', 'Actual_Finish']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['Total_Float'] = pd.to_numeric(df['Total_Float'], errors='coerce')

    # Split into baseline and updates
    baseline_df = df[df['Update_Id'] == 'Baseline']
    update_dfs = df[df['Update_Id'] != 'Baseline']

    def calculate_delays(update_df, baseline_df, update_id):
        longest_path_df = update_df[
            (update_df['Update_Id'] == update_id) &
            (update_df['Longest_Path'].isin([True, 'Yes', 'TRUE', 'yes']))
        ][['Activity_Id', 'Activity_Name', 'Actual_Finish', 'Total_Float']]

        longest_path_df = longest_path_df.rename(columns={
            'Actual_Finish': 'Actual_Finish_Update',
            'Total_Float': 'Total_Float_Update'
        })

        baseline_part = baseline_df[['Activity_Id', 'Planned_Finish', 'Total_Float']].rename(columns={
            'Planned_Finish': 'Planned_Finish_Baseline',
            'Total_Float': 'Total_Float_Baseline'
        })

        merged_df = pd.merge(longest_path_df, baseline_part, on='Activity_Id', how='inner')

        if merged_df.empty:
            st.warning(f"No longest path matches found for update: {update_id}")
            return pd.DataFrame()

        merged_df['Delay_Days'] = (
            merged_df['Actual_Finish_Update'] - merged_df['Planned_Finish_Baseline']
        ).dt.days

        merged_df['Update_Id'] = update_id

        return merged_df[['Update_Id', 'Activity_Id', 'Activity_Name', 'Delay_Days',
                          'Planned_Finish_Baseline', 'Actual_Finish_Update',
                          'Total_Float_Update', 'Total_Float_Baseline']]

    all_updates = update_dfs['Update_Id'].unique()
    all_delays = []

    for update_id in all_updates:
        delay_df = calculate_delays(update_dfs, baseline_df, update_id)
        if not delay_df.empty:
            all_delays.append(delay_df)

    if all_delays:
        all_delays_df = pd.concat(all_delays, ignore_index=True)

        st.subheader("Detailed Delay Analysis Table")
        st.dataframe(all_delays_df)

        st.subheader("Finish Date Drift Tracking (Gantt Style)")
        drift_data = all_delays_df.copy()
        drift_data['Baseline'] = drift_data['Planned_Finish_Baseline']
        drift_data['Actual'] = drift_data['Actual_Finish_Update']

        gantt_df = pd.melt(
            drift_data,
            id_vars=['Update_Id', 'Activity_Id', 'Activity_Name'],
            value_vars=['Baseline', 'Actual'],
            var_name='Type',
            value_name='Finish_Date'
        )

        fig2 = px.timeline(
            gantt_df,
            x_start='Finish_Date', x_end='Finish_Date',
            y='Activity_Name', color='Type', facet_col='Update_Id',
            title='Finish Date Shifts of Longest Path Activities'
        )
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No delays detected for longest path activities. Please check your data.")
else:
    st.info("Please upload an Excel file with baseline and update data.")
