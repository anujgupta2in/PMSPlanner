import re
import pandas as pd
from datetime import datetime, timedelta

class FrequencyParser:
    """Utility class for parsing maintenance frequencies"""
    
    def __init__(self):
        # Patterns for different frequency formats
        self.hour_pattern = re.compile(r'(\d+)\s*hours?', re.IGNORECASE)
        self.month_pattern = re.compile(r'(\d+)\s*months?', re.IGNORECASE)
        self.year_pattern = re.compile(r'(\d+)\s*years?', re.IGNORECASE)
        self.day_pattern = re.compile(r'(\d+)\s*days?', re.IGNORECASE)
        self.week_pattern = re.compile(r'(\d+)\s*weeks?', re.IGNORECASE)
    
    def parse_to_hours(self, frequency_str):
        """Parse frequency string to hours (for comparison)"""
        if pd.isna(frequency_str) or frequency_str == '':
            return None
        
        frequency_str = str(frequency_str).strip()
        
        # Direct hours
        hour_match = self.hour_pattern.search(frequency_str)
        if hour_match:
            return int(hour_match.group(1))
        
        # Convert months to approximate hours (assuming 30 days/month, 24 hours/day)
        month_match = self.month_pattern.search(frequency_str)
        if month_match:
            months = int(month_match.group(1))
            return months * 30 * 24  # Approximate conversion
        
        # Convert years to hours
        year_match = self.year_pattern.search(frequency_str)
        if year_match:
            years = int(year_match.group(1))
            return years * 365 * 24  # Approximate conversion
        
        # Convert days to hours
        day_match = self.day_pattern.search(frequency_str)
        if day_match:
            days = int(day_match.group(1))
            return days * 24
        
        # Convert weeks to hours
        week_match = self.week_pattern.search(frequency_str)
        if week_match:
            weeks = int(week_match.group(1))
            return weeks * 7 * 24
        
        return None
    
    def parse_to_months(self, frequency_str):
        """Parse frequency string to months (for comparison)"""
        if pd.isna(frequency_str) or frequency_str == '':
            return None
        
        frequency_str = str(frequency_str).strip()
        
        # Direct months
        month_match = self.month_pattern.search(frequency_str)
        if month_match:
            return int(month_match.group(1))
        
        # Convert years to months
        year_match = self.year_pattern.search(frequency_str)
        if year_match:
            years = int(year_match.group(1))
            return years * 12
        
        # Convert hours to approximate months (assuming 720 hours/month)
        hour_match = self.hour_pattern.search(frequency_str)
        if hour_match:
            hours = int(hour_match.group(1))
            return round(hours / 720, 1)  # Approximate conversion
        
        # Convert days to months
        day_match = self.day_pattern.search(frequency_str)
        if day_match:
            days = int(day_match.group(1))
            return round(days / 30, 1)  # Approximate conversion
        
        # Convert weeks to months
        week_match = self.week_pattern.search(frequency_str)
        if week_match:
            weeks = int(week_match.group(1))
            return round(weeks / 4.33, 1)  # Approximate conversion
        
        return None
    
    def get_frequency_category(self, frequency_str):
        """Categorize frequency into predefined categories"""
        hours = self.parse_to_hours(frequency_str)
        months = self.parse_to_months(frequency_str)
        
        if hours is not None:
            if hours < 1000:
                return "High Frequency"
            elif hours < 4000:
                return "Medium Frequency"
            else:
                return "Low Frequency (Major)"
        
        if months is not None:
            if months < 6:
                return "High Frequency"
            elif months < 24:
                return "Medium Frequency"
            else:
                return "Low Frequency (Major)"
        
        return "Unknown"

class DateUtils:
    """Utility class for date operations"""
    
    @staticmethod
    def parse_date(date_str):
        """Parse date string to datetime object"""
        if pd.isna(date_str) or date_str == '':
            return None
        
        try:
            return pd.to_datetime(date_str)
        except:
            return None
    
    @staticmethod
    def get_year_from_date(date_obj):
        """Extract year from datetime object"""
        if pd.isna(date_obj):
            return None
        return date_obj.year
    
    @staticmethod
    def is_overdue(due_date, reference_date=None):
        """Check if a date is overdue compared to reference date"""
        if reference_date is None:
            reference_date = datetime.now()
        
        if pd.isna(due_date):
            return False
        
        try:
            due_date_obj = pd.to_datetime(due_date)
            return due_date_obj < reference_date
        except:
            return False
    
    @staticmethod
    def days_until_due(due_date, reference_date=None):
        """Calculate days until due date"""
        if reference_date is None:
            reference_date = datetime.now()
        
        if pd.isna(due_date):
            return None
        
        try:
            due_date_obj = pd.to_datetime(due_date)
            delta = due_date_obj - reference_date
            return delta.days
        except:
            return None
    
    @staticmethod
    def get_quarter(date_obj):
        """Get quarter from datetime object"""
        if pd.isna(date_obj):
            return None
        return f"Q{date_obj.quarter}"
    
    @staticmethod
    def get_month_name(date_obj):
        """Get month name from datetime object"""
        if pd.isna(date_obj):
            return None
        return date_obj.strftime("%B")

def format_number(num):
    """Format number with appropriate units"""
    if pd.isna(num):
        return "N/A"
    
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(int(num))

def safe_divide(numerator, denominator):
    """Safely divide two numbers, returning 0 if denominator is 0"""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return 0
    return numerator / denominator

def clean_text(text):
    """Clean text by removing extra whitespace and special characters"""
    if pd.isna(text):
        return ""
    
    text = str(text).strip()
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text
