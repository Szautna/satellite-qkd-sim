import unittest

import numpy as np

from BB84_sim import (
    qkd_bb84_init,
    qkd_bb84_error,
    qkd_bb84_measure_fast,
    qkd_bb84_measure_aer,
)
from Channel import optical_channel
from Main import run_simulation


class BB84SimulationTests(unittest.TestCase):
    def test_matching_bases_without_eve_have_zero_qber(self):
        alice_bits = np.array([0, 1, 0, 1])
        bases = np.array(["Z", "X", "Z", "X"])

        bob_bits, eve_bits = qkd_bb84_measure_fast(
            alice_bits,
            bases,
            bases,
        )
        result = qkd_bb84_error(alice_bits, bases, bob_bits, bases)

        np.testing.assert_array_equal(bob_bits, alice_bits)
        self.assertEqual(len(eve_bits), 0)
        self.assertEqual(result["true_qber"], 0)
        self.assertEqual(result["sample_qber"], 0)

    def test_intercept_resend_qber_is_close_to_theoretical_value(self):
        np.random.seed(42)
        alice_bits = np.random.randint(0, 2, 100_000)
        alice_bases = np.random.choice(["X", "Z"], 100_000)
        bob_bases = np.random.choice(["X", "Z"], 100_000)
        eve_bases = np.random.choice(["X", "Z"], 100_000)

        bob_bits, _ = qkd_bb84_measure_fast(
            alice_bits,
            alice_bases,
            bob_bases,
            eve_bases,
        )
        result = qkd_bb84_error(
            alice_bits,
            alice_bases,
            bob_bits,
            bob_bases,
        )

        self.assertAlmostEqual(result["true_qber"], 0.25, delta=0.02)

    def test_empty_qber_input_returns_zero(self):
        empty_bits = np.array([], dtype=int)
        empty_bases = np.array([], dtype="U1")

        result = qkd_bb84_error(
            empty_bits,
            empty_bases,
            empty_bits,
            empty_bases,
        )

        self.assertEqual(result["true_qber"], 0)
        self.assertEqual(result["sample_qber"], 0)

    def test_channel_probability_is_bounded(self):
        self.assertEqual(optical_channel(9.9, 500), 0)
        self.assertGreaterEqual(optical_channel(45, 500), 0)
        self.assertLessEqual(optical_channel(45, 500), 1)

    def test_main_simulation_returns_expected_result_fields(self):
        orbital_pass = {
            "data": [
                {"elevation_deg": 10, "range_km": 1_000, "seconds": 0},
                {"elevation_deg": 10, "range_km": 1_000, "seconds": 1},
            ]
        }

        result = run_simulation(orbital_pass, photons_per_datapoint=10)

        self.assertEqual(len(result["received_photons"]), 2)
        self.assertIn("sample_qber", result)
        self.assertIn("actual_qber", result)

    def test_aer_matches_fast_qber(self):

        N = 500
        N_TRIALS = 20

        aer_qbers = []
        fast_qbers = []

        for _ in range(N_TRIALS):

            alice_bits, alice_bases, bob_bases, eve_bases = qkd_bb84_init(
                N,
                True
            )

            bob_bits_aer, _ = qkd_bb84_measure_aer(
                alice_bits,
                alice_bases,
                bob_bases,
                eve_bases
            )

            aer_results = qkd_bb84_error(
                alice_bits,
                alice_bases,
                bob_bits_aer,
                bob_bases
            )

            bob_bits_fast, _ = qkd_bb84_measure_fast(
                alice_bits,
                alice_bases,
                bob_bases,
                eve_bases
            )

            fast_results = qkd_bb84_error(
                alice_bits,
                alice_bases,
                bob_bits_fast,
                bob_bases
            )

            aer_qbers.append(aer_results["true qber"])
            fast_qbers.append(fast_results["true qber"])

        self.assertAlmostEqual(
                np.mean(aer_qbers),
                np.mean(fast_qbers),
                delta=0.05
                )

        self.assertAlmostEqual(
                np.mean(aer_qbers),
                0.25,
                delta=0.05
            )

        self.assertAlmostEqual(
                np.mean(fast_qbers),
                0.25,
                delta=0.05
)


if __name__ == "__main__":
    unittest.main()
