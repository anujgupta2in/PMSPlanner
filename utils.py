import re
import pandas as pd
from datetime import datetime

class FrequencyParser:
    """Utility class for parsing maintenance frequencies"""
    
    def __init__(self):
        # Common patterns for hour-based frequencies
        self.hour_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:hour|hr|h)s?',
            r'(\d+(?:\.\d+)?)\s*(?:operating|running|service)\s*(?:hour|hr|h)s?'
        ]
        
        # Common patterns for month-based frequencies
        self.month_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:month|mon|m)s?',
            r'(\d+(?:\.\d+)?)\s*(?:monthly|mo)s?'
        ]
    
    def parse_to_hours(self, frequency_str):
        """Parse frequency string to hours (for comparison)"""
        if not frequency_str or pd.isna(frequency_str):
            return None
        
        frequency_str = str(frequency_str).lower().strip()
        
        for pattern in self.hour_patterns:
            match = re.search(pattern, frequency_str)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def parse_to_months(self, frequency_str):
        """Parse frequency string to months (for comparison)"""
        if not frequency_str or pd.isna(frequency_str):
            return None
        
        frequency_str = str(frequency_str).lower().strip()
        
        for pattern in self.month_patterns:
            match = re.search(pattern, frequency_str)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def get_frequency_category(self, frequency_str):
        """Categorize frequency into predefined categories"""
        hours = self.parse_to_hours(frequency_str)
        months = self.parse_to_months(frequency_str)
        
        if hours:
            if hours >= 8000:
                return "Very High (8000+ hours)"
            elif hours >= 4000:
                return "High (4000-7999 hours)"
            elif hours >= 2000:
                return "Medium (2000-3999 hours)"
            else:
                return "Low (<2000 hours)"
        elif months:
            if months >= 60:
                return "Very High (60+ months)"
            elif months >= 30:
                return "High (30-59 months)"
            elif months >= 12:
                return "Medium (12-29 months)"
            else:
                return "Low (<12 months)"
        
        return "Unknown"

class DateUtils:
    """Utility class for date operations"""
    
    @staticmethod
    def parse_date(date_str):
        """Parse date string to datetime object"""
        if pd.isna(date_str) or date_str == '':
            return None
        
        # Common date formats
        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d/%m/%y',
            '%d-%m-%y',
            '%m/%d/%Y',
            '%m-%d-%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        # Try pandas to_datetime as fallback
        try:
            return pd.to_datetime(date_str, dayfirst=True)
        except:
            return None
    
    @staticmethod
    def get_year_from_date(date_obj):
        """Extract year from datetime object"""
        if date_obj and hasattr(date_obj, 'year'):
            return date_obj.year
        return None
    
    @staticmethod
    def is_overdue(due_date, reference_date=None):
        """Check if a date is overdue compared to reference date"""
        if not due_date:
            return False
        
        if not reference_date:
            reference_date = datetime.now()
        
        if isinstance(due_date, str):
            due_date = DateUtils.parse_date(due_date)
        
        return due_date < reference_date if due_date else False
    
    @staticmethod
    def days_until_due(due_date, reference_date=None):
        """Calculate days until due date"""
        if not due_date:
            return None
        
        if not reference_date:
            reference_date = datetime.now()
        
        if isinstance(due_date, str):
            due_date = DateUtils.parse_date(due_date)
        
        if due_date:
            delta = due_date - reference_date
            return delta.days
        
        return None
    
    @staticmethod
    def get_quarter(date_obj):
        """Get quarter from datetime object"""
        if not date_obj or not hasattr(date_obj, 'month'):
            return None
        
        month = date_obj.month
        if month in [1, 2, 3]:
            return 1
        elif month in [4, 5, 6]:
            return 2
        elif month in [7, 8, 9]:
            return 3
        else:
            return 4
    
    @staticmethod
    def get_month_name(date_obj):
        """Get month name from datetime object"""
        if date_obj and hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%B')
        return None

def format_number(num):
    """Format number with appropriate units"""
    if pd.isna(num):
        return "N/A"
    
    if isinstance(num, (int, float)):
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(int(num))
    
    return str(num)

def safe_divide(numerator, denominator):
    """Safely divide two numbers, returning 0 if denominator is 0"""
    try:
        if denominator == 0:
            return 0
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return 0

def clean_text(text):
    """Clean text by removing extra whitespace and special characters"""
    if pd.isna(text) or text == '':
        return ''
    
    text = str(text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove common problematic characters
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text.strip()
