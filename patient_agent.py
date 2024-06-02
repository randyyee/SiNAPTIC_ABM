from mesa import Agent
import random

# Define PatientAgent
# Patients will spawn randomly every step with one of the 3 worse health statuses
# TODO implement waiting time for surgery and getting worse, penalty to health state probabilities
# TODO add word-of-mouth behavior that influences new patients if made significant improvement post-surgery
# TODO implement future chance of adverse events, would affect health state

class PatientAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.step_spawned = self.model.schedule.steps  # Record the step when the patient is spawned
        self.health_status = random.choice(["severe", "crippled", "bedbound"])  # Initial health status will be one of these poor states
        self.health_status_history = []  # For recording entire health status history
        self.assigned_y_n = False  # Initialize assigned_y_n as False
        self.manufacturer_id = None  # Initialize manufacturer_id as None will record the manufacturer ID received
        self.days_waiting_for_surgery = 0  # For counting days waiting for surgery
        self.received_surgery = False  # Initialize received_surgery as False
        self.step_received_treatment = None  # Initialize step_received_treatment as None

        self.follow_up_steps = []  # Initialize follow_up_steps as an empty list
        self.next_follow_up = None  # Initialize next_follow_up as None will record the next follow-up step
        self.next_follow_up_index = 0  # Initialize next_follow_up_index as 0

        self.needs_urgent_surgery = False  # Initialize needs_urgent_surgery as False
        self.step_followup_treatment = None  # Initialize step_followup_treatment as None

    def step(self):
        if self.needs_urgent_surgery or not self.received_surgery:
            self.days_waiting_for_surgery += 1  # Increment days_waiting_for_surgery
