import mesa
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import pandas as pd
# Import your agent classes
from manufacturer_agent import ManufacturerAgent
from healthcare_provider_agent import HealthcareProviderAgent
from patient_agent import PatientAgent
import random

class ImplantMarketModel(mesa.Model):
    def __init__(self, num_providers, initial_num_patients, patient_incidence, additive_adoption_preference, ae_probability):
        super().__init__()
        self.additive_adoption_preference = additive_adoption_preference
        self.ae_probability = ae_probability
        self.schedule = RandomActivation(self)
        self.manufacturers = []
        self.providers = []
        self.patients = []
        self.patient_incidence = patient_incidence
        self.patients_waiting = []
        # For tracking patients needing assignment
        self.patients_needing_surgery = []
        # For recording data
        self.manufacturer_rows = []
        self.provider_rows = []
        self.patient_rows = []

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

    def step(self):
        print(f"Current step: {self.schedule.steps}")

        # Try to spawn new patients
        self.try_spawn_patient()

        # Update the list of patients needing surgery who are not assigned yet
        self.patients_needing_surgery = [p for p in self.patients if not p.assigned_y_n]

        # ---------------------------------------------------------------------------------------------
        # Assign patients to providers
        for patient in self.patients_needing_surgery:
            available_providers = [provider for provider in self.providers if len(provider.surgery_patients) < provider.patient_max_capacity]
            if available_providers:
                provider = random.choice(available_providers)  # Select a provider randomly from the list of available providers
                patient.provider_id = provider.unique_id  # Assign the provider ID to the patient
                provider.surgery_patients.append(patient)  # Add patient to surgery_patients list first
                provider.admit_patient(patient)  # Provider will then assign the patient to a manufacturer
                self.patients_needing_surgery.remove(patient)  # Remove patient from master list of patients needing surgery

        # ---------------------------------------------------------------------------------------------
        # Execute all agents' step methods
        self.schedule.step()

        # ---------------------------------------------------------------------------------------------
        # Record data for each agent at every step
        print(f"Patients waiting for surgery: {len(self.patients_needing_surgery)}")

        for manufacturer in self.manufacturers:
            new_row = {
                "step": self.schedule.steps,
                "manufacturer_id": manufacturer.unique_id,
                "revenue": round(manufacturer.sales_revenue, 2),
                "costs": round(manufacturer.get_costs(), 2),
                "profit": round(manufacturer.get_profit(), 2),
                "production": manufacturer.production_history,
                #"orders": manufacturer.total_orders,
                "inventory": manufacturer.inventory#,
                #"pending": manufacturer.pending_implants,
                #"production_steps": manufacturer.next_production_steps
            }
            print(f"Manufacturer new_row: {new_row}")
            self.manufacturer_rows.append(new_row)

        for provider in self.providers:
            new_row = {
                "step": self.schedule.steps,
                "provider_id": provider.unique_id,
                #"surgeries_performed": provider.surgeries_performed_step,
                "surgery_patients": len(provider.surgery_patients),
                "cumulative_patients": len(provider.all_patients),
                "additive_preference": self.additive_adoption_preference
            }
            print(f"Provider new_row: {new_row}")
            self.provider_rows.append(new_row)

        for patient in self.patients:
            new_row = {
                "step": self.schedule.steps,
                "patient_id": patient.unique_id,
                "health_status": patient.health_status,
                "received_surgery": patient.received_surgery,
                "days_waiting_for_surgery": patient.days_waiting_for_surgery,
                "step_received_treatment": patient.step_received_treatment,
                "manufacturer_id": patient.manufacturer_id,
                #"days_since_surgery": patient.days_since_surgery,
                "next_follow_up": patient.next_follow_up,
                #"change_state": patient.change_state,
                "needs_urgent_surgery": patient.needs_urgent_surgery,
                "step_followup_treatment": patient.step_followup_treatment
            }
            self.patient_rows.append(new_row)

        print("-------------------")