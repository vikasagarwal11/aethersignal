"""
AetherSignal Quantum Computing Modules

Optional advanced quantum computing features for pharmacovigilance analytics.
All modules include automatic classical fallbacks for reliability.
"""

from typing import Optional

# Try to import quantum frameworks (optional)
try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

try:
    import pennylane as qml
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False

try:
    from openqaoa import QAOA
    OPENQAOA_AVAILABLE = True
except ImportError:
    OPENQAOA_AVAILABLE = False

__all__ = [
    "QISKIT_AVAILABLE",
    "PENNYLANE_AVAILABLE",
    "OPENQAOA_AVAILABLE",
]

