import streamlit as st
import io
import contextlib
import time
from implant_market_model import ImplantMarketModel
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt


def plot_metrics(data, title):
    fig, ax = plt.subplots()
    for metric in ['revenue', 'cost', 'profit']:
        # Pivot data for the current metric
        pivoted_data = data.pivot(index='step', columns='manufacturer_id', values=metric)
        # Plot each manufacturer's metric over time
        pivoted_data.plot(ax=ax, label=metric)
    plt.title(title)
    plt.xlabel('Step')
    plt.ylabel('Value')
    plt.legend()
    plt.show()


st.set_page_config(
    page_title="SiNAPTIC ABM",
    page_icon="",
    layout="wide",
)

st.title('SiNAPTIC Agent-Based Model (ABM)')
st.write('''This is an agent-based model for simulating competition between manufacturing types, a subtractive manufacturer making titanium implants vs. a 3D printing manufacturer (i.e., SiNAPTIC) making silicon nitride implants. The following agents will be included: manufacturers, healthcare providers (i.e., hospitals), and patients. 
Use the parameters on the sidebar to modify the model.''')

with st.sidebar:
    st.header('Model Parameters')
    st.write('Set your parameters before running the model.')
    num_providers = st.sidebar.number_input('Number of Providers', min_value=1, value=3)
    initial_num_patients = st.sidebar.number_input('Initial Number of Patients', min_value=1, value=1000)
    patient_incidence = st.sidebar.number_input('Patient Incidence', min_value=1, value=48)
    time_period = st.sidebar.number_input('Time Period', min_value=1, value=365)
    additive_adoption_preference = st.sidebar.slider('Additive Adoption Preference (0.50 means no preference for either manufacturer)', min_value=0.0, max_value=1.0, value=0.5)
    ae_probability_additive = st.sidebar.slider('Adverse Events Probability (silicon nitride)', min_value=0.0, max_value=1.0, value=0.3)
    ae_probability_subtractive = st.sidebar.slider('Adverse Events Probability (titanium)', min_value=0.0, max_value=1.0, value=0.3)
    run_button = st.button('Run Model')

# col1, col2 = st.columns(2)
col5, col6 = st.columns(2)

if run_button:
    # Create and run the model
    model = ImplantMarketModel(num_providers, initial_num_patients, patient_incidence, 
                               additive_adoption_preference, ae_probability_additive, ae_probability_subtractive)
    
    # Create placeholders for each element
    output_placeholder = st.empty()
    result_placeholder = st.empty()
    divider_placehoder = st.empty()
    
    col1, col2 = st.columns(2)
    with col1:
        chart_title_placeholder = st.empty()
        chart_placeholder = st.empty()
    with col2:
        chart_title_placeholder2 = st.empty()
        chart_placeholder2 = st.empty()
    
    fighead_placeholder = st.empty()
    chart_placeholder3 = st.empty()
    
    col3, col4 = st.columns(2)
    with col3:
        fighead_placeholder2 = st.empty()
        table_placeholder2 = st.empty()
    with col4:
        fighead_placeholder3 = st.empty()
        table_placeholder3 = st.empty()

    for i in range(time_period):  # Run for x steps
        
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            model.step()  # Run the steps outlined in implantmarketmodel
        output_placeholder.code(output_buffer.getvalue())
        time.sleep(0.2)

        manufacturer_id_mapping = {
            0: 'additive',
            1: 'subtractive'
        }

        manufacturer_data = pd.DataFrame(model.manufacturer_rows)
        manufacturer_data['manufacturer_id'] = manufacturer_data['manufacturer_id'].map(manufacturer_id_mapping)
        # Filter data for additive and subtractive processes
        additive_data = manufacturer_data[manufacturer_data['manufacturer_id'] == 'additive']
        subtractive_data = manufacturer_data[manufacturer_data['manufacturer_id'] == 'subtractive']

        provider_data = pd.DataFrame(model.provider_rows)
        patient_data = pd.DataFrame(model.patient_rows)
        patient_data['manufacturer_id'] = patient_data['manufacturer_id'].map(manufacturer_id_mapping)

        # Display data in Streamlit
        result_placeholder.subheader('Results')
        divider_placehoder.divider()
        
        # Printout model summaries
        manufacturer_summary = manufacturer_data.groupby('manufacturer_id').agg({
            'revenue': 'sum',
            'costs': 'sum',
            'profit': 'sum'  ,
            'inventory': 'sum'
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

        # Add utility values TODO summarize utilities for every step of patient history instead of just last
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

        # Display the manufacturer charts
        # afig = pd.melt(additive_data, id_vars=['step', 'manufacturer_id'], value_vars=['revenue', 'costs', 'profit'], var_name='metric', value_name='value')
        # sfig = pd.melt(subtractive_data, id_vars=['step', 'manufacturer_id'], value_vars=['revenue', 'costs', 'profit'], var_name='metric', value_name='value')
        chart_title_placeholder.write('Revenue by Manufacturer')
        # chart_placeholder.line_chart(afig.pivot(index='step', columns='metric', values='value'))
        chart_placeholder.line_chart(manufacturer_data.pivot(index='step', columns='manufacturer_id', values='revenue'))
        chart_title_placeholder2.write('Profit by Manufacturer')
        # chart_placeholder2.line_chart(sfig.pivot(index='step', columns='metric', values='value'))
        chart_placeholder2.line_chart(manufacturer_data.pivot(index='step', columns='manufacturer_id', values='profit'))
        
        # Display the patient health status chart
        fighead_placeholder.write('Patient Health Summary by Manufacturer')
        # Desired order of columns
        columns_order = ['minimal', 'moderate', 'severe', 'crippled', 'bedbound']
        # Filter columns_order to include only columns that exist in patient_health_summary_pivot
        filtered_columns_order = [col for col in columns_order if col in patient_health_summary_pivot.columns]

        # Reorder the columns in patient_health_summary_pivot using the filtered list
        patient_health_summary_pivot = patient_health_summary_pivot[filtered_columns_order]
        fig = px.bar(patient_health_summary_pivot.reset_index(), x='manufacturer_id',
                    y=patient_health_summary_pivot.columns, barmode='group')
        # Display the grouped bar chart in Streamlit
        chart_placeholder3.plotly_chart(fig)

        # Display the costs and utilities tables
        fighead_placeholder2.write("Manufacturer Summary:")
        table_placeholder2.write(manufacturer_summary)
        fighead_placeholder3.write("Average Utility Summary:")
        table_placeholder3.write(average_utility)


        # tab3, tab4, tab5 = st.tabs(["Manufacturer Data", "Provider Data", "Patient Data"])
        
    # with tab3:
            # st.header('Manufacturer Data')
        # st.dataframe(manufacturer_data)

    # with tab4:
            # st.header('Provider Data')
        # st.dataframe(provider_data)
        
    # with tab5:
            # st.header('Patient Data')
        # st.dataframe(patient_data)
