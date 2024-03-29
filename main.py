from implant_market_model import ImplantMarketModel
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def main():
    # Model parameters
    num_providers = 3
    initial_num_patients = 1000
    patient_incidence = 48 #(54/1000000) * initial_num_patients # Est. 17,500 new spinal cord injury cases each year
    time_period = 365 # 1 step = 1 day, so 10 years 3650
    additive_adoption_preference = 0.7 # Used in provider agent for  Example: 70% preference for additive manufacturing

    # Collect cumulative data
    cumulative_data = []

    # Create and run the model
    model = ImplantMarketModel(num_providers, initial_num_patients, patient_incidence, additive_adoption_preference)
    for i in range(time_period):  # Run for x steps
        model.step()  # Run the steps outlined in implantmarketmodel

    #     outcomes = model.summarize_manufacturer_outcomes()  #
    #     # Accumulate outcomes
    #     if i > 0:
    #         prev_outcomes = cumulative_data[-1]
    #         for manu_id in outcomes:
    #             for state in outcomes[manu_id]:
    #                 outcomes[manu_id][state] += prev_outcomes[manu_id][state]
    #     cumulative_data.append(outcomes)
    #
    # # Convert data to DataFrame
    # rows = []
    # for step, step_data in enumerate(cumulative_data):
    #     for manu_id, manu_data in step_data.items():
    #         for state, count in manu_data.items():
    #             rows.append({"Step": step, "Manufacturer": manu_id, "Health State": state, "Count": count})
    #
    # df = pd.DataFrame(rows)
    # # Assuming df is the DataFrame created previously
    # # Organize the data for the bar chart
    # pivot_df = df.pivot_table(index='Step', columns=['Manufacturer', 'Health State'], values='Count', fill_value=0)
    # n_steps = len(pivot_df)
    # fig, ax = plt.subplots()
    # bar_container = ax.bar(range(len(pivot_df.columns)), [0] * len(pivot_df.columns), align='edge')
    #
    # # Set the axis labels and titles as needed
    # ax.set_xticks(range(len(pivot_df.columns)))
    # ax.set_xticklabels(['{} - {}'.format(manu, state) for manu, state in pivot_df.columns], rotation=45, ha='right')
    # ax.set_ylabel('Count')
    # ax.set_xlabel('Manufacturer - Health State')
    # ax.set_title('Cumulative Health State Totals by Manufacturer Over Time')
    #
    # def animate(step):
    #     # Update the heights of the bars
    #     bar_heights = pivot_df.iloc[step].values
    #     for bar, height in zip(bar_container.patches, bar_heights):
    #         bar.set_height(height)
    #     ax.set_ylim(0, max(bar_heights) * 1.1)  # Adjust y-axis limit for visibility
    #
    # ani = animation.FuncAnimation(fig, animate, frames=n_steps, repeat=False, interval=100)
    #
    # plt.tight_layout()
    # plt.show()
if __name__ == "__main__":
    main()