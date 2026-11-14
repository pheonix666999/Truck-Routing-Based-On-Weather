
from routing.ranking import calculate_risk_miles


def test_risk_miles():

    # A 100-mile route with checkpoints every 25 miles.
    checkpoints = [
        {"mile": 0, "risk": {"overall_risk": "Low"}},
        {"mile": 25, "risk": {"overall_risk": "Low"}},
        {"mile": 50, "risk": {"overall_risk": "Moderate"}},
        {"mile": 75, "risk": {"overall_risk": "Low"}},
        {"mile": 100, "risk": {"overall_risk": "Low"}}
    ]

    result = calculate_risk_miles(checkpoints)

    print("\nRISK MILEAGE TEST")
    print("-" * 35)

    for risk, miles in result["risk_miles"].items():
        print(f"{risk}: {miles:.2f} miles")

    print(f"Average risk: {result['average_risk']:.2f}")

    # Verify our calculated mile counts.
    assert result["risk_miles"]["Low"] == 50
    assert result["risk_miles"]["Moderate"] == 50
    assert result["risk_miles"]["High"] == 0
    assert result["risk_miles"]["Severe"] == 0

    # (50 * 0 + 50 * 1) / 100 = 0.5
    assert result["average_risk"] == 0.5

    assert result["contains_no_travel"] is False

    print("\nSUCCESS: Risk mileage calculations are correct!")


if __name__ == "__main__":
    test_risk_miles()


