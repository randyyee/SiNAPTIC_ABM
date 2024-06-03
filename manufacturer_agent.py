from mesa import Agent

# Define ManufacturerAgent
# On-time manufacturing of implants for additive, silicon nitride, means that implants can be produced immediately
# reducing risk of stockouts
# TODO add an adoption feature to optimize production (speed, cost, quality,
#  buy more machines if see consistently low inventory = increase production etc.) based on # of orders filled
# TODO add a COGs feature to track costs of goods sold, Operating expenses, Interest, Taxes, Depreciation
# TODO add workweek (production doesn't happen on weekends)
# TODO add chance of machine breakdowns
class ManufacturerAgent(Agent):

    def __init__(self, unique_id, model, type_of_manufacturer, cost_modifier):
        super().__init__(unique_id, model)
        self.type_of_manufacturer = type_of_manufacturer  # Either additive or subtractive
        self.machines = 2
        # self.initial_inventory = 0 # Define initial inventory
        self.inventory = 0
        self.total_orders = 0  # Keep track of total orders
        self.base_production_cost = 10  # Example base cost
        self.cost_modifier = cost_modifier  # How much cheaper should subtractive be, set in main
        self.adjusted_production_cost = self.base_production_cost * self.cost_modifier
        self.production_capacity = 100  # Example capacity to replenish inventory, per machine
        self.sales_revenue = 0
        self.profit_margin = 0.3  # Example profit margin
        #self.production_strategy = lambda step: 1 if step % 2 == 0 else 0.5  # Example strategy
        self.pending_implants = 0  # Record the number of implants to produce in a future step
        self.next_production_steps = 0  # Record the step when implants will be produced
        self.production_history = {}

    def schedule_implant_production(self):  # Schedule implants to be produced in future steps only if there are orders
        # ... (existing code)
        if self.type_of_manufacturer == 'subtractive':
            self.production_history[self.model.schedule.steps + 2] = self.total_orders  # Change this line
        else:
            self.production_history[self.model.schedule.steps + 1] = self.total_orders  # Change this line
        self.total_orders = 0  # Reset total orders

    def produce_implant(self, quantity):  # Produce implants and store in inventory
        self.inventory += quantity  # Add implants to inventory

    def order_implant(self, quantity):
        self.total_orders += quantity  # Increase total orders
        revenue = quantity * (self.adjusted_production_cost / self.profit_margin)
        self.sales_revenue += revenue

    def deliver_implant(self, quantity):
        self.inventory -= quantity

    def calculate_costs(self):
        return self.inventory * self.adjusted_production_cost

    def get_costs(self):
        return self.calculate_costs()

    def calculate_profit(self):
        return self.sales_revenue * self.profit_margin

    def get_profit(self):
        return self.calculate_profit()

    def step(self):
        # self.total_orders = 0  # Reset total orders for the step
        # Schedule production of implants if there are orders
        if self.total_orders > 0:
            self.schedule_implant_production()
        # Produce implants and store in inventory
        if self.model.schedule.steps in self.production_history:
            self.produce_implant(self.production_history[self.model.schedule.steps])
        print(f"Pending: {self.pending_implants}")
