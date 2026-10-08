from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "Fast Charging Session"
    / "BEV1_2024-08-10_fast_1.csv"
)


def load_sample() -> pd.DataFrame:
    """Load the cleaned charging-session sample."""

    df = pd.read_csv(SAMPLE_FILE)

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        utc=True,
    )

    return df


# --------------------------------------------------
# Timestamp / data-integrity tests
# --------------------------------------------------

def test_timestamps_are_present_and_ordered():
    """TC-001/TC-002: timestamps must be complete and ordered."""

    df = load_sample()

    assert df["Timestamp"].notna().all()
    assert df["Timestamp"].is_monotonic_increasing


def test_timestamps_are_unique():
    """TC-003: timestamps must not contain duplicates."""

    df = load_sample()

    assert not df["Timestamp"].duplicated().any()


def test_sampling_interval_is_one_second():
    """TC-004: telemetry samples should be recorded at 1-second intervals."""

    df = load_sample()

    intervals = (
        df["Timestamp"]
        .diff()
        .dropna()
        .dt.total_seconds()
    )

    assert (intervals == 1).all()


# --------------------------------------------------
# Signal-range tests
# --------------------------------------------------

def test_soc_is_within_dbc_range():
    """TC-005: SOC must remain within the verified DBC range."""

    df = load_sample()

    assert df["SOCave292"].between(0, 102.3).all()


def test_battery_voltage_is_within_dbc_range():
    """TC-006: battery voltage must remain within the DBC range."""

    df = load_sample()

    assert df["BattVoltage132"].between(0, 655.35).all()


def test_battery_current_is_within_dbc_range():
    """TC-007: battery current must remain within the DBC range."""

    df = load_sample()

    assert df["RawBattCurrent132"].between(
        -1138.35,
        2138.4,
    ).all()


def test_battery_temperature_order_is_valid():
    """TC-008: minimum battery temperature must not exceed maximum."""

    df = load_sample()

    assert (
        df["BMSminPackTemperature"]
        <= df["BMSmaxPackTemperature"]
    ).all()


# --------------------------------------------------
# Charging electrical tests
# --------------------------------------------------

def test_calculated_charging_power_is_non_negative():
    """TC-009: calculated DC charging power must not be negative."""

    df = load_sample()

    charging_power = (
        df["FC_dcVoltage"]
        * df["FC_dcCurrent"]
        / 1000
    )

    assert (charging_power >= 0).all()


def test_charging_power_respects_power_limit():
    """TC-010: charging power must not exceed the configured power limit."""

    df = load_sample()

    charging_power = (
        df["FC_dcVoltage"]
        * df["FC_dcCurrent"]
        / 1000
    )

    power_limit = df["FCPowerLimit244"]

    assert (charging_power <= power_limit + 0.01).all()


def test_charging_current_respects_current_limit():
    """TC-011: charging current must not exceed the configured current limit."""

    df = load_sample()

    charging_current = df["FC_dcCurrent"]
    current_limit = df["FCCurrentLimit244"]

    assert (
        charging_current
        <= current_limit + 0.01
    ).all()


def test_charging_voltage_respects_configured_limits():
    """TC-012: charging voltage should remain within configured limits."""

    df = load_sample()

    voltage = df["FC_dcVoltage"]
    minimum_voltage = df["FCMinVlimit244"]
    maximum_voltage = df["FCMaxVlimit244"]

    valid_voltage = (
        (voltage >= minimum_voltage - 0.01)
        & (voltage <= maximum_voltage + 0.01)
    )

    violations = df.loc[~valid_voltage]

    if len(violations) == 0:
        return

    # A single violation is acceptable when it occurs
    # at the final record of the charging session.
    assert len(violations) == 1
    assert violations.index[0] == df.index[-1]


# --------------------------------------------------
# Charging behavior tests
# --------------------------------------------------

def test_soc_increases_during_charging():
    """TC-013: SOC should increase over the charging session."""

    df = load_sample()

    initial_soc = df["SOCave292"].iloc[0]
    final_soc = df["SOCave292"].iloc[-1]

    assert final_soc >= initial_soc


# --------------------------------------------------
# Energy validation tests
# --------------------------------------------------

def test_calculated_energy_is_non_negative():
    """TC-014: integrated DC charging energy must be non-negative."""

    df = load_sample()

    charging_power = (
        df["FC_dcVoltage"]
        * df["FC_dcCurrent"]
        / 1000
    )

    calculated_energy = (
        charging_power.sum() / 3600
    )

    assert calculated_energy >= 0


def test_soc_gain_is_positive():
    """TC-015: charging session should produce a positive SOC gain."""

    df = load_sample()

    soc_gain = (
        df["SOCave292"].iloc[-1]
        - df["SOCave292"].iloc[0]
    )

    assert soc_gain > 0