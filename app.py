import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
from data_processor import DataProcessor
from utils import FrequencyParser, DateUtils

# Configure page
st.set_page_config(
    page_title="Machinery Maintenance Analysis",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_processors' not in st.session_state:
    st.session_state.data_processors = {}
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'combined_data' not in st.session_state:
    st.session_state.combined_data = None

def main():
    st.title("⚙️ Machinery Maintenance Analysis Tool")
    st.markdown("### Analyze vessel maintenance data by frequency and due dates")
    
    # Sidebar for file upload and filters
    with st.sidebar:
        st.header("📁 Data Upload")
        
        # Multiple file upload option
        upload_mode = st.radio(
            "Upload Mode",
            ["Single File", "Multiple Files"],
            help="Choose single file for one vessel or multiple files for vessel comparison"
        )
        
        if upload_mode == "Single File":
            uploaded_file = st.file_uploader(
                "Upload CSV maintenance data file",
                type=['csv'],
                help="Upload a CSV file containing machinery maintenance data"
            )
            
            if uploaded_file is not None:
                try:
                    # Load and process data
                    with st.spinner("Processing data..."):
                        processor = DataProcessor()
                        processor.load_data(uploaded_file)
                        st.session_state.data_processors = {uploaded_file.name: processor}
                        if processor.df is not None:
                            st.session_state.combined_data = processor.df.copy()
                        else:
                            st.session_state.combined_data = None
                    
                    if st.session_state.combined_data is not None:
                        st.success(f"✅ Data loaded: {len(st.session_state.combined_data)} records")
                        
                        # Display data info
                        st.subheader("📊 Data Overview")
                        st.write(f"**Total Records:** {len(st.session_state.combined_data)}")
                        st.write(f"**Vessels:** {st.session_state.combined_data['Vessel'].nunique()}")
                        st.write(f"**Vessel Names:** {', '.join(st.session_state.combined_data['Vessel'].unique())}")
                        st.write(f"**Departments:** {st.session_state.combined_data['Department'].nunique()}")
                        st.write(f"**Machinery Locations:** {st.session_state.combined_data['Machinery Location'].nunique()}")
                    else:
                        st.error("Failed to load data")
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
        
        else:  # Multiple Files mode
            uploaded_files = st.file_uploader(
                "Upload multiple CSV files (one per vessel)",
                type=['csv'],
                accept_multiple_files=True,
                help="Upload multiple CSV files for vessel comparison analysis"
            )
            
            if uploaded_files:
                try:
                    with st.spinner("Processing multiple files..."):
                        all_dataframes = []
                        st.session_state.data_processors = {}
                        
                        for uploaded_file in uploaded_files:
                            processor = DataProcessor()
                            processor.load_data(uploaded_file)
                            if processor.df is not None:
                                st.session_state.data_processors[uploaded_file.name] = processor
                                all_dataframes.append(processor.df)
                        
                        # Combine all dataframes
                        if all_dataframes:
                            st.session_state.combined_data = pd.concat(all_dataframes, ignore_index=True)
                    
                    if st.session_state.combined_data is not None:
                        st.success(f"✅ Loaded {len(uploaded_files)} files with {len(st.session_state.combined_data)} total records")
                        
                        # Display combined data info
                        st.subheader("📊 Combined Data Overview")
                        st.write(f"**Total Records:** {len(st.session_state.combined_data)}")
                        st.write(f"**Total Vessels:** {st.session_state.combined_data['Vessel'].nunique()}")
                        st.write(f"**Vessel Names:** {', '.join(st.session_state.combined_data['Vessel'].unique())}")
                        st.write(f"**Departments:** {st.session_state.combined_data['Department'].nunique()}")
                        st.write(f"**Machinery Locations:** {st.session_state.combined_data['Machinery Location'].nunique()}")
                        
                        # Show breakdown by file
                        st.subheader("📋 Files Loaded")
                        for filename, processor in st.session_state.data_processors.items():
                            vessels = processor.df['Vessel'].unique()
                            st.write(f"**{filename}:** {len(processor.df)} records, Vessels: {', '.join(vessels)}")
                    else:
                        st.error("Failed to load data from files")
                        
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
        
        # Filter controls (show if any data is loaded)
        if st.session_state.combined_data is not None:
            st.subheader("🔍 Filters")
            
            # Frequency filter options
            st.write("**Major Machinery Criteria:**")
            freq_hours = st.number_input(
                "Minimum Hours",
                min_value=1000,
                max_value=50000,
                value=4000,
                step=1000,
                help="Filter for frequency greater than this many hours"
            )
            
            freq_months = st.number_input(
                "Minimum Months",
                min_value=6,
                max_value=120,
                value=30,
                step=6,
                help="Filter for frequency greater than this many months"
            )
            
            # Date range filter
            st.write("**Date Range:**")
            date_range = st.selectbox(
                "Analysis Period",
                ["All Years", "2024", "2025", "2026", "2027", "2028", "2029"],
                index=0
            )
            
            # Vessel filter
            st.write("**Vessel:**")
            all_vessels = sorted(st.session_state.combined_data['Vessel'].dropna().unique().tolist())
            selected_vessels = st.multiselect(
                "Filter by Vessel (multiple selection)",
                all_vessels,
                default=[],
                help="Select one or more vessels. Leave empty to include all vessels."
            )
            
            # Machinery location filter
            st.write("**Machinery Location:**")
            all_machinery_locations = sorted(st.session_state.combined_data['Machinery Location'].dropna().unique().tolist())
            selected_machinery = st.multiselect(
                "Filter by Machinery (multiple selection)",
                all_machinery_locations,
                default=[],
                help="Select one or more machinery locations. Leave empty to include all locations."
            )
            
            # Job Action filter
            st.write("**Job Action:**")
            job_actions = sorted(st.session_state.combined_data['Job Action'].dropna().unique().tolist())
            selected_job_actions = st.multiselect(
                "Filter by Job Action (multiple selection)",
                job_actions,
                default=[],
                help="Select specific job action types. Leave empty to include all job actions."
            )
            
            # Apply filters
            if st.button("🔄 Apply Filters", type="primary"):
                with st.spinner("Filtering data..."):
                    # Store current filter values in session state
                    st.session_state.current_freq_hours = freq_hours
                    st.session_state.current_freq_months = freq_months
                    st.session_state.current_vessels = selected_vessels
                    st.session_state.current_job_actions = selected_job_actions
                    
                    # Create a temporary processor for filtering
                    temp_processor = DataProcessor()
                    temp_processor.df = st.session_state.combined_data.copy()
                    
                    st.session_state.filtered_data = temp_processor.filter_major_machinery(
                        min_hours=freq_hours,
                        min_months=freq_months,
                        year_filter=date_range if date_range != "All Years" else None,
                        vessel_filter=selected_vessels if selected_vessels else None,
                        machinery_filter=selected_machinery if selected_machinery else None,
                        job_action_filter=selected_job_actions if selected_job_actions else None
                    )
                st.rerun()
    
    # Main content area
    if st.session_state.combined_data is not None and st.session_state.filtered_data is not None:
        display_analysis()
    elif st.session_state.combined_data is not None:
        st.info("👆 Please apply filters in the sidebar to view analysis")
    else:
        display_welcome()

def display_welcome():
    """Display welcome message and instructions"""
    st.markdown("""
    ## Welcome to the Machinery Maintenance Analysis Tool
    
    This tool helps you analyze vessel maintenance data focusing on major machinery components.
    
    ### Features:
    - 📊 **Data Filtering**: Filter by frequency (hours/months) to identify major machinery
    - 📅 **Yearly Analysis**: Analyze maintenance schedules by calculated due dates
    - 📈 **Interactive Visualizations**: View trends and patterns in maintenance data
    - 🚢 **Multi-Vessel Support**: Upload single or multiple files for vessel comparison
    - 💾 **Export Results**: Download filtered data and analysis reports
    
    ### Getting Started:
    1. Choose upload mode: Single File or Multiple Files
    2. Upload your CSV maintenance data file(s) using the sidebar
    3. Set your frequency criteria for major machinery
    4. Select analysis period and machinery locations
    5. Click "Apply Filters" to generate analysis
    
    ### Upload Modes:
    - **Single File**: Upload one CSV file for single vessel analysis
    - **Multiple Files**: Upload multiple CSV files to compare maintenance data across vessels
    
    ### Frequency Criteria:
    - **Hours**: Maintenance intervals greater than specified hours (default: 4000+ hours)
    - **Months**: Maintenance intervals greater than specified months (default: 30+ months)
    """)

def display_analysis():
    """Display the main analysis dashboard"""
    filtered_df = st.session_state.filtered_data
    
    if filtered_df.empty:
        st.warning("⚠️ No records match the current filter criteria. Try adjusting the frequency thresholds.")
        return
    
    # Create combined Job Code + Title column for better display
    filtered_df['Job_Details'] = filtered_df['Job Code'].astype(str) + " - " + filtered_df['Title'].astype(str)
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Major Machinery Items", len(filtered_df))
    
    with col2:
        pending_count = len(filtered_df[filtered_df['Job Status'] == 'Pending'])
        st.metric("Pending Jobs", pending_count)
    
    with col3:
        overdue_count = len(filtered_df[
            (filtered_df['Calculated Due Date'].notna()) & 
            (pd.to_datetime(filtered_df['Calculated Due Date'], errors='coerce') < datetime.now())
        ])
        st.metric("Overdue Items", overdue_count)
    
    with col4:
        unique_machinery = filtered_df['Machinery Location'].nunique()
        st.metric("Unique Machinery", unique_machinery)
    
    with col5:
        unique_vessels = filtered_df['Vessel'].nunique()
        st.metric("Vessels", unique_vessels)
    
    # Display vessel names prominently
    if 'Vessel' in filtered_df.columns:
        vessel_names = filtered_df['Vessel'].unique()
        st.info(f"🚢 **Vessels in Analysis:** {', '.join(vessel_names)}")
    
    # Vessel KPIs Summary Table
    st.subheader("📈 Vessel KPIs - Machinery Count by Year & Quarter")
    display_vessel_kpis_summary(filtered_df)
    
    # Tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["📅 Yearly Analysis", "🔧 Machinery wise analysis", "📋 Data Export"])
    
    with tab1:
        display_yearly_analysis(filtered_df)
    
    with tab2:
        display_machinery_breakdown(filtered_df)
    
    with tab3:
        display_export_options(filtered_df)

def display_vessel_kpis_summary(df):
    """Display vessel KPIs as a clean summary table with color formatting"""
    if df.empty or 'Vessel' not in df.columns:
        st.warning("No vessel data available for KPI analysis.")
        return
    
    # Parse due dates and extract year/quarter
    df_copy = df.copy()
    df_copy['Due_Date'] = pd.to_datetime(df_copy['Calculated Due Date'], errors='coerce')
    df_copy['Year'] = df_copy['Due_Date'].dt.year
    df_copy['Quarter'] = df_copy['Due_Date'].dt.quarter
    
    # Filter out rows with invalid dates
    df_with_dates = df_copy[df_copy['Due_Date'].notna()]
    
    if df_with_dates.empty:
        st.warning("No valid due dates found for KPI analysis.")
        return
    
    # Create pivot table: Vessel -> Year -> Quarter -> Machinery Count
    kpi_data = []
    
    for vessel in sorted(df_with_dates['Vessel'].unique()):
        vessel_data = df_with_dates[df_with_dates['Vessel'] == vessel]
        
        for year in sorted(vessel_data['Year'].unique()):
            year_data = vessel_data[vessel_data['Year'] == year]
            
            # Total machinery for the year
            year_machinery_count = year_data['Machinery Location'].nunique()
            
            # Quarterly breakdown
            for quarter in [1, 2, 3, 4]:
                quarter_data = year_data[year_data['Quarter'] == quarter]
                quarter_machinery_count = quarter_data['Machinery Location'].nunique() if not quarter_data.empty else 0
                
                kpi_data.append({
                    'Vessel': vessel,
                    'Year': int(year),
                    'Quarter': f'Q{quarter}',
                    'Machinery_Count': quarter_machinery_count,
                    'Year_Total': year_machinery_count
                })
    
    if not kpi_data:
        st.warning("No KPI data available.")
        return
    
    kpi_df = pd.DataFrame(kpi_data)
    
    # Create pivot table for better visualization
    pivot_table = kpi_df.pivot_table(
        index=['Vessel', 'Year'], 
        columns='Quarter', 
        values='Machinery_Count', 
        fill_value=0,
        aggfunc='sum'
    )
    
    # Add year totals
    pivot_table['Year Total'] = kpi_df.groupby(['Vessel', 'Year'])['Year_Total'].first()
    
    # Format column names for better display
    pivot_table.columns = ['Q1', 'Q2', 'Q3', 'Q4', 'Year Total']
    
    # Apply color formatting to the dataframe
    def color_cells(val):
        if val == 0:
            return 'background-color: #c3e6cb; color: #333333'  # Dark green for zero
        elif val <= 10:
            return 'background-color: #d4edda; color: #333333'  # Light green for low values
        elif val <= 50:
            return 'background-color: #fff2cc; color: #333333'  # Light yellow for medium values
        else:
            return 'background-color: #ffcccc; color: #333333'  # Light red for high values
    
    # Style the dataframe with colors and formatting
    styled_table = pivot_table.style.map(color_cells).format({
        'Q1': '{:.0f}',
        'Q2': '{:.0f}', 
        'Q3': '{:.0f}',
        'Q4': '{:.0f}',
        'Year Total': '{:.0f}'
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#4472C4'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('text-align', 'center'),
            ('padding', '10px')
        ]},
        {'selector': 'td', 'props': [
            ('text-align', 'center'),
            ('padding', '8px'),
            ('font-weight', 'bold'),
            ('border', '1px solid #ddd')
        ]},
        {'selector': 'tr:hover', 'props': [
            ('background-color', '#f5f5f5')
        ]}
    ])
    
    st.dataframe(styled_table, use_container_width=True)
    
    # Add legend for color coding
    st.markdown("""
    **Color Legend:**
    - 🟢 **Dark Green**: 0 machinery items
    - 🟢 **Light Green**: 1-10 machinery items  
    - 🟡 **Yellow**: 11-50 machinery items
    - 🔴 **Red**: 50+ machinery items
    """)

def display_yearly_analysis(df):
    """Display yearly analysis of due dates"""
    st.header("📅 Yearly Maintenance Schedule Analysis")
    
    # Parse dates and create yearly breakdown
    df_with_dates = df.copy()
    df_with_dates['Due Date Parsed'] = pd.to_datetime(df_with_dates['Calculated Due Date'], errors='coerce')
    df_with_dates = df_with_dates.dropna(subset=['Due Date Parsed'])
    
    if df_with_dates.empty:
        st.warning("No valid due dates found in the filtered data.")
        return
    
    df_with_dates['Year'] = df_with_dates['Due Date Parsed'].dt.year
    df_with_dates['Month'] = df_with_dates['Due Date Parsed'].dt.month
    df_with_dates['Quarter'] = df_with_dates['Due Date Parsed'].dt.quarter
    
    # Yearly summary
    yearly_summary = df_with_dates.groupby('Year').agg({
        'Job Code': 'count',
        'Job Status': lambda x: (x == 'Pending').sum(),
        'Department': lambda x: x.nunique()
    }).rename(columns={
        'Job Code': 'Total Jobs',
        'Job Status': 'Pending Jobs',
        'Department': 'Unique Departments'
    })
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Timeline chart
        fig_timeline = px.scatter(
            df_with_dates,
            x='Due Date Parsed',
            y='Machinery Location',
            color='Vessel',
            hover_data=['Job_Details', 'Job Status', 'Frequency', 'Department'],
            title="Maintenance Timeline by Machinery and Vessel"
        )
        fig_timeline.update_layout(height=600)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        st.subheader("Yearly Summary")
        st.dataframe(yearly_summary, use_container_width=True)
    
    # Monthly distribution
    monthly_dist = df_with_dates.groupby(['Year', 'Month']).size().reset_index(name='Count')
    
    fig_monthly = px.bar(
        monthly_dist,
        x='Month',
        y='Count',
        color='Year',
        title="Monthly Distribution of Due Dates",
        labels={'Month': 'Month', 'Count': 'Number of Jobs'}
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Quarterly analysis
    quarterly_dist = df_with_dates.groupby(['Year', 'Quarter']).size().reset_index(name='Count')
    
    fig_quarterly = px.line(
        quarterly_dist,
        x='Quarter',
        y='Count',
        color='Year',
        title="Quarterly Maintenance Load",
        markers=True
    )
    st.plotly_chart(fig_quarterly, use_container_width=True)



def display_machinery_breakdown(df):
    """Display machinery-specific breakdown"""
    st.header("🔧 Machinery Breakdown Analysis")
    
    # Note: df is already filtered for major machinery based on frequency criteria
    
    # Top machinery by job count
    machinery_counts = df['Machinery Location'].value_counts().head(20)
    
    fig_machinery = px.bar(
        x=machinery_counts.values,
        y=machinery_counts.index,
        orientation='h',
        title="Top 20 Machinery by Job Count",
        labels={'x': 'Number of Jobs', 'y': 'Machinery Location'}
    )
    fig_machinery.update_layout(height=600)
    st.plotly_chart(fig_machinery, use_container_width=True)
    
    # Job action distribution
    action_dist = df['Job Action'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_actions = px.pie(
            values=action_dist.values,
            names=action_dist.index,
            title="Distribution of Job Actions"
        )
        st.plotly_chart(fig_actions, use_container_width=True)
    
    with col2:
        # Status distribution
        status_dist = df['Job Status'].value_counts()
        fig_status = px.pie(
            values=status_dist.values,
            names=status_dist.index,
            title="Distribution of Job Status"
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Detailed machinery table
    st.subheader("Detailed Machinery Information (Pending Jobs Only - Major Machinery)")
    
    # Use already filtered data from session state instead of re-filtering
    if 'filtered_data' in st.session_state and st.session_state.filtered_data is not None:
        filtered_df = st.session_state.filtered_data
    else:
        filtered_df = df
    
    # Filter for pending jobs only
    pending_df = filtered_df[filtered_df['Job Status'] == 'Pending'].copy()
    
    # Apply job action filter if any are stored in session state
    if hasattr(st.session_state, 'current_job_actions') and st.session_state.current_job_actions:
        pending_df = pending_df[pending_df['Job Action'].isin(st.session_state.current_job_actions)]
    
    if pending_df.empty:
        st.warning("No pending jobs found for major machinery in the selected criteria.")
        return
    
    # Get current filter values from session state for display
    freq_hours = getattr(st.session_state, 'current_freq_hours', 4000)
    freq_months = getattr(st.session_state, 'current_freq_months', 30)
    
    # Display current filter criteria for clarity
    st.info(f"📋 Showing pending jobs for machinery with frequency ≥ {freq_hours} hours OR ≥ {freq_months} months")
    
    # Show count of filtered vs total
    total_pending = len(df[df['Job Status'] == 'Pending'])
    major_pending = len(pending_df)
    st.write(f"**Filtered Results:** {major_pending} pending jobs for major machinery (out of {total_pending} total pending jobs)")
    
    # Show vessel count
    unique_vessels = pending_df['Vessel'].nunique()
    vessel_names = ', '.join(pending_df['Vessel'].unique())
    st.write(f"**Vessels:** {unique_vessels} vessel(s) - {vessel_names}")
    
    # Create detailed summary by machinery location for pending jobs only
    machinery_details = pending_df.groupby('Machinery Location').agg({
        'Job Code': lambda x: ', '.join(x.dropna().astype(str)) + f' (Total: {len(x)})',
        'Title': lambda x: ', '.join(x.dropna().astype(str)) + f' (Total: {len(x)})',
        'Job Status': 'count',  # All are pending, so just count them
        'Vessel': lambda x: ', '.join(x.dropna().astype(str).unique()),
        'Department': lambda x: ', '.join(x.dropna().astype(str).unique()),
        'Frequency': lambda x: ', '.join(x.dropna().astype(str).unique()),
        'Calculated Due Date': lambda x: x.min() if x.notna().any() else None
    })
    
    # Rename columns
    machinery_details.columns = ['Job Codes', 'Job Titles', 'Pending Jobs', 'Vessels', 'Departments', 'Frequencies', 'Next Due Date']
    
    # Add total job count as separate column (from pending jobs only)
    machinery_details['Total Jobs'] = pending_df.groupby('Machinery Location').size()
    
    # Reorder columns
    machinery_details = machinery_details[['Total Jobs', 'Pending Jobs', 'Vessels', 'Job Codes', 'Job Titles', 'Departments', 'Frequencies', 'Next Due Date']]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(machinery_details, use_container_width=True, height=600)
    
    with col2:
        st.subheader("Export Options")
        
        # Export detailed machinery information
        csv_detailed = machinery_details.to_csv()
        st.download_button(
            label="📥 Download Detailed Machinery Info (CSV)",
            data=csv_detailed,
            file_name=f"detailed_machinery_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Also provide full detailed records export (pending jobs only)
        full_detailed_view = pending_df[['Vessel', 'Machinery Location', 'Job Code', 'Title', 'Job_Details', 'Frequency', 
                                       'Calculated Due Date', 'Job Status', 'Department', 'Performing Rank']].copy()
        full_detailed_view = full_detailed_view.sort_values(['Machinery Location', 'Calculated Due Date'])
        
        csv_full_detailed = full_detailed_view.to_csv(index=False)
        st.download_button(
            label="📋 Download Pending Records (CSV)",
            data=csv_full_detailed,
            file_name=f"pending_machinery_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.subheader("Quick Stats")
        total_machinery = len(machinery_details)
        total_jobs = machinery_details['Total Jobs'].sum()
        total_pending = machinery_details['Pending Jobs'].sum()
        
        st.metric("Machinery Locations", total_machinery)
        st.metric("Total Jobs", total_jobs)
        st.metric("Pending Jobs", total_pending)

def prepare_export_data(df):
    """Prepare data for export with specified columns and naming"""
    export_df = df.copy()
    
    # Define the exact column order based on the original data, excluding "Unnamed: 3"
    export_columns = [
        'Critical Job',           # Renamed from 'Unnamed: 0'
        'Job Code',
        'Frequency',
        'Calculated Due Date',
        'Job Status',
        'Performing Rank',
        'Machinery Location',
        'Sub Component Location',
        'Remaining Running Hours',
        'Vessel',
        'CMS Code',
        'Last Done Date',
        'Completion Date',
        'Last Done Running Hours',
        'Function',
        'Machinery Running Hours',
        'Attachment Indicator',
        'Department',
        'Job Source',
        'Due Date',
        'Next Due',
        'Job Action',
        'Title',
        'Job_Details'
    ]
    
    # Create export dataframe with specified columns
    export_data = pd.DataFrame()
    
    for col in export_columns:
        if col == 'Critical Job':
            # Use original 'Unnamed: 0' data if available, otherwise create sequential numbers
            if 'Unnamed: 0' in export_df.columns:
                export_data[col] = export_df['Unnamed: 0']
            else:
                export_data[col] = range(1, len(export_df) + 1)
        elif col == 'Job_Details':
            # Use the combined Job Code + Title column we created, or create it if missing
            if 'Job_Details' in export_df.columns:
                export_data[col] = export_df['Job_Details']
            else:
                job_code = export_df.get('Job Code', '').astype(str)
                title = export_df.get('Title', '').astype(str)
                export_data[col] = job_code + " - " + title
        else:
            # Use existing column if available, otherwise create empty column
            export_data[col] = export_df.get(col, '')
    
    return export_data

def display_export_options(df):
    """Display data export options"""
    st.header("📋 Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Filtered Data")
        
        # Prepare export data with specified columns and order
        export_df = prepare_export_data(df)
        
        # CSV export
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_data,
            file_name=f"major_machinery_maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Summary statistics  
        st.subheader("Summary Statistics")
        
        # Show export preview
        export_preview = export_df.head(5)
        st.write("**Export Preview (First 5 rows):**")
        st.dataframe(export_preview, use_container_width=True)
        
        summary_stats = {
            "Total Records": len(export_df),
            "Export Columns": len(export_df.columns),
            "Date Range": f"{df['Calculated Due Date'].min()} to {df['Calculated Due Date'].max()}" if 'Calculated Due Date' in df.columns else "N/A"
        }
        
        for key, value in summary_stats.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.subheader("Analysis Report")
        
        # Generate analysis report
        report = generate_analysis_report(df)
        
        st.download_button(
            label="📊 Download Analysis Report (TXT)",
            data=report,
            file_name=f"maintenance_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        st.subheader("Data Preview")
        
        # Show complete filtered data with key columns
        preview_columns = ['Vessel', 'Job_Details', 'Machinery Location', 'Frequency', 'Calculated Due Date', 'Job Status', 'Department']
        available_columns = [col for col in preview_columns if col in df.columns]
        preview_df = df[available_columns]
        
        st.write(f"**Complete Filtered Data:** {len(preview_df)} records")
        st.dataframe(preview_df, use_container_width=True, height=400)
        
        # Download option for complete preview data
        preview_csv = preview_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Complete Preview Data (CSV)",
            data=preview_csv,
            file_name=f"filtered_data_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def generate_analysis_report(df):
    """Generate a text-based analysis report"""
    report = f"""
MACHINERY MAINTENANCE ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS:
- Total Major Machinery Records: {len(df)}
- Unique Machinery Locations: {df['Machinery Location'].nunique()}
- Departments Involved: {df['Department'].nunique()}
- Pending Jobs: {len(df[df['Job Status'] == 'Pending'])}
- Overdue Items: {len(df[(df['Calculated Due Date'].notna()) & (pd.to_datetime(df['Calculated Due Date'], errors='coerce') < datetime.now())])}

TOP 10 MACHINERY BY JOB COUNT:
{df['Machinery Location'].value_counts().head(10).to_string()}

JOB ACTION DISTRIBUTION:
{df['Job Action'].value_counts().to_string()}

DEPARTMENT BREAKDOWN:
{df['Department'].value_counts().to_string()}

FREQUENCY ANALYSIS:
Most Common Frequencies:
{df['Frequency'].value_counts().head(10).to_string()}

DATE RANGE:
Earliest Due Date: {df['Calculated Due Date'].min()}
Latest Due Date: {df['Calculated Due Date'].max()}

This report was generated by the Machinery Maintenance Analysis Tool.
"""
    return report

if __name__ == "__main__":
    main()
