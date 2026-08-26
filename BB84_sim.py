from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

simulator = AerSimulator()


def qkd_bb84_init(N, eve):

    alice_bits = np.random.randint(0, 2, N)

    alice_bases = np.random.choice(["X", "Z"], N)

    bob_bases = np.random.choice(["X", "Z"], N)

    if eve:
        eve_bases = np.random.choice(["X", "Z"], N)
    else:
        eve_bases = None

    return alice_bits, alice_bases, bob_bases, eve_bases
    

def qkd_bb84_measure_aer(alice_bits,alice_bases,bob_bases,eve_bases=None):
    bob_bits = []
    eve_bits = []

    for i in range(len(alice_bits)):
        qc = QuantumCircuit(1, 1)

        # Alice prepares
        if alice_bits[i] == 1:
            qc.x(0)

        if alice_bases[i] == "X":
            qc.h(0)

        # Eve intercepts
        if eve_bases is not None:
            if eve_bases[i] == "X":
                qc.h(0)

            qc.measure(0, 0)

            result = simulator.run(
                qc,
                shots=1,
                memory=True
            ).result()

            eve_result = int(result.get_memory()[0])
            eve_bits.append(eve_result)

            # Eve resends
            qc = QuantumCircuit(1, 1)

            if eve_result == 1:
                qc.x(0)

            if eve_bases[i] == "X":
                qc.h(0)

        # Bob measures
        if bob_bases[i] == "X":
            qc.h(0)

        qc.measure(0, 0)

        result = simulator.run(
            qc,
            shots=1,
            memory=True
        ).result()

        bob_bits.append(
            int(result.get_memory()[0])
        )

    return np.array(bob_bits), np.array(eve_bits)



def qkd_bb84_measure_fast(
    alice_bits,
    alice_bases,
    bob_bases,
    eve_bases=None
):

    N = len(alice_bits)

    if eve_bases is None:

        same_basis = bob_bases == alice_bases

        random_bits = np.random.randint(0, 2, N)

        bob_bits = np.where(
            same_basis,
            alice_bits,
            random_bits
        )

        return bob_bits, np.array([])

    # Eve measures Alice
    eve_same_basis = eve_bases == alice_bases

    eve_random_bits = np.random.randint(0, 2, N)

    eve_bits = np.where(
        eve_same_basis,
        alice_bits,
        eve_random_bits
    )

    # Bob measures Eve's resent state
    bob_same_basis = bob_bases == eve_bases

    bob_random_bits = np.random.randint(0, 2, N)

    bob_bits = np.where(
        bob_same_basis,
        eve_bits,
        bob_random_bits
    )

    return bob_bits, eve_bits

def qkd_bb84_error(alice_bits, alice_bases, bob_bits, bob_bases):
    # Sifting
    same_basis = alice_bases == bob_bases

    sifted_alice_bits = alice_bits[same_basis]
    sifted_bob_bits = bob_bits[same_basis]

    #calculate estimated QBER
    sample_size = int(len(sifted_alice_bits) * 0.2)

    if sample_size > 0:

        sample_indices = np.random.choice(
            len(sifted_alice_bits),
            sample_size,
            replace=False
        )

        estimated_qber = np.mean(
            sifted_alice_bits[sample_indices]
            != sifted_bob_bits[sample_indices]
        )

    else:
        sample_indices = np.array([], dtype=int)
        estimated_qber = 0


    # Discard publicly revealed sample

    keep = np.ones(len(sifted_alice_bits), dtype=bool)
    keep[sample_indices] = False

    alice_key = sifted_alice_bits[keep]
    bob_key = sifted_bob_bits[keep]

    # Calculate TRUE QBER
    if len(sifted_alice_bits) > 0:
        qber = np.mean(
            sifted_alice_bits != sifted_bob_bits
        )
    else:
        qber = 0




    return {
        "sample_qber": estimated_qber,
        "sifted_alice_bits": sifted_alice_bits,
        "sifted_bob_bits": sifted_bob_bits,
        "true_qber": qber,
        "alice_key": alice_key,
        "bob_key": bob_key
    }


def run_sim(N, eve=False):
    alice_bits, alice_bases, bob_bases, eve_bases = qkd_bb84_init(N, eve)
    bob_bits, _ = qkd_bb84_measure_aer(alice_bits, alice_bases, bob_bases, eve_bases)
    return qkd_bb84_error(alice_bits, alice_bases, bob_bits, bob_bases)


