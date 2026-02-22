"""
Data loading functions for Dashboard_py
Handles all CSV and Excel file loading with preprocessing
"""
import pandas as pd
import numpy as np
from config import DATA_FILES, DATA_SCALE_FACTOR

# Global data variables (loaded once at startup)
sample_data = None
tool_sample = None
scenw_sample = None
type_sample = None
events_data = None
min_year = None
max_year = None
year_marks = None

def load_all_data():
    """
    Load all data files and store in global variables.
    This function should be called once at application startup.
    """
    global sample_data, tool_sample, scenw_sample, type_sample, events_data
    global min_year, max_year, year_marks

    try:
        # Load main dataset
        sample_data = pd.read_csv(DATA_FILES['main'])
        sample_data['Date'] = pd.to_datetime(sample_data['Date'], format='%Y-%m')
        sample_data = sample_data.rename(columns={'Date': 'date'})
        numeric_cols = sample_data.select_dtypes(include=[np.number]).columns
        sample_data[numeric_cols] = sample_data[numeric_cols] * DATA_SCALE_FACTOR
        sample_data = sample_data.sort_values('date').reset_index(drop=True)
        print(f"Successfully loaded {len(sample_data)} records from Example_df.csv")

        # Load tool correction dataset
        tool_sample = pd.read_csv(DATA_FILES['correction'])
        tool_sample['Date'] = pd.to_datetime(tool_sample['Date'], format='%Y-%m')
        tool_sample = tool_sample.rename(columns={'Date': 'date'})
        numeric_cols = tool_sample.select_dtypes(include=[np.number]).columns
        tool_sample[numeric_cols] = tool_sample[numeric_cols] * DATA_SCALE_FACTOR
        tool_sample = tool_sample.sort_values('date').reset_index(drop=True)
        print(f"Successfully loaded {len(tool_sample)} records from Example_correction.csv")

        # Load scenario dataset
        scenw_sample = pd.read_csv(DATA_FILES['scenario'])
        scenw_sample['Date'] = pd.to_datetime(scenw_sample['Date'], format='%Y-%m')
        scenw_sample = scenw_sample.rename(columns={'Date': 'date', 'Name': 'ScenName'})
        scenw_sample = scenw_sample.sort_values('date').reset_index(drop=True)
        print(f"Successfully loaded {len(scenw_sample)} records from Example_scenw.csv")

        # Load type detail dataset
        type_sample = pd.read_csv(DATA_FILES['type_detail'])
        type_sample['Date'] = pd.to_datetime(type_sample['Date'], format='%Y-%m')
        type_sample = type_sample.rename(columns={'Date': 'date'})
        numeric_cols = type_sample.select_dtypes(include=[np.number]).columns
        type_sample[numeric_cols] = type_sample[numeric_cols] * DATA_SCALE_FACTOR
        type_sample = type_sample.sort_values('date').reset_index(drop=True)
        print(f"Successfully loaded {len(type_sample)} records from Type_detail.csv")

        # Load events data
        try:
            events_data = pd.read_excel(DATA_FILES['events'])
            events_data['Date'] = pd.to_datetime(events_data['Date'], format='%Y-%m')
            events_data = events_data.sort_values('Date').reset_index(drop=True)
            print(f"Successfully loaded {len(events_data)} records from Events.xlsx")
        except FileNotFoundError:
            print("Events.xlsx not found. Creating empty events DataFrame.")
            events_data = pd.DataFrame(columns=['Date', 'Division', 'Metric', 'Summary', 'Additional_Details'])

        # Calculate year range for sliders
        min_year = sample_data['date'].dt.year.min()
        max_year = sample_data['date'].dt.year.max()
        year_marks = {year: {'label': str(year)} for year in range(min_year, max_year + 1)}

    except FileNotFoundError as e:
        print(f"Error loading data files: {e}")
        print("Creating empty DataFrames as fallback.")
        sample_data = pd.DataFrame()
        tool_sample = pd.DataFrame()
        scenw_sample = pd.DataFrame()
        type_sample = pd.DataFrame()
        events_data = pd.DataFrame(columns=['Date', 'Division', 'Metric', 'Summary', 'Additional_Details'])
        min_year = 2020
        max_year = 2025
        year_marks = {year: {'label': str(year)} for year in range(min_year, max_year + 1)}

# Load data on module import
load_all_data()
