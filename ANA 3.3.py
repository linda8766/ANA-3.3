import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Streamlit app title
st.title("MIP 3.3 Contemporaneous As-Is Analysis (Longest Path with Total Float)")

# File uploader for Excel file
uploaded_file = st.file_uploader("Upload your project schedule Excel file", type=["xlsx"])

if uploaded_file:
    # Read Excel file
    df = pd.read_excel(uploaded_file)

    # Ensure date columns are in datetime format
    date_columns = ['Planned_Start', 'Planned_Finish', 'Actual_Start', 'Actual_Finish']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Ensure Total_Float is numeric
    df['Total_Float'] = pd.to_numeric(df['Total_Float'], errors='coerce')

    # Separate baseline and updates
    baseline_df = df[df['Update_ID'] == 'Baseline']
    update_dfs = df[df['Update_ID'] != 'Baseline']

    # Function to calculate delays for longest path activities relative to baseline
    def calculate_delays(update_df, baseline_df, update_id):
        # Filter for the specific update and longest path activities
        longest_path_df = update_df[(update_df['Update_ID'] == update_id) & 
                                   (update_df['Longest_Path'].isin([True, 'Yes']))]

        # Merge with baseline to get baseline planned finish dates and float
        merged_df = longest_path_df.merge(
            baseline_df[['Activity_ID', 'Planned_Finish', 'Longest_Path', 'Total_Float']],
            on='Activity_ID',
            suffixes=('_update', '_baseline')
        )

        # Calculate delay (Actual_Finish - Baseline Planned_Finish) in days
        merged_df['Delay_Days'] = (merged_df['Actual_Finish_update'] - 
                                  merged_df['Planned_Finish_baseline']).dt.days

        # Filter out rows where delay is calculable (non-NaN)
        merged_df = merged_df.dropna(subset=['Delay_Days'])

        return merged_df[['Activity_ID', 'Activity_Name', 'Delay_Days', 'Delay_Cause', 
                         'Planned_Finish_baseline', 'Actual_Finish_update', 
                         'Total_Float_update', 'Total_Float_baseline']]

    # Get unique update IDs (excluding Baseline)
    update_ids = update_dfs['Update_ID'].unique()

    # Initialize results
    all_delays = []
    summary_data = []

    # Analyze each update
    for update_id in update_ids:
        delay_df = calculate_delays(update_dfs, baseline_df, update_id)
        if not delay_df.empty:
            all_delays.append(delay_df)
            # Summarize delays by cause for this update
            summary = delay_df.groupby('Delay_Cause')['Delay_Days'].sum().reset_index()
            summary['Update_ID'] = update_id
            summary_data.append(summary)

    if all_delays:
        # Combine all delay data
        all_delays_df = pd.concat(all_delays)

        # Display detailed delay table
        st.subheader("Detailed Delay Analysis (Longest Path, Relative to Baseline)")
        st.dataframe(all_delays_df)

        # Combine summary data
        summary_df = pd.concat(summary_data)

        # Display summary table
        st.subheader("Summary of Delays by Update and Cause")
        st.dataframe(summary_df)

        # Visualize delays by update and cause
        st.subheader("Delay Visualization")
        fig = px.bar(summary_df, 
                     x='Update_ID', 
                     y='Delay_Days', 
                     color='Delay_Cause', 
                     title='Total Delays by Update and Cause (Longest Path)',
                     labels={'Update_ID': 'Schedule Update', 'Delay_Days': 'Delay (Days)'},
                     barmode='stack')
        st.plotly_chart(fig)
    else:
        st.write("No longest path delays found in the provided data.")
else:
    st.write("Please upload an Excel file to analyze.")
