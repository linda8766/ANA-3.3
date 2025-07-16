import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio


st.set_page_config(
    page_title= "Construction project Dashboard",
    layout="wide"
)


uploaded_file = st.file_uploader("📂 Upload Your Primavera P6 Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Project Data")
    col = st.columns((2.5, 8), gap='medium')
    
    # Convert date columns
    df["Baseline Start"] = pd.to_datetime(df["Baseline Start"])
    df["Baseline Finish"] = pd.to_datetime(df["Baseline Finish"])
    df["Actual Start"] = pd.to_datetime(df["Actual Start"])
    df["Actual Finish"] = pd.to_datetime(df["Actual Finish"])
    
    st.sidebar.title("📊 Filters")
    selected_wbs = st.sidebar.multiselect("Filter by WBS", df["WBS"].unique(), default=df["WBS"].unique())
    df = df[df["WBS"].isin(selected_wbs)]
    selected_area = st.sidebar.multiselect("Filter by Area", df["Area"].unique(), default=df["Area"].unique())
    df = df[df["Area"].isin(selected_area)]
    selected_resource_name = st.sidebar.multiselect("Filter by Resource Name", df["Resource Name"].unique(), default=df["Resource Name"].unique())
    df = df[df["Resource Name"].isin(selected_resource_name)]
    
    with col[0]:

        st.subheader("📌 Earned Value Management")
        df["EV"] = df["Budgeted Cost"] * df["Actual %"] / 100
        df["PV"] = df["Budgeted Cost"] * df["Planned %"] / 100
        df["AC"] = df["Actual Cost"]
        EV = df["EV"].sum()
        PV = df["PV"].sum()
        AC = df["AC"].sum()
        latest_date = df["Actual Finish"].max()
        df_latest = df[df["Actual Finish"] == latest_date]
        EV = df_latest["EV"].sum()
        AC = df_latest["AC"].sum()
        PV = df_latest["PV"].sum()
        CPI = EV / AC if AC != 0 else 0
        SPI = EV / PV if PV != 0 else 0
        CV = EV - AC
        SV = EV - PV
        AT = 100
        ES = SPI * AT if SPI else None
        Schedule_Variance_Time = ES - AT if ES else None
    
        st.metric("Planned Value (PV)", f"${PV:,.2f}")
        st.metric("Earned Value (EV)", f"${EV:,.2f}")
        st.metric("Actual Cost (AC)", f"${AC:,.2f}")
        st.metric("Cost Variance (CV)", f"${CV:,.2f}")
        st.metric("Schedule Variance (SV)", f"${SV:,.2f}")
        # Create columns for two charts
        col1, col2 = st.columns(2)
        
        # Donut for CPI
        with col1:
            cpi_color = "green" if CPI >= 1 else "red"
            cpi_fig = go.Figure(data=[go.Pie(
                labels=["CPI", "Remaining"],
                values=[CPI, max(2 - CPI, 0.01)],  # Ensure donut has a visible ring
                hole=0.6,
                marker=dict(colors=[cpi_color, "lightgray"]),
                textinfo='label+percent',
                hoverinfo='label+value'
            )])
            cpi_fig.update_layout(
                title_text=f"CPI = {CPI:.2f}",
                showlegend=False
            )
            st.plotly_chart(cpi_fig, use_container_width=True)
        
        # Donut for SPI
        with col2:
            spi_color = "blue" if SPI >= 1 else "orange"
            spi_fig = go.Figure(data=[go.Pie(
                labels=["SPI", "Remaining"],
                values=[SPI, max(2 - SPI, 0.01)],
                hole=0.6,
                marker=dict(colors=[spi_color, "lightgray"]),
                textinfo='label+percent',
                hoverinfo='label+value'
            )])
            spi_fig.update_layout(
                title_text=f"SPI = {SPI:.2f}",
                showlegend=False
            )
            st.plotly_chart(spi_fig, use_container_width=True)
            
        st.metric("Earned Schedule (ES)", f"{ES:.2f}" if ES else "N/A")
        st.metric("Schedule Variance (Time)", f"{Schedule_Variance_Time:.2f}" if Schedule_Variance_Time else "N/A")

    with col[1]:

        st.markdown('#### Gantt Chart, S-Curve, and Resource Histogram')
        df_sorted = df.sort_values(by="Activity ID")
        
        # Create a new column for color coding
        df["Critical Color"] = df["Critical "].fillna("").apply(lambda x: "Critical" if str(x).strip().lower() == "yes" else "Non-Critical")
        
        # Set custom order for y-axis (activity names)
        activity_order = df_sorted["Activity Name"].tolist()
    
        # Plot using the new color column
        gantt_fig = px.timeline(
            df,
            x_start= "Baseline Start",
            x_end="Baseline Finish",
            y="Activity Name",
            color="Critical Color",  # Use color based on criticality
            color_discrete_map={
                "Non-Critical": "green"
            },
            category_orders={"Activity Name": activity_order}, 
            hover_data=["Activity ID", "Activity Code", "Planned %", "Actual %", "Remarks"]
        )
    
        gantt_fig.update_layout(
            yaxis_autorange="max",
            title="Gantt Chart with Critical Path Highlighted",
            height=500
        )
        st.plotly_chart(gantt_fig, use_container_width=True)

        fig_col1, fig_col2 = st.columns(2)  # Corrected variable names
    
        with fig_col1:
            # Sort and compute cumulative values
            df_sorted = df.sort_values("Actual Finish")
            df_sorted["Cumulative Planned Cost"] = df_sorted["Budgeted Cost"].cumsum()
            df_sorted["Cumulative Actual Cost"] = df_sorted["Actual Cost"].cumsum()
    
            # Create a figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
    
            # Add S-Curve lines (secondary y-axis)
            fig.add_trace(
                go.Scatter(x=df_sorted["Actual Finish"], y=df_sorted["Cumulative Planned Cost"],
                       mode='lines+markers', name='Planned Cumulative Cost'),
                secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=df_sorted["Actual Finish"], y=df_sorted["Cumulative Actual Cost"],
                       mode='lines+markers', name='Actual Cumulative Cost'),
                secondary_y=True
            )
    
            # Add bar chart for individual activity costs (primary y-axis)
            fig.add_trace(
                go.Bar(x=df_sorted["Actual Finish"], y=df_sorted["Budgeted Cost"], name="Budgeted Cost", opacity=0.5),
                secondary_y=False
            )
            fig.add_trace(
            go.Bar(x=df_sorted["Actual Finish"], y=df_sorted["Actual Cost"], name="Actual Cost", opacity=0.5),
            secondary_y=False
            )
    
            # Update axis titles
            fig.update_layout(
                title="S-Curve and Cost Histogram Combined",
                xaxis_title="Actual Finish Date",
                barmode="group"
            )
            fig.update_yaxes(title_text="Cost", secondary_y=False)
            fig.update_yaxes(title_text="Cumulative Cost", secondary_y=True)
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    
            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
        with fig_col2:
            st.markdown("### Man-hour Histogram")
            hist_fig_manhour = px.bar(df, x="Activity Name", y=["Budgeted Hours", "Actual Hours"], barmode="group")
            st.plotly_chart(hist_fig_manhour, use_container_width=True)

 
    st.subheader("📈 Performance Indices Over Time")
    df_grouped = df.groupby("Actual Finish").agg({"EV": "sum", "PV": "sum", "AC": "sum"}).sort_index().reset_index()
    df_grouped["CPI"] = df_grouped["EV"] / df_grouped["AC"]
    df_grouped["SPI"] = df_grouped["EV"] / df_grouped["PV"]
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(x=df_grouped["Actual Finish"], y=df_grouped["CPI"],
                                    mode='lines+markers', name="CPI", line=dict(color='green')))
    trend_fig.add_trace(go.Scatter(x=df_grouped["Actual Finish"], y=df_grouped["SPI"],
                                    mode='lines+markers', name="SPI", line=dict(color='blue')))
    trend_fig.update_layout(xaxis_title="Date", yaxis_title="Index Value", yaxis=dict(range=[0, 2]))
    st.plotly_chart(trend_fig, use_container_width=True)
