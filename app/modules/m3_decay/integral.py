from dataclasses import dataclass
from math import fsum, log10
from statistics import median

from app.reasons import reason

TAIL_FRACTION = 0.15


@dataclass
class Curve:
    signal: object
    power: tuple[float, ...]
    db: list[float | None]
    tail_from: int
    noise_power: float
    floor_db: float | None
    first_energy: float
    error: dict | None = None


def tail_power(power):
    tail_length = max(10, round(len(power) * TAIL_FRACTION))
    start = max(0, len(power) - tail_length)
    tail = power[start:]
    blocks = [tail[i * len(tail) // 5:(i + 1) * len(tail) // 5] for i in range(5)]
    return start, median(fsum(block) / len(block) for block in blocks if block)


def reverse_energy(power, noise):
    result = [0.0] * len(power)
    total = 0.0
    envelope = 0.0
    for index in range(len(power) - 1, -1, -1):
        total += power[index] - noise
        envelope = max(envelope, total)
        result[index] = envelope
    return result


def integrate(signal):
    power = tuple(value * value for value in signal.pa[signal.peak_index:])
    tail_from, noise = tail_power(power)
    energy = reverse_energy(power, noise)
    initial = energy[0]
    floor = 10 * log10(noise / initial) if noise > 0 and initial > 0 else None
    if not any(power):
        error = reason('NO_ENERGY')
    elif len(power) < max(40, round(signal.rate * 0.04)) or tail_from < 16:
        error = reason('TAIL_TOO_SHORT')
    elif initial <= 0:
        error = reason('DYNAMIC_RANGE')
    else:
        error = None
    db = [10 * log10(value / initial) if value > 0 and initial > 0 else None for value in energy]
    return Curve(signal, power, db, tail_from, noise, floor, initial, error)
