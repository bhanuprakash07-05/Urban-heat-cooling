def sample_recommendations(city="Delhi"):
    strategies = [
        {"id":"s1","title":"Plant 10km green corridor","priority":"high","cost_estimate":5000000,"expected_impact":"2.5°C","implementation_time":"12 months","location":"South Delhi","type":"green_infrastructure"},
        {"id":"s2","title":"Cool roof program (residential)","priority":"medium","cost_estimate":2000000,"expected_impact":"1.5°C","implementation_time":"6 months","location":"North Delhi","type":"cooling_infrastructure"},
        {"id":"s3","title":"Increase urban water bodies","priority":"low","cost_estimate":8000000,"expected_impact":"3.0°C","implementation_time":"18 months","location":"East Delhi","type":"green_infrastructure"}
    ]
    optimal = max(strategies, key=lambda s: s["cost_estimate"]/ (1 if "impact" not in s else 1))
    return {"strategies": strategies, "optimal_solution": optimal, "recommendations": strategies}
