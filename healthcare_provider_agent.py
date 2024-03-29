from mesa import Agent
import random


# Define HealthcareProviderAgent
# TODO record manufacturer to track surgeries and outcomes here (note patient agent will also track manufacturer itself)
# TODO implement patient feedback on implant preference
# TODO mirror patient methods but for provider
#  e.g. provider - give_treatment(queuing, capacity, manufacturer buy) , patient - get_treatment (track post-surgery health),
#  conduct_followup, attend_followup
# If implant not available go to other or wait?


class HealthcareProviderAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.patient_capacity = 5  # Example capacity
        self.patients = []
        self.surgeries_performed = 0
        self.post_surgery_health_counts = {"minimal": 0, "moderate": 0, "severe": 0, "crippled": 0, "bedbound": 0}

    def receive_patient(self, patient):  # Receive patients, get implant, give them surgery
        if len(self.patients) < self.patient_capacity:
            self.patients.append(patient)  # Keep track of patients that received surgery from this provider
            if random.random() < self.model.additive_adoption_preference:
                chosen_manufacturer = next(m for m in self.model.manufacturers if m.type_of_manufacturer == 'additive')
            else:
                chosen_manufacturer = next(
                    m for m in self.model.manufacturers if m.type_of_manufacturer == 'subtractive')
            chosen_manufacturer.sell_implant(1)
            patient.manufacturer_id = chosen_manufacturer.unique_id  # Record the manufacturer ID
        #     print(f"Provider {self.unique_id} received patient {patient.unique_id} for surgery.")  # Uncomment to see everyone going to surgery
        # else:
        #     print(f"Provider {self.unique_id} is at capacity. Patient {patient.unique_id} could not be treated.")

    def perform_surgery(self, patient):
        outcome_probabilities = {
            "minimal": 0.5,
            "moderate": 0.30,
            "severe": 0.1,
            "crippled": 0.05,
            "bedbound": 0.05
        }
        patient.health_status = random.choices(
            population=list(outcome_probabilities.keys()),
            weights=list(outcome_probabilities.values()),
            k=1
        )[0]
        self.surgeries_performed += 1
        self.post_surgery_health_counts[patient.health_status] += 1
        # print(f"Provider {self.unique_id} performed surgery on patient {patient.unique_id}. Post-surgery health: {patient.health_status}")
        # Update the cumulative outcomes for the manufacturer
        manu_id = patient.manufacturer_id
        health_status = patient.health_status

        # Check and update the outcomes
        if manu_id in self.model.manufacturer_cumulative_outcomes:
            if health_status in self.model.manufacturer_cumulative_outcomes[manu_id]:
                self.model.manufacturer_cumulative_outcomes[manu_id][health_status] += 1

        patient.received_surgery = True

    def step(self):
        # Prioritize patients marked for urgent surgery
        urgent_patients = [p for p in self.patients if p.needs_urgent_surgery]
        for patient in urgent_patients:
            self.perform_surgery(patient)
            patient.needs_urgent_surgery = False
        # Handle other patients
        for patient in [p for p in self.patients if not p.needs_urgent_surgery]:
            if not patient.received_surgery:
                self.perform_surgery(patient)
            elif patient.model.schedule.steps == patient.next_follow_up:
                patient.attend_follow_up()
        # Clear patient list at the end of each step
        self.patients.clear()
