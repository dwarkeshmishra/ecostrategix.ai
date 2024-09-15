import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prediction_module import load_climate_data, predict_climate
from llama_strategy_module import generate_climate_strategies
import folium
from streamlit_folium import st_folium
from PIL import Image
import numpy as np
from datetime import datetime

# Load the dataset
DATA_PATH = 'climate_data/delhi-temp-rains.csv'
climate_data = load_climate_data(DATA_PATH)


# Display sustainability image banner
st.image("logo.jpg", use_column_width=True)

# Streamlit UI - Title and Introduction
st.title('🌍 NCR Climate Change Prediction and Adaptation System')
st.markdown("""
Welcome to our sustainability-driven dashboard! This tool provides monthly climate change predictions and AI-generated adaptation strategies for the NCR Delhi region. 🌱  
Let's explore the temperature, air quality, and water availability projections over the next few years, all while embracing sustainability.
""")


# Sidebar for user inputs
st.sidebar.title("Filter Options")
area = st.sidebar.text_input("Enter the area (for information purposes only)", "Delhi")

# Define current date and future end date options
current_date = datetime.now()
start_year = current_date.year
start_month = current_date.month

# End Year and Month Slider
end_year = st.sidebar.slider("Select the End Year", min_value=start_year, max_value=start_year + 20, value=start_year + 5)
end_month = st.sidebar.slider("Select the End Month", min_value=1, max_value=12, value=1)

# Display the map
st.sidebar.markdown("### Map Visualization")
m = folium.Map(location=[28.6139, 77.209], zoom_start=10)  # Centered on Delhi

# Add a marker for visualization purposes (could be dynamic based on user input later)
folium.Marker([28.6139, 77.209], popup="NCR Delhi").add_to(m)

# Render the map in Streamlit
st_folium(m, width=700, height=450)

# Helper function to generate temperature warning images
def generate_warning_image(temp):
    if temp > 40:
        img = Image.open('extreme_heat_warning.png')
    elif temp < 5:
        img = Image.open('extreme_cold_warning.png')
    else:
        img = Image.open('moderate_temp.png')
    return img

# Display predictions and strategies
if st.sidebar.button('Predict Climate Data'):
    try:
        # Convert selected end month and year into timeline
        years_to_predict = end_year - start_year
        months_to_predict = end_month - start_month if end_year == start_year else 12 - start_month + end_month
        predicted_data = predict_climate(area, years_to_predict, months_to_predict, climate_data)
        
        st.markdown("### Predicted Climate Data:")
        st.write(predicted_data)

        # Display line chart for monthly predictions
        st.markdown("### Climate Predictions over Time")
        
        # Combine Year and Month into a single string for plotting
        predicted_data['Date'] = pd.to_datetime(predicted_data[['Year', 'Month']].assign(DAY=1))

        # Line Chart
        fig = px.line(predicted_data, x='Date', y='Predicted_Avg_Temperature', title='Monthly Climate Projections')
        st.plotly_chart(fig)

        # Add markers for extreme temperatures
        extreme_temps = predicted_data[(predicted_data['Predicted_Avg_Temperature'] > 40) | 
                                       (predicted_data['Predicted_Avg_Temperature'] < 5)]
        fig.add_trace(go.Scatter(x=extreme_temps['Date'], 
                                 y=extreme_temps['Predicted_Avg_Temperature'], 
                                 mode='markers',
                                 marker=dict(color='red', size=10),
                                 name='Extreme Temperatures'))

        # Bar Chart
        st.markdown("### Monthly Temperature Bar Chart")
        fig_bar = px.bar(predicted_data, x='Date', y='Predicted_Avg_Temperature', title='Monthly Average Temperatures')
        st.plotly_chart(fig_bar)

        # Heatmap
        st.markdown("### Heatmap of Predicted Temperatures")
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=predicted_data['Predicted_Avg_Temperature'],
            x=predicted_data['Month'],
            y=predicted_data['Year'],
            colorscale='Viridis'))
        fig_heatmap.update_layout(title='Heatmap of Temperature Predictions (Year vs. Month)')
        st.plotly_chart(fig_heatmap)

        # Display relevant images for extreme temperatures
        st.markdown("### Temperature Warning Images")
        for temp in extreme_temps['Predicted_Avg_Temperature']:
            st.image(generate_warning_image(temp), caption=f"Temperature: {temp}°C")

        st.session_state.predicted_data = predicted_data
    except Exception as e:
        st.error(f"An error occurred while predicting climate data: {e}")

# Button to generate adaptation strategies
if st.sidebar.button('Generate Strategies'):
    if 'predicted_data' in st.session_state:
        try:
            strategies = generate_climate_strategies(st.session_state.predicted_data)
            st.markdown("### 🌱 AI-Generated Climate Adaptation Strategies:")
            st.write(strategies)
            st.image("adaptation_strategy_image.jpg", use_column_width=True, caption="Sustainability strategies in action")
        except Exception as e:
            st.error(f"An error occurred while generating strategies: {e}")
    else:
        st.error("Please generate the predictions first.")

# Clear button to reset predictions and strategies
if st.sidebar.button('Clear'):
    st.session_state.pop('predicted_data', None)
    st.write("Predictions and strategies cleared.")
