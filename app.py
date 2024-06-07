import streamlit as st
from implant_market_model import ImplantMarketModel
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="SiNAPTIC Model Dashboard",
    page_icon="",
    layout="wide",
)

st.title('SiNAPTIC Agent-Based Model (ABM)')
st.write('''This is an agent-based model for capturing competition between manufacturing types, a subtractive manufacturer making titanium implants vs. a 3D printing manufacturer (i.e., SiNAPTIC) making silicon nitride implants. The following agents will be included: manufacturers, healthcare providers (i.e., hospitals), and patients. 
Use the parameters on the sidebar to modify the model.''')

with st.sidebar:
    st.header('Model Parameters')
    num_providers = st.sidebar.number_input('Number of Providers', min_value=1, value=3)
    initial_num_patients = st.sidebar.number_input('Initial Number of Patients', min_value=1, value=1000)
    patient_incidence = st.sidebar.number_input('Patient Incidence', min_value=1, value=48)
    time_period = st.sidebar.number_input('Time Period', min_value=1, value=365)
    additive_adoption_preference = st.sidebar.slider('Additive Adoption Preference', min_value=0.0, max_value=1.0, value=0.5)
    ae_probability = st.sidebar.slider('Adverse Events Probability', min_value=0.0, max_value=1.0, value=0.3)
    run_button = st.button('Run Model')

if run_button:
    # Create and run the model
    model = ImplantMarketModel(num_providers, initial_num_patients, patient_incidence, additive_adoption_preference, ae_probability)
    for i in range(time_period):  # Run for x steps
        model.step()  # Run the steps outlined in implantmarketmodel

    manufacturer_id_mapping = {
        0: 'additive',
        1: 'subtractive'
    }

    manufacturer_data = pd.DataFrame(model.manufacturer_rows)
    manufacturer_data['manufacturer_id'] = manufacturer_data['manufacturer_id'].map(manufacturer_id_mapping)
    provider_data = pd.DataFrame(model.provider_rows)
    patient_data = pd.DataFrame(model.patient_rows)
    patient_data['manufacturer_id'] = patient_data['manufacturer_id'].map(manufacturer_id_mapping)

    # Display data in Streamlit
    st.title('Results')

    # Printout model summaries
    manufacturer_summary = manufacturer_data.groupby('manufacturer_id').agg({
        'revenue': 'sum',
        'costs': 'sum',
        'profit': 'sum'  # ,
        # 'implants_produced': 'sum'
    })

    # Add summary for patient_data grouped by health_state and manufacturer_id
    # Filter for the last step
    final_step = patient_data['step'].max()
    final_step_data = patient_data[patient_data['step'] == final_step]
    patient_health_summary = final_step_data.groupby(['manufacturer_id', 'health_status']).size().reset_index(
        name='counts')

    # Pivot the patient_health_summary DataFrame
    patient_health_summary_pivot = patient_health_summary.pivot(index='manufacturer_id', columns='health_status',
                                                                values='counts')

    # Add utility values
    utility_values = {
        'minimal': 0.84,
        'moderate': 0.61,
        'severe': 0.55,
        'crippled': 0.51,
        'bedbound': 0.5
    }
    # Map health_status to utility values and multiply by counts
    patient_health_summary['total_utility'] = patient_health_summary['health_status'].map(utility_values) * \
                                              patient_health_summary['counts']

    # Calculate total utility for each manufacturer
    manufacturer_total_utility = patient_health_summary.groupby('manufacturer_id')['total_utility'].sum()
    # print(manufacturer_total_utility)

    # Calculate total number of patients for each manufacturer
    manufacturer_patient_counts = patient_health_summary.groupby('manufacturer_id')['counts'].sum()
    # print(manufacturer_patient_counts)

    # Calculate average utility for each manufacturer
    average_utility = manufacturer_total_utility / manufacturer_patient_counts.astype(float)
    average_utility = average_utility.reset_index()
    average_utility.columns = ['manufacturer_id', 'average_utility']

    # Create two columns
    col1, col2 = st.columns(2)

    # Display the line chart for revenue by manufacturer in the first column
    with col1:
        st.write('Revenue by Manufacturer')
        st.line_chart(manufacturer_data.pivot(index='step', columns='manufacturer_id', values='revenue'))

    # Display the patient health summary table in the second column
    with col2:
        st.write('Profit by Manufacturer')
        st.line_chart(manufacturer_data.pivot(index='step', columns='manufacturer_id', values='profit'))

    # Display the line chart for profit by manufacturer in the third column

    st.write('Patient Health Summary by Manufacturer')
    # Create a grouped bar chart with plotly
    fig = px.bar(patient_health_summary_pivot.reset_index(), x='manufacturer_id',
                 y=patient_health_summary_pivot.columns, barmode='group')
    # Display the grouped bar chart in Streamlit
    st.plotly_chart(fig)

    col5, col6 = st.columns(2)

    with col5:
        st.write("Manufacturer Summary:")
        st.write(manufacturer_summary)

    with col6:
        st.write("Average Utility Summary:")
        st.write(average_utility)

    tab1, tab2, tab3 = st.tabs(["Manufacturer Data", "Provider Data", "Patient Data"])
    
    with tab1:
        # st.header('Manufacturer Data')
        st.dataframe(manufacturer_data)

    with tab2:
        # st.header('Provider Data')
        st.dataframe(provider_data)
    
    with tab3:
        # st.header('Patient Data')
        st.dataframe(patient_data)
