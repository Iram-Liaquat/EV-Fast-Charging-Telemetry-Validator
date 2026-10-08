from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "Fast Charging Session"
    / "BEV1_2024-08-10_fast_1.csv"
)

REPORTS_DIR = PROJECT_ROOT / "reports"


# --------------------------------------------------
# Load session
# --------------------------------------------------

def load_session(file_path: Path) -> pd.DataFrame:
    """Load and prepare a cleaned charging session."""

    df = pd.read_csv(file_path)

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

    return df


# --------------------------------------------------
# Plot charging power
# --------------------------------------------------

def plot_charging_power(df: pd.DataFrame) -> None:
    """Plot calculated DC charging power over time."""

    calculated_power = (
        df["FC_dcVoltage"] * df["FC_dcCurrent"] / 1000
    )

    elapsed_minutes = (
        df["Timestamp"] - df["Timestamp"].iloc[0]
    ).dt.total_seconds() / 60

    peak_index = calculated_power.idxmax()
    peak_power = calculated_power.loc[peak_index]
    peak_time = elapsed_minutes.loc[peak_index]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        elapsed_minutes,
        calculated_power,
        linewidth=1.5,
    )

    ax.scatter(
        peak_time,
        peak_power,
        zorder=3,
    )

    ax.annotate(
        f"Peak: {peak_power:.1f} kW",
        xy=(peak_time, peak_power),
        xytext=(peak_time + 1, peak_power - 10),
        arrowprops=dict(arrowstyle="->"),
    )

    ax.set_xlabel("Elapsed time (minutes)")
    ax.set_ylabel("DC charging power (kW)")
    ax.set_title("Fast-Charging Power Profile")

    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    output_file = REPORTS_DIR / "charging_power_profile.png"

    fig.savefig(output_file, dpi=200, format="png")
    plt.close(fig)

    print(f"\nSaved visualization: {output_file}")
# --------------------------------------------------
# Plot battery temperature
# --------------------------------------------------

def plot_battery_temperature(df: pd.DataFrame) -> None:
    """Plot minimum and maximum battery temperature over time."""

    elapsed_minutes = (
        df["Timestamp"] - df["Timestamp"].iloc[0]
    ).dt.total_seconds() / 60

    min_temperature = df["BMSminPackTemperature"]
    max_temperature = df["BMSmaxPackTemperature"]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        elapsed_minutes,
        min_temperature,
        linewidth=1.5,
        label="Minimum battery temperature",
    )

    ax.plot(
        elapsed_minutes,
        max_temperature,
        linewidth=1.5,
        label="Maximum battery temperature",
    )

    plt.xlabel("Elapsed time (minutes)")
    plt.ylabel("Battery temperature (°C)")
    plt.title("Battery Temperature During Fast Charging")

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    REPORTS_DIR.mkdir(exist_ok=True)

    output_file = REPORTS_DIR / "battery_temperature_profile.png"

    plt.savefig(output_file, dpi=200)
    plt.show()

    print(f"\nSaved visualization: {output_file}")

    # --------------------------------------------------
# Plot state of charge
# --------------------------------------------------

def plot_soc(df: pd.DataFrame) -> None:
    """Plot battery state of charge over time."""

    elapsed_minutes = (
        df["Timestamp"] - df["Timestamp"].iloc[0]
    ).dt.total_seconds() / 60

    soc = df["SOCave292"]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        elapsed_minutes,
        soc,
        linewidth=1.5,
    )

    ax.set_xlabel("Elapsed time (minutes)")
    ax.set_ylabel("State of charge (%)")
    ax.set_title("Battery State of Charge During Fast Charging")

    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    output_file = REPORTS_DIR / "soc_profile.png"

    fig.savefig(output_file, dpi=200, format="png")
    plt.close(fig)

    print(f"\nSaved visualization: {output_file}")
# --------------------------------------------------
# Main
# --------------------------------------------------

def main() -> None:
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(
            f"Sample file not found:\n{SAMPLE_FILE}"
        )

    df = load_session(SAMPLE_FILE)

    plot_charging_power(df)
    plot_battery_temperature(df)
    plot_soc(df)

if __name__ == "__main__":
    main()