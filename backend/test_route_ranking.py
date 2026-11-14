
from routing.ranking import rank_routes


def make_route(route_id, risks, hours):

    # Five checkpoints, spaced 25 miles apart.
    mile_markers = [0, 25, 50, 75, 100]

    checkpoints = []

    for mile, risk in zip(mile_markers, risks):
        checkpoints.append({
            "mile": mile,
            "risk": {
                "overall_risk": risk
            }
        })

    return {
        "route_id": route_id,
        "distance_miles": 100,
        "duration_seconds": hours * 3600,
        "checkpoints": checkpoints
    }


def test_route_ranking():

    # Route 1: Fastest, but has 50 Severe miles.
    route_1 = make_route(
        1,
        ["Low", "Low", "Severe", "Low", "Low"],
        4
    )

    # Route 2: No Severe miles, but 50 High miles.
    route_2 = make_route(
        2,
        ["Low", "Low", "High", "Low", "Low"],
        5
    )

    # Route 3: No Severe or High miles.
    route_3 = make_route(
        3,
        ["Low", "Moderate", "Moderate", "Low", "Low"],
        6
    )

    results = rank_routes([route_1, route_2, route_3])

    print("\nROUTE RANKING RESULTS")
    print("-" * 45)

    for index, route in enumerate(results["ranked_routes"], start=1):

        print(
            f"Rank {index}: Route {route['route_id']} | "
            f"Severe: {route['risk_miles']['Severe']} mi | "
            f"High: {route['risk_miles']['High']} mi | "
            f"Average risk: {route['average_risk']:.2f}"
        )

    recommended = results["recommended_route"]

    print(f"\nRecommended route: {recommended['route_id']}")

    # Verify the expected order.
    ranked_ids = [
        route["route_id"]
        for route in results["ranked_routes"]
    ]

    assert ranked_ids == [3, 2, 1]
    assert recommended["route_id"] == 3

    print("SUCCESS: Route ranking is correct!")


if __name__ == "__main__":
    test_route_ranking()
