import os
import pandas as pd
from groq import Groq

# Set your GROQ_API_KEY environment variable
os.environ['GROQ_API_KEY'] = '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' 

# Initialize the Groq client
client = Groq()

def generate_climate_strategies(predicted_data):
    # Create the prompt for the LLaMA model
    prompt = f"""
    Given the following climate predictions for the next few years in Delhi:
    {predicted_data.to_string(index=False)},
    
    Please provide a list of effective strategies to mitigate the impact of climate change in Delhi. 
    Focus on areas such as how to deal with this at user level , water conservation, agricultural adaptation, urban planning, and disaster preparedness.
    """

    # Call the Groq API with the prompt and get the response
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-8b-8192",  # Replace with the correct model name
    )

    # Return the text output from the model
    return chat_completion.choices[0].message.content

def load_climate_data(filepath):
    # Load climate data from a CSV file
    df = pd.read_csv(filepath, parse_dates=['Date'])
    
    # Ensure columns are of correct types
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
    df['Temp Max'] = pd.to_numeric(df['Temp Max'], errors='coerce')
    df['Temp Min'] = pd.to_numeric(df['Temp Min'], errors='coerce')
    
    return df

def predict_climate(area, years):
    # Load climate data
    climate_df = load_climate_data('data/delhi-temp-rains.csv')

    # Filter data for the selected area and years
    climate_df = climate_df[climate_df['Date'].dt.year >= area]

    # Example of prediction logic (e.g., linear trend)
    climate_df['Year'] = climate_df['Date'].dt.year
    temp_trend = climate_df[['Year', 'Temp Max']].dropna().groupby('Year').mean().reset_index()
    temp_trend = temp_trend.set_index('Year').rolling(window=years).mean().reset_index()

    # Create the predicted data as a DataFrame
    predicted_data = temp_trend

    return predicted_data
