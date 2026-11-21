from app.modules.m4_fit.windows import fit_window
from app.modules.m5_noise.gate import noise_gate


def fits(curves):
    reports, noise = [], []
    for hz, curve in curves.items():
        gate = noise_gate(curve)
        noise.append(gate)
        reports.append({'band_hz': hz, 't20': fit_window(curve, gate, 25), 't30': fit_window(curve, gate, 35)})
    return {'bands': reports}, {'bands': noise}
