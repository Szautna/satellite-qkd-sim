import random

from Orbit import find_next_pass
from Channel import optical_channel
from BB84_sim import (
    qkd_bb84_init,
    qkd_bb84_measure,
    qkd_bb84_error
)

PHOTONS_PER_DATAPOINT = 10000


def main():

    orbital_pass = find_next_pass()

    channel_stats = []

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
            PHOTONS_PER_DATAPOINT,
            eve=True
        )

        surviving_indices = []

        for i in range(PHOTONS_PER_DATAPOINT):
            if random.random() < probability:
                surviving_indices.append(i)

        # Track photons dropped at this orbital datapoint
        channel_stats.append(
            PHOTONS_PER_DATAPOINT - len(surviving_indices)
        )

        alice_bits = [alice_bits[i] for i in surviving_indices]
        alice_bases = [alice_bases[i] for i in surviving_indices]
        bob_bases = [bob_bases[i] for i in surviving_indices]

        if eve_bases is not None:
            eve_bases = [eve_bases[i] for i in surviving_indices]

        bob_bits, eve_bits = qkd_bb84_measure(
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
        pass_alice_bits,
        pass_alice_bases,
        pass_bob_bits,
        pass_bob_bases
    )

    avg_dropped = sum(channel_stats) / len(channel_stats)

    avg_drop_percentage = (
        avg_dropped / PHOTONS_PER_DATAPOINT
    ) * 100

    print(results)
    print("Average photons dropped per datapoint:", avg_dropped)
    print("Average photon loss:", avg_drop_percentage, "%")


if __name__ == "__main__":
    main()