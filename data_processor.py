import pandas as pd
import numpy as np
from datetime import datetime
import re
from utils import FrequencyParser, DateUtils

class DataProcessor:
    """Main data processing class for machinery maintenance data"""
    
    def __init__(self):
        self.df = None
        self.frequency_parser = FrequencyParser()
        self.date_utils = DateUtils()
    
    def load_data(self, file):
        """Load and clean data from uploaded CSV file"""
        try:
            # Read CSV file
            self.df = pd.read_csv(file)
            
            # Clean column names (remove BOM and whitespace)
            self.df.columns = self.df.columns.str.strip().str.replace('\ufeff', '')
            
            # Basic data cleaning
            self._clean_data()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def _clean_data(self):
        """Perform basic data cleaning operations"""
        # Remove completely empty rows
        self.df = self.df.dropna(how='all')
        
        # Strip whitespace from string columns
        string_columns = self.df.select_dtypes(include=['object']).columns
        for col in string_columns:
            self.df[col] = self.df[col].astype(str).str.strip()
        
        # Replace empty strings and 'nan' with NaN
        self.df = self.df.replace(['', 'nan', 'None'], np.nan)
        
        # Clean numeric columns
        if 'Remaining Running Hours' in self.df.columns:
            self.df['Remaining Running Hours'] = pd.to_numeric(
                self.df['Remaining Running Hours'], errors='coerce'
            )
        
        if 'Machinery Running Hours' in self.df.columns:
            self.df['Machinery Running Hours'] = pd.to_numeric(
                self.df['Machinery Running Hours'], errors='coerce'
            )
        
        # Parse dates with flexible format handling
        date_columns = ['Calculated Due Date', 'Last Done Date', 'Completion Date', 'Due Date', 'Next Due']
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], dayfirst=True, errors='coerce')
    
    def filter_major_machinery(self, min_hours=4000, min_months=30, year_filter=None, vessel_filter=None, machinery_filter=None, job_action_filter=None):
        """Filter data for major machinery based on frequency criteria"""
        if self.df is None:
            raise Exception("No data loaded. Please load data first.")
        
        # Create a copy for filtering
        filtered_df = self.df.copy()
        
        # Parse frequencies to comparable values
        filtered_df['Frequency_Hours'] = filtered_df['Frequency'].apply(
            self.frequency_parser.parse_to_hours
        )
        filtered_df['Frequency_Months'] = filtered_df['Frequency'].apply(
            self.frequency_parser.parse_to_months
        )
        
        # Apply frequency filters with strict checking based on original frequency format
        frequency_mask = pd.Series([False] * len(filtered_df))
        
        for idx, freq_str in enumerate(filtered_df['Frequency']):
            if pd.isna(freq_str) or freq_str == '':
                continue
            freq_str = str(freq_str).strip()
            
            # Check if it's an hour-based frequency
            if 'hour' in freq_str.lower():
                hours = self.frequency_parser.parse_to_hours(freq_str)
                if hours and hours >= min_hours:
                    frequency_mask.iloc[idx] = True
            
            # Check if it's a month-based frequency  
            elif 'month' in freq_str.lower():
                months = self.frequency_parser.parse_to_months(freq_str)
                if months and months >= min_months:
                    frequency_mask.iloc[idx] = True
        
        filtered_df = filtered_df[frequency_mask]
        
        # Apply year filter if specified
        if year_filter and year_filter != "All Years":
            try:
                target_year = int(year_filter)
                due_dates = pd.to_datetime(filtered_df['Calculated Due Date'], errors='coerce')
                filtered_df['Due_Year'] = due_dates.dt.year
                year_mask = (filtered_df['Due_Year'] == target_year) | filtered_df['Due_Year'].isna()
                filtered_df = filtered_df[year_mask]
            except ValueError:
                pass  # Skip year filtering if invalid year
        
        # Apply vessel filter if specified (supports multiple selections)
        if vessel_filter:
            if isinstance(vessel_filter, list) and len(vessel_filter) > 0:
                vessel_mask = filtered_df['Vessel'].isin(vessel_filter)
                filtered_df = filtered_df[vessel_mask]
            elif isinstance(vessel_filter, str):
                vessel_mask = filtered_df['Vessel'] == vessel_filter
                filtered_df = filtered_df[vessel_mask]
        
        # Apply machinery location filter if specified (supports multiple selections)
        if machinery_filter:
            if isinstance(machinery_filter, list) and len(machinery_filter) > 0:
                machinery_mask = filtered_df['Machinery Location'].isin(machinery_filter)
                filtered_df = filtered_df[machinery_mask]
            elif isinstance(machinery_filter, str) and machinery_filter != "All Locations":
                machinery_mask = filtered_df['Machinery Location'] == machinery_filter
                filtered_df = filtered_df[machinery_mask]
        
        # Apply job action filter if specified (supports multiple selections)
        if job_action_filter:
            if isinstance(job_action_filter, list) and len(job_action_filter) > 0:
                job_action_mask = filtered_df['Job Action'].isin(job_action_filter)
                filtered_df = filtered_df[job_action_mask]
            elif isinstance(job_action_filter, str):
                job_action_mask = filtered_df['Job Action'] == job_action_filter
                filtered_df = filtered_df[job_action_mask]
        
        # Remove helper columns
        columns_to_drop = ['Frequency_Hours', 'Frequency_Months']
        if 'Due_Year' in filtered_df.columns:
            columns_to_drop.append('Due_Year')
        
        for col in columns_to_drop:
            if col in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=[col])
        
        return filtered_df
    
    def get_summary_stats(self):
        """Get summary statistics for the loaded data"""
        if self.df is None:
            return {}
        
        stats = {
            'total_records': len(self.df),
            'vessels': self.df['Vessel'].nunique() if 'Vessel' in self.df.columns else 0,
            'departments': self.df['Department'].nunique() if 'Department' in self.df.columns else 0,
            'machinery_locations': self.df['Machinery Location'].nunique() if 'Machinery Location' in self.df.columns else 0,
            'pending_jobs': len(self.df[self.df['Job Status'] == 'Pending']) if 'Job Status' in self.df.columns else 0,
            'date_range': {
                'min_date': self.df['Calculated Due Date'].min() if 'Calculated Due Date' in self.df.columns else None,
                'max_date': self.df['Calculated Due Date'].max() if 'Calculated Due Date' in self.df.columns else None
            }
        }
        
        return stats
    
    def get_frequency_distribution(self):
        """Get distribution of maintenance frequencies"""
        if self.df is None or 'Frequency' not in self.df.columns:
            return {}
        
        freq_counts = self.df['Frequency'].value_counts()
        return freq_counts.to_dict()
    
    def get_machinery_breakdown(self):
        """Get breakdown by machinery location"""
        if self.df is None or 'Machinery Location' not in self.df.columns:
            return pd.DataFrame()
        
        breakdown = self.df.groupby('Machinery Location').agg({
            'Job Code': 'count',
            'Job Status': lambda x: (x == 'Pending').sum(),
            'Department': lambda x: ', '.join(x.dropna().astype(str).unique()) if x.notna().any() else 'Unknown',
            'Frequency': lambda x: ', '.join(x.dropna().astype(str).unique()[:3]) if x.notna().any() else 'Unknown'
        })
        
        # Rename columns manually
        breakdown.columns = ['Total Jobs', 'Pending Jobs', 'Departments', 'Frequencies']
        
        return breakdown.sort_values('Total Jobs', ascending=False)
    
    def validate_data(self):
        """Validate the loaded data for required columns"""
        if self.df is None:
            return False, "No data loaded"
        
        required_columns = ['Job Code', 'Frequency', 'Calculated Due Date', 'Machinery Location']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        return True, "Data validation passed"
