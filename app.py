import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from audio_utils import AudioRecorder, AudioNoteManager

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Configuration 
st.set_page_config(page_title="HealthAnalytics Pro",
                    layout="wide",
                    page_icon="🏥",
                    initial_sidebar_state="expanded")

# Gemini AI Configuration
def initialize_gemini():
    try:
        genai.configure(api_key="AIzaSyCXMBjjHT2ETl-TsuH77Ur0GeVoh5EH3vQ")  # Replace with actual key
        # Test the connection
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Test connection")
        if response and response.text:
            return True
    except Exception as e:
        st.error(f"Failed to initialize Gemini AI: {e}")
        return False
    return False

# Initialize Gemini client
if 'gemini_initialized' not in st.session_state:
    st.session_state.gemini_initialized = initialize_gemini()

# Custom CSS with enhanced styling
st.markdown("""
<style>
    .main, .stApp {
        background-color: #1E1E2E;
        color: white;
    }
    .stMetric, div.stDataFrame {
        background-color: #252638;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #3A3A5A;
    }
    button[kind="primary"] {
        background-color: #4A4A8A;
        color: white;
    }
    h1, h2, h3, p {
        color: white !important;
    }
    .js-plotly-plot {
        background-color: #252638;
    }

    /* Navigation Bar Styling */
    .nav-container {
        background-color: #252638;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border: 1px solid #3A3A5A;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .nav-button {
        background-color: #4A4A8A;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
    }

    .nav-button:hover {
        background-color: #5A5A9A;
    }

    /* Health Card Styling */
    .health-card {
        background-color: #252638;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border: 1px solid #3A3A5A;
    }

    /* Timeline Styling */
    .timeline-item {
        background-color: #252638;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #4A4A8A;
    }
</style>
""",
            unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_logout_dialog' not in st.session_state:
    st.session_state.show_logout_dialog = False

# RBAC Configuration
USERS = {
    "admin": {
        "password": "1234",
        "role": "Admin",
        "name": "Admin User"
    },
    "doctor": {
        "password": "1234",
        "role": "Doctor",
        "name": "Dr. Smith"
    },
    "patient": {
        "password": "1234",
        "role": "Patient",
        "name": "Patient 610"
    }
}


@st.cache_data
def generate_sample_data():
    """Generate sample healthcare data"""
    np.random.seed(42)

    # Generate patients data
    patients = pd.DataFrame({
        'patient_id': [f"P{i:03d}" for i in range(1, 1001)],
        'name': [f"Patient {i}" for i in range(1, 1001)],
        'age':
        np.random.randint(18, 90, 1000),
        'gender':
        np.random.choice(['Male', 'Female'], 1000),
        'blood_type':
        np.random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-'],
                         1000),
        'state':
        np.random.choice(['MH', 'UP', 'TN', 'WB', 'KA', 'GJ'], 1000),
        'registration_date':
        pd.date_range(start='2023-01-01', periods=1000, freq='D')
    })

    # Generate medical records
    medical = pd.DataFrame({
        'record_id': [f"R{i:04d}" for i in range(1, 3001)],
        'patient_id': [patients['patient_id'][i % 1000] for i in range(3000)],
        'diagnosis':
        np.random.choice(
            ['Hypertension', 'Diabetes', 'TB', 'Heart Disease', 'Asthma'],
            3000),
        'systolic_bp':
        np.random.randint(90, 180, 3000),
        'diastolic_bp':
        np.random.randint(60, 120, 3000),
        'glucose':
        np.random.randint(70, 300, 3000),
        'visit_date':
        [patients['registration_date'][i % 1000] for i in range(3000)]
    })

    # Generate hospitals data
    hospitals = pd.DataFrame({
        'hospital_id': [f"H{i:02d}" for i in range(1, 51)],
        'name': [f"Hospital {i}" for i in range(1, 51)],
        'state':
        np.random.choice(['MH', 'UP', 'TN', 'WB', 'KA', 'GJ'], 50),
        'beds':
        np.random.randint(50, 500, 50)
    })

    # Save data
    patients.to_csv('data/patients.csv', index=False)
    medical.to_csv('data/medical.csv', index=False)
    hospitals.to_csv('data/hospitals.csv', index=False)

    return patients, medical, hospitals


@st.cache_data
def load_data():
    """Load or generate sample data"""
    try:
        patients = pd.read_csv('data/patients.csv')
        medical = pd.read_csv('data/medical.csv')
        hospitals = pd.read_csv('data/hospitals.csv')
        return patients, medical, hospitals
    except:
        return generate_sample_data()


def calculate_risk(row):
    """Calculate patient risk score"""
    try:
        age_factor = row['age'] / 100
        bp_factor = (row['systolic_bp'] - 120) / 100
        glucose_factor = (row['glucose'] - 100) / 200
        risk = (age_factor * 0.3) + (bp_factor * 0.4) + (glucose_factor * 0.3)
        return max(min(risk + 0.5, 1), 0)
    except:
        return 0.5


def navigation_bar():
    """Render navigation bar with profile switching and logout"""
    st.markdown("""
    <div class="nav-container">
        <div style="display: flex; align-items: center;">
            <h2 style="margin: 0;">🏥 HealthAnalytics Pro</h2>
        </div>
        <div style="display: flex; gap: 1rem;">
            <button class="nav-button" onclick="switchProfile()">Switch Profile</button>
            <button class="nav-button" onclick="logout()">Logout</button>
        </div>
    </div>
    """,
                unsafe_allow_html=True)

    # Handle logout button click
    if st.button("Logout", key="logout_btn"):
        st.session_state.user = None
        st.rerun()

    # Handle switch profile button click
    if st.button("Switch Profile", key="switch_profile_btn"):
        st.session_state.user = None
        st.rerun()


def login_page():
    """Render login page"""
    st.markdown(
        "<h1 style='text-align: center; color: white;'>🏥 HealthAnalytics Pro</h1>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<div style='background-color: #252638; padding: 20px; border-radius: 10px;'>",
            unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: white;'>Login</h2>",
                    unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.user = {
                    "username": username,
                    "role": USERS[username]["role"],
                    "name": USERS[username]["name"]
                }
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.markdown("</div>", unsafe_allow_html=True)


def analyze_patient_data(patient_data, medical_records):
    """Use Gemini AI to analyze patient data and provide insights"""
    if not st.session_state.gemini_initialized:
        return "AI analysis unavailable. Please check API configuration."

    try:
        # Format data for analysis
        patient_info = f"""
        Patient: {patient_data['name']}
        Age: {patient_data['age']}
        Gender: {patient_data['gender']}
        Blood Type: {patient_data['blood_type']}

        Recent Vitals:
        - Blood Pressure: {medical_records.iloc[-1]['systolic_bp']}/{medical_records.iloc[-1]['diastolic_bp']}
        - Glucose: {medical_records.iloc[-1]['glucose']} mg/dL
        - Diagnosis: {medical_records.iloc[-1]['diagnosis']}

        Historical Data:
        {medical_records[['visit_date', 'systolic_bp', 'diastolic_bp', 'glucose', 'diagnosis']].to_string()}
        """

        prompt = f"""
        Based on the following patient data, provide a concise health analysis:
        {patient_info}

        Include:
        1. Key health insights
        2. Potential risk factors
        3. Recommendations for improvement
        4. Trends in vital signs
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating analysis: {e}"


def analyze_population_health(patients_df, medical_df):
    """Use Gemini AI to analyze population health trends"""
    if not st.session_state.gemini_initialized:
        return "AI analysis unavailable. Please check API configuration."

    try:
        # Prepare summary statistics
        age_mean = patients_df['age'].mean()
        gender_dist = patients_df['gender'].value_counts().to_dict()
        common_diagnoses = medical_df['diagnosis'].value_counts().head(5).to_dict()
        avg_bp = f"{medical_df['systolic_bp'].mean():.1f}/{medical_df['diastolic_bp'].mean():.1f}"
        avg_glucose = f"{medical_df['glucose'].mean():.1f}"

        data_summary = f"""
        Population Statistics:
        - Total Patients: {len(patients_df)}
        - Average Age: {age_mean:.1f}
        - Gender Distribution: {gender_dist}
        - Average Blood Pressure: {avg_bp}
        - Average Glucose: {avg_glucose}
        - Top Diagnoses: {common_diagnoses}
        """

        prompt = f"""
        Based on the following healthcare population data, provide a concise analysis:
        {data_summary}

        Include:
        1. Key population health insights
        2. Notable trends or patterns
        3. Potential areas of concern
        4. Recommendations for healthcare providers
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating analysis: {e}"


def admin_dashboard():
    """Render admin dashboard"""
    st.title("Healthcare Analytics Dashboard")

    # Load data
    patients_df, medical_df, hospitals_df = load_data()

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", len(patients_df))
    with col2:
        st.metric("Total Hospitals", len(hospitals_df))
    with col3:
        st.metric("Active Cases", len(medical_df))
    with col4:
        high_risk = len(
            medical_df[medical_df.apply(calculate_risk, axis=1) > 0.7])
        st.metric("High Risk Cases", high_risk)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        state_counts = patients_df['state'].value_counts()
        fig = px.bar(x=state_counts.index,
                     y=state_counts.values,
                     title="Patient Distribution by State",
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        diagnosis_counts = medical_df['diagnosis'].value_counts()
        fig = px.pie(values=diagnosis_counts.values,
                     names=diagnosis_counts.index,
                     title="Diagnosis Distribution",
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # Add population health analysis section
    st.subheader("AI-Powered Population Health Insights")

    if st.button("Generate Population Health Analysis"):
        with st.spinner("Analyzing population health data..."):
            analysis = analyze_population_health(patients_df, medical_df)

        st.markdown(f"""
        <div style='background-color: #252638; padding: 20px; border-radius: 5px; margin-top: 20px;'>
            <h3>Population Health Analysis</h3>
            <p>{analysis}</p>
        </div>
        """, unsafe_allow_html=True)


def doctor_dashboard():
    if 'note_manager' not in st.session_state:
        st.session_state.note_manager = AudioNoteManager("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")

    st.markdown("<h1 style='color: white;'>Doctor Dashboard</h1>",
                unsafe_allow_html=True)

    patients_df, medical_df, hospitals_df = load_data()

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    # Get doctor's patients (using sample data for now)
    doctor_patients = patients_df['patient_id'].unique()[:10]
    total_patients = len(doctor_patients)
    active_cases = len(
        medical_df[medical_df['patient_id'].isin(doctor_patients)])

    with col1:
        st.metric("Total Patients", total_patients)
    with col2:
        st.metric("Active Cases", active_cases)
    with col3:
        high_risk = len(
            medical_df[(medical_df['patient_id'].isin(doctor_patients))
                       & (medical_df.apply(calculate_risk, axis=1) > 0.7)])
        st.metric("High Risk Patients", high_risk)
    with col4:
        avg_satisfaction = 4.5  # Placeholder
        st.metric("Patient Satisfaction", f"{avg_satisfaction}/5")

    # Tabs for different views
    tabs = st.tabs(["Patient Overview", "Health Analytics", "Appointments", "Clinical Notes"])

    with tabs[0]:  # Patient Overview
        st.subheader("My Patients")

        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("Search Patients by Name", "")
        with col2:
            risk_filter = st.selectbox(
                "Filter by Risk Level",
                ["All", "High Risk", "Medium Risk", "Low Risk"])

        # Filter patients
        my_patients = patients_df[patients_df['patient_id'].isin(
            doctor_patients)]
        if search:
            my_patients = my_patients[my_patients['name'].str.contains(
                search, case=False)]

        # Merge with medical data for risk calculation
        patient_risks = medical_df[medical_df['patient_id'].isin(
            my_patients['patient_id'])]
        patient_risks['risk_score'] = patient_risks.apply(calculate_risk,
                                                          axis=1)
        latest_risks = patient_risks.groupby(
            'patient_id')['risk_score'].last().reset_index()

        my_patients = pd.merge(my_patients,
                               latest_risks,
                               on='patient_id',
                               how='left')

        if risk_filter != "All":
            if risk_filter == "High Risk":
                my_patients = my_patients[my_patients['risk_score'] > 0.7]
            elif risk_filter == "Medium Risk":
                my_patients = my_patients[(my_patients['risk_score'] > 0.3)
                                          & (my_patients['risk_score'] <= 0.7)]
            else:  # Low Risk
                my_patients = my_patients[my_patients['risk_score'] <= 0.3]

        # Display patient list with risk scores
        st.dataframe(
            my_patients[['name', 'age', 'gender', 'blood_type',
                         'risk_score']].style.format({'risk_score': '{:.1%}'}),
            use_container_width=True)

    with tabs[1]:  # Health Analytics
        st.subheader("Patient Health Distribution")

        col1, col2 = st.columns(2)

        with col1:
            # Age distribution
            fig = px.histogram(my_patients,
                               x='age',
                               nbins=20,
                               title="Age Distribution",
                               template="plotly_dark")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Risk score distribution
            fig = px.histogram(my_patients,
                               x='risk_score',
                               nbins=20,
                               title="Risk Score Distribution",
                               template="plotly_dark")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        # Diagnosis breakdown
        st.subheader("Common Diagnoses")
        patient_diagnoses = medical_df[medical_df['patient_id'].isin(
            my_patients['patient_id'])]['diagnosis'].value_counts()

        fig = px.pie(values=patient_diagnoses.values,
                     names=patient_diagnoses.index,
                     title="Diagnosis Distribution",
                     template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                          paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # Add AI insights section
        st.subheader("AI-Powered Clinical Insights")

        selected_patient = st.selectbox("Select Patient for Analysis",
                                        my_patients['name'].tolist())

        if st.button("Generate Patient Analysis"):
            patient_id = my_patients[my_patients['name'] == selected_patient]['patient_id'].iloc[0]
            patient_data = patients_df[patients_df['patient_id'] == patient_id].iloc[0]
            patient_records = medical_df[medical_df['patient_id'] == patient_id].sort_values('visit_date')

            with st.spinner("Analyzing patient data..."):
                analysis = analyze_patient_data(patient_data, patient_records)

            st.markdown(f"""
            <div style='background-color: #252638; padding: 20px; border-radius: 5px; margin-top: 20px;'>
                <h3>Clinical Analysis for {selected_patient}</h3>
                <p>{analysis}</p>
            </div>
            """, unsafe_allow_html=True)

    with tabs[2]:  # Appointments
        st.subheader("Upcoming Appointments")

        # Date selection
        selected_date = st.date_input("Select Date", datetime.now())

        # Placeholder appointments data
        appointments = pd.DataFrame({
            'time':
            pd.date_range(start=f"{selected_date} 09:00", periods=5, freq='H'),
            'patient_name': ["Patient " + str(i) for i in range(1, 6)],
            'status': ['Scheduled'] * 5
        })

        # Display appointments in a modern card layout
        for _, appt in appointments.iterrows():
            with st.container():
                st.markdown(f"""
                <div style='
                    background-color: #252638;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                    border: 1px solid #3A3A5A;
                '>
                    <h4 style='margin: 0; color: white;'>{appt['time'].strftime('%H:%M')} - {appt['patient_name']}</h4>
                    <p style='margin: 5px 0; color: #B0B0B0;'>Status: {appt['status']}</p>
                </div>
                """,
                            unsafe_allow_html=True)

    with tabs[3]:  # Clinical Notes tab
        st.subheader("Clinical Notes with Voice Transcription")
        
        # Patient selection
        selected_patient = st.selectbox(
            "Select Patient",
            patients_df['name'].tolist(),
            key="clinical_notes_patient"
        )
        
        # Audio recording controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Start Voice Recording"):
                st.session_state.note_manager.start_recording()
                st.info("Recording started... Speak your clinical notes")
                
        with col2:
            if st.button("⏹️ Stop & Save Recording"):
                if selected_patient:
                    patient_id = patients_df[patients_df['name'] == selected_patient]['patient_id'].iloc[0]
                    transcription = st.session_state.note_manager.stop_and_save(patient_id)
                    st.success("Recording saved!")
                    st.text_area("Audio Transcription Preview", 
                                transcription, 
                                height=150,
                                key="audio_transcription")
        
        # Text input fallback
        note_text = st.text_area(
            "Or enter notes manually",
            height=150,
            placeholder="Type your clinical notes here..."
        )
        
        # Analysis and saving
        if st.button("💾 Save & Analyze Notes"):
            if note_text or 'audio_transcription' in st.session_state:
                final_text = note_text or st.session_state.audio_transcription
                patient_id = patients_df[patients_df['name'] == selected_patient]['patient_id'].iloc[0]
                
                # Save to notes
                st.session_state.note_manager.notes.setdefault(patient_id, []).append({
                    "timestamp": datetime.now().isoformat(),
                    "transcription": final_text
                })
                
                # Generate AI analysis
                with st.spinner("Analyzing notes..."):
                    analysis = st.session_state.note_manager.analyze_note(final_text)
                    
                    st.markdown(f"""
                    <div style='background-color: #252638; 
                                padding: 15px; 
                                border-radius: 5px;
                                margin-top: 15px;'>
                        <h4>AI Analysis</h4>
                        <p>{analysis}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
        # Display previous notes (placeholder for now)
        st.subheader("Previous Notes")
        st.markdown("""
        <div style='background-color: #252638; padding: 15px; border-radius: 5px;'>
            <p><strong>Note History</strong></p>
            <p>This section will display previous notes for the selected patient.</p>
        </div>
        """, unsafe_allow_html=True)



def patient_dashboard():
    """Enhanced patient dashboard with more features and graphs"""
    navigation_bar()

    patients_df, medical_df, hospitals_df = load_data()

    # Get patient data
    patient_id = "P001"  # In real app, this would come from session state
    patient_data = patients_df[patients_df['patient_id'] == patient_id].iloc[0]

    # Header with patient info
    st.markdown(f"""
    <div class="health-card">
        <h1>{patient_data['name']}</h1>
        <p>Age: {patient_data['age']} | Gender: {patient_data['gender']} | Blood Type: {patient_data['blood_type']}</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Health Overview Cards
    st.subheader("📊 Health Overview")
    cols = st.columns(4)

    latest_record = medical_df[medical_df['patient_id'] ==
                               patient_id].sort_values('visit_date').iloc[-1]

    with cols[0]:
        st.metric(
            "Blood Pressure",
            f"{latest_record['systolic_bp']}/{latest_record['diastolic_bp']}",
            delta="-5/3",
            help="Systolic/Diastolic blood pressure in mmHg")

    with cols[1]:
        st.metric("Blood Glucose",
                  f"{latest_record['glucose']} mg/dL",
                  delta="-10",
                  help="Blood glucose level in mg/dL")

    with cols[2]:
        risk_score = calculate_risk(latest_record)
        st.metric("Health Risk Score",
                  f"{risk_score:.1%}",
                  delta="-0.5%",
                  help="Overall health risk assessment")

    with cols[3]:
        st.metric("Next Appointment",
                  "Tomorrow",
                  delta="1 day",
                  help="Time until your next scheduled appointment")

    # Tabs for different sections
    tabs = st.tabs([
        "📈 Health Trends", "🗓️ Appointments", "📋 Medical Records",
        "💊 Medications", "🎯 Health Goals", "🤖 AI Analysis"
    ])

    with tabs[0]:  # Health Trends
        st.subheader("Vital Signs History")

        # Get historical data
        patient_records = medical_df[medical_df['patient_id'] ==
                                     patient_id].sort_values('visit_date')

        # Interactive date range selector
        date_range = st.date_input("Select Date Range",
                                   value=(datetime.now() - timedelta(days=30),
                                          datetime.now()),
                                   key="trends_date_range")

        col1, col2 = st.columns(2)

        with col1:
            # Blood Pressure Trend
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=patient_records['visit_date'],
                           y=patient_records['systolic_bp'],
                           name='Systolic',
                           line=dict(color='#4A4A8A', width=2)))
            fig.add_trace(
                go.Scatter(x=patient_records['visit_date'],
                           y=patient_records['diastolic_bp'],
                           name='Diastolic',
                           line=dict(color='#8A4A4A', width=2)))

            fig.update_layout(title="Blood Pressure History",
                              template="plotly_dark",
                              plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)',
                              height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Glucose Trend
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=patient_records['visit_date'],
                           y=patient_records['glucose'],
                           name='Glucose',
                           line=dict(color='#4A8A4A', width=2),
                           fill='tozeroy'))

            fig.update_layout(title="Blood Glucose History",
                              template="plotly_dark",
                              plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)',
                              height=400)
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:  # Appointments
        st.subheader("Appointment Management")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="health-card">
                <h3>Schedule New Appointment</h3>
            </div>
            """,
                        unsafe_allow_html=True)

            appointment_type = st.selectbox("Appointment Type", [
                "Regular Checkup", "Specialist Consultation", "Follow-up",
                "Lab Tests"
            ])

            appointment_date = st.date_input("Preferred Date", datetime.now())
            appointment_time = st.selectbox("Preferred Time", [
                "Morning (9:00 AM - 12:00 PM)", "Afternoon (2:00 PM - 5:00 PM)"
            ])

            if st.button("Schedule Appointment", key="schedule_btn"):
                st.success("Appointment request submitted successfully!")

        with col2:
            st.markdown("""
            <div class="health-card">
                <h3>Upcoming Appointments</h3>
            </div>
            """,
                        unsafe_allow_html=True)

            # Sample upcoming appointments
            appointments = [{
                "date": "Tomorrow",
                "time": "10:00 AM",
                "type": "Regular Checkup"
            }, {
                "date": "Next Week",
                "time": "2:30 PM",
                "type": "Lab Tests"
            }]

            for appt in appointments:
                st.markdown(f"""
                <div class="timeline-item">
                    <h4>{appt['type']}</h4>
                    <p>{appt['date']} at {appt['time']}</p>
                </div>
                """,
                            unsafe_allow_html=True)

    with tabs[2]:  # Medical Records
        st.subheader("Medical History Timeline")

        # Filter records by date
        date_filter = st.date_input("Filter by Date",
                                    value=(datetime.now() - timedelta(days=90),
                                           datetime.now()),
                                    key="records_date_filter")

        # Display medical records in timeline format
        for _, record in patient_records.iterrows():
            st.markdown(f"""
            <div class="timeline-item">
                <h4>{record['visit_date'].split()[0]}</h4>
                <p><strong>Diagnosis:</strong> {record['diagnosis']}</p>
                <p><strong>Vitals:</strong> BP: {record['systolic_bp']}/{record['diastolic_bp']}, 
                   Glucose: {record['glucose']} mg/dL</p>
            </div>
            """,
                        unsafe_allow_html=True)

    with tabs[3]:  # Medications
        st.subheader("Medication Tracking")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="health-card">
                <h3>Current Medications</h3>
            </div>
            """,
                        unsafe_allow_html=True)

            # Sample medications
            medications = [{
                "name": "Medication A",
                "dosage": "10mg",
                "frequency": "Twice daily"
            }, {
                "name": "Medication B",
                "dosage": "5mg",
                "frequency": "Once daily"
            }]

            for med in medications:
                st.markdown(f"""
                <div class="timeline-item">
                    <h4>{med['name']}</h4>
                    <p>Dosage: {med['dosage']}</p>
                    <p>Frequency: {med['frequency']}</p>                </div>
                """,
                            unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="health-card">
                <h3>Medication Schedule</h3>
            </div>
            """,
                        unsafe_allow_html=True)

            # Sample schedule
            schedule = [{
                "time": "8:00 AM",
                "medications": ["Medication A"]
            }, {
                "time": "8:00 PM",
                "medications": ["Medication A", "Medication B"]
            }]

            for slot in schedule:
                st.markdown(f"""
                <div class="timeline-item">
                    <h4>{slot['time']}</h4>
                    <p>{', '.join(slot['medications'])}</p>
                </div>
                """,
                            unsafe_allow_html=True)

    with tabs[4]:  # Health Goals
        st.subheader("Health Goals and Progress")

        # Sample health goals
        goals = [{
            "goal": "Lower Blood Pressure",
            "target": "120/80",
            "progress": 75
        }, {
            "goal": "Maintain Glucose Levels",
            "target": "100 mg/dL",
            "progress": 90
        }, {
            "goal": "Regular Exercise",
            "target": "30 mins/day",
            "progress": 60
        }]

        for goal in goals:
            st.markdown(f"""
            <div class="health-card">
                <h4>{goal['goal']}</h4>
                <p>Target: {goal['target']}</p>
                <div style="width: 100%; background-color: #3A3A5A; height: 20px; border-radius: 10px;">
                    <div style="width: {goal['progress']}%; background-color: #4A8A4A; height: 100%; border-radius: 10px;">
                    </div>
                </div>
                <p style="text-align: right;">{goal['progress']}%</p>
            </div>
            """,
                        unsafe_allow_html=True)

    with tabs[5]:  # AI Analysis
        st.subheader("AI-Powered Health Insights")

        patient_records = medical_df[medical_df['patient_id'] == patient_id].sort_values('visit_date')

        with st.spinner("Generating personalized health insights..."):
            analysis = analyze_patient_data(patient_data, patient_records)

        st.markdown(f"""
        <div class="health-card">
            <h3>Your Personalized Health Analysis</h3>
            <p>{analysis}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate New Analysis"):
            with st.spinner("Updating analysis..."):
                analysis = analyze_patient_data(patient_data, patient_records)
                st.markdown(f"""
                <div class="health-card">
                    <h3>Your Personalized Health Analysis</h3>
                    <p>{analysis}</p>
                </div>
                """, unsafe_allow_html=True)


# Main function to run the app
def main():
    if st.session_state.user is None:
        login_page()
    else:
        if st.session_state.user['role'] == 'Admin':
            admin_dashboard()
        elif st.session_state.user['role'] == 'Doctor':
            doctor_dashboard()
        elif st.session_state.user['role'] == 'Patient':
            patient_dashboard()


if __name__ == "__main__":
    main()
