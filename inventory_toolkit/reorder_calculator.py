class ReorderCalculator:


    def __init__(self, lead_time_days=7, safety_buffer_ratio=0.2):
        self.lead_time_days = lead_time_days
        self.safety_buffer_ratio = safety_buffer_ratio

    def average_daily_usage(self, usage_history):
        """
        usage_history: list of numeric quantities used per day,
        e.g. [12, 15, 9, 20, 11]
        """
        if not usage_history:
            return 0
        return sum(usage_history) / len(usage_history)

    def suggested_reorder_quantity(self, usage_history, current_stock):
        """
        Core calculation: covers expected demand during lead time,
        plus a safety buffer, minus what's already in stock.
        """
        avg_daily = self.average_daily_usage(usage_history)
        expected_demand = avg_daily * self.lead_time_days
        buffer_amount = expected_demand * self.safety_buffer_ratio
        required = expected_demand + buffer_amount

        suggestion = max(0, round(required - current_stock))
        return suggestion