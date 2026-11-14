from routing.risk import RISK_LEVELS

def calculate_risk_miles(checkpoints):
    if len(checkpoints) < 2:
        raise ValueError("At least two checkpoints are required")

    risk_miles = {
        "Low": 0.0,
        "Moderate": 0.0,
        "High": 0.0,
        "Severe": 0.0,
        "No Travel": 0.0
    }

    for i in range(len(checkpoints) - 1):
        start = checkpoints[i]
        end = checkpoints[i + 1]
        segment_miles = end["mile"] - start["mile"]
        if segment_miles <= 0:
            raise ValueError("Checkpoints must be in increasing mile order")
        start_risk = start["risk"]["overall_risk"]
        end_risk = end["risk"]["overall_risk"]
        segment_risk = max(
            start_risk,
            end_risk,
            key=lambda risk: RISK_LEVELS[risk]
        )
        risk_miles[segment_risk] += segment_miles
    total_miles = sum(risk_miles.values())

    weighted_total = sum(
        RISK_LEVELS[risk] * miles 
        for risk, miles in risk_miles.items()
    )
    average_risk = weighted_total / total_miles
    return {
        "risk_miles": risk_miles,
        "average_risk": average_risk,
        "contains_no_travel": risk_miles["No Travel"] > 0
    }

def rank_routes(analyzed_routes):
    scored_routes = []
    for route in analyzed_routes:
        risk_summary = calculate_risk_miles(
            route['checkpoints']
        )
        scored_routes.append({
            "route_id": route['route_id'],
            "distance_miles": route['distance_miles'],
            "duration_seconds": route["duration_seconds"],
            **risk_summary
        })

        safe_candidates = [
            route for route in scored_routes
            if not route["contains_no_travel"]
        ]

        excluded_routes = [
            route for route in scored_routes
            if route["contains_no_travel"]
        ]

        safe_candidates.sort(
            key=lambda route: (
                route["risk_miles"]["Severe"],
                route["risk_miles"]["High"],
                route["average_risk"],
                route["duration_seconds"]
            )
        )

        recommended = (
            safe_candidates[0]
            if safe_candidates
            else None
        )

    return {
        "recommended_route": recommended,
        "ranked_routes": safe_candidates,
        "excluded_routes": excluded_routes
    }
