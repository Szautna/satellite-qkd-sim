from qiskit import QuantumCircuit
from secrets import choice
from qiskit_aer import AerSimulator
from random import SystemRandom
simulator = AerSimulator()

def qkd_bb84_init(N, eve):
    alice_bits = [choice([0, 1]) for _ in range(N)]
    alice_bases = [choice(["X", "Z"]) for _ in range(N)]
    bob_bases = [choice(["X", "Z"]) for _ in range(N)]

    if eve:
        eve_bases = [choice(["X", "Z"]) for _ in range(N)]
    else:
        eve_bases = None

    return alice_bits, alice_bases, bob_bases, eve_bases

    

def qkd_bb84_measure(alice_bits,alice_bases,bob_bases,eve_bases=None):
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

    return bob_bits, eve_bits

def qkd_bb84_error(alice_bits, alice_bases, bob_bits, bob_bases):
    # Sifting
    sifted_alice_bits = []
    sifted_bob_bits = []

    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice_bits.append(alice_bits[i])
            sifted_bob_bits.append(bob_bits[i])

    #calculate estimated QBER
    rng = SystemRandom()

    sample_size = int(len(sifted_alice_bits) * 0.2)

    sample_indices = rng.sample(
        range(len(sifted_alice_bits)),
        sample_size
    )

    sample_errors = sum(
        1 for i in sample_indices
        if sifted_alice_bits[i] != sifted_bob_bits[i]
    )

    estimated_qber = (
        sample_errors / sample_size
        if sample_size > 0 else 0
    )

    # Discard publicly revealed sample
    sample_set = set(sample_indices)

    alice_key = [
        bit for i, bit in enumerate(sifted_alice_bits)
        if i not in sample_set
    ]

    bob_key = [
        bit for i, bit in enumerate(sifted_bob_bits)
        if i not in sample_set
    ]

    # Calculate TRUE QBER
    errors = sum(
        1 for a, b in zip(sifted_alice_bits, sifted_bob_bits) if a != b
    )
    qber = errors / len(sifted_alice_bits) if sifted_alice_bits else 0




    return {
        "sample qber": estimated_qber,
        "sifted_alice_bits": sifted_alice_bits,
        "sifted_bob_bits": sifted_bob_bits,
        "true qber": qber,
        "alice_key": alice_key,     
        "bob_key": bob_key
    }


def run_sim(N, eve=False):
     alice_bits, alice_bases, bob_bases, eve_bases = qkd_bb84_init(N, eve)
     bob_bits, eve_bits = qkd_bb84_measure(alice_bits, alice_bases, bob_bases, eve_bases)       
     return qkd_bb84_error(alice_bits, alice_bases, bob_bits, bob_bases)



run_sim(1000, False)
run_sim(1000, True)