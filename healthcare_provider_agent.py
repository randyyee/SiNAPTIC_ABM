from mesa import Agent
import random


# Define HealthcareProviderAgent
# TODO implement patient feedback on implant preference
# TODO use before and after to figure out what to recommend
# TODO make if so only the patient is recording the health states and the provider can collect from their list of patients when they need the data
# TODO after collecting patient stats use that to determine which manufacturer to recommend
# TODO If implant not available go to other manufacturer


class HealthcareProviderAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.patient_max_capacity = 15  # Max capacity
        self.surgery_patients = []  # Keep track of patients needing surgery only, patients should be removed after receiving surgery
        self.patient_capacity = self.patient_max_capacity - len(self.surgery_patients)  # Capacity is max_capacity - patients needing surgery
        self.all_patients = []  # Keep track of all patients
        self.follow_up_intervals = [6 * 7, 3 * 30, 6 * 30, 365, 2 * 365]  # 6 weeks, 3 month, 6 month, 1 year, 2 years
        self.surgery_history = []  # Record the number of surgeries performed in each step
        self.surgeries_performed_step = 0  # Record the number of surgeries performed in each step

    def admit_patient(self, patient):  # Receive patients, get implant, perform surgery
        patient.assigned_y_n = True  # Mark the patient as assigned
        patient.health_status_history.append(('pre-surgery', patient.health_status))  # Have patient record their pre-surgery health status
        health_states = self.get_patient_health_states()  # Get the health states

        # Calculate the total rate of improvement for each manufacturer
        additive_manufacturer_rate = health_states.get('additive', {}).get('improved', 0)
        if additive_manufacturer_rate == 0:
            additive_manufacturer_rate = 1
        # Adjust the additive_adoption_preference based on the rates
        additive_adoption_preference = (self.model.additive_adoption_preference * additive_manufacturer_rate)
        # print("Additive Rate: ", additive_manufacturer_rate)
        # print("Additive Adoption Preference: ", additive_adoption_preference)
        # Use a random number to determine if the patient will go to additive or subtractive
        if random.random() < additive_adoption_preference:
            chosen_manufacturer = next((m for m in self.model.manufacturers if m.type_of_manufacturer == 'additive'), None)
        else:
            chosen_manufacturer = next((m for m in self.model.manufacturers if m.type_of_manufacturer == 'subtractive'), None)

        # Patient reserves implant on assignment
        chosen_manufacturer.order_implant(1)  # Order implant from manufacturer
        patient.manufacturer_id = chosen_manufacturer.unique_id  # Record the manufacturer ID, provider will take this from patient

    # Surgery ---------------------------------------------------------------------------------------
    def record_surgery(self):
        # Record the number of surgeries performed in each step
        self.surgery_history.append({"step": self.model.schedule.steps, "surgeries": self.surgeries_performed_step})

    def perform_surgery(self, patient):  # TODO make this different for manufacturer (i.e., type of implant)
        # Check if the manufacturer has inventory
        chosen_manufacturer = next((m for m in self.model.manufacturers if m.unique_id == patient.manufacturer_id), None)
        if chosen_manufacturer.inventory > 0:
            chosen_manufacturer.deliver_implant(1)  # Get implant from manufacturer
            self.surgeries_performed_step += 1  # Increment surgeries_performed
            self.record_surgery()  # Record the surgery
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

            # Record the step when the patient received treatment
            patient.step_received_treatment = self.model.schedule.steps

            # Change flags post-surgery
            patient.received_surgery = True
            patient.needs_urgent_surgery = False  # Reset urgent surgery flag, ok since those receiving regular surgery will be FALSE anyway
            # Record the step when the patient received surgery and their post-surgery health status
            patient.health_status_history.append(('post-surgery', patient.health_status))  # Record post-surgery health status, if second post-surgery in history means they received urgent surgery
            # Remove patient from surgery_patients list after surgery
            self.surgery_patients.remove(patient)  # Remove patient from surgery_patients list after surgery
            # Add patient to all_patients list after surgery
            self.all_patients.append(patient)
            # Finally, schedule all the follow-ups
            patient.follow_up_steps = [self.model.schedule.steps + interval for interval in self.follow_up_intervals]
            # Then set the next follow-up for the patient using the follow_up_steps list and next_follow_up_index
            patient.next_follow_up = patient.follow_up_steps.pop(patient.next_follow_up_index)

    # Follow-up -------------------------------------------------------------------------------------
    def perform_follow_up(self, patient):
        patient.next_follow_up_index += 1  # Increment next_follow_up_index, so we can get the patient's next follow-up step at the end of the method

        improvement_probabilities = {
            "improved": 0.33,
            "stable": 0.62,
            "worse": 0.05
        }

        new_status = random.choices(
            population=list(improvement_probabilities.keys()),
            weights=list(improvement_probabilities.values()),
            k=1
        )[0]

        if new_status == "improved":  # Chance for health_state to move to better if not already minimal
            if patient.health_status != "minimal":
                patient.health_status = "minimal"
        elif new_status == "worse":  # Chance for health_state to move to worse if not already bedbound
            if patient.health_status != "bedbound":
                patient.health_status = "bedbound"
                # Determine if patient needs urgent surgery for those who got worse
                if random.random() < self.model.ae_probability:  # 50% chance of needing urgent surgery
                    patient.needs_urgent_surgery = True
                    patient.received_surgery = False
                    self.surgery_patients.append(patient)  # Add patient back to surgery_patients list for urgent surgery

        # Update patient's health_status_history
        patient.health_status_history.append(('follow-up at step ' + str(self.model.schedule.steps),
                                              patient.health_status))  # Record follow-up health status with model step
        # Schedule the next follow-up based on the patient's follow_up_steps list
        patient.next_follow_up = patient.follow_up_steps.pop(patient.next_follow_up_index)

    # Analysis --------------------------------------------------------------------------------------
    # This method summarizes the before and after health states for each manufacturer. Only the last health status and
    # second to last is considered for each patient. Then the counts turned into rates for each manufacturer to determine
    # the effectiveness of the implants.
    def get_patient_health_states(self):
        health_states = {}
        health_state_order = ["minimal", "moderate", "severe", "crippled", "bedbound"]  # Define the order of health states

        for patient in self.all_patients:
            manufacturer_id = patient.manufacturer_id
            before_health_state = patient.health_status_history[-2][1]  # Get the second to last health state
            after_health_state = patient.health_status_history[-1][1]  # Get the last health state

            # Compare the before and after health states and categorize them
            if before_health_state is None or before_health_state == after_health_state:
                category = "same"
            elif health_state_order.index(before_health_state) > health_state_order.index(after_health_state):
                category = "improved"
            else:
                category = "worsened"

            # Increment the count of this category for this manufacturer
            if manufacturer_id not in health_states:
                health_states[manufacturer_id] = {"same": 0, "improved": 0, "worsened": 0}
            health_states[manufacturer_id][category] += 1

        # Convert counts to rates
        for manufacturer_id, categories in health_states.items():
            total = sum(categories.values())
            for category, count in categories.items():
                health_states[manufacturer_id][category] = count / total

        return health_states

    def get_cumulative_surgeries_performed(self):
        surgeries_performed = 0
        for patient in self.all_patients:
            surgeries_performed += sum(1 for status in patient.health_status_history if status[0] == 'post-surgery')
        return surgeries_performed

    # Step ------------------------------------------------------------------------------------------
    def step(self):
        # self.surgeries_performed = 0  # Reset surgeries_performed for each step
        # Prioritize patients marked for urgent surgery
        urgent_patients = [p for p in self.surgery_patients if p.needs_urgent_surgery]
        for patient in urgent_patients:
            self.perform_surgery(patient)
        # Handle regular surgery
        for patient in [p for p in self.surgery_patients if not p.needs_urgent_surgery]:
            self.perform_surgery(patient)
        # Handle follow-ups
        for patient in [p for p in self.all_patients if p.received_surgery]:
            if self.model.schedule.steps == patient.next_follow_up:
                self.perform_follow_up(patient)

        # Update patient_capacity
        self.patient_capacity = self.patient_max_capacity - len(self.surgery_patients)