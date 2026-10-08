from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "Fast Charging Session"
    / "BEV1_2024-08-10_fast_1.csv"
)


# --------------------------------------------------
# Load session
# --------------------------------------------------

def load_session(file_path: Path) -> pd.DataFrame:
    """Load a fast-charging session CSV."""
    df = pd.read_csv(file_path)

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

    return df

def validate_timestamps(df,results):
    """Validate timestamp completeness and sampling continuity."""

    print("\nTimestamp Integrity")
    print("-" * 40)

    timestamps = df["Timestamp"]

    # Missing timestamps
    missing = timestamps.isna().sum()
    print(f"Missing timestamps:       {missing}")

    if missing > 0:
        record_result(
            results,
            "No missing timestamps",
            "FAIL",
            f"{missing} missing timestamps"
        )
    else:
        record_result(
            results,
            "No missing timestamps",
            "PASS",
            f"{missing} missing timestamps"
        )

    # Work only with valid timestamps
    valid_timestamps = timestamps.dropna()

    # Chronological ordering
    non_monotonic = (valid_timestamps.diff().dropna() <= pd.Timedelta(0)).sum()
    print(f"Non-monotonic records:    {non_monotonic}")

    if non_monotonic > 0:
        print("  [FAIL] Timestamp ordering problem detected")
    else:
        print("  [PASS] Timestamps are strictly increasing")

    # Duplicate timestamps
    duplicates = valid_timestamps.duplicated().sum()
    print(f"Duplicate timestamps:     {duplicates}")

    if duplicates > 0:
        print("  [FAIL] Duplicate timestamps detected")
    else:
        print("  [PASS] No duplicate timestamps")

    # Sampling intervals
    intervals = valid_timestamps.diff().dropna()

    if len(intervals) > 0:
        most_common = intervals.mode().iloc[0]
        max_interval = intervals.max()

        print(f"Expected interval:        1 second")
        print(f"Most common interval:     {most_common}")
        print(f"Maximum observed gap:     {max_interval}")

        unexpected = (intervals != pd.Timedelta(seconds=1)).sum()

        print(f"Unexpected intervals:     {unexpected}")

        if unexpected == 0:
            print("  [PASS] Consistent 1-second sampling")
        else:
            print("  [WARN] Sampling gaps detected")
    else:
        print("  [WARN] Not enough timestamps to calculate intervals")

def validate_signals(df, results):
    """Validate core battery and thermal signals."""

    print("\nSignal-Level Validation")
    print("-" * 40)

    # SOC physical range
    soc_invalid = ((df["SOCave292"] < 0) | (df["SOCave292"] > 100)).sum()

    print(f"SOC outside 0-100%:      {soc_invalid}")

    if soc_invalid == 0:
        record_result(
                    results,
                    "SOC within physical range",
                    "PASS",
                    f"{soc_invalid} invalid values"
                )
    else:
        record_result(
                    results,
                    "SOC within physical range",
                    "FAIL",
                    f"{soc_invalid} invalid values"
                )

    # Battery voltage against DBC range
    voltage_invalid = (
        (df["BattVoltage132"] < 0) |
        (df["BattVoltage132"] > 655.35)
    ).sum()

    print(f"Battery voltage outside DBC range: {voltage_invalid}")

    if voltage_invalid == 0:
        record_result(
                    results,
                    "Battery voltage within DBC range",
                    "PASS",
                    f"{voltage_invalid} invalid values"
                )
    else:
        record_result(
                    results,
                    "Battery voltage within DBC range",
                    "FAIL",
                    f"{voltage_invalid} invalid values"
                )

    # Battery current against DBC range
    current_invalid = (
        (df["RawBattCurrent132"] < -1138.35) |
        (df["RawBattCurrent132"] > 2138.4)
    ).sum()

    print(f"Battery current outside DBC range: {current_invalid}")

    if current_invalid == 0:
        record_result(
                    results,
                    "Battery current within DBC range",
                    "PASS",
                    f"{current_invalid} invalid values"
                )
    else:
        record_result(
                    results,
                    "Battery current within DBC range",
                    "FAIL",
                    f"{current_invalid} invalid values"
                )

    # Temperature relationship
    temperature_invalid = (
        df["BMSminPackTemperature"] >
        df["BMSmaxPackTemperature"]
    ).sum()

    print(f"Temperature min > max:   {temperature_invalid}")

    if temperature_invalid == 0:
        record_result(
                    results,
                    "Temperature relationship valid",
                    "PASS",
                    f"{temperature_invalid} invalid records"
                )
    else:
        record_result(
                    results,
                    "Temperature relationship valid",
                    "FAIL",
                    f"{temperature_invalid} invalid records"
                )

def validate_charging_electrical(df, results):
    """Validate fast-charging electrical relationships and limits."""

    print("\nFast-Charging Electrical Validation")
    print("-" * 40)

    # Calculate DC charging power
    calculated_power = (
        df["FC_dcVoltage"] * df["FC_dcCurrent"] / 1000
    )

    # Check calculated power for invalid values
    invalid_power = (
        calculated_power.isna() |
        (calculated_power < 0)
    ).sum()

    print(f"Invalid calculated DC power: {invalid_power}")

    if invalid_power == 0:
        record_result(
        results,
        "Calculated DC power is valid",
        "PASS",
        f"{invalid_power} invalid values"
    )
    else:
        record_result(
        results,
        "Calculated DC power is valid",
        "FAIL",
        f"{invalid_power} invalid values"
    )

    # Check charging power against fast-charge power limit
    power_limit_violations = (
        calculated_power > df["FCPowerLimit244"]
    ).sum()

    print(f"Power limit violations:       {power_limit_violations}")

    if power_limit_violations == 0:
        record_result(
            results,
            "Charging power within power limit",
            "PASS",
            f"{power_limit_violations} violations"
        )
    else:
        record_result(
            results,
            "Charging power within power limit",
            "FAIL",
            f"{power_limit_violations} violations"
        )

    # Check charging current against current limit
    current_limit_violations = (
        df["FC_dcCurrent"] > df["FCCurrentLimit244"]
    ).sum()

    print(f"Current limit violations:     {current_limit_violations}")

    if current_limit_violations == 0:
        record_result(
            results,
            "Charging current within current limit",
            "PASS",
            f"{current_limit_violations} violations"
        )
    else:
        record_result(
            results,
            "Charging current within current limit",
            "FAIL",
            f"{current_limit_violations} violations"
        )

    # Check charging voltage against configured voltage window
    voltage_window_violations = (
        (df["FC_dcVoltage"] < df["FCMinVlimit244"]) |
        (df["FC_dcVoltage"] > df["FCMaxVlimit244"])
    ).sum()

    print(f"Voltage window violations:     {voltage_window_violations}")

    if voltage_window_violations == 0:
        record_result(
            results,
            "Charging voltage within configured limits",
            "PASS",
            f"{voltage_window_violations} violations"
        )
    else:
        record_result(
            results,
            "Charging voltage within configured limits",
            "WARN",
            f"{voltage_window_violations} violations"
        )


def validate_charging_behavior(df, results):
    """Validate charging-session behavior and summarize key trends."""

    print("\nCharging-Behavior Validation")
    print("-" * 40)

    # SOC progression
    initial_soc = df["SOCave292"].iloc[0]
    final_soc = df["SOCave292"].iloc[-1]

    soc_decreases = (
        df["SOCave292"].diff().dropna() < 0
    ).sum()

    print(f"Initial SOC:                {initial_soc:.3f}%")
    print(f"Final SOC:                  {final_soc:.3f}%")
    print(f"SOC decreases observed:     {soc_decreases}")

    if final_soc >= initial_soc:
        record_result(
            results,
            "SOC increased during charging",
            "PASS",
            f"{initial_soc:.3f}% -> {final_soc:.3f}%"
        )
    else:
        record_result(
            results,
            "SOC increased during charging",
            "FAIL",
            f"{initial_soc:.3f}% -> {final_soc:.3f}%"
        )

    # Peak charging power
    calculated_power = (
        df["FC_dcVoltage"] * df["FC_dcCurrent"] / 1000
    )

    peak_power_index = calculated_power.idxmax()
    peak_power = calculated_power.loc[peak_power_index]

    peak_power_timestamp = df.loc[
        peak_power_index, "Timestamp"
    ]

    peak_power_soc = df.loc[
        peak_power_index, "SOCave292"
    ]

    peak_current = df.loc[
        peak_power_index, "FC_dcCurrent"
    ]

    print(f"\nPeak charging power:        {peak_power:.3f} kW")
    print(f"Peak power timestamp:       {peak_power_timestamp}")
    print(f"SOC at peak power:          {peak_power_soc:.3f}%")
    print(f"Current at peak power:      {peak_current:.3f} A")

    # Battery temperature progression
    initial_min_temp = df["BMSminPackTemperature"].iloc[0]
    final_min_temp = df["BMSminPackTemperature"].iloc[-1]

    initial_max_temp = df["BMSmaxPackTemperature"].iloc[0]
    final_max_temp = df["BMSmaxPackTemperature"].iloc[-1]

    print("\nBattery Temperature")
    print(
        f"Minimum temperature:        "
        f"{initial_min_temp:.2f} -> {final_min_temp:.2f} °C"
    )
    print(
        f"Maximum temperature:        "
        f"{initial_max_temp:.2f} -> {final_max_temp:.2f} °C"
    )

    min_temp_change = final_min_temp - initial_min_temp
    max_temp_change = final_max_temp - initial_max_temp

    print(f"Minimum temperature change: {min_temp_change:+.2f} °C")
    print(f"Maximum temperature change: {max_temp_change:+.2f} °C")

def validate_energy(df, results):
    """Calculate charging energy from DC power and report SOC change."""

    print("\nEnergy Validation")
    print("-" * 40)

    # Calculate DC charging power
    calculated_power = (
        df["FC_dcVoltage"] * df["FC_dcCurrent"] / 1000
    )

    # Calculate time intervals in hours
    timestamps = df["Timestamp"]
    intervals = timestamps.diff().dt.total_seconds() / 3600

    # First row has no preceding interval
    intervals = intervals.fillna(0)

    # Integrate charging power over time
    calculated_energy = (
        calculated_power * intervals
    ).sum()

    print(f"Calculated DC charging energy: {calculated_energy:.3f} kWh")

    if calculated_energy >= 0:
        record_result(
            results,
            "Calculated charging energy is non-negative",
            "PASS",
            f"{calculated_energy:.3f} kWh"
        )
    else:
        record_result(
            results,
            "Calculated charging energy is non-negative",
            "FAIL",
            f"{calculated_energy:.3f} kWh"
        )

    # SOC change
    initial_soc = df["SOCave292"].iloc[0]
    final_soc = df["SOCave292"].iloc[-1]
    soc_change = final_soc - initial_soc

    print(f"Initial SOC:                   {initial_soc:.3f}%")
    print(f"Final SOC:                     {final_soc:.3f}%")
    print(f"SOC change:                    {soc_change:+.3f} percentage points")

    if soc_change >= 0:
        print("  [PASS] SOC increased during the recorded session")
    else:
        print("  [WARN] SOC decreased during the recorded session")

def record_result(results, check, status, details=""):
    """Store a structured validation result and print it."""

    result = {
        "check": check,
        "status": status,
        "details": details,
    }

    results.append(result)

    print(f"  [{status}] {check}")

def print_summary(results):
    """Print a summary of all validation results."""

    print("\nQA VALIDATION SUMMARY")
    print("=" * 40)

    pass_count = sum(
        result["status"] == "PASS"
        for result in results
    )

    warn_count = sum(
        result["status"] == "WARN"
        for result in results
    )

    fail_count = sum(
        result["status"] == "FAIL"
        for result in results
    )

    print(f"PASS: {pass_count}")
    print(f"WARN: {warn_count}")
    print(f"FAIL: {fail_count}")

    if fail_count > 0:
        overall_status = "FAIL"
    elif warn_count > 0:
        overall_status = "PASS WITH WARNINGS"
    else:
        overall_status = "PASS"

    print(f"\nOverall Status: {overall_status}")
# --------------------------------------------------
# Inspect session
# --------------------------------------------------

def inspect_session(df: pd.DataFrame) -> None:
    """Print a basic summary of the charging session."""

    print("=" * 60)
    print("EV FAST-CHARGING SESSION INSPECTION")
    print("=" * 60)

    print(f"\nRows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nTimestamp")
    print("-" * 40)
    print(f"Start: {df['Timestamp'].min()}")
    print(f"End:   {df['Timestamp'].max()}")

    duration = df["Timestamp"].max() - df["Timestamp"].min()
    print(f"Duration: {duration}")

    # Timestamp quality
    timestamp_diff = df["Timestamp"].diff().dropna()

    print("\nSampling")
    print("-" * 40)
    print(f"Most common interval: {timestamp_diff.mode().iloc[0]}")
    print(f"Unique intervals:     {timestamp_diff.nunique()}")

    duplicate_timestamps = df["Timestamp"].duplicated().sum()
    print(f"Duplicate timestamps: {duplicate_timestamps}")

    # Missing data
    print("\nMissing Values")
    print("-" * 40)

    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    if missing.empty:
        print("No missing values found.")
    else:
        for column, count in missing.items():
            percentage = count / len(df) * 100
            print(f"{column}: {count:,} ({percentage:.2f}%)")

    # Core charging signals
    signals = [
        "SOCave292",
        "BattVoltage132",
        "RawBattCurrent132",
        "BMSminPackTemperature",
        "BMSmaxPackTemperature",
        "FC_dcCurrent",
        "FC_dcVoltage",
        "FCMaxPowerLimit541",
        "FCMaxCurrentLimit541",
        "FCPowerLimit244",
        "FCCurrentLimit244",
        "FCMinVlimit244",
        "FCMaxVlimit244",
    ]

    print("\nCore Signal Ranges")
    print("-" * 40)

    for signal in signals:
        if signal not in df.columns:
            print(f"{signal}: NOT FOUND")
            continue

        values = df[signal].dropna()

        if values.empty:
            print(f"{signal}: no valid values")
            continue

        print(
            f"{signal}: "
            f"min={values.min():.3f}, "
            f"max={values.max():.3f}"
        )

    # Calculated DC charging power
    if "FC_dcVoltage" in df.columns and "FC_dcCurrent" in df.columns:
        power_kw = (
            df["FC_dcVoltage"] * df["FC_dcCurrent"] / 1000
        )

        print("\nCalculated DC Charging Power")
        print("-" * 40)
        print(f"Minimum: {power_kw.min():.3f} kW")
        print(f"Maximum: {power_kw.max():.3f} kW")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main() -> None:
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(
            f"Sample file not found:\n{SAMPLE_FILE}"
        )

    df = load_session(SAMPLE_FILE)
    results = []

    inspect_session(df)
    validate_timestamps(df, results)
    validate_signals(df, results)
    validate_charging_electrical(df, results)
    validate_charging_behavior(df, results)
    validate_energy(df, results)

    print_summary(results)

if __name__ == "__main__":
    main()