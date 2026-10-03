"""Safety boundary verification tests."""

from backend.app.safety.states import SafetyStatus


def test_safety_states_contract():
    """Verify the documented safety states are correctly established."""
    assert SafetyStatus.CLEAR.value == "CLEAR"
    assert SafetyStatus.CONCERNING.value == "CONCERNING"
    assert SafetyStatus.EMERGENCY.value == "EMERGENCY"
    assert set(s.value for s in SafetyStatus) == {"CLEAR", "CONCERNING", "EMERGENCY"}
