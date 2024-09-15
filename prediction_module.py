import pandas as pd
import numpy as np

def load_climate_data(filepath):
    # Load climate data from a CSV file
    df = pd.read_csv(filepath)
    
    # Convert 'Temp Max' and 'Temp Min' to numeric, coercing any errors to NaN
    df['Temp Max'] = pd.to_numeric(df['Temp Max'], errors='coerce')
    df['Temp Min'] = pd.to_numeric(df['Temp Min'], errors='coerce')
    
    return df

def predict_climate(area, years, months, climate_df):
    # Ensure 'Date' is a datetime type
    climate_df['Date'] = pd.to_datetime(climate_df['Date'], format='%d-%m-%Y', errors='coerce')
    
    # Drop rows with missing values in 'Date', 'Temp Max', or 'Temp Min'
    climate_df = climate_df.dropna(subset=['Date', 'Temp Max', 'Temp Min'])
    
    # Extract year and month from 'Date'
    climate_df['Year'] = climate_df['Date'].dt.year
    climate_df['Month'] = climate_df['Date'].dt.month
    
    # Calculate monthly average temperature
    climate_df['Average_Temperature'] = (climate_df['Temp Max'] + climate_df['Temp Min']) / 2
    
    # Group by year and month to get monthly averages
    monthly_avg_temp = climate_df.groupby(['Year', 'Month']).agg({'Average_Temperature': 'mean'}).reset_index()
    
    # Fit a linear regression model to the data (years and months combined)
    monthly_avg_temp['Time'] = monthly_avg_temp['Year'] + (monthly_avg_temp['Month'] - 1) / 12.0  # Convert to fractional years
    try:
        # Fit the linear model for temperature trend
        temp_trend = np.polyfit(monthly_avg_temp['Time'], monthly_avg_temp['Average_Temperature'], 1)
        
        # Generate future time points (years + months) for predictions
        current_year = climate_df['Year'].max()
        current_month = climate_df['Month'].max()
        total_months = years * 12 + months
        
        # Calculate future months and years
        future_times = np.arange(current_year + (current_month - 1) / 12, current_year + total_months / 12, 1/12)
        future_years = future_times.astype(int)
        future_months = ((future_times - future_years) * 12 + 1).astype(int)
        
        # Predict future temperatures
        future_temps = np.polyval(temp_trend, future_times)
        
        # Create a DataFrame for predicted values
        predicted_df = pd.DataFrame({
            'Year': future_years,
            'Month': future_months,
            'Predicted_Avg_Temperature': future_temps
        })
        
        return predicted_df
    
    except Exception as e:
        raise RuntimeError(f"An error occurred while predicting climate data: {e}")
