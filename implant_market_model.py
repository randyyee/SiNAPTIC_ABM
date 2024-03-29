from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from collections import Counter
# Import your agent classes
from manufacturer_agent import ManufacturerAgent
from healthcare_provider_agent import HealthcareProviderAgent
from patient_agent import PatientAgent
import random

class ImplantMarketModel(Model):
    def __init__(self, num_providers, initial_num_patients, patient_incidence, additive_adoption_preference):
        super().__init__()
        self.additive_adoption_preference = additive_adoption_preference
        self.schedule = RandomActivation(self)
        self.manufacturers = []
        self.providers = []
        self.patients = []
        self.patient_incidence = patient_incidence
        self.follow_up_outcomes = []
        self.change_states = []

        # Create one additive and one subtractive manufacturer
        additive_manufacturer = ManufacturerAgent(0, self, 'additive', 1.0)
        subtractive_manufacturer = ManufacturerAgent(1, self, 'subtractive', 0.5)
        self.manufacturer_cumulative_outcomes = {
            0: {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0},
            1: {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0}}
        self.manufacturers.extend([additive_manufacturer, subtractive_manufacturer])
        self.schedule.add(additive_manufacturer)
        self.schedule.add(subtractive_manufacturer)

        # Create Healthcare Provider Agents
        for i in range(num_providers):
            provider = HealthcareProviderAgent(i + 2, self)  # Create a new provider
            self.providers.append(provider)  # Add to provider list
            self.schedule.add(provider)  # Add to model schedule so that each step it will be active

        # Create Patient Agents
        for j in range(initial_num_patients):
            patient = PatientAgent(j + num_providers + 2, self)  # Create a new patient
            self.patients.append(patient)  # Add to patient list
            self.schedule.add(patient)  # Add to model schedule so that each step it will be active

        # DataCollector setup
        self.datacollector = DataCollector(
            model_reporters={
                "Total Implants Sold": lambda m: sum([manufacturer.inventory for manufacturer in m.manufacturers]),
                "Average Health Status": lambda m: self.calculate_average_health_status(),
                "Manufacturer Profits": lambda m: {f"manufacturer_{manufacturer.unique_id}_profit": manufacturer.calculate_profit() for manufacturer in m.manufacturers}
            }
        )

    def try_spawn_patient(self):
        new_patients_count = random.randint(0, self.patient_incidence)
        for _ in range(new_patients_count):
            new_patient_id = "Patient_" + str(len(self.patients) + 1)
            new_patient = PatientAgent(new_patient_id, self)
            self.schedule.add(new_patient)
            self.patients.append(new_patient)
            #print(f"New patient {new_patient_id} spawned") # Uncomment if want to see each individual patient spawned
        if new_patients_count > 0:
            print(f"{new_patients_count} new patients spawned this step")

    def calculate_average_health_status(self):
        health_values = {"minimal": 0.84, "moderate": 0.61, "severe": 0.55, "crippled": 0.51, "bedbound": 0.5}  # Based off previous work
        if not self.patients:
            return 0
        total_health = sum([health_values.get(patient.health_status, 0) for patient in self.patients])
        return total_health / len(self.patients)

    def summarize_patients(self):
        # Initialize counters
        health_status_counts_awaiting = {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0, "improved": 0, "worse": 0, "critical": 0}
        health_status_counts_treated = {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0, "improved": 0, "worse": 0, "critical": 0}

        # Count health statuses
        for patient in self.patients:
            if patient.received_surgery:
                health_status_counts_treated[patient.health_status] += 1
            else:
                health_status_counts_awaiting[patient.health_status] += 1

        # Print summaries
        print("Health Status Counts for Patients Awaiting Treatment:")
        for status, count in health_status_counts_awaiting.items():
            print(f"  {status}: {count}")

        print("\nHealth Status Counts for Patients Who Received Treatment:")
        for status, count in health_status_counts_treated.items():
            print(f"  {status}: {count}")

    def summarize_provider_activities(self):  # Summarize the provider outcomes for each step
        print("Provider Surgery Summary:")
        for provider in self.providers:
            print(f"Provider {provider.unique_id} performed {provider.surgeries_performed} surgeries.")
            for health_status, count in provider.post_surgery_health_counts.items():
                print(f"  {health_status}: {count} patients")

    def summarize_follow_ups(self):
        follow_up_health_counts = {status: self.follow_up_outcomes.count(status) for status in ["minimal", "moderate", "severe", "crippled", "bedbound"]}
        print("Follow-Up Health Status Summary:")
        for status, count in follow_up_health_counts.items():
            print(f"  {status}: {count}")

    def summarize_change_states(self):
        if self.change_states:
            change_state_counts = Counter(self.change_states)
            print("Change State Summary for This Step:")
            for state, count in change_state_counts.items():
                print(f"  {state}: {count}")
        else:
            print("No change states to report for this step.")
        self.change_states.clear()  # Reset for the next step

    def summarize_manufacturer_outcomes(self):  # Summarizes each step
        manufacturer_outcomes = {
            manu.unique_id: {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0} for manu in
            self.manufacturers}

        for patient in self.patients:
            if hasattr(patient, 'manufacturer_id'):
                manu_id = patient.manufacturer_id
                health_state = patient.health_status
                if manu_id in manufacturer_outcomes and health_state in manufacturer_outcomes[manu_id]:
                    manufacturer_outcomes[manu_id][health_state] += 1

        print("Manufacturer Surgery Outcomes:")
        for manu_id, outcomes in manufacturer_outcomes.items():
            print(f"Manufacturer {manu_id}:")
            for state, count in outcomes.items():
                print(f"  {state}: {count}")

    def print_cumulative_outcomes(self):
        print("Cumulative Manufacturer Outcomes:")
        for manu_id, outcomes in self.manufacturer_cumulative_outcomes.items():
            print(f"Manufacturer {manu_id}:")
            for health_state, count in outcomes.items():
                print(f"  {health_state}: {count}")

    def step(self):
        self.datacollector.collect(self)

        # Access and print the latest collected data
        latest_data = self.datacollector.get_model_vars_dataframe().iloc[-1]
        print(f"----- Step {self.schedule.steps} -----")
        print("DataCollector Summary for this Step:")
        print(latest_data)

        # Print detailed information for each manufacturer
        for manufacturer in self.manufacturers:
            profit = manufacturer.calculate_profit()
            print(f"Manufacturer {manufacturer.unique_id} (Type: {manufacturer.type_of_manufacturer}) - Profit: {profit}, Inventory: {manufacturer.inventory}")

        self.try_spawn_patient()
        self.schedule.step()
        #self.summarize_provider_activities()
        #self.summarize_manufacturer_outcomes()
        print("Cumulative outcomes for each tech:")
        self.print_cumulative_outcomes()
        self.summarize_follow_ups()
        self.follow_up_outcomes.clear()
        self.summarize_patients()
        self.summarize_change_states()
        print("\n")