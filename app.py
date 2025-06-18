import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import DataProcessor
from utils import DateUtils, format_number
import io

def main():
    st.set_page_config(
        page_title="Machinery Maintenance Analysis",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔧 Machinery Maintenance Analysis Tool")
    st.markdown("*Analyze vessel maintenance data focusing on major machinery with frequencies > 4000 hours OR 30+ months*")
    
    # Initialize session state
    if 'combined_data' not in st.session_state:
        st.session_state.combined_data = None
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = None
    if 'data_processors' not in st.session_state:
        st.session_state.data_processors = {}
    
    # Sidebar for file upload and controls
    with st.sidebar:
        st.header("📁 Data Upload")
        
        # Upload mode selection
        upload_mode = st.radio(
            "Choose Upload Mode:",
            ["Single File", "Multiple Files"],
            help="Single File: Upload one CSV file\nMultiple Files: Upload multiple CSV files for vessel comparison"
        )
        
        if upload_mode == "Single File":
            uploaded_file = st.file_uploader(
                "Choose CSV file",
                type="csv",
                help="Upload your machinery maintenance CSV file"
            )
            
            if uploaded_file is not None:
                try:
                    with st.spinner("Loading data..."):
                        processor = DataProcessor()
                        processor.load_data(uploaded_file)
                        if processor.df is not None:
                            st.session_state.combined_data = processor.df.copy()
                            st.session_state.data_processors = {uploaded_file.name: processor}
                    
                    if st.session_state.combined_data is not None:
                        st.success(f"✅ Loaded {len(st.session_state.combined_data)} records")
                        
                        # Display data info
                        st.subheader("📊 Data Overview")
                        st.write(f"**Records:** {len(st.session_state.combined_data)}")
                        st.write(f"**Vessels:** {st.session_state.combined_data['Vessel'].nunique()}")
                        st.write(f"**Departments:** {st.session_state.combined_data['Department'].nunique()}")
                        st.write(f"**Machinery Locations:** {st.session_state.combined_data['Machinery Location'].nunique()}")
                    else:
                        st.error("Failed to load data from file")
                        
                except Exception as e:
                    st.error(f"❌ Error loading file: {str(e)}")
        
        else:  # Multiple Files mode
            uploaded_files = st.file_uploader(
                "Choose CSV files",
                type="csv",
                accept_multiple_files=True,
                help="Upload multiple CSV files for vessel comparison"
            )
            
            if uploaded_files:
                try:
                    with st.spinner("Loading multiple files..."):
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
        total_jobs = len(filtered_df)
        st.metric("Total Jobs", total_jobs)
    
    with col2:
        unique_machinery = filtered_df['Machinery Location'].nunique()
        st.metric("Machinery Locations", unique_machinery)
    
    with col3:
        unique_departments = filtered_df['Department'].nunique()
        st.metric("Departments", unique_departments)
    
    with col4:
        unique_job_codes = filtered_df['Job Code'].nunique()
        st.metric("Job Codes", unique_job_codes)
    
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
    
    # Create pivot table: Vessel -> Year -> Quarter -> Job Count (not unique machinery)
    kpi_data = []
    
    for vessel in sorted(df_with_dates['Vessel'].unique()):
        vessel_data = df_with_dates[df_with_dates['Vessel'] == vessel]
        
        for year in sorted(vessel_data['Year'].unique()):
            year_data = vessel_data[vessel_data['Year'] == year]
            
            # Total jobs for the year (not unique machinery count)
            year_job_count = len(year_data)
            
            # Quarterly breakdown - count of jobs, not unique machinery
            for quarter in [1, 2, 3, 4]:
                quarter_data = year_data[year_data['Quarter'] == quarter]
                quarter_job_count = len(quarter_data) if not quarter_data.empty else 0
                
                kpi_data.append({
                    'Vessel': vessel,
                    'Year': int(year),
                    'Quarter': f'Q{quarter}',
                    'Job_Count': quarter_job_count,
                    'Year_Total': year_job_count
                })
    
    if not kpi_data:
        st.warning("No KPI data available.")
        return
    
    kpi_df = pd.DataFrame(kpi_data)
    
    # Create pivot table for better visualization
    pivot_table = kpi_df.pivot_table(
        index=['Vessel', 'Year'], 
        columns='Quarter', 
        values='Job_Count', 
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
    - 🟢 **Dark Green**: 0 maintenance jobs
    - 🟢 **Light Green**: 1-10 maintenance jobs  
    - 🟡 **Yellow**: 11-50 maintenance jobs
    - 🔴 **Red**: 50+ maintenance jobs
    """)

def display_yearly_analysis(df):
    """Display yearly analysis of due dates"""
    st.header("📅 Yearly Maintenance Schedule Analysis")
    
    # Parse dates and create yearly breakdown
    df_copy = df.copy()
    df_copy['Due_Date'] = pd.to_datetime(df_copy['Calculated Due Date'], errors='coerce')
    df_copy['Due_Year'] = df_copy['Due_Date'].dt.year
    
    # Filter out invalid dates
    df_with_dates = df_copy[df_copy['Due_Date'].notna()]
    
    if df_with_dates.empty:
        st.warning("No valid due dates found for yearly analysis.")
        return
    
    # Yearly summary
    yearly_counts = df_with_dates['Due_Year'].value_counts().sort_index()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Yearly trend chart
        fig = px.bar(
            x=yearly_counts.index,
            y=yearly_counts.values,
            title="Maintenance Jobs by Year",
            labels={'x': 'Year', 'y': 'Number of Jobs'},
            color=yearly_counts.values,
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Yearly statistics
        st.subheader("📊 Yearly Statistics")
        for year in sorted(yearly_counts.index):
            st.metric(f"Year {int(year)}", int(yearly_counts[year]))
    
    # Monthly breakdown for current/selected years
    st.subheader("📅 Monthly Breakdown")
    df_with_dates['Due_Month'] = df_with_dates['Due_Date'].dt.month
    df_with_dates['Month_Name'] = df_with_dates['Due_Date'].dt.month_name()
    
    # Create monthly chart for each year
    years_available = sorted(df_with_dates['Due_Year'].unique())
    selected_year = st.selectbox("Select Year for Monthly Analysis", years_available)
    
    if selected_year:
        year_data = df_with_dates[df_with_dates['Due_Year'] == selected_year]
        monthly_counts = year_data['Month_Name'].value_counts()
        
        # Reorder months properly
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        monthly_counts = monthly_counts.reindex([month for month in month_order if month in monthly_counts.index], fill_value=0)
        
        fig = px.bar(
            x=monthly_counts.index,
            y=monthly_counts.values,
            title=f"Monthly Distribution for {int(selected_year)}",
            labels={'x': 'Month', 'y': 'Number of Jobs'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def display_machinery_breakdown(df):
    """Display machinery-specific breakdown"""
    st.header("🔧 Machinery wise analysis")
    
    # Machinery location analysis
    machinery_counts = df['Machinery Location'].value_counts().head(20)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Top machinery locations chart
        fig = px.bar(
            x=machinery_counts.values,
            y=machinery_counts.index,
            orientation='h',
            title="Top 20 Machinery Locations by Job Count",
            labels={'x': 'Number of Jobs', 'y': 'Machinery Location'}
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Machinery statistics
        st.subheader("📊 Machinery Statistics")
        st.metric("Total Machinery Locations", df['Machinery Location'].nunique())
        st.metric("Total Jobs", len(df))
        st.metric("Avg Jobs per Machinery", round(len(df) / df['Machinery Location'].nunique(), 2))
    
    # Department breakdown
    st.subheader("🏢 Department Analysis")
    dept_counts = df['Department'].value_counts()
    
    fig = px.pie(
        values=dept_counts.values,
        names=dept_counts.index,
        title="Jobs Distribution by Department"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed machinery information by vessel
    st.subheader("🚢 Detailed Machinery Information by Vessel")
    
    # Group by vessel and machinery location
    vessel_machinery = df.groupby(['Vessel', 'Machinery Location']).agg({
        'Job Code': 'count',
        'Frequency': lambda x: ', '.join(x.dropna().unique()[:3]) if len(x.dropna()) > 0 else 'N/A',
        'Job Action': lambda x: ', '.join(x.dropna().unique()[:2]) if len(x.dropna()) > 0 else 'N/A'
    }).reset_index()
    
    vessel_machinery.columns = ['Vessel', 'Machinery Location', 'Job Count', 'Frequency Sample', 'Job Actions']
    vessel_machinery = vessel_machinery.sort_values(['Vessel', 'Job Count'], ascending=[True, False])
    
    # Display by vessel
    for vessel in sorted(df['Vessel'].unique()):
        with st.expander(f"🚢 {vessel} - Machinery Details"):
            vessel_data = vessel_machinery[vessel_machinery['Vessel'] == vessel]
            st.dataframe(vessel_data.drop('Vessel', axis=1), use_container_width=True)

def prepare_export_data(df):
    """Prepare data for export with specified columns and naming"""
    export_df = df.copy()
    
    # Create a renamed copy for export
    if 'Unnamed: 0' in export_df.columns:
        export_df = export_df.rename(columns={'Unnamed: 0': 'Critical Job'})
    
    # Remove Unnamed: 3 column if it exists
    if 'Unnamed: 3' in export_df.columns:
        export_df = export_df.drop('Unnamed: 3', axis=1)
    
    return export_df

def display_export_options(df):
    """Display data export options"""
    st.header("📋 Data Export & Reports")
    
    # Prepare export data
    export_df = prepare_export_data(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export Filtered Data")
        st.write(f"**Records to export:** {len(export_df)}")
        st.write(f"**Columns:** {len(export_df.columns)}")
        
        # CSV export
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"machinery_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download the filtered data as a CSV file"
        )
    
    with col2:
        st.subheader("📄 Analysis Report")
        
        # Generate report
        report_text = generate_analysis_report(df)
        
        st.download_button(
            label="📥 Download Report",
            data=report_text,
            file_name=f"analysis_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download a text-based analysis report"
        )
    
    # Data preview
    st.subheader("👀 Export Data Preview")
    st.dataframe(export_df.head(10), use_container_width=True)

def generate_analysis_report(df):
    """Generate a text-based analysis report"""
    report = f"""
MACHINERY MAINTENANCE ANALYSIS REPORT
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================

SUMMARY STATISTICS:
- Total Jobs: {len(df)}
- Unique Machinery Locations: {df['Machinery Location'].nunique()}
- Unique Vessels: {df['Vessel'].nunique()}
- Unique Departments: {df['Department'].nunique()}
- Unique Job Codes: {df['Job Code'].nunique()}

VESSEL BREAKDOWN:
"""
    
    for vessel in sorted(df['Vessel'].unique()):
        vessel_data = df[df['Vessel'] == vessel]
        report += f"- {vessel}: {len(vessel_data)} jobs\n"
    
    report += f"""
DEPARTMENT BREAKDOWN:
"""
    
    dept_counts = df['Department'].value_counts()
    for dept, count in dept_counts.head(10).items():
        report += f"- {dept}: {count} jobs\n"
    
    report += f"""
TOP MACHINERY LOCATIONS:
"""
    
    machinery_counts = df['Machinery Location'].value_counts()
    for machinery, count in machinery_counts.head(10).items():
        report += f"- {machinery}: {count} jobs\n"
    
    # Add yearly analysis if dates are available
    df_copy = df.copy()
    df_copy['Due_Date'] = pd.to_datetime(df_copy['Calculated Due Date'], errors='coerce')
    df_with_dates = df_copy[df_copy['Due_Date'].notna()]
    
    if not df_with_dates.empty:
        df_with_dates['Due_Year'] = df_with_dates['Due_Date'].dt.year
        yearly_counts = df_with_dates['Due_Year'].value_counts().sort_index()
        
        report += f"""
YEARLY SCHEDULE:
"""
        for year in sorted(yearly_counts.index):
            report += f"- {int(year)}: {int(yearly_counts[year])} jobs\n"
    
    return report

if __name__ == "__main__":
    main()
