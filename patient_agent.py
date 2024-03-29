from mesa import Agent
import random

# Define PatientAgent
# Patients will spawn randomly every step with one of the 3 worse health statuses until they can receive treatment
# TODO implement waiting time for surgery and getting worse, penalty to health state probabilities
# TODO keep track of implant received
# TODO add word-of-mouth behavior that influences new patients if made significant improvement post-surgery
# TODO implement reoperation need
class PatientAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.health_status = random.choice(["severe", "crippled", "bedbound"])  # Initial health status will be one of these poor states
        self.change_state = None  # New attribute for change in health state
        self.received_surgery = False
        self.days_since_surgery = 0
        self.follow_up_intervals = [6 * 7, 3 * 30, 6 * 30, 365, 2 * 365]  # 6 weeks, 3 month, 6 month, 1 year, 2 years
        self.next_follow_up = None
        self.needs_urgent_surgery = False

    def schedule_next_follow_up(self):
        if not self.follow_up_intervals:
            return  # No more follow-ups scheduled
        self.next_follow_up = self.model.schedule.steps + self.follow_up_intervals.pop(0)

    def attend_follow_up(self):
        if self.model.schedule.steps == self.next_follow_up:
            self.reassess_health()

            # Handle adverse event chance
            adverse_event_chance = 0.05  # Example probability
            if random.random() < adverse_event_chance:
                self.change_state = "critical"

            if self.change_state == "critical":
                self.needs_urgent_surgery = True

            self.schedule_next_follow_up()

    def reassess_health(self):
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
        self.model.change_states.append(self.change_state)  # Report the change state
        # if new_status == "improved": # Chance for health_state to move to better if not already minimal
        #     self.change_state = "improved"
        # elif new_status == "worse": # Chance for health_state to move to worse if not already bedbound
        #     self.change_state = "worse"

    def find_and_receive_treatment(self):
        available_providers = [provider for provider in self.model.providers if len(provider.patients) < provider.patient_capacity]
        if available_providers:
            chosen_provider = self.random.choice(available_providers)
            chosen_provider.receive_patient(self)

    def step(self):
        if self.needs_urgent_surgery or (not self.received_surgery and self.health_status in ["severe", "crippled", "bedbound"]):
            self.find_and_receive_treatment()
        elif self.received_surgery:  # Otherwise schedule a followup
            self.days_since_surgery += 1
            if self.next_follow_up is None:
                self.schedule_next_follow_up()
            elif self.model.schedule.steps >= self.next_follow_up:
                self.attend_follow_up()