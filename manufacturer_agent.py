from mesa import Agent

# Define ManufacturerAgent
# On-time manufacturing of implants for additive, silicon nitride, means that implants can be produced immediately
# reducing risk of stockouts
# TODO add an adoption feature to optimize production (speed, cost, quality,
#  buy more machines if see consistently low inventory = increase production etc.) based on # of orders filled
class ManufacturerAgent(Agent):
    def __init__(self, unique_id, model, type_of_manufacturer, cost_modifier):
        super().__init__(unique_id, model)
        self.type_of_manufacturer = type_of_manufacturer  # Either additive or subtractive
        self.initial_inventory = 200 # Define initial inventory
        self.inventory = self.initial_inventory  # Start with the initial inventory
        self.base_production_cost = 10  # Example base cost
        self.cost_modifier = cost_modifier  # How much cheaper should subtractive be, set in main
        self.adjusted_production_cost = self.base_production_cost * self.cost_modifier
        self.production_capacity = 100  # Example capacity to replenish inventory
        self.sales_revenue = 0
        self.profit_margin = 0.3  # Example profit margin
        #self.production_strategy = lambda step: 1 if step % 2 == 0 else 0.5  # Example strategy
        self.pending_implants = {}  # Record the number of implants to produce in the future for subtractive

    def produce_implants(self):
        if self.inventory < self.initial_inventory:
            production_amount = self.initial_inventory - self.inventory
            if self.type_of_manufacturer == 'subtractive':
                self.pending_implants[self.model.schedule.steps + 1] = production_amount
            else:
                self.inventory += production_amount
            return production_amount

    def sell_implant(self, quantity):
        if self.inventory >= quantity:
            self.inventory -= quantity
            revenue = quantity * (self.adjusted_production_cost / self.profit_margin)
            self.sales_revenue += revenue

    def calculate_costs(self):
        return self.inventory * self.adjusted_production_cost

    def get_costs(self):
        return self.calculate_costs()

    def calculate_profit(self):
        return self.sales_revenue * self.profit_margin

    def get_profit(self):
        return self.calculate_profit()

    def step(self):
        self.produce_implants()
        if self.type_of_manufacturer == 'subtractive' and self.model.schedule.steps in self.pending_implants:
            self.inventory += self.pending_implants[self.model.schedule.steps]
            del self.pending_implants[self.model.schedule.steps]
