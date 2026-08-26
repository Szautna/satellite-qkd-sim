import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from Orbit import find_next_pass
from Channel import optical_channel
from BB84_sim import (
    qkd_bb84_init,
    qkd_bb84_measure_fast,
    qkd_bb84_error,
)

PHOTONS_PER_DATAPOINT = 10000
N_TRIALS = 10000
IMAGE_DIRECTORY = Path(__file__).parent / "images"


def run_simulation(orbital_pass, photons_per_datapoint=PHOTONS_PER_DATAPOINT):
    received_photons = []
    pass_alice_bits = []
    pass_alice_bases = []
    pass_bob_bases = []
    pass_bob_bits = []

    for orbital_param in orbital_pass["data"]:

        probability = optical_channel(
            orbital_param["elevation_deg"],
            orbital_param["range_km"]
        )

        alice_bits, alice_bases, bob_bases, eve_bases = qkd_bb84_init(
            photons_per_datapoint,
            eve=True
        )

        surviving_indices = np.where(
            np.random.random(photons_per_datapoint) < probability
        )[0]

        received_photons.append(len(surviving_indices))

        alice_bits = alice_bits[surviving_indices]

        alice_bases = alice_bases[surviving_indices]

        bob_bases = bob_bases[surviving_indices]

        if eve_bases is not None:
            eve_bases = eve_bases[surviving_indices]

        bob_bits, _ = qkd_bb84_measure_fast(
            alice_bits,
            alice_bases,
            bob_bases,
            eve_bases
        )

        pass_alice_bits.extend(alice_bits)
        pass_alice_bases.extend(alice_bases)
        pass_bob_bases.extend(bob_bases)
        pass_bob_bits.extend(bob_bits)

    results = qkd_bb84_error(
        np.array(pass_alice_bits),
        np.array(pass_alice_bases),
        np.array(pass_bob_bits),
        np.array(pass_bob_bases)
    )


    return {
        "received_photons": received_photons,
        "sample_qber": results["sample_qber"],
        "actual_qber": results["true_qber"],
    }


def save_plots(orbital_pass, simulations):
    received = np.array([sim["received_photons"] for sim in simulations])
    sample_qbers = np.array([sim["sample_qber"] for sim in simulations])
    actual_qbers = np.array([sim["actual_qber"] for sim in simulations])
    mean_received = np.mean(received, axis=0)
    timestamps = [point["seconds"] for point in orbital_pass["data"]]

    IMAGE_DIRECTORY.mkdir(exist_ok=True)

    plt.figure()
    plt.plot(timestamps, mean_received)
    plt.xlabel("Time into satellite pass (s)")
    plt.ylabel(f"Mean received photons per {PHOTONS_PER_DATAPOINT:,} transmitted")
    plt.title("Mean Received Photons During Satellite Pass")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGE_DIRECTORY / "mean_received_photons.png", dpi=300)

    plt.figure()
    plt.hist(sample_qbers, bins=30)
    plt.xlabel("Sampled QBER")
    plt.ylabel("Number of Monte Carlo trials")
    plt.title("Distribution of Sampled QBER")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGE_DIRECTORY / "sampled_qber_distribution.png", dpi=300)

    plt.figure()
    plt.scatter(actual_qbers, sample_qbers, alpha=0.35, s=8)
    lims = [
        min(actual_qbers.min(), sample_qbers.min()),
        max(actual_qbers.max(), sample_qbers.max())
    ]
    plt.plot(lims, lims, "--", label="Perfect agreement (y = x)")
    plt.xlim(lims)
    plt.ylim(lims)
    plt.xlabel("True QBER")
    plt.ylabel("Sampled QBER")
    plt.title("Sampled QBER vs True QBER")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGE_DIRECTORY / "sampled_vs_true_qber.png", dpi=300)

    plt.show()


def main():
    orbital_pass = find_next_pass()
    simulations = []

    for trial in range(N_TRIALS):
        simulations.append(run_simulation(orbital_pass))

        if (trial + 1) % 100 == 0:
            print(f"{trial + 1}/{N_TRIALS}")

    save_plots(orbital_pass, simulations)

    sample_qbers = np.array([sim["sample_qber"] for sim in simulations])
    actual_qbers = np.array([sim["actual_qber"] for sim in simulations])
    received = np.array([sim["received_photons"] for sim in simulations])
    print(f"Mean received photons per datapoint: {received.mean():.2f}")
    print(f"True QBER: {actual_qbers.mean():.3f} +/- {actual_qbers.std():.3f}")
    print(f"Sampled QBER: {sample_qbers.mean():.3f} +/- {sample_qbers.std():.3f}")


if __name__ == "__main__":
    main()