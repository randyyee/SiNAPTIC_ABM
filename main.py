from implant_market_model import ImplantMarketModel
import pandas as pd


def main():
    # Model parameters
    num_providers = 3
    initial_num_patients = 1000
    patient_incidence = 48  # (54/1000000) * initial_num_patients # Est. 17,500 new spinal cord injury cases each year
    time_period = 365  # 1 step = 1 day, so 10 years 3650
    additive_adoption_preference = 0.5  # Used in provider agent, starts at 50% preference for additive manufacturing
    # to be modified over time

    # Create and run the model
    model = ImplantMarketModel(num_providers, initial_num_patients, patient_incidence, additive_adoption_preference)
    for i in range(time_period):  # Run for x steps
        model.step()  # Run the steps outlined in implantmarketmodel

    # Write the DataFrames to CSV files after the model has finished running
    manufacturer_data = pd.DataFrame(model.manufacturer_rows)
    manufacturer_data.to_csv('manufacturer_data.csv', index=False)
    provider_data = pd.DataFrame(model.provider_rows)
    provider_data.to_csv('provider_data.csv', index=False)
    patient_data = pd.DataFrame(model.patient_rows)
    patient_data.to_csv('patient_data.csv', index=False)

    # Printout model summaries
    manufacturer_summary = manufacturer_data.groupby('manufacturer_id').agg({
        'revenue': 'sum',
        'costs': 'sum',
        'profit': 'sum',
        'implants_produced': 'sum'
    })
    print("Manufacturer Summary:")
    print(manufacturer_summary)

    # Add summary for provider_data
    provider_summary = provider_data.groupby('provider_id').agg({
        'surgeries_performed': 'max'
    })
    print("\nProvider Summary:")
    print(provider_summary)

    # Add summary for patient_data grouped by health_state and manufacturer_id
    # Filter for the last step
    final_step = patient_data['step'].max()
    final_step_data = patient_data[patient_data['step'] == final_step]
    patient_health_summary = final_step_data.groupby(['manufacturer_id', 'health_status']).size().reset_index(
        name='counts')
    print("\nPatient Health Summary:")
    print(patient_health_summary)

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

    print("\nAverage Utility Summary:")
    print(average_utility)


if __name__ == "__main__":
    main()
