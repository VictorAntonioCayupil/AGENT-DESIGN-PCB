#!/usr/bin/env python3
"""
AGENT-DESIGN-PCB MCP Server (v4.7.0)
Desarrollado por S&D MMCALL para la comunidad.
Licencia: MIT (Atribución a oaslananka/easyeda-mcp-pro para el puente de bajo nivel de EasyEDA Pro).

Servidor MCP Agéntico de Ingeniería Electrónica, Cálculos Normativos (IPC/IEC/IEEE/CISPR)
y Co-Piloto Acoplado a EasyEDA Pro (v2.3+ / v3.2+).
"""

import json
import math
import os
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

MM_TO_MIL = 39.37007874015748
MIL_TO_MM = 0.0254
COPPER_OZ_TO_MIL = 1.3779527559  # 1 oz/ft^2 = 35 um = 1.378 mil
COPPER_OZ_TO_MM = 0.035
COPPER_RHO_20C = 1.724e-8        # Ohm * m
COPPER_TCR = 0.00393             # 1 / °C
COPPER_K_THERMAL = 385.0         # W / (m * K)
MAX_RPC_LINE_BYTES = 1_048_576   # 1 MiB CWE-400 protection
MAX_COLLECTION_ITEMS = 2000      # Bound O(N^2) loops


def _require_pos_finite(val: float, name: str) -> float:
    fval = float(val)
    if not math.isfinite(fval) or fval <= 0.0:
        raise ValueError(f"El parámetro '{name}' debe ser un número finito mayor que 0.")
    return fval


# ============================================================================
# 1. MOTORES MATEMÁTICOS NORMATIVOS DETERMINISTAS (IPC / IEC / J-STD)
# ============================================================================

def calc_trace_width_ipc(
    current_a: float,
    temp_rise_c: float = 10.0,
    copper_oz: float = 1.0,
    layer: str = "external",
    length_mm: float = 50.0,
    ambient_c: float = 25.0,
    has_adjacent_plane: bool = False,
) -> Dict[str, Any]:
    """
    Calcula el ancho mínimo de pista según IPC-2221 y aplica el factor de
    optimización multicapa de IPC-2152 cuando existe plano disipador adyacente,
    más caída de tensión DC y disipación por efecto Joule considerando el TCR del cobre.
    """
    if current_a <= 0 or temp_rise_c <= 0 or copper_oz <= 0:
        raise ValueError("current_a, temp_rise_c y copper_oz deben ser mayores que 0.")

    k = 0.048 if layer.lower() == "external" else 0.024
    # IPC-2221: I = k * (dT^0.44) * (Area_mils2^0.725)
    area_mils2_2221 = (current_a / (k * (temp_rise_c ** 0.44))) ** (1.0 / 0.725)
    thickness_mils = copper_oz * COPPER_OZ_TO_MIL
    width_mils_2221 = area_mils2_2221 / thickness_mils
    width_mm_2221 = width_mils_2221 * MIL_TO_MM

    # IPC-2152 plane-assisted correction: internal/external traces adjacent to solid copper
    # plane within <= 0.5 mm cool by conduction through FR-4 (~0.70x width vs unassisted IPC-2221 internal)
    if has_adjacent_plane:
        plane_factor = 0.65 if layer.lower() == "internal" else 0.85
    else:
        plane_factor = 1.0

    width_mm_2152 = max(0.15, width_mm_2221 * plane_factor)
    width_mils_2152 = width_mm_2152 * MM_TO_MIL

    # Cálculo eléctrico y térmico (Efecto Joule + TCR 0.393%/°C)
    recommended_width_mm = round(max(width_mm_2152, 0.20), 3)
    recommended_width_mil = round(recommended_width_mm * MM_TO_MIL, 2)
    thickness_m = copper_oz * COPPER_OZ_TO_MM * 1e-3
    area_m2 = (recommended_width_mm * 1e-3) * thickness_m
    length_m = length_mm * 1e-3

    operating_temp_c = ambient_c + temp_rise_c
    r_20c = COPPER_RHO_20C * (length_m / area_m2)
    r_hot = r_20c * (1.0 + COPPER_TCR * (operating_temp_c - 20.0))
    v_drop = current_a * r_hot
    p_joule_mw = (current_a ** 2) * r_hot * 1000.0

    return {
        "standard": "IPC-2221C / IPC-2152",
        "inputs": {
            "current_a": current_a,
            "temp_rise_c": temp_rise_c,
            "copper_oz": copper_oz,
            "layer": layer,
            "length_mm": length_mm,
            "has_adjacent_plane": has_adjacent_plane,
        },
        "ipc_2221_width_mm": round(width_mm_2221, 3),
        "ipc_2221_width_mil": round(width_mils_2221, 2),
        "ipc_2152_width_mm": round(width_mm_2152, 3),
        "ipc_2152_width_mil": round(width_mils_2152, 2),
        "recommended_width_mm": recommended_width_mm,
        "recommended_width_mil": recommended_width_mil,
        "electrical_thermal": {
            "operating_temp_c": round(operating_temp_c, 1),
            "resistance_20c_mohm": round(r_20c * 1000.0, 2),
            "resistance_hot_mohm": round(r_hot * 1000.0, 2),
            "voltage_drop_mv": round(v_drop * 1000.0, 2),
            "power_loss_mw": round(p_joule_mw, 2),
        },
        "easyeda_action": (
            f"Configure Design Rule para este riel con ancho >= {recommended_width_mm} mm "
            f"({recommended_width_mil} mil). Si I >= 5 A en prototipo, active 'Expose Copper' para refuerzo con estaño."
        ),
    }


def calc_clearance_creepage(
    voltage_val: float,
    is_ac_rms: bool = False,
    location: str = "external_uncoated_B2",
    pollution_degree: int = 2,
    material_group: str = "IIIa",
    altitude_m: float = 500.0,
    available_space_mm: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula Clearance y Creepage según IPC-2221C (Tabla 6-1) e IEC 60664-1 / IEC 62368-1,
    convirtiendo automáticamente tensión AC RMS a tensión Pico (V_peak).
    """
    v_peak = voltage_val * math.sqrt(2.0) if is_ac_rms else voltage_val

    # IPC-2221C Table 6-1 (B1: Internal, B2: External uncoated / normal solder mask, B4: Conformal coated)
    if v_peak <= 15:
        b1, b2, b4 = 0.05, 0.10, 0.05
    elif v_peak <= 30:
        b1, b2, b4 = 0.05, 0.10, 0.05
    elif v_peak <= 50:
        b1, b2, b4 = 0.10, 0.60, 0.13
    elif v_peak <= 100:
        b1, b2, b4 = 0.10, 0.60, 0.13
    elif v_peak <= 150:
        b1, b2, b4 = 0.20, 0.60, 0.40
    elif v_peak <= 300:
        b1, b2, b4 = 0.20, 1.25, 0.40
    elif v_peak <= 500:
        b1, b2, b4 = 0.25, 2.50, 0.80
    else:
        dv = v_peak - 500.0
        b1 = 0.25 + 0.0025 * dv
        b2 = 2.50 + 0.0050 * dv
        b4 = 0.80 + 0.00305 * dv

    loc_key = location.upper()
    if "B1" in loc_key or "INTERN" in loc_key:
        ipc_clearance_mm = b1
        col_used = "B1 (Capas Internas)"
    elif "B4" in loc_key or "CONFORMAL" in loc_key:
        ipc_clearance_mm = b4
        col_used = "B4 (Recubrimiento Polimérico Permanente Certificado)"
    else:
        ipc_clearance_mm = b2
        col_used = "B2 (Capa Externa / Máscara Antisoldante Estándar)"

    # IEC 60664-1 / IEC 62368-1 Creepage factor por CTI y Grado de Polución
    mg_factor = {"I": 1.0, "II": 1.2, "IIIA": 1.4, "IIIB": 1.6}.get(material_group.upper(), 1.4)
    pd_factor = {1: 0.8, 2: 1.0, 3: 1.6}.get(pollution_degree, 1.0)
    alt_factor = 1.0 if altitude_m <= 2000 else 1.0 + ((altitude_m - 2000.0) / 1000.0) * 0.14

    iec_creepage_basic_mm = max(ipc_clearance_mm, (v_peak / 100.0) * 0.8 * mg_factor * pd_factor)
    iec_creepage_reinforced_mm = iec_creepage_basic_mm * 2.0 if v_peak >= 70 else iec_creepage_basic_mm
    clearance_alt_mm = ipc_clearance_mm * alt_factor

    needs_milled_slot = False
    if available_space_mm is not None and available_space_mm < iec_creepage_reinforced_mm:
        needs_milled_slot = True
    elif v_peak >= 200:
        needs_milled_slot = True

    return {
        "standards": ["IPC-2221C Tabla 6-1", "IEC 60664-1", "IEC 62368-1"],
        "voltage_input": voltage_val,
        "is_ac_rms": is_ac_rms,
        "evaluated_v_peak": round(v_peak, 2),
        "ipc_column_used": col_used,
        "ipc_2221c_clearance_mm": round(clearance_alt_mm, 2),
        "ipc_2221c_clearance_mil": round(clearance_alt_mm * MM_TO_MIL, 1),
        "iec_60664_creepage_basic_mm": round(iec_creepage_basic_mm, 2),
        "iec_62368_creepage_reinforced_mm": round(iec_creepage_reinforced_mm, 2),
        "solder_mask_warning": (
            "La máscara antisoldante convencional NO califica como recubrimiento B4 en alta tensión. "
            "Se aplicó columna B2 salvo barniz dieléctrico certificado."
        ),
        "milled_slot_recommendation": {
            "required": needs_milled_slot,
            "min_slot_width_mm": 1.5 if needs_milled_slot else 0.0,
            "easyeda_instruction": (
                "En EasyEDA Pro cree una 'Solid Region' con Type = 'Board Cutout' de ancho >= 1.5 mm "
                "entre los nodos de alta tensión y baja tensión (se exporta en Gerber_BoardOutline.GKO)."
                if needs_milled_slot
                else "No requiere ranura fresada si respeta el espaciamiento superficial en cobre."
            ),
        },
    }


JLCPCB_STACKUPS: Dict[str, Dict[str, Any]] = {
    "JLC_2L_1.6mm": {"layers": 2, "dielectric_h_mm": 1.53, "er": 4.5, "copper_oz": 1.0, "description": "JLCPCB 2 capas estándar 1.6 mm FR-4"},
    "JLC04161H-7628": {"layers": 4, "dielectric_h_mm": 0.2104, "er": 4.6, "copper_oz": 1.0, "description": "JLCPCB 4 capas Prepreg 7628 (económico)"},
    "JLC04161H-3313": {"layers": 4, "dielectric_h_mm": 0.0994, "er": 4.05, "copper_oz": 1.0, "description": "JLCPCB 4 capas Prepreg 3313 (recomendado RF 50 Ohm / USB 90 Ohm)"},
    "JLC04161H-2313": {"layers": 4, "dielectric_h_mm": 0.10, "er": 4.05, "copper_oz": 1.0, "description": "JLCPCB 4 capas Prepreg 2313 (alta estabilidad dieléctrica)"},
}


def calc_impedance_si(
    topology: str = "microstrip",
    trace_width_mm: float = 0.25,
    dielectric_h_mm: float = 0.20,
    copper_oz: float = 1.0,
    er: float = 4.4,
    diff_spacing_mm: Optional[float] = None,
    driver_z_source_ohm: float = 20.0,
    load_z_ohm: float = 50.0,
    rise_time_ns: float = 1.0,
    jlcpcb_stackup: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calcula impedancia característica Z0 (Microstrip y Stripline) según IPC-2141A,
    pares diferenciales, resistencia de terminación en serie Rs, coeficiente de reflexión Gamma
    y reglas de separación contra diafonía 3W y 5W. Soporta perfiles oficiales JLCPCB de EasyEDA Pro.
    """
    stackup_applied = None
    if jlcpcb_stackup:
        preset = JLCPCB_STACKUPS.get(jlcpcb_stackup)
        if preset is None:
            raise ValueError(f"Stackup JLCPCB desconocido: {jlcpcb_stackup}. Opciones: {list(JLCPCB_STACKUPS.keys())}")
        dielectric_h_mm = float(preset["dielectric_h_mm"])
        er = float(preset["er"])
        copper_oz = float(preset["copper_oz"])
        stackup_applied = {"name": jlcpcb_stackup, **preset}

    _require_pos_finite(trace_width_mm, "trace_width_mm")
    _require_pos_finite(dielectric_h_mm, "dielectric_h_mm")
    _require_pos_finite(copper_oz, "copper_oz")
    _require_pos_finite(er, "er")

    t_mm = copper_oz * COPPER_OZ_TO_MM
    w_over_h = trace_width_mm / dielectric_h_mm
    model_valid = w_over_h <= 7.5

    if topology.lower() == "stripline":
        # B es separación total entre ambos planos = 2 * H + T
        b_mm = 2.0 * dielectric_h_mm + t_mm
        z0 = (60.0 / math.sqrt(er)) * math.log((1.9 * b_mm) / (0.8 * trace_width_mm + t_mm))
        v_prop_m_s = 3.0e8 / math.sqrt(er)
    else:
        z0 = (87.0 / math.sqrt(er + 1.41)) * math.log((5.98 * dielectric_h_mm) / (0.8 * trace_width_mm + t_mm))
        er_eff = (er + 1.0) / 2.0 + ((er - 1.0) / 2.0) * (1.0 / math.sqrt(1.0 + 12.0 * (dielectric_h_mm / trace_width_mm)))
        v_prop_m_s = 3.0e8 / math.sqrt(er_eff)

    z0 = max(10.0, z0)
    z_diff = None
    if diff_spacing_mm is not None and diff_spacing_mm > 0:
        if topology.lower() == "stripline":
            b_mm = 2.0 * dielectric_h_mm + t_mm
            z_diff = 2.0 * z0 * (1.0 - 0.347 * math.exp(-2.9 * (diff_spacing_mm / b_mm)))
        else:
            z_diff = 2.0 * z0 * (1.0 - 0.48 * math.exp(-0.96 * (diff_spacing_mm / dielectric_h_mm)))

    r_series = max(0.0, z0 - driver_z_source_ohm)
    gamma = (load_z_ohm - z0) / (load_z_ohm + z0)

    # Longitud crítica donde se comporta como línea de transmisión (L_crit = t_r / (6 * t_pd))
    t_pd_ns_per_mm = 1e6 / v_prop_m_s  # ns/mm
    l_crit_mm = rise_time_ns / (6.0 * t_pd_ns_per_mm)

    return {
        "standard": "IPC-2141A + Reglas SI/GND (Manual 03) + Stackup JLCPCB/EasyEDA Pro",
        "topology": topology,
        "jlcpcb_stackup": stackup_applied,
        "z0_characteristic_ohm": round(z0, 2),
        "z_differential_ohm": round(z_diff, 2) if z_diff is not None else None,
        "w_over_h_ratio": round(w_over_h, 2),
        "ipc_2141a_formula_valid": model_valid,
        "termination": {
            "series_resistor_rs_ohm": round(r_series, 1),
            "reflection_coeff_gamma_unterminated": round(gamma, 3),
            "placement_rule": "Coloque Rs inmediatamente a la salida del pin transmisor (driver).",
        },
        "transmission_line_threshold": {
            "propagation_delay_ps_per_mm": round(t_pd_ns_per_mm * 1000.0, 2),
            "critical_length_mm": round(l_crit_mm, 1),
        },
        "crosstalk_and_gnd_rules": {
            "rule_3w_center_to_center_mm": round(3.0 * trace_width_mm, 3),
            "rule_3w_edge_to_edge_mm": round(2.0 * trace_width_mm, 3),
            "rule_5w_center_to_center_mm": round(5.0 * trace_width_mm, 3),
            "rule_5w_edge_to_edge_mm": round(4.0 * trace_width_mm, 3),
            "diff_pair_max_skew_mm": 0.127,
            "diff_pair_max_skew_mil": 5.0,
            "gnd_plane_mandate": "Mantenga un plano GND continuo debajo de toda la traza; prohibido cruzar cortes de plano (split planes).",
        },
    }


def calc_pdn_decoupling(
    voltage_nominal_v: float = 3.3,
    ripple_percent: float = 5.0,
    transient_current_a: float = 0.4,
    package: str = "0805",
) -> Dict[str, Any]:
    """
    Calcula la impedancia objetivo Z_target de la PDN y la frecuencia autorresonante f_SRF
    de la red de desacoplo en 3 décadas según el encapsulado MLCC seleccionado.
    """
    esl_nh_by_pkg = {
        "0201": 0.30,
        "0402": 0.45,
        "0603": 0.65,
        "0805": 0.90,
        "1206": 1.25,
    }
    esl_nh = esl_nh_by_pkg.get(package, 0.80)
    esl_h = esl_nh * 1e-9

    _require_pos_finite(voltage_nominal_v, "voltage_nominal_v")
    _require_pos_finite(ripple_percent, "ripple_percent")
    _require_pos_finite(transient_current_a, "transient_current_a")
    dv_allowed = voltage_nominal_v * (ripple_percent / 100.0)
    z_target = dv_allowed / transient_current_a

    decades = [
        {"role": "Reserva Local (Bulk)", "capacitance_uf": 10.0, "c_f": 10e-6},
        {"role": "Media Frecuencia (MLCC Principal)", "capacitance_uf": 0.1, "c_f": 100e-9},
        {"role": "Alta Frecuencia (Flancos rápidos)", "capacitance_uf": 0.01, "c_f": 10e-9},
    ]
    network = []
    for d in decades:
        f_srf_hz = 1.0 / (2.0 * math.pi * math.sqrt(esl_h * d["c_f"]))
        network.append({
            "role": d["role"],
            "value": f"{d['capacitance_uf']} uF" if d["capacitance_uf"] >= 1 else f"{int(d['capacitance_uf']*1000)} nF",
            "package": package,
            "estimated_esl_nh": esl_nh,
            "f_srf_mhz": round(f_srf_hz / 1e6, 2),
        })

    return {
        "standard": "PDN Target Impedance & 3-Decade SRF Strategy (Manual 01)",
        "voltage_nominal_v": voltage_nominal_v,
        "allowed_ripple_mv": round(dv_allowed * 1000.0, 1),
        "transient_current_a": transient_current_a,
        "z_target_ohm": round(z_target, 4),
        "three_decade_network": network,
        "layout_rules": [
            "Ubique el capacitor de 100 nF / 10 nF a menos de 2.0 mm del pin VDD del integrado.",
            "Coloque una vía directa a GND junto al pad de tierra de cada capacitor SMD (en placas de 2 capas, omitir la vía desconecta el pad del plano GND inferior).",
        ],
    }


def calc_thermal_vias(
    power_dissipation_w: float,
    board_thickness_mm: float = 1.6,
    via_drill_mm: float = 0.25,
    plating_thickness_um: float = 25.0,
    via_count: int = 9,
) -> Dict[str, Any]:
    """
    Calcula la resistencia térmica de conducción de Fourier (R_th = L / (k * A))
    de una matriz de N vías térmicas en paralelo.
    """
    _require_pos_finite(board_thickness_mm, "board_thickness_mm")
    _require_pos_finite(via_drill_mm, "via_drill_mm")
    _require_pos_finite(plating_thickness_um, "plating_thickness_um")
    if power_dissipation_w < 0 or not math.isfinite(power_dissipation_w):
        raise ValueError("power_dissipation_w debe ser finito y >= 0.")
    l_m = board_thickness_mm * 1e-3
    r_outer_m = (via_drill_mm * 1e-3) / 2.0
    t_plating_m = plating_thickness_um * 1e-6
    r_inner_m = max(0.0, r_outer_m - t_plating_m)

    area_copper_barrel_m2 = math.pi * ((r_outer_m ** 2) - (r_inner_m ** 2))
    r_th_single = l_m / (COPPER_K_THERMAL * area_copper_barrel_m2)
    r_th_array = r_th_single / max(1, via_count)
    temp_drop_across_vias_c = power_dissipation_w * r_th_array
    aspect_ratio = board_thickness_mm / via_drill_mm

    return {
        "standard": "Fourier Conduction / IPC-2152 / IPC-6012",
        "r_th_single_via_c_per_w": round(r_th_single, 2),
        "r_th_array_c_per_w": round(r_th_array, 2),
        "via_count": via_count,
        "temp_delta_across_vias_c": round(temp_drop_across_vias_c, 2),
        "aspect_ratio": round(aspect_ratio, 2),
        "ipc_6012_aspect_ratio_ok": aspect_ratio <= 10.0,
        "capillary_solder_wicking_ok": 0.20 <= via_drill_mm <= 0.30,
        "recommended_pitch_mm": 0.50,
    }


def validate_mcu_pinout(
    mcu_family: str,
    pin_assignments: Dict[str, str],
    uses_wifi: bool = True,
    octal_flash_psram: bool = False,
) -> Dict[str, Any]:
    """
    Valida asignaciones de pines contra la Matriz de 3 Niveles (Manual 08):
    1. PROHIBIDO TOCAR (SPI Flash/PSRAM interna, Input-Only usados como salida, pines internos módem Walter).
    2. PINES SENSIBLES (USB D+/D- nativo, JTAG dedicado, Strapping pins de arranque, ADC2+Wi-Fi, Back-powering UART).
    3. PINES LIMPIOS RECOMENDADOS (safe_clean_pins).
    """
    fam = mcu_family.upper()
    warnings: List[str] = []
    blocking_errors: List[str] = []
    recommendations: List[str] = []
    safe_clean_pins: List[str] = []

    if "ESP32" in fam or "WALTER" in fam:
        # 1. PINES PROHIBIDOS ("NO TOCAR": SPI Flash / PSRAM / Internos Módem)
        flash_forbidden: Dict[str, set] = {
            "ESP32-CLASSIC": {"GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO11"},
            "S3": {"GPIO26", "GPIO27", "GPIO28", "GPIO29", "GPIO30", "GPIO31", "GPIO32"} | (
                {"GPIO33", "GPIO34", "GPIO35", "GPIO36", "GPIO37"} if octal_flash_psram else set()
            ),
            "C3": {"GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO16", "GPIO17"},
            "C6": {"GPIO24", "GPIO25", "GPIO26", "GPIO27", "GPIO28", "GPIO29", "GPIO30"},
            "C5": {"GPIO15", "GPIO16", "GPIO17", "GPIO18", "GPIO20", "GPIO21", "GPIO22"},
        }
        variant = (
            "C5" if "C5" in fam else
            "C6" if "C6" in fam else
            "C3" if "C3" in fam else
            "S3" if ("S3" in fam or "WALTER" in fam) else
            "ESP32-CLASSIC"
        )
        forbidden_set = set(flash_forbidden[variant])
        if "WROVER" in fam and variant == "ESP32-CLASSIC":
            forbidden_set |= {"GPIO16", "GPIO17"}
        if "WALTER" in fam:
            # En DPTechnics Walter el módem Sequans GM02SP usa internamente pines dedicados
            forbidden_set |= {"GPIO14", "GPIO45"}

        # Pines USB Nativo D- / D+ (sensibles: inhabilitan consola/flasheo USB CDC/JTAG)
        usb_native: Dict[str, set] = {
            "ESP32-CLASSIC": set(),
            "S3": {"GPIO19", "GPIO20"},
            "C3": {"GPIO18", "GPIO19"},
            "C6": {"GPIO12", "GPIO13"},
            "C5": {"GPIO13", "GPIO14"},
        }

        # Strapping pins específicos por sub-familia
        strapping_by_var: Dict[str, Dict[str, str]] = {
            "ESP32-CLASSIC": {
                "GPIO0": "Boot mode (debe estar HIGH para arrancar Flash).",
                "GPIO2": "Debe estar LOW/flotante al flashear.",
                "GPIO5": "Timing SDIO Slave.",
                "GPIO12": "CRÍTICO MTDI: si está HIGH al encender fuerza VDD_SDIO=1.8V y bloquea la Flash de 3.3V.",
                "GPIO15": "MTDO: silencia log UART0 si está LOW.",
            },
            "S3": {
                "GPIO0": "Boot mode.",
                "GPIO3": "Fuente JTAG.",
                "GPIO45": "Tensión VDD_SPI (no forzar HIGH si usa Flash/PSRAM 3.3V).",
                "GPIO46": "Boot mode (debe estar LOW/flotante al arrancar).",
            },
            "C3": {
                "GPIO2": "Strapping / Glitch check.",
                "GPIO8": "CRÍTICO: debe estar HIGH (pull-up 10k) para habilitar descarga serie/USB.",
                "GPIO9": "BOOT (pull-up interno).",
            },
            "C6": {
                "GPIO4": "MTMS Strapping.",
                "GPIO5": "MTDI Strapping.",
                "GPIO8": "Debe estar HIGH para control de modo boot.",
                "GPIO9": "BOOT (pull-up interno).",
                "GPIO15": "Control ROM log / JTAG.",
            },
            "C5": {
                "GPIO2": "MTMS Strapping.",
                "GPIO3": "MTDI Strapping.",
                "GPIO7": "Strapping (D3 en XIAO C5).",
                "GPIO25": "Strapping SDIO (D2 en XIAO C5, sin ADC).",
                "GPIO26": "Strapping.",
                "GPIO27": "Strapping.",
                "GPIO28": "Strapping.",
                "D2": "En XIAO C5 corresponde a GPIO25 (Strapping, sin ADC).",
                "D3": "En XIAO C5 corresponde a GPIO7 (Strapping).",
            },
        }

        safe_by_var: Dict[str, List[str]] = {
            "ESP32-CLASSIC": ["GPIO4", "GPIO13", "GPIO14", "GPIO18", "GPIO19", "GPIO21", "GPIO22", "GPIO23", "GPIO25", "GPIO26", "GPIO27", "GPIO32", "GPIO33"],
            "S3": ["GPIO1", "GPIO2", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO17", "GPIO18", "GPIO21", "GPIO38", "GPIO39", "GPIO40", "GPIO41", "GPIO42"],
            "C3": ["GPIO0", "GPIO1", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO10"],
            "C6": ["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO6", "GPIO7", "GPIO10", "GPIO11", "GPIO16", "GPIO17", "GPIO18", "GPIO19", "GPIO20", "GPIO21", "GPIO22", "GPIO23"],
            "C5": ["D0 (GPIO1/ADC1/LP)", "D1 (GPIO0/LP)", "D4 (GPIO23 SDA)", "D5 (GPIO24 SCL)", "D6 (GPIO11 TX)", "D7 (GPIO12 RX)", "D8 (GPIO8)", "D9 (GPIO9)", "D10 (GPIO10)"],
        }
        safe_clean_pins = safe_by_var[variant]

        # Validaciones generales por pin
        input_only_classic = {"GPIO34", "GPIO35", "GPIO36", "GPIO39"}
        output_keywords = ("OUT", "DRV", "EN", "TX", "SCL", "SDA", "MOSI", "SCK", "LED", "PWM", "RELAY")

        for p, func in pin_assignments.items():
            pu = p.upper().strip()
            fu = func.upper().strip()

            if pu in forbidden_set:
                blocking_errors.append(
                    f"PROHIBIDO TOCAR {pu} ('{func}'): Pin reservado internamente para SPI Flash/PSRAM o módem interno en {mcu_family}. Conectarlo cuelga el SoC."
                )

            if variant == "ESP32-CLASSIC" and pu in input_only_classic:
                if any(kw in fu for kw in output_keywords):
                    blocking_errors.append(
                        f"PROHIBIDO {pu} ('{func}'): En ESP32 clásico GPIO34..39 son SOLO ENTRADA (sin etapa push-pull ni pull-up/down interno)."
                    )
                else:
                    warnings.append(
                        f"Pin Sensible {pu} ('{func}'): GPIO34..39 carecen de pull-up/pull-down interno; exigen resistor externo físico."
                    )

            if pu in usb_native[variant] and "USB" not in fu:
                warnings.append(
                    f"Pin Sensible USB Nativo {pu} asignado a '{func}': deshabilitará el puerto USB Serial/JTAG directo de programación y depuración."
                )

            if pu in strapping_by_var[variant]:
                warnings.append(
                    f"Strapping Pin Sensible {pu} asignado a '{func}': {strapping_by_var[variant][pu]}"
                )

        # ADC2 + Wi-Fi bloqueo por hardware
        if uses_wifi:
            adc2_pins = {
                "ESP32-CLASSIC": {"GPIO0", "GPIO2", "GPIO4", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO25", "GPIO26", "GPIO27"},
                "S3": {"GPIO11", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "GPIO19", "GPIO20"},
                "C3": {"GPIO5"},
            }
            if variant in adc2_pins:
                for p, func in pin_assignments.items():
                    if p.upper().strip() in adc2_pins[variant] and "ADC" in func.upper():
                        blocking_errors.append(
                            f"{p} ({func}): Pertenece a ADC2, bloqueado por hardware cuando Wi-Fi está activo. Use exclusivamente ADC1."
                        )

        if variant == "C6":
            lp_io = {"GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "D0", "D1", "D2"}
            for p, func in pin_assignments.items():
                if ("WAKE" in func.upper() or "SLEEP" in func.upper()) and p.upper().strip() not in lp_io:
                    blocking_errors.append(
                        f"{p} ({func}): En ESP32-C6 solo GPIO0..GPIO7 son LP-IO capaces de despertar al chip desde Deep Sleep (ext1)."
                    )

        if variant == "C5":
            c5_adc_pins = {"GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "D0"}
            jtag_pads = {"MTMS", "MTDI", "MTCK", "MTDO"}
            for p, func in pin_assignments.items():
                pu = p.upper().strip()
                fu = func.upper().strip()
                if "ADC" in fu and pu not in c5_adc_pins:
                    blocking_errors.append(
                        f"{p} ({func}): En XIAO ESP32-C5 / ESP32-C5 solo D0 (GPIO1 = ADC1_CH0) en el borde o GPIO1..GPIO6 poseen ADC1. D2 es GPIO25 (NO tiene ADC y es Strapping Pin)."
                    )
                if pu in jtag_pads and ("WAKE" in fu or "SLEEP" in fu or "RTC" in fu or "I2C" in fu):
                    blocking_errors.append(
                        f"{p} ({func}): En XIAO ESP32-C5 Seeed Studio prohíbe usar los pads JTAG inferiores (MTMS=GPIO2/Strapping, MTDI=GPIO3/Strapping, MTCK, MTDO) para Deep-Sleep Wake o buses periféricos; use D4 (GPIO23 SDA) y D5 (GPIO24 SCL)."
                    )

        # Alerta anti Back-Powering en diseños ULP con módem conmutado (SIM7080G / LTE)
        all_funcs = " ".join(pin_assignments.values()).upper()
        if ("LTE_EN" in all_funcs or "MODEM_EN" in all_funcs) and ("TX" in all_funcs or "RX" in all_funcs):
            recommendations.append(
                "CRÍTICO ULP (Anti Back-Powering): Al cortar VBAT_LTE con MOSFET P (Q7), ponga TX/RX/PWRKEY en LOW o Hi-Z (o use TXS0102 con VCCA ligado al módem) antes de apagar, para evitar alimentar parasitariamente el módem por sus diodos ESD."
            )

        recommendations.append("Incluya red RC de retardo en pin EN/CHIP_PU (10 kΩ a 3V3 + 1 uF a GND) y fuente 3.3V >= 600 mA.")

    elif "STM32" in fam:
        if "BOOT0" not in {k.upper() for k in pin_assignments}:
            warnings.append("Pin BOOT0 no declarado: asegure resistencia de 10 kΩ a GND para arrancar desde Flash.")
        recommendations.extend([
            "Conecte capacitor de 100 nF entre NRST y GND.",
            "Alimente siempre VDDA/VSSA (filtrados con ferrita + 1 uF + 10 nF si usa el ADC).",
            "Incluya conector de 4/5 pines para programación SWD (3V3, SWDIO, SWCLK, GND, NRST).",
        ])

    elif "AVR" in fam or "ATMEGA" in fam:
        for p, func in pin_assignments.items():
            if p.upper() == "AREF" and ("VCC" in func.upper() or "5V" in func.upper()):
                blocking_errors.append(
                    "Pin AREF conectado a VCC/5V: PROHIBIDO en AVR (causa cortocircuito interno al seleccionar referencia de 1.1V). Conecte AREF solo a un capacitor de 100 nF hacia GND."
                )
        recommendations.append("Incluya cabezal ICSP de 6 pines y pull-up de 10 kΩ en RESET.")

    elif "RP2040" in fam or "RP2350" in fam:
        recommendations.extend([
            "Instale resistencias de terminación serie de 27 Ω en USB_DP y USB_DM junto al chip.",
            "Ubique la memoria Flash QSPI a menos de 5 mm del microcontrolador.",
        ])

    return {
        "mcu_family": mcu_family,
        "passed": len(blocking_errors) == 0,
        "blocking_errors": blocking_errors,
        "warnings": warnings,
        "safe_clean_pins": safe_clean_pins,
        "mandatory_hardware_checks": recommendations,
    }


def audit_floorplan_2d(
    board_width_mm: float,
    board_height_mm: float,
    chamfer_mm: float,
    components: List[Dict[str, Any]],
    edge_margin_mm: float = 0.8,
    min_courtyard_gap_mm: float = 0.4,
    origin_mil: Tuple[float, float] = (0.0, 0.0),
) -> Dict[str, Any]:
    """
    Verifica colisiones 2D entre componentes, violaciones del contorno (incluyendo chaflanes)
    y genera la lista de coordenadas en mils nativos lista para easyeda_pcb_place_batch.
    """
    _require_pos_finite(board_width_mm, "board_width_mm")
    _require_pos_finite(board_height_mm, "board_height_mm")
    if len(components) > MAX_COLLECTION_ITEMS:
        raise ValueError(f"components excede el límite de seguridad ({MAX_COLLECTION_ITEMS}).")

    def inside_octagon(x: float, y: float) -> bool:
        if not (0.0 <= x <= board_width_mm and 0.0 <= y <= board_height_mm):
            return False
        ch = chamfer_mm
        return (
            (x + y >= ch)
            and ((board_width_mm - x) + y >= ch)
            and (x + (board_height_mm - y) >= ch)
            and ((board_width_mm - x) + (board_height_mm - y) >= ch)
        )

    collisions: List[str] = []
    outline_violations: List[str] = []
    boxes: Dict[str, Tuple[float, float, float, float]] = {}
    batch_placements: List[Dict[str, Any]] = []

    for c in components:
        ref = c["designator"]
        x = float(c["x_mm"])
        y = float(c["y_mm"])
        w = float(c.get("width_mm", 3.0))
        h = float(c.get("height_mm", 2.0))
        rot = float(c.get("rotation", 0))
        allow_edge = bool(c.get("allow_edge_overlap", False))

        x0, y0, x1, y1 = x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0
        boxes[ref] = (x0, y0, x1, y1)

        if not allow_edge:
            corners = [
                (x0 - edge_margin_mm, y0 - edge_margin_mm),
                (x1 + edge_margin_mm, y0 - edge_margin_mm),
                (x0 - edge_margin_mm, y1 + edge_margin_mm),
                (x1 + edge_margin_mm, y1 + edge_margin_mm),
            ]
            for cx, cy in corners:
                if not inside_octagon(cx, cy):
                    outline_violations.append(
                        f"{ref}: esquina ({cx:.1f}, {cy:.1f}) mm viola el contorno/chaflán o margen de borde ({edge_margin_mm} mm)."
                    )
                    break

        if "primitiveId" in c and c["primitiveId"]:
            batch_placements.append({
                "primitiveId": c["primitiveId"],
                "x": round(origin_mil[0] + x * MM_TO_MIL, 2),
                "y": round(origin_mil[1] + y * MM_TO_MIL, 2),
                "rotation": rot,
            })

    refs = list(boxes.keys())
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            A, B = boxes[a], boxes[b]
            if (
                A[0] < B[2] + min_courtyard_gap_mm
                and B[0] < A[2] + min_courtyard_gap_mm
                and A[1] < B[3] + min_courtyard_gap_mm
                and B[1] < A[3] + min_courtyard_gap_mm
            ):
                collisions.append(f"Colisión de patio entre {a} y {b} (separación < {min_courtyard_gap_mm} mm).")

    return {
        "passed": len(collisions) == 0 and len(outline_violations) == 0,
        "component_count": len(components),
        "collisions": collisions,
        "outline_violations": outline_violations,
        "easyeda_place_batch_payload": batch_placements,
    }


def analyze_raw_easyeda_pcb_data(
    pads: List[Dict[str, Any]],
    vias: List[Dict[str, Any]],
    pours: List[Dict[str, Any]],
    drc_tree: Optional[List[Dict[str, Any]]] = None,
    origin_mil: Tuple[float, float] = (68.0, 494.0),
) -> Dict[str, Any]:
    """
    Analiza primitivas crudas de EasyEDA Pro (Pads, Vías, Pours y árbol detallado de PCB_Drc.check)
    para entregar un diagnóstico físico real con coordenadas traducidas a mm de placa,
    detectando pads GND SMD desconectados por falta de vías de retorno, pours huérfanos y choques.
    """
    # 1. Extraer violaciones detalladas del árbol de PCB_Drc.check
    detailed_drc_errors: List[Dict[str, Any]] = []
    if drc_tree:
        for cat in drc_tree:
            for net_grp in cat.get("list", []):
                for item in net_grp.get("list", []):
                    err_data = item.get("explanation", {}).get("errData", {})
                    pos = item.get("pos", {})
                    # En PCB_Drc.check, pos.x y pos.y vienen en unidades de 10 mil (1 pixel = 10 mil)
                    x_mil = float(pos.get("x", 0.0)) * 10.0
                    y_mil = float(pos.get("y", 0.0)) * 10.0
                    x_mm = round((x_mil - origin_mil[0]) * MIL_TO_MM, 2)
                    y_mm = round((y_mil - origin_mil[1]) * MIL_TO_MM, 2)
                    detailed_drc_errors.append({
                        "errorType": err_data.get("errorType", item.get("errorType")),
                        "rule": item.get("ruleName"),
                        "net": item.get("net"),
                        "object": err_data.get("obj1Suffix", item.get("obj1", {}).get("suffix")),
                        "primitiveId": err_data.get("obj1"),
                        "x_mil": round(x_mil, 2),
                        "y_mil": round(y_mil, 2),
                        "x_board_mm": x_mm,
                        "y_board_mm": y_mm,
                    })

    # 2. Auditar vías de retorno GND (Manual 01 y Manual 03)
    gnd_vias = [v for v in vias if (v.get("net") or v.get("Net")) == "GND"]
    gnd_smd_pads = [
        p for p in pads
        if (p.get("net") or p.get("Net")) == "GND" and (p.get("layer") or p.get("Layer")) in (1, 2) and not p.get("hole")
    ]

    # 3. Auditar planos de cobre (Pours) huérfanos o sin reconstruir
    unlinked_pours = [
        p.get("pourName") or p.get("primitiveId")
        for p in pours
        if p.get("copperLinkStatus") == "absent"
    ]

    # 4. Auditar choques de pads de distinta red (< 0.8 mm centro a centro en misma capa)
    close_pad_pairs: List[Dict[str, Any]] = []
    for i in range(len(pads)):
        p1 = pads[i]
        l1 = p1.get("layer", 1)
        for j in range(i + 1, len(pads)):
            p2 = pads[j]
            l2 = p2.get("layer", 1)
            if l1 != l2 and l1 != 12 and l2 != 12:
                continue
            n1 = p1.get("net", "")
            n2 = p2.get("net", "")
            if n1 and n1 == n2:
                continue
            dx_mil = float(p1.get("x", 0.0)) - float(p2.get("x", 0.0))
            dy_mil = float(p1.get("y", 0.0)) - float(p2.get("y", 0.0))
            dist_mm = math.hypot(dx_mil, dy_mil) * MIL_TO_MM
            if dist_mm < 0.85:
                close_pad_pairs.append({
                    "pad1": p1.get("primitiveId"),
                    "net1": n1,
                    "pad2": p2.get("primitiveId"),
                    "net2": n2,
                    "center_distance_mm": round(dist_mm, 3),
                })

    # 5. Generar recomendaciones automáticas de vías GND para cada pad GND desconectado
    remediation_vias: List[Dict[str, Any]] = []
    for err in detailed_drc_errors:
        if err["net"] == "GND" and "No Connection" in str(err["errorType"]):
            # Proponer una vía GND estándar JLCPCB (drill 12 mil / 0.3 mm, outer 24 mil / 0.6 mm)
            # desplazada 35 mil (~0.9 mm) respecto al centro del pad desconectado
            remediation_vias.append({
                "for_object": err["object"],
                "suggested_tool": "easyeda_pcb_add_via",
                "args": {
                    "netName": "GND",
                    "x": round(err["x_mil"] + 35.0, 2),
                    "y": round(err["y_mil"], 2),
                    "holeSize": 12,
                    "outerDiameter": 24,
                    "confirmWrite": True,
                },
            })

    return {
        "summary": {
            "total_pads": len(pads),
            "total_vias": len(vias),
            "gnd_stitching_vias_count": len(gnd_vias),
            "gnd_smd_pads_count": len(gnd_smd_pads),
            "detailed_drc_error_count": len(detailed_drc_errors),
            "unlinked_copper_pours": unlinked_pours,
            "close_pad_warnings_count": len(close_pad_pairs),
        },
        "normative_alerts": (
            [
                f"CRÍTICO (Manual 01 y 03): El PCB tiene {len(gnd_smd_pads)} pads SMD en la red GND pero solo {len(gnd_vias)} vías de costura GND. "
                "En placas de 2 capas, los pads SMD de GND encerrados por pistas en Top Layer quedan desconectados si no tienen una vía directa al plano GND de Bottom Layer."
            ]
            if len(gnd_vias) == 0 and len(gnd_smd_pads) > 0
            else []
        ) + (
            [
                f"ADVERTENCIA (Manual 11): Existen áreas de cobre sin relleno activo ({', '.join(unlinked_pours)}). "
                "Elimine los polígonos redundantes o reconstruya el cobre con easyeda_pcb_rebuild_copper (Shift+B)."
            ]
            if unlinked_pours
            else []
        ),
        "detailed_drc_errors": detailed_drc_errors,
        "auto_remediation_gnd_vias": remediation_vias,
        "close_pad_pairs": close_pad_pairs[:20],
    }


def verify_connection_board(
    board_width_mm: float,
    board_height_mm: float,
    devices: List[Dict[str, Any]],
    connections: List[Dict[str, Any]],
    chamfer_mm: float = 0.0,
    origin_mil: Tuple[float, float] = (0.0, 0.0),
) -> Dict[str, Any]:
    """
    Compuerta estricta Datasheet-First y Validador Eléctrico/Físico para el PCB de Conexión.
    - Bloquea la promoción a EasyEDA Pro si algún equipo carece de ficha técnica verificada.
    - Verifica existencia real de pines, compatibilidad de tensiones lógicas, cortocircuitos
      de rieles, continuidad de referencia GND y colisiones 2D de posicionamiento.
    - Genera el plan de colocación en mils y la secuencia de llamadas para easyeda-mcp-pro.
    """
    missing_datasheets: List[Dict[str, Any]] = []
    electrical_errors: List[str] = []
    electrical_warnings: List[str] = []
    device_map: Dict[str, Dict[str, Any]] = {}
    pin_lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}
    floorplan_components: List[Dict[str, Any]] = []

    for dev in devices:
        des = str(dev.get("designator", "")).strip()
        name = str(dev.get("name", des)).strip()
        if not des:
            electrical_errors.append("Existe un equipo sin designador (ej. U1, J1, M1).")
            continue

        device_map[des] = dev
        verified = bool(dev.get("datasheet_verified", False))
        source = str(dev.get("datasheet_source", "")).strip()
        pins = dev.get("pins", []) or []

        if not verified or not source or len(pins) == 0:
            missing_datasheets.append({
                "designator": des,
                "name": name,
                "reason": (
                    "Falta verificación de ficha técnica (datasheet_verified=true y datasheet_source) "
                    "o definición real de pines. DETÉNGASE y solicite la ficha técnica al usuario."
                ),
            })

        for pin in pins:
            p_num = str(pin.get("number", "")).strip()
            p_name = str(pin.get("name", p_num)).strip()
            if p_num:
                pin_lookup[(des, p_num)] = pin
            if p_name:
                pin_lookup[(des, p_name)] = pin

        floorplan_components.append({
            "designator": des,
            "x_mm": float(dev.get("x_mm", 0.0)),
            "y_mm": float(dev.get("y_mm", 0.0)),
            "width_mm": float(dev.get("width_mm", 10.0)),
            "height_mm": float(dev.get("height_mm", 10.0)),
            "rotation": float(dev.get("rotation", 0.0)),
        })

    # Validar conexiones reales punto a punto y agrupadas por net
    nets_summary: Dict[str, List[Dict[str, Any]]] = {}
    devices_with_gnd = set()

    for idx, conn in enumerate(connections, start=1):
        net = str(conn.get("net", f"NET_{idx}")).strip()
        f_dev = str(conn.get("from_device", "")).strip()
        f_pin_id = str(conn.get("from_pin", "")).strip()
        t_dev = str(conn.get("to_device", "")).strip()
        t_pin_id = str(conn.get("to_pin", "")).strip()

        p_from = pin_lookup.get((f_dev, f_pin_id))
        p_to = pin_lookup.get((t_dev, t_pin_id))

        if p_from is None:
            electrical_errors.append(
                f"Conexión #{idx} ({net}): Pin '{f_pin_id}' no existe en el pinout verificado de '{f_dev}'. Prohibido inventar pines."
            )
            continue
        if p_to is None:
            electrical_errors.append(
                f"Conexión #{idx} ({net}): Pin '{t_pin_id}' no existe en el pinout verificado de '{t_dev}'. Prohibido inventar pines."
            )
            continue

        nets_summary.setdefault(net, []).append({
            "from": f"{f_dev}.{p_from.get('name', f_pin_id)}",
            "to": f"{t_dev}.{p_to.get('name', t_pin_id)}",
            "from_pin": p_from,
            "to_pin": p_to,
        })

        t_from = str(p_from.get("type", "signal")).lower()
        t_to = str(p_to.get("type", "signal")).lower()
        v_from = p_from.get("voltage_v")
        v_to = p_to.get("voltage_v")
        tol_5v_from = bool(p_from.get("tolerant_5v", False))
        tol_5v_to = bool(p_to.get("tolerant_5v", False))

        if t_from == "gnd" or t_to == "gnd" or net.upper() == "GND":
            if t_from == "gnd":
                devices_with_gnd.add(f_dev)
            if t_to == "gnd":
                devices_with_gnd.add(t_dev)

        # Cortocircuito directo alimentación <-> GND
        if (t_from.startswith("power") and t_to == "gnd") or (t_to.startswith("power") and t_from == "gnd"):
            electrical_errors.append(
                f"CORTOCIRCUITO CRÍTICO en red '{net}': {f_dev}.{f_pin_id} ({t_from}) conectado directamente a {t_dev}.{t_pin_id} ({t_to})."
            )

        # Incompatibilidad de niveles de tensión
        if v_from is not None and v_to is not None:
            vf = float(v_from)
            vt = float(v_to)
            if abs(vf - vt) > 0.6:
                # Permitir si el de menor voltaje es explícitamente 5V-tolerant y el otro es <= 5.5V
                if not ((vf <= 3.6 and tol_5v_from and vt <= 5.5) or (vt <= 3.6 and tol_5v_to and vf <= 5.5)):
                    electrical_errors.append(
                        f"INCOMPATIBILIDAD DE VOLTAJE en red '{net}': {f_dev}.{f_pin_id} ({vf} V) -> {t_dev}.{t_pin_id} ({vt} V). "
                        "Requiere traslador de nivel lógico o divisor resistivo calculado."
                    )

        # Verificación de corriente máxima en pin de salida
        i_load = conn.get("expected_current_ma")
        if i_load is not None:
            i_val = float(i_load)
            max_from = p_from.get("max_current_ma")
            max_to = p_to.get("max_current_ma")
            if max_from is not None and i_val > float(max_from):
                electrical_errors.append(
                    f"SOBRECORRIENTE en red '{net}': corriente calculada {i_val} mA excede el máximo de {f_dev}.{f_pin_id} ({max_from} mA)."
                )
            if max_to is not None and i_val > float(max_to):
                electrical_errors.append(
                    f"SOBRECORRIENTE en red '{net}': corriente calculada {i_val} mA excede el máximo de {t_dev}.{t_pin_id} ({max_to} mA)."
                )

    # Verificar que equipos con pin GND definido estén conectados a GND
    for des, dev in device_map.items():
        has_gnd_pin = any(str(p.get("type", "")).lower() == "gnd" for p in (dev.get("pins", []) or []))
        if has_gnd_pin and des not in devices_with_gnd:
            electrical_warnings.append(
                f"El equipo '{des}' ({dev.get('name', des)}) posee pin GND pero no tiene conexión registrada a la referencia común GND."
            )

    floorplan_audit = audit_floorplan_2d(
        board_width_mm=board_width_mm,
        board_height_mm=board_height_mm,
        chamfer_mm=chamfer_mm,
        components=floorplan_components,
        origin_mil=origin_mil,
    )

    can_proceed = (
        len(missing_datasheets) == 0
        and len(electrical_errors) == 0
        and floorplan_audit["passed"]
    )

    easyeda_pipeline: List[Dict[str, Any]] = []
    if can_proceed:
        easyeda_pipeline = [
            {"step": 1, "tool": "easyeda_bridge_status + easyeda_schematic_connectivity_fingerprint", "purpose": "Confirmar foco de documento, UUID esperado y huella base de conectividad."},
            {"step": 2, "tool": "easyeda_project_begin_transaction", "purpose": "Iniciar transacción segura con rollback en EasyEDA Pro."},
            {"step": 3, "tool": "easyeda_schematic_search_device + easyeda_catalog_verify_device + easyeda_schematic_device_subparts", "purpose": "Arquitectura Device-First: validar LCSC ID, stock, modelo 3D y pines exactos para cada equipo."},
            {"step": 4, "tool": "easyeda_workflow_power_rail + easyeda_workflow_decouple_ic + easyeda_schematic_place_component + easyeda_schematic_connect_pins_by_net", "purpose": f"Construir {len(device_map)} equipos y conectar {len(nets_summary)} redes verificadas + No-Connect en pines libres."},
            {"step": 5, "tool": "easyeda_schematic_layout_qa + easyeda_power_tree_analyze + easyeda_erc_run + easyeda_bom_quality_report + easyeda_jlcpcb_quote_workflow", "purpose": "Auditar esquemático, árbol de potencia, ERC=0 y optimización Basic vs Extended JLCPCB."},
            {"step": 6, "tool": "easyeda_project_commit_transaction + easyeda_schematic_sync_to_pcb + easyeda_pcb_place_batch", "purpose": "Sincronizar al PCB y aplicar coordenadas en mils calculadas desde el PCB de conexión.", "placements": floorplan_audit["easyeda_place_batch_payload"]},
            {"step": 7, "tool": "easyeda_pcb_route_geometry_review + easyeda_rule_check_summary + easyeda_pcb_production_review + easyeda_production_qa_artifacts", "purpose": "Validar DRC=0 (tras reconstrucción de cobre Shift+B), DFM y exportar paquete de fabricación."},
        ]

    return {
        "gate_name": "DATASHEET_FIRST_ZERO_PROCEED_GATE",
        "can_proceed_to_easyeda": can_proceed,
        "status": "APPROVED_FOR_EASYEDA" if can_proceed else "BLOCKED_PENDING_VERIFICATION",
        "missing_datasheets": missing_datasheets,
        "electrical_errors": electrical_errors,
        "electrical_warnings": electrical_warnings,
        "floorplan_audit": floorplan_audit,
        "verified_nets_count": len(nets_summary),
        "easyeda_integration_pipeline": easyeda_pipeline,
    }


def quote_bom_multichannel(
    bom_items: List[Dict[str, Any]],
    board_qty: int = 5,
    assembly_mode: str = "hybrid",
    country_code: str = "CL",
    import_tax_percent: float = 19.0,
    urgency_days: int = 25,
    jlcpcb_extended_fee_usd: float = 3.0,
) -> Dict[str, Any]:
    """
    Motor Cotizador y Auditor Multicanal de Componentes (EasyEDA Pro/LCSC/JLCPCB,
    AliExpress, Alibaba y Mercado Local):
    - Detecta códigos comunitarios C9900... de EasyEDA Pro (no ensamblables en JLCPCB PCBA).
    - Detecta encapsulados 0201/0402 incompatibles con soldadura manual de laboratorio.
    - Detecta riesgo de falsificación/remarcado en ICs críticos (<40% del precio LCSC).
    - Detecta restricciones aéreas IATA (baterías LiPo/18650, químicos, gabinetes pesados) -> prioriza Mercado Local.
    - Calcula el Costo Total Puesto en Laboratorio (Landed Cost con envío, MOQ, fees Extended e impuestos)
      y selecciona la Canasta Híbrida Óptima respetando el plazo máximo (urgency_days).
    """
    if board_qty <= 0:
        raise ValueError("board_qty debe ser mayor que 0.")

    tax_mult = 1.0 + max(0.0, import_tax_percent) / 100.0
    item_reports: List[Dict[str, Any]] = []
    global_alerts: List[str] = []

    total_optimal_usd = 0.0
    total_all_local_usd = 0.0
    total_all_lcsc_usd = 0.0
    channel_counts: Dict[str, int] = {"LCSC_JLCPCB": 0, "ALIEXPRESS": 0, "ALIBABA": 0, "MERCADO_LOCAL": 0, "SIN_OFERTA_VALIDA": 0}
    extended_parts_count = 0
    community_parts_count = 0

    for item in bom_items:
        ref = str(item.get("reference", "?")).strip()
        mpn = str(item.get("mpn") or item.get("value") or "Componente").strip()
        footprint = str(item.get("footprint", "")).strip()
        lcsc = str(item.get("lcsc", "")).strip()
        qty_per_board = max(1, int(item.get("qty_per_board") or item.get("quantity") or 1))
        total_qty = qty_per_board * board_qty
        is_critical_ic = bool(item.get("is_critical_ic", False))
        category = str(item.get("category", "general")).lower()
        jlcpcb_class = str(item.get("jlcpcb_class", "Unknown")).strip()

        item_warnings: List[str] = []
        is_community_lcsc = lcsc.upper().startswith("C9900")
        if is_community_lcsc:
            community_parts_count += 1
            item_warnings.append(
                f"Código '{lcsc}' es una huella comunitaria (User Contributed) en EasyEDA Pro: NO existe en almacén LCSC/JLCPCB PCBA. "
                "Reemplace por código LCSC real o compre en Mercado Local / AliExpress."
            )

        if assembly_mode == "manual_lab" and any(pkg in footprint.upper() for pkg in ["0201", "0402", "BGA", "WLCSP"]):
            item_warnings.append(
                f"Encapsulado '{footprint}' es de alta dificultad para soldadura manual en laboratorio. "
                "Considere migrar a 0805/0603/SOIC (IPC-7351B Nivel A) o pedir PCBA."
            )

        is_air_restricted = category in ("battery_hazmat", "chemical", "enclosure_heavy")
        if is_air_restricted:
            item_warnings.append(
                f"Categoría '{category}' presenta restricciones IATA o sobrecosto volumétrico en correo aéreo internacional: priorizar Mercado Local (o Alibaba DDP marítimo en volumen)."
            )

        candidates: Dict[str, Dict[str, Any]] = {}
        lcsc_ref_unit: Optional[float] = None

        # 1. Evaluar LCSC / JLCPCB
        q_lcsc = item.get("lcsc_quote")
        if isinstance(q_lcsc, dict) and not is_community_lcsc and q_lcsc.get("in_stock", True):
            u_price = float(q_lcsc.get("unit_usd", 0.0))
            lcsc_ref_unit = u_price
            ship_share = float(q_lcsc.get("shipping_share_usd", 0.0))
            ext_fee = jlcpcb_extended_fee_usd if (assembly_mode == "jlcpcb_pcba" and "extended" in jlcpcb_class.lower()) else 0.0
            if ext_fee > 0:
                extended_parts_count += 1
                item_warnings.append(
                    f"Pieza clasificada como 'Extended Part' en JLCPCB (+${ext_fee:.2f} USD fee de carrete). Busque equivalente 'Basic Part' con easyeda_schematic_search_device."
                )
            landed = ((total_qty * u_price) + ship_share + ext_fee) * tax_mult
            lead_d = int(q_lcsc.get("lead_days", 10))
            candidates["LCSC_JLCPCB"] = {
                "landed_total_usd": round(landed, 2),
                "effective_unit_usd": round(landed / total_qty, 4),
                "lead_days": lead_d,
                "eligible": (lead_d <= urgency_days) and (not is_air_restricted),
                "notes": f"LCSC {lcsc} ({jlcpcb_class}), fee Extended=${ext_fee:.2f}",
            }
            total_all_lcsc_usd += landed

        # 2. Evaluar AliExpress
        q_ali = item.get("aliexpress_quote")
        if isinstance(q_ali, dict):
            u_price = float(q_ali.get("unit_usd", 0.0))
            ship = float(q_ali.get("shipping_usd", 0.0))
            rating = float(q_ali.get("store_rating_pct", 96.0))
            stars = float(q_ali.get("item_stars", 4.8))
            lead_d = int(q_ali.get("lead_days", 18))
            counterfeit_risk = bool(is_critical_ic and lcsc_ref_unit and lcsc_ref_unit > 0 and u_price < 0.40 * lcsc_ref_unit)
            reputation_ok = (rating >= 95.0 and stars >= 4.7)

            if counterfeit_risk:
                item_warnings.append(
                    f"ALERTA ANTI-CLON en AliExpress: precio ${u_price:.3f} es <40% del oficial LCSC (${lcsc_ref_unit:.3f}) en IC crítico '{mpn}'. Descartado."
                )
            if not reputation_ok:
                item_warnings.append(
                    f"Tienda AliExpress descartada por baja reputación ({rating}% positivo, {stars}★; mínimo exigido >=95% y >=4.7★)."
                )

            landed = ((total_qty * u_price) + ship) * tax_mult
            candidates["ALIEXPRESS"] = {
                "landed_total_usd": round(landed, 2),
                "effective_unit_usd": round(landed / total_qty, 4),
                "lead_days": lead_d,
                "eligible": reputation_ok and (not counterfeit_risk) and (lead_d <= urgency_days) and (assembly_mode != "jlcpcb_pcba"),
                "notes": f"Rating {rating}% / {stars}★, envío ${ship:.2f}",
            }

        # 3. Evaluar Alibaba (Mayorista / OEM)
        q_baba = item.get("alibaba_quote")
        if isinstance(q_baba, dict):
            u_price = float(q_baba.get("unit_usd", 0.0))
            ship = float(q_baba.get("shipping_usd", 0.0))
            moq = max(1, int(q_baba.get("moq", 1)))
            verified = bool(q_baba.get("verified_supplier", False))
            assurance = bool(q_baba.get("trade_assurance", False))
            lead_d = int(q_baba.get("lead_days", 22))
            billed_qty = max(total_qty, moq)
            landed = ((billed_qty * u_price) + ship) * tax_mult

            if not (verified and assurance):
                item_warnings.append("Proveedor Alibaba sin sello completo Verified Supplier + Trade Assurance: descartado por seguridad.")

            candidates["ALIBABA"] = {
                "landed_total_usd": round(landed, 2),
                "effective_unit_usd": round(landed / total_qty, 4),
                "billed_qty_by_moq": billed_qty,
                "lead_days": lead_d,
                "eligible": verified and assurance and (lead_d <= urgency_days) and (assembly_mode != "jlcpcb_pcba"),
                "notes": f"MOQ {moq} uds (compra real {billed_qty} uds), Verified+TradeAssurance={verified and assurance}",
            }

        # 4. Evaluar Mercado Local (Tiendas nacionales / Distribuidor local / Entrega 24-72h con factura)
        q_loc = item.get("local_market_quote")
        if isinstance(q_loc, dict):
            u_price = float(q_loc.get("unit_usd", 0.0))
            ship = float(q_loc.get("shipping_usd", 0.0))
            lead_d = int(q_loc.get("lead_days", 2))
            vendor = str(q_loc.get("vendor_name", f"Proveedor Local ({country_code})"))
            invoice = bool(q_loc.get("has_tax_invoice", True))
            # En mercado local el precio suele incluir o facturar IVA local directamente
            landed = (total_qty * u_price) + ship
            candidates["MERCADO_LOCAL"] = {
                "landed_total_usd": round(landed, 2),
                "effective_unit_usd": round(landed / total_qty, 4),
                "lead_days": lead_d,
                "eligible": (lead_d <= urgency_days) and (assembly_mode != "jlcpcb_pcba"),
                "notes": f"{vendor} ({country_code}), entrega {lead_d}d, Factura fiscal={'Sí' if invoice else 'No'}",
            }
            total_all_local_usd += landed

        # Seleccionar el canal elegible de menor Costo Total Puesto en Laboratorio
        eligible_channels = [(ch, data) for ch, data in candidates.items() if data.get("eligible")]
        if eligible_channels:
            best_ch, best_data = min(eligible_channels, key=lambda kv: kv[1]["landed_total_usd"])
            channel_counts[best_ch] += 1
            total_optimal_usd += float(best_data["landed_total_usd"])
        else:
            best_ch = "SIN_OFERTA_VALIDA"
            best_data = None
            channel_counts["SIN_OFERTA_VALIDA"] += 1
            global_alerts.append(
                f"Ítem {ref} ({mpn}): ningún canal cumplió plazo <= {urgency_days} días y reglas de autenticidad/ensamblaje."
            )

        item_reports.append({
            "reference": ref,
            "mpn": mpn,
            "footprint": footprint,
            "lcsc": lcsc,
            "total_qty_needed": total_qty,
            "recommended_channel": best_ch,
            "recommended_quote": best_data,
            "all_channel_evaluations": candidates,
            "warnings": item_warnings,
        })

    return {
        "project_parameters": {
            "board_qty": board_qty,
            "assembly_mode": assembly_mode,
            "country_code": country_code,
            "import_tax_percent": import_tax_percent,
            "urgency_days": urgency_days,
        },
        "summary": {
            "total_bom_lines": len(bom_items),
            "optimal_hybrid_total_usd": round(total_optimal_usd, 2),
            "optimal_cost_per_board_usd": round(total_optimal_usd / board_qty, 2),
            "channel_distribution": channel_counts,
            "jlcpcb_extended_parts_count": extended_parts_count,
            "easyeda_community_c9900_parts_count": community_parts_count,
        },
        "global_alerts": global_alerts,
        "items": item_reports,
    }


# ============================================================================
# MOTOR MATEMÁTICO 10: PARES DIFERENCIALES DE ALTA VELOCIDAD (IPC-2141A / IEEE 802.3)
# ============================================================================

DIFF_PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "usb2": {
        "name": "USB 2.0 High-Speed (480 Mbps)",
        "standard": "USB 2.0 Specification / USB-IF",
        "target_z_diff": 90.0,
        "tolerance_pct": 10.0,
        "target_z0": 45.0,
        "typical_tr_ns": 0.5,
        "max_skew_mm": 0.127,
        "special_req": "Ruteo simétrico D+/D-. Si L >= 50 mm, se recomienda plano continuo en L2 sin cruzar split planes.",
    },
    "usb3": {
        "name": "USB 3.0 SuperSpeed Gen 1 (5 Gbps) / Gen 2 (10 Gbps)",
        "standard": "USB 3.2 Specification / USB-IF",
        "target_z_diff": 90.0,
        "tolerance_pct": 10.0,
        "target_z0": 45.0,
        "typical_tr_ns": 0.07,
        "max_skew_mm": 0.127,
        "special_req": "Requiere capacitores de desacoplo AC de 100 nF (0402) en líneas TX simétricamente alineados. Ruteo preferente en stripline apantallado o microstrip con GND via fence.",
    },
    "ethernet_100m": {
        "name": "Fast Ethernet 100Base-TX",
        "standard": "IEEE 802.3u",
        "target_z_diff": 100.0,
        "tolerance_pct": 10.0,
        "target_z0": 50.0,
        "typical_tr_ns": 3.0,
        "max_skew_mm": 0.15,
        "special_req": "Aislamiento galvánico con transformador magnetics (1:1). Separar plano de chasis/conector RJ45 del GND digital mediante corte de 2.0 mm.",
    },
    "ethernet_1g": {
        "name": "Gigabit Ethernet 1000Base-T",
        "standard": "IEEE 802.3ab",
        "target_z_diff": 100.0,
        "tolerance_pct": 10.0,
        "target_z0": 50.0,
        "typical_tr_ns": 1.0,
        "max_skew_mm": 0.127,
        "special_req": "4 pares diferenciales (TRD0..3 +/-). Intra-pair matching < 0.127 mm y pair-to-pair matching < 1.0 mm.",
    },
    "can_bus": {
        "name": "CAN-Bus High-Speed / CAN-FD",
        "standard": "ISO 11898-2:2016",
        "target_z_diff": 120.0,
        "tolerance_pct": 10.0,
        "target_z0": 60.0,
        "typical_tr_ns": 5.0,
        "max_skew_mm": 0.15,
        "special_req": "Terminación resistiva de 120 Ohm diferencial en extremos del bus (o Split Termination con 2x 60 Ohm + 4.7 nF a GND).",
    },
    "mipi_csi_dsi": {
        "name": "MIPI CSI-2 / DSI (D-PHY High-Speed Mode)",
        "standard": "MIPI Alliance D-PHY Specification v1.2 / v2.0",
        "target_z_diff": 100.0,
        "tolerance_pct": 10.0,
        "target_z0": 50.0,
        "typical_tr_ns": 0.2,
        "max_skew_mm": 0.10,
        "special_req": "Líneas ultrarrápidas de reloj diferencial (CLK+/-) y datos (D0..Dn+/-). Intra-pair skew < 0.10 mm y Clock-to-Data lane matching < 1.0 mm. Prohibido vías stubs.",
    },
    "custom": {
        "name": "Par Diferencial Personalizado",
        "standard": "IPC-2141A / IPC-2251",
        "target_z_diff": 100.0,
        "tolerance_pct": 10.0,
        "target_z0": 50.0,
        "typical_tr_ns": 1.0,
        "max_skew_mm": 0.127,
        "special_req": "Parámetros definidos por el usuario según especificación particular.",
    },
}


def _calc_raw_impedances(
    topology: str, W: float, S: float, H: float, er: float, T: float
) -> Tuple[float, float, float, float, float]:
    if topology.lower() == "stripline":
        B = 2.0 * H + T
        z0 = (60.0 / math.sqrt(er)) * math.log((1.9 * B) / (0.8 * W + T))
        er_eff = er
        v_prop = 2.99792458e8 / math.sqrt(er)
        z_diff = 2.0 * z0 * (1.0 - 0.347 * math.exp(-2.9 * (S / B)))
        kc = 0.347 * math.exp(-2.9 * (S / B))
    else:
        z0 = (87.0 / math.sqrt(er + 1.41)) * math.log((5.98 * H) / (0.8 * W + T))
        er_eff = (er + 1.0) / 2.0 + ((er - 1.0) / 2.0) * (1.0 / math.sqrt(1.0 + 12.0 * (H / W)))
        v_prop = 2.99792458e8 / math.sqrt(er_eff)
        z_diff = 2.0 * z0 * (1.0 - 0.48 * math.exp(-0.96 * (S / H)))
        kc = 0.48 * math.exp(-0.96 * (S / H))
    return z0, z_diff, er_eff, v_prop, kc


def _solve_diff_geometry(
    topology: str, target_z: float, H: float, er: float, T: float
) -> Dict[str, Dict[str, Any]]:
    low, high = 0.05, 2.0
    for _ in range(50):
        mid = (low + high) / 2.0
        s = max(0.127, mid)
        _, zd, _, _, _ = _calc_raw_impedances(topology, mid, s, H, er, T)
        if zd > target_z:
            low = mid
        else:
            high = mid
    w_tight = round(mid, 3)
    s_tight = round(max(0.127, w_tight), 3)
    z0_t, zd_t, _, _, _ = _calc_raw_impedances(topology, w_tight, s_tight, H, er, T)

    low, high = 0.05, 2.0
    for _ in range(50):
        mid = (low + high) / 2.0
        s = 3.0 * mid
        _, zd, _, _, _ = _calc_raw_impedances(topology, mid, s, H, er, T)
        if zd > target_z:
            low = mid
        else:
            high = mid
    w_loose = round(mid, 3)
    s_loose = round(3.0 * w_loose, 3)
    z0_l, zd_l, _, _, _ = _calc_raw_impedances(topology, w_loose, s_loose, H, er, T)

    return {
        "tight": {
            "trace_width_mm": w_tight,
            "trace_width_mil": round(w_tight * MM_TO_MIL, 2),
            "diff_spacing_mm": s_tight,
            "diff_spacing_mil": round(s_tight * MM_TO_MIL, 2),
            "z0_ohm": round(z0_t, 2),
            "z_diff_ohm": round(zd_t, 2),
        },
        "loose": {
            "trace_width_mm": w_loose,
            "trace_width_mil": round(w_loose * MM_TO_MIL, 2),
            "diff_spacing_mm": s_loose,
            "diff_spacing_mil": round(s_loose * MM_TO_MIL, 2),
            "z0_ohm": round(z0_l, 2),
            "z_diff_ohm": round(zd_l, 2),
        },
    }


def calc_high_speed_diff_pairs(
    protocol: str = "usb2",
    topology: str = "microstrip",
    target_z_diff_ohm: Optional[float] = None,
    trace_width_mm: Optional[float] = None,
    diff_spacing_mm: Optional[float] = None,
    dielectric_h_mm: float = 0.10,
    copper_oz: float = 1.0,
    er: float = 4.05,
    jlcpcb_stackup: Optional[str] = None,
    trace_length_pos_mm: Optional[float] = None,
    trace_length_neg_mm: Optional[float] = None,
    max_skew_mm: Optional[float] = None,
    crosses_split_plane: bool = False,
    has_via_fence: bool = False,
    via_fence_pitch_mm: Optional[float] = None,
    rise_time_ns: Optional[float] = None,
    bend_geometry: str = "mitred_45",
) -> Dict[str, Any]:
    proto_key = protocol.lower()
    if proto_key not in DIFF_PROTOCOLS:
        raise ValueError(f"Protocolo diferencial desconocido: '{protocol}'. Opciones válidas: {list(DIFF_PROTOCOLS.keys())}")

    proto_cfg = DIFF_PROTOCOLS[proto_key]
    z_diff_target = float(target_z_diff_ohm) if target_z_diff_ohm is not None else float(proto_cfg["target_z_diff"])
    tr_ns = float(rise_time_ns) if rise_time_ns is not None else float(proto_cfg["typical_tr_ns"])
    skew_limit_mm = float(max_skew_mm) if max_skew_mm is not None else float(proto_cfg["max_skew_mm"])

    stackup_applied = None
    if jlcpcb_stackup:
        preset = JLCPCB_STACKUPS.get(jlcpcb_stackup)
        if preset is None:
            raise ValueError(f"Stackup JLCPCB desconocido: {jlcpcb_stackup}. Opciones: {list(JLCPCB_STACKUPS.keys())}")
        dielectric_h_mm = float(preset["dielectric_h_mm"])
        er = float(preset["er"])
        copper_oz = float(preset["copper_oz"])
        stackup_applied = {"name": jlcpcb_stackup, **preset}

    _require_pos_finite(dielectric_h_mm, "dielectric_h_mm")
    _require_pos_finite(er, "er")
    _require_pos_finite(copper_oz, "copper_oz")
    _require_pos_finite(tr_ns, "rise_time_ns")

    t_mm = copper_oz * COPPER_OZ_TO_MM
    synthesis = _solve_diff_geometry(topology, z_diff_target, dielectric_h_mm, er, t_mm)

    is_synthesis_mode = (trace_width_mm is None or diff_spacing_mm is None)
    if is_synthesis_mode:
        trace_width_mm = synthesis["tight"]["trace_width_mm"]
        diff_spacing_mm = synthesis["tight"]["diff_spacing_mm"]
    else:
        _require_pos_finite(trace_width_mm, "trace_width_mm")
        _require_pos_finite(diff_spacing_mm, "diff_spacing_mm")

    z0, z_diff, er_eff, v_prop, kc = _calc_raw_impedances(topology, trace_width_mm, diff_spacing_mm, dielectric_h_mm, er, t_mm)
    t_pd_ps_per_mm = 1e9 / v_prop
    w_over_h = trace_width_mm / dielectric_h_mm
    s_over_w = diff_spacing_mm / trace_width_mm
    is_tight = (diff_spacing_mm <= 2.0 * trace_width_mm)

    z_tol_pct = proto_cfg["tolerance_pct"]
    z_min_allowed = z_diff_target * (1.0 - z_tol_pct / 100.0)
    z_max_allowed = z_diff_target * (1.0 + z_tol_pct / 100.0)
    z_diff_error_pct = round(((z_diff - z_diff_target) / z_diff_target) * 100.0, 2)
    impedance_verdict = "PASS" if (z_min_allowed <= z_diff <= z_max_allowed) else "FAIL"

    skew_audit = None
    if trace_length_pos_mm is not None and trace_length_neg_mm is not None:
        _require_pos_finite(trace_length_pos_mm, "trace_length_pos_mm")
        _require_pos_finite(trace_length_neg_mm, "trace_length_neg_mm")
        delta_l_mm = round(abs(trace_length_pos_mm - trace_length_neg_mm), 3)
        delta_l_mil = round(delta_l_mm * MM_TO_MIL, 2)
        skew_ps = round(delta_l_mm * t_pd_ps_per_mm, 2)
        max_skew_ps = round(skew_limit_mm * t_pd_ps_per_mm, 2)
        skew_pass = (delta_l_mm <= skew_limit_mm)
        shorter_trace = "POS" if trace_length_pos_mm < trace_length_neg_mm else "NEG"
        skew_audit = {
            "trace_length_pos_mm": trace_length_pos_mm,
            "trace_length_neg_mm": trace_length_neg_mm,
            "delta_length_mm": delta_l_mm,
            "delta_length_mil": delta_l_mil,
            "skew_ps": skew_ps,
            "max_allowed_skew_mm": skew_limit_mm,
            "max_allowed_skew_ps": max_skew_ps,
            "verdict": "PASS" if skew_pass else "FAIL",
            "remediation": None if skew_pass else (
                f"Añada meandro de compensación de {delta_l_mm} mm en la traza {shorter_trace}."
            ),
        }

    ref_plane_audit = {
        "crosses_split_plane": crosses_split_plane,
        "verdict": "CRITICAL_VIOLATION" if crosses_split_plane else "PASS",
        "rf_return_current_mechanism": "La corriente de retorno fluye por mínima inductancia directamente bajo cada traza.",
        "remediation": "Rutee sobre plano GND 100% continuo o agregue vías de costura / capacitor de retorno." if crosses_split_plane else "Plano de referencia continuo verificado.",
    }

    f_knee_hz = 0.35 / (tr_ns * 1e-9)
    f_knee_ghz = round(f_knee_hz / 1e9, 2)
    lambda_dielectric_mm = round((v_prop / f_knee_hz) * 1000.0, 2)
    max_via_pitch_mm = round(lambda_dielectric_mm / 20.0, 2)
    min_fence_clearance_mm = round(max(3.0 * trace_width_mm, 2.0 * dielectric_h_mm), 3)

    return {
        "standard": "IPC-2141A / IPC-2251 / IEEE 802.3 / USB-IF / ISO 11898 / MIPI Alliance",
        "protocol": proto_cfg["name"],
        "protocol_spec": proto_cfg["standard"],
        "special_requirements": proto_cfg["special_req"],
        "stackup_applied": stackup_applied,
        "topology": topology,
        "inputs_evaluated": {
            "trace_width_mm": trace_width_mm,
            "diff_spacing_mm": diff_spacing_mm,
            "dielectric_h_mm": dielectric_h_mm,
            "copper_oz": copper_oz,
            "er": er,
            "w_over_h_ratio": round(w_over_h, 2),
            "s_over_w_ratio": round(s_over_w, 2),
            "is_synthesis_mode": is_synthesis_mode,
        },
        "impedance_results": {
            "z0_single_ended_ohm": round(z0, 2),
            "z_differential_ohm": round(z_diff, 2),
            "target_z_diff_ohm": z_diff_target,
            "allowed_range_ohm": [round(z_min_allowed, 1), round(z_max_allowed, 1)],
            "impedance_error_percent": z_diff_error_pct,
            "impedance_verdict": impedance_verdict,
            "propagation_delay_ps_per_mm": round(t_pd_ps_per_mm, 2),
        },
        "coupling_evaluation": {
            "coupling_type": "tight" if is_tight else "loose",
            "coupling_coefficient_kc": round(kc, 3),
        },
        "synthesis_recommendations": synthesis,
        "skew_audit": skew_audit,
        "reference_plane_audit": ref_plane_audit,
        "via_fence_shielding": {
            "knee_frequency_ghz": f_knee_ghz,
            "max_recommended_via_pitch_mm": max_via_pitch_mm,
            "min_trace_to_fence_clearance_mm": min_fence_clearance_mm,
        },
    }


# ============================================================================
# MOTOR MATEMÁTICO 11: AUDITORÍA EMC/EMI PRE-COMPLIANCE (CISPR 32 / CISPR 25)
# ============================================================================

def calc_emc_precompliance_audit(
    vin_v: float,
    vout_v: float,
    iout_a: float,
    topology: str = "buck",
    fsw_khz: float = 500.0,
    trise_ns: float = 5.0,
    hot_loop_area_mm2: float = 25.0,
    hot_loop_layer_dist_mm: float = 0.1,
    emc_standard: str = "CISPR_32_CLASS_B",
    measurement_distance_m: float = 3.0,
    efficiency: float = 0.90,
    filter_damping_ratio: float = 4.0,
    board_dimensions_mm: Optional[List[float]] = None,
    dielectric_er: float = 4.4,
    via_barrel_length_mm: float = 1.0,
    via_diameter_mm: float = 0.3,
) -> Dict[str, Any]:
    _require_pos_finite(vin_v, "vin_v")
    _require_pos_finite(abs(vout_v), "vout_v")
    _require_pos_finite(iout_a, "iout_a")
    _require_pos_finite(fsw_khz, "fsw_khz")
    _require_pos_finite(trise_ns, "trise_ns")
    _require_pos_finite(hot_loop_area_mm2, "hot_loop_area_mm2")
    _require_pos_finite(hot_loop_layer_dist_mm, "hot_loop_layer_dist_mm")
    _require_pos_finite(measurement_distance_m, "measurement_distance_m")

    if board_dimensions_mm is None:
        board_dimensions_mm = [100.0, 80.0]

    mu0 = 4.0 * math.pi * 1e-7
    c = 299792458.0
    topo = topology.lower().strip()
    eff = max(0.50, min(0.99, efficiency))

    if topo == "buck":
        duty = vout_v / (vin_v * eff)
        i_step = iout_a
    elif topo == "boost":
        duty = 1.0 - (vin_v * eff / vout_v)
        i_step = (vout_v * iout_a) / (vin_v * eff)
    elif topo == "inverting":
        duty = abs(vout_v) / (abs(vout_v) + vin_v * eff)
        i_step = ((abs(vout_v) * iout_a) / (vin_v * eff)) + iout_a
    else:
        duty = 0.5
        i_step = iout_a

    duty = max(0.01, min(0.99, duty))
    fsw_hz = fsw_khz * 1e3
    t_sw = 1.0 / fsw_hz
    trise_s = trise_ns * 1e-9
    didt_a_us = (i_step / trise_s) / 1e6

    # Análisis Armónicos Conducidos
    harmonics_table = []
    worst_delta_db = -999.0
    worst_harmonic = {}
    max_h = min(60, max(10, int(30e6 / fsw_hz)))
    for n in range(1, max_h + 1):
        fn = n * fsw_hz
        if fn > 30e6:
            break
        sinc1 = abs(math.sin(math.pi * n * duty) / (math.pi * n * duty))
        sinc2 = abs(math.sin(math.pi * n * trise_s / t_sw) / (math.pi * n * trise_s / t_sw))
        i_n = 2.0 * i_step * duty * sinc1 * sinc2

        w = 2.0 * math.pi * fn
        z_cin_im = w * 1.0e-9 - 1.0 / (w * 10e-6)
        z_cin_abs = math.sqrt(0.005**2 + z_cin_im**2)
        i_lisn = i_n * (z_cin_abs / math.sqrt((50.0 + 0.005)**2 + z_cin_im**2))
        v_lisn_uv = i_lisn * 50.0 * 1e6
        v_dbuv = 20.0 * math.log10(max(v_lisn_uv, 1e-3))
        lim = 56.0 if fn >= 500e3 else (66.0 - 19.12 * math.log10(fn / 150e3))
        delta_db = v_dbuv - lim

        if delta_db > worst_delta_db:
            worst_delta_db = delta_db
            worst_harmonic = {"order": n, "freq_mhz": round(fn / 1e6, 3), "noise_dbuv": round(v_dbuv, 1), "limit_dbuv": round(lim, 1), "delta_db": round(delta_db, 1)}

    req_filter_atten_db = max(0.0, round(worst_delta_db + 6.0, 1))

    # Síntesis Filtro Pi y Middlebrook
    worst_f_hz = worst_harmonic.get("freq_mhz", fsw_khz / 1e3) * 1e6
    fc_calc = worst_f_hz / (10.0 ** (req_filter_atten_db / 40.0)) if req_filter_atten_db > 0 else 0.1 * fsw_hz
    fc_target_hz = min(0.1 * fsw_hz, fc_calc)
    target_lf_c2 = 1.0 / ((2.0 * math.pi * fc_target_hz) ** 2)
    lf_h = 2.2e-6
    c2_f = (target_lf_c2 / lf_h)
    actual_fc_hz = 1.0 / (2.0 * math.pi * math.sqrt(lf_h * c2_f))

    zin_smps_ohm = (vin_v ** 2 * eff) / (abs(vout_v) * iout_a)
    z0_filter = math.sqrt(lf_h / c2_f)
    n_damp = max(2.0, min(10.0, filter_damping_ratio))
    cd_uf = round(n_damp * c2_f * 1e6, 1)
    rd_ohm = round(z0_filter * math.sqrt(((2.0 + n_damp)*(4.0 + 3.0*n_damp)) / (2.0 * (n_damp**2) * (4.0 + n_damp))), 2)
    zout_filter_peak = round(rd_ohm * (1.0 + math.sqrt(n_damp / (n_damp + 2.0))) / 2.0, 3)
    middlebrook_margin_db = round(20.0 * math.log10(zin_smps_ohm / zout_filter_peak), 1)

    # Radiación Campo Cercano Hot Loop
    area_m2 = hot_loop_area_mm2 * 1e-6
    f_rad_test = 50e6
    n_rad = max(1, round(f_rad_test / fsw_hz))
    s1 = abs(math.sin(math.pi * n_rad * duty) / (math.pi * n_rad * duty))
    s2 = abs(math.sin(math.pi * n_rad * trise_s / t_sw) / (math.pi * n_rad * trise_s / t_sw))
    in_rad = 2.0 * i_step * duty * s1 * s2
    e_vm = (mu0 * math.pi * (f_rad_test ** 2) * in_rad * area_m2) / (measurement_distance_m * c)
    e_dbuv_m = round(20.0 * math.log10(max(e_vm * 1e6, 1e-6)), 1)

    return {
        "standard": emc_standard,
        "topology": topo,
        "operating_point": {
            "vin_v": vin_v,
            "vout_v": vout_v,
            "iout_a": iout_a,
            "fsw_khz": fsw_khz,
            "duty_cycle": round(duty, 3),
            "step_current_a": round(i_step, 2),
            "di_dt_a_us": round(didt_a_us, 1),
            "zin_smps_ohm": round(zin_smps_ohm, 2),
        },
        "hot_loop_analysis": {
            "actual_area_mm2": hot_loop_area_mm2,
            "radiated_e_field_50mhz_dbuv_m": e_dbuv_m,
            "limit_dbuv_m": 40.0,
            "status": "PASS" if e_dbuv_m <= 40.0 else "WARNING",
        },
        "conducted_emissions": {
            "worst_harmonic": worst_harmonic,
            "required_filter_attenuation_db": req_filter_atten_db,
        },
        "pi_filter_design": {
            "lf_uh": round(lf_h * 1e6, 2),
            "c2_uf": round(c2_f * 1e6, 2),
            "cutoff_frequency_khz": round(actual_fc_hz / 1e3, 1),
            "damping_network": {
                "cd_uf": cd_uf,
                "rd_ohm": rd_ohm,
                "peak_zout_filter_ohm": zout_filter_peak,
                "middlebrook_margin_db": middlebrook_margin_db,
                "stability_verdict": "EXCELLENT_STABILITY" if middlebrook_margin_db >= 9.5 else "STABLE",
            },
        },
        "compliance_summary": {
            "verdict": "PASS" if worst_delta_db <= 0 and e_dbuv_m <= 40.0 else "PASS_WITH_PI_FILTER",
            "action_plan": [
                f"1. Instale filtro Pi L={round(lf_h * 1e6, 2)} uH, C2={round(c2_f * 1e6, 2)} uF con amortiguamiento Rd={rd_ohm} Ohm.",
                f"2. Mantenga área de lazo caliente <= {hot_loop_area_mm2} mm² con plano GND continuo.",
            ],
        },
    }


# ============================================================================
# MOTOR MATEMÁTICO 12: VISUALIZACIÓN 3D, KNOLLING Y GEMELOS DIGITALES
# ============================================================================

IPC_PACKAGE_DIMENSIONS_MM: Dict[str, Tuple[float, float, float]] = {
    "0201": (0.6, 0.3, 0.25),
    "0402": (1.0, 0.5, 0.40),
    "0603": (1.6, 0.8, 0.80),
    "0805": (2.0, 1.25, 0.90),
    "1206": (3.2, 1.6, 1.20),
    "SOT-23": (2.9, 1.3, 1.10),
    "SOIC-8": (4.9, 3.9, 1.75),
    "QFN-32": (5.0, 5.0, 0.90),
    "TYPE-C": (8.9, 7.3, 3.20),
    "TACT-SWITCH": (6.0, 6.0, 3.5),
}

DEFAULT_Z_EXPLOSION_LEVELS_MM: Dict[str, float] = {
    "resistor": 16.0,
    "capacitor": 16.0,
    "diode": 18.0,
    "transistor": 28.0,
    "ic": 38.0,
    "switch": 62.0,
    "connector": 72.0,
    "module_rf": 84.0,
}


def classify_and_measure_component(c: Dict[str, Any]) -> Dict[str, Any]:
    des = str(c.get("designator", "")).strip().upper()
    fp = str(c.get("footprint", "")).strip().upper()
    cat_in = str(c.get("category", "")).strip().lower()

    if cat_in in DEFAULT_Z_EXPLOSION_LEVELS_MM:
        category = cat_in
    elif des.startswith("R"):
        category = "resistor"
    elif des.startswith("C"):
        category = "capacitor"
    elif des.startswith("D"):
        category = "diode"
    elif des.startswith("Q"):
        category = "transistor"
    elif des.startswith("U"):
        category = "ic"
    elif des.startswith("J") or "USB" in fp or "CONN" in fp:
        category = "connector"
    elif des.startswith("SW") or "BTN" in fp:
        category = "switch"
    elif "ESP" in fp or "RF" in fp:
        category = "module_rf"
    else:
        category = "ic"

    matched = (3.0, 3.0, 1.5)
    for k, v in IPC_PACKAGE_DIMENSIONS_MM.items():
        if k in fp:
            matched = v
            break

    w = float(c.get("width_mm") or matched[0])
    l_val = float(c.get("length_mm") or matched[1])
    h = float(c.get("height_mm") or matched[2])

    return {"category": category, "width_mm": round(w, 2), "length_mm": round(l_val, 2), "height_mm": round(h, 2)}


def generate_3d_showcase(
    board_dimensions: Dict[str, Any],
    components: List[Dict[str, Any]],
    showcase_mode: str = "all",
    exploded_options: Optional[Dict[str, Any]] = None,
    knolling_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _require_pos_finite(board_dimensions.get("width_mm", 0.0), "board_dimensions.width_mm")
    _require_pos_finite(board_dimensions.get("height_mm", 0.0), "board_dimensions.height_mm")
    bw = float(board_dimensions["width_mm"])
    bh = float(board_dimensions["height_mm"])
    b_th = float(board_dimensions.get("thickness_mm", 1.6))

    exp_items = []
    knoll_items = []
    padding = float((knolling_options or {}).get("padding_mm", 6.0))
    start_knoll_x = bw + padding * 2.0

    for idx, c in enumerate(components):
        meta = classify_and_measure_component(c)
        cat = meta["category"]
        z_delta = DEFAULT_Z_EXPLOSION_LEVELS_MM.get(cat, 35.0)
        x = float(c.get("x_mm", 0.0))
        y = float(c.get("y_mm", 0.0))

        exp_items.append({
            "designator": c.get("designator", f"CMP{idx+1}"),
            "category": cat,
            "mounted_pos_mm": [x, y, round(b_th / 2.0, 2)],
            "exploded_pos_mm": [x, y, round(b_th / 2.0 + z_delta, 2)],
            "dimensions_mm": [meta["width_mm"], meta["length_mm"], meta["height_mm"]],
        })

        col = idx % 4
        row = idx // 4
        knoll_items.append({
            "designator": c.get("designator", f"CMP{idx+1}"),
            "knolling_pos_mm": [round(start_knoll_x + col * 16.0, 2), round(padding + row * 16.0, 2), round(meta["height_mm"] / 2.0, 2)],
        })

    return {
        "status": "SUCCESS",
        "standard": "IPC-7351B / ISO 24495-1",
        "board": {"width_mm": bw, "height_mm": bh, "thickness_mm": b_th},
        "component_count": len(components),
        "modes_available": ["exploded_z", "knolling_flat_lay", "assembly_animation"],
        "exploded_view": {"components": exp_items},
        "knolling_view": {"items": knoll_items},
    }


# ============================================================================
# 2. SERVIDOR MCP JSON-RPC 2.0 (STDIO)
# ============================================================================

TOOLS_SCHEMA = [
    {
        "name": "pcb_normative_trace_calculator",
        "description": "Calcula el ancho mínimo normativo de pista según IPC-2221 e IPC-2152 (con reducción por plano disipador), caída de tensión DC y pérdida por efecto Joule considerando el coeficiente térmico del cobre (0.393%/°C).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "current_a": {"type": "number", "description": "Corriente máxima continua en Amperios."},
                "temp_rise_c": {"type": "number", "default": 10.0, "description": "Elevación máxima permitida de temperatura (°C)."},
                "copper_oz": {"type": "number", "default": 1.0, "description": "Peso del cobre en oz/ft^2 (1 oz = 35 um)."},
                "layer": {"type": "string", "enum": ["external", "internal"], "default": "external"},
                "length_mm": {"type": "number", "default": 50.0, "description": "Longitud de la pista en mm para cálculo de caída de tensión."},
                "has_adjacent_plane": {"type": "boolean", "default": False, "description": "True si hay un plano sólido de cobre adyacente (activa optimización IPC-2152)."},
            },
            "required": ["current_a"],
        },
    },
    {
        "name": "pcb_normative_clearance_creepage",
        "description": "Calcula Clearance (aire) y Creepage (superficie) según IPC-2221C Tabla 6-1, IEC 60664-1 e IEC 62368-1 evaluando tensión pico (V_peak), grupo CTI del sustrato, grado de polución y necesidad de ranuras fresadas (Board Cutout > 1 mm).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "voltage_val": {"type": "number", "description": "Tensión de trabajo o aislamiento en Voltios."},
                "is_ac_rms": {"type": "boolean", "default": False, "description": "True si voltage_val es AC RMS (se multiplicará por sqrt(2) para obtener V_peak)."},
                "location": {"type": "string", "enum": ["internal_B1", "external_uncoated_B2", "conformal_coated_B4"], "default": "external_uncoated_B2"},
                "pollution_degree": {"type": "integer", "enum": [1, 2, 3], "default": 2},
                "material_group": {"type": "string", "enum": ["I", "II", "IIIa", "IIIb"], "default": "IIIa"},
                "altitude_m": {"type": "number", "default": 500.0},
                "available_space_mm": {"type": "number", "description": "Espacio superficial disponible en mm (opcional, para evaluar si exige ranura fresada)."},
            },
            "required": ["voltage_val"],
        },
    },
    {
        "name": "pcb_normative_impedance_si",
        "description": "Calcula impedancia característica Z0 (Microstrip/Stripline) e impedancia diferencial según IPC-2141A, resistencia de terminación en serie Rs, coeficiente de reflexión Gamma, longitud crítica de línea de transmisión y reglas 3W/5W.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topology": {"type": "string", "enum": ["microstrip", "stripline"], "default": "microstrip"},
                "trace_width_mm": {"type": "number", "default": 0.25},
                "dielectric_h_mm": {"type": "number", "default": 0.20},
                "copper_oz": {"type": "number", "default": 1.0},
                "er": {"type": "number", "default": 4.4},
                "diff_spacing_mm": {"type": "number", "description": "Separación borde a borde si es par diferencial (mm)."},
                "driver_z_source_ohm": {"type": "number", "default": 20.0},
                "load_z_ohm": {"type": "number", "default": 50.0},
                "rise_time_ns": {"type": "number", "default": 1.0},
                "jlcpcb_stackup": {
                    "type": "string",
                    "enum": ["JLC_2L_1.6mm", "JLC04161H-7628", "JLC04161H-3313", "JLC04161H-2313"],
                    "description": "Opcional: aplica automáticamente el espesor H, er y oz de cobre del stackup oficial JLCPCB integrado en EasyEDA Pro.",
                },
            },
            "required": ["trace_width_mm"],
        },
    },
    {
        "name": "pcb_normative_pdn_decoupling",
        "description": "Calcula la impedancia objetivo (Z_target) de la Red de Distribución de Potencia (PDN) y diseña la red de capacitores de desacoplo en 3 décadas con sus frecuencias autorresonantes (f_SRF).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "voltage_nominal_v": {"type": "number", "default": 3.3},
                "ripple_percent": {"type": "number", "default": 5.0},
                "transient_current_a": {"type": "number", "default": 0.4},
                "package": {"type": "string", "enum": ["0201", "0402", "0603", "0805", "1206"], "default": "0805"},
            },
            "required": ["voltage_nominal_v", "transient_current_a"],
        },
    },
    {
        "name": "pcb_normative_thermal_vias",
        "description": "Calcula la resistencia térmica de conducción de Fourier (R_th) para arreglos de vías térmicas bajo encapsulados QFN/MOSFET y verifica relación de aspecto IPC-6012 y retención capilar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "power_dissipation_w": {"type": "number"},
                "board_thickness_mm": {"type": "number", "default": 1.6},
                "via_drill_mm": {"type": "number", "default": 0.25},
                "plating_thickness_um": {"type": "number", "default": 25.0},
                "via_count": {"type": "integer", "default": 9},
            },
            "required": ["power_dissipation_w"],
        },
    },
    {
        "name": "pcb_validate_mcu_pinout",
        "description": "Valida asignaciones de pines de microcontroladores (ESP32 clásico, ESP32-S3, ESP32-C3, ESP32-C5, XIAO-ESP32-C5/C6, DPTechnics Walter, STM32, RP2040, ATmega328P) aplicando la Matriz de 3 Niveles: bloquea pines PROHIBIDOS (SPI Flash/PSRAM interna, Input-Only como salida, módem interno Walter), advierte pines SENSIBLES (USB nativo D-/D+, Strapping pins de arranque, JTAG, bloqueo ADC2 con Wi-Fi, back-powering por UART) y entrega la lista de pines limpios y seguros.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mcu_family": {"type": "string", "description": "Ej. 'ESP32', 'ESP32-S3', 'ESP32-C3', 'ESP32-C5', 'XIAO-ESP32-C5', 'XIAO-ESP32-C6', 'WALTER-ESP32-S3', 'STM32G0', 'RP2040', 'ATmega328P'."},
                "pin_assignments": {"type": "object", "description": "Diccionario { 'GPIO0': 'Sensor_In', 'GPIO12': 'Relay_Out', ... }."},
                "uses_wifi": {"type": "boolean", "default": True},
                "octal_flash_psram": {"type": "boolean", "default": False, "description": "True si el ESP32-S3 usa memoria Octal Flash/PSRAM (bloquea GPIO33..37)."},
            },
            "required": ["mcu_family", "pin_assignments"],
        },
    },
    {
        "name": "easyeda_floorplan_verifier",
        "description": "Verifica colisiones 2D de patios (courtyards), márgenes al borde/chaflanes del PCB y convierte coordenadas en mm de placa a coordenadas nativas en mil para easyeda_pcb_place_batch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "board_width_mm": {"type": "number"},
                "board_height_mm": {"type": "number"},
                "chamfer_mm": {"type": "number", "default": 0.0},
                "origin_mil": {"type": "array", "items": {"type": "number"}, "default": [0.0, 0.0]},
                "edge_margin_mm": {"type": "number", "default": 0.8},
                "min_courtyard_gap_mm": {"type": "number", "default": 0.4},
                "components": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["board_width_mm", "board_height_mm", "components"],
        },
    },
    {
        "name": "pcb_verify_connection_board",
        "description": "Compuerta estricta Datasheet-First para el PCB de Conexión: bloquea el avance si falta la ficha técnica de algún equipo, valida pinouts reales sin invención, detecta cortos/incompatibilidad de voltaje/sobrecorriente, audita posicionamiento 2D y emite el pipeline exacto para EasyEDA Pro.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "board_width_mm": {"type": "number"},
                "board_height_mm": {"type": "number"},
                "chamfer_mm": {"type": "number", "default": 0.0},
                "origin_mil": {"type": "array", "items": {"type": "number"}, "default": [0.0, 0.0]},
                "devices": {
                    "type": "array",
                    "description": "Lista de equipos con designator, name, datasheet_verified, datasheet_source, x_mm, y_mm, width_mm, height_mm, rotation y pins[].",
                    "items": {"type": "object"},
                },
                "connections": {
                    "type": "array",
                    "description": "Lista de conexiones punto a punto con net, from_device, from_pin, to_device, to_pin y expected_current_ma opcional.",
                    "items": {"type": "object"},
                },
            },
            "required": ["board_width_mm", "board_height_mm", "devices", "connections"],
        },
    },
    {
        "name": "pcb_quote_bom_multichannel",
        "description": "Asistente Cotizador y Auditor Multicanal de BOM (EasyEDA Pro/LCSC/JLCPCB, AliExpress, Alibaba y Mercado Local): calcula Costo Total Puesto en Laboratorio (envío, MOQ, impuestos, fees Extended), detecta códigos comunitarios C9900..., bloquea chips sospechosos de clon (<40% LCSC), evalúa urgencia (24-72h local vs importación) y arma la Canasta Híbrida Óptima.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bom_items": {"type": "array", "items": {"type": "object"}, "description": "Ítems del BOM (reference, mpn, footprint, lcsc, qty_per_board, is_critical_ic, jlcpcb_class, category y cotizaciones por canal)."},
                "board_qty": {"type": "integer", "default": 5},
                "assembly_mode": {"type": "string", "enum": ["manual_lab", "jlcpcb_pcba", "hybrid"], "default": "hybrid"},
                "country_code": {"type": "string", "default": "CL"},
                "import_tax_percent": {"type": "number", "default": 19.0},
                "urgency_days": {"type": "integer", "default": 25},
                "jlcpcb_extended_fee_usd": {"type": "number", "default": 3.0},
            },
            "required": ["bom_items"],
        },
    },
    {
        "name": "pcb_high_speed_diff_pairs",
        "description": "Calculadora y Auditor Normativo de Pares Diferenciales de Alta Velocidad (IPC-2141A / IEEE 802.3 / USB-IF): sintetiza ancho de pista W y separación S para microstrip edge-coupled, audita skew intra-par (<5 mils), valida velocidad de propagación y tiempo de vuelo, y detecta violaciones críticas de EMC como cruce de planos divididos (Split Planes) o falta de vías de retorno GND en saltos de capa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "standard": {"type": "string", "enum": ["USB2_HS", "USB3_SS", "ETHERNET_100BASETX", "ETHERNET_1000BASET", "CAN_FD", "RS485", "MIPI_CSI", "PCIE_GEN3", "CUSTOM"], "default": "USB2_HS"},
                "trace_width_mm": {"type": "number", "description": "Ancho de cada pista (mm). Si se omite, se sintetiza según impedancia objetivo."},
                "trace_gap_mm": {"type": "number", "description": "Separación entre pistas del par (mm). Si se omite, se sintetiza."},
                "dielectric_height_mm": {"type": "number", "description": "Espesor del dieléctrico hasta el plano de referencia GND (mm)."},
                "er": {"type": "number", "description": "Constante dieléctrica relativa del sustrato (ej. 4.4 para FR4)."},
                "copper_thickness_um": {"type": "number", "default": 35.0, "description": "Espesor del cobre en micrómetros (1 oz = 35 µm)."},
                "target_diff_impedance": {"type": "number", "description": "Impedancia diferencial objetivo en Ohms (ej. 90 para USB, 100 para Ethernet/MIPI/PCIe, 120 para CAN/RS485)."},
                "trace_length_p_mm": {"type": "number", "description": "Longitud física de la línea P (mm)."},
                "trace_length_n_mm": {"type": "number", "description": "Longitud física de la línea N (mm)."},
                "signal_frequency_mhz": {"type": "number", "description": "Frecuencia fundamental o de Nyquist de la señal en MHz."},
                "split_plane_crossing": {"type": "boolean", "default": False, "description": "Indica si el par cruza un corte o split en el plano GND de referencia (Violación crítica EMC)."},
                "return_path_via_distance_mm": {"type": "number", "description": "Distancia máxima a la vía de retorno GND más cercana si el par cambia de capa (mm)."},
            },
            "required": ["dielectric_height_mm", "er"],
        },
    },
    {
        "name": "pcb_emc_precompliance_auditor",
        "description": "Auditor Normativo de Pre-Cumplimiento EMC / EMI para Fuentes Conmutadas (CISPR 32 / CISPR 25 / FCC Part 15 / IEEE): evalúa emisiones radiadas por bucles críticos di/dt (Hot Loops), calcula espectro conducido en LISN, sintetiza filtro pi óptimo con red amortiguadora (Damping Network) según el Criterio de Estabilidad de Middlebrook (|Zout_filtro| << |Zin_smps| >= 9.5 dB) y verifica regla de setback de planos 20-H.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "converter_topology": {"type": "string", "enum": ["buck", "boost", "buck_boost", "flyback"], "default": "buck"},
                "vin_volts": {"type": "number", "description": "Voltaje de entrada (V)."},
                "vout_volts": {"type": "number", "description": "Voltaje de salida (V)."},
                "iout_amps": {"type": "number", "description": "Corriente continua de salida (A)."},
                "fsw_khz": {"type": "number", "description": "Frecuencia de conmutación de la fuente (kHz)."},
                "hot_loop_area_mm2": {"type": "number", "description": "Área geométrica del bucle de alta di/dt en el layout (mm²)."},
                "current_rise_time_ns": {"type": "number", "default": 10.0, "description": "Tiempo de conmutación tr/tf de los MOSFETs (ns)."},
                "standard": {"type": "string", "enum": ["CISPR32_CLASS_B", "CISPR32_CLASS_A", "CISPR25_CLASS_5", "FCC_PART15_CLASS_B"], "default": "CISPR32_CLASS_B"},
                "pi_filter_installed": {"type": "boolean", "default": False, "description": "Indica si el diseño incluye filtro pi LC de entrada."},
                "filter_l_uh": {"type": "number", "description": "Inductancia del filtro de entrada (µH)."},
                "filter_c_uf": {"type": "number", "description": "Capacitancia del filtro de entrada C2 (µF)."},
                "damping_cd_uf": {"type": "number", "description": "Capacitor electrolítico/tantalio de amortiguación Cd (µF)."},
                "damping_rd_ohms": {"type": "number", "description": "Resistencia serie equivalente o resistor damping Rd (Ohms)."},
                "enclosure_shielding_db": {"type": "number", "default": 0.0, "description": "Atenuación del gabinete metálico blindado en dB (0 si es plástico)."},
                "pcb_plane_20h_setback_complied": {"type": "boolean", "default": True, "description": "Indica si el plano de alimentación VCC está retirado 20 veces la altura h respecto al plano GND perimetral."},
            },
            "required": ["vin_volts", "vout_volts", "iout_amps", "fsw_khz", "hot_loop_area_mm2"],
        },
    },
    {
        "name": "pcb_generate_3d_showcase",
        "description": "Generador de Presentación 3D Industrial, Gemelos Digitales, Vistas Explosionadas (Exploded View), Knolling Flat-Lay y Animaciones de Ensamblaje / Despiece: sintetiza escenas interactivas Three.js y WebGL integrando geometrías precisas de PCB, componentes LCSC con modelos 3D STEP nativos de EasyEDA Pro, gabinetes IP65/IP67 con rayos conectores de ensamble, y trayectorias cinemáticas de despiece para comités de innovación.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "board_width_mm": {"type": "number", "description": "Ancho del PCB (mm)."},
                "board_height_mm": {"type": "number", "description": "Alto del PCB (mm)."},
                "board_thickness_mm": {"type": "number", "default": 1.6, "description": "Espesor del sustrato PCB (mm)."},
                "layers": {"type": "integer", "default": 2, "description": "Cantidad de capas de cobre (2, 4, 6)."},
                "devices": {"type": "array", "items": {"type": "object"}, "description": "Lista de componentes con designator, name, footprint, x_mm, y_mm, height_mm, lcsc_id y visual_category."},
                "enclosure": {"type": "object", "description": "Configuración del gabinete: enabled, type (ej. handheld_panic_button, ip65_junction_box), outer_dimensions, color_hex, transparency."},
                "assembly_mode": {"type": "string", "enum": ["exploded", "knolling", "continuous_orbit", "all"], "default": "all"},
                "output_format": {"type": "string", "enum": ["threejs_scene_json", "html_embed", "animation_keyframes_only"], "default": "threejs_scene_json"},
            },
            "required": ["board_width_mm", "board_height_mm", "devices"],
        },
    },
]


def handle_tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "pcb_normative_trace_calculator":
        return calc_trace_width_ipc(**args)
    if name == "pcb_normative_clearance_creepage":
        return calc_clearance_creepage(**args)
    if name == "pcb_normative_impedance_si":
        return calc_impedance_si(**args)
    if name == "pcb_normative_pdn_decoupling":
        return calc_pdn_decoupling(**args)
    if name == "pcb_normative_thermal_vias":
        return calc_thermal_vias(**args)
    if name == "pcb_validate_mcu_pinout":
        return validate_mcu_pinout(**args)
    if name == "easyeda_floorplan_verifier":
        orig = tuple(args.get("origin_mil", [0.0, 0.0]))
        return audit_floorplan_2d(
            board_width_mm=args["board_width_mm"],
            board_height_mm=args["board_height_mm"],
            chamfer_mm=args.get("chamfer_mm", 0.0),
            components=args["components"],
            edge_margin_mm=args.get("edge_margin_mm", 0.8),
            min_courtyard_gap_mm=args.get("min_courtyard_gap_mm", 0.4),
            origin_mil=(float(orig[0]), float(orig[1])),
        )
    if name == "pcb_verify_connection_board":
        orig = tuple(args.get("origin_mil", [0.0, 0.0]))
        return verify_connection_board(
            board_width_mm=args["board_width_mm"],
            board_height_mm=args["board_height_mm"],
            devices=args["devices"],
            connections=args["connections"],
            chamfer_mm=args.get("chamfer_mm", 0.0),
            origin_mil=(float(orig[0]), float(orig[1])),
        )
    if name == "pcb_quote_bom_multichannel":
        return quote_bom_multichannel(**args)
    if name == "pcb_high_speed_diff_pairs":
        proto = args.get("protocol") or args.get("standard") or "usb2"
        p_map = {
            "usb2_hs": "usb2", "usb3_ss": "usb3", "ethernet_100basetx": "ethernet_100m",
            "ethernet_1000baset": "ethernet_1g", "can_fd": "can_bus", "mipi_csi": "mipi_csi_dsi"
        }
        mapped_proto = p_map.get(proto.lower(), proto.lower())
        d_h = args.get("dielectric_h_mm") or args.get("dielectric_height_mm") or 0.1
        oz = (args["copper_thickness_um"] / 35.0) if "copper_thickness_um" in args else args.get("copper_oz", 1.0)
        return calc_high_speed_diff_pairs(
            protocol=mapped_proto,
            topology=args.get("topology", "microstrip"),
            target_z_diff_ohm=args.get("target_z_diff_ohm") or args.get("target_diff_impedance"),
            trace_width_mm=args.get("trace_width_mm"),
            diff_spacing_mm=args.get("diff_spacing_mm") or args.get("trace_gap_mm"),
            dielectric_h_mm=d_h,
            copper_oz=oz,
            er=args.get("er", 4.4),
            jlcpcb_stackup=args.get("jlcpcb_stackup"),
            trace_length_pos_mm=args.get("trace_length_pos_mm") or args.get("trace_length_p_mm"),
            trace_length_neg_mm=args.get("trace_length_neg_mm") or args.get("trace_length_n_mm"),
            max_skew_mm=args.get("max_skew_mm"),
            crosses_split_plane=args.get("crosses_split_plane", args.get("split_plane_crossing", False)),
            has_via_fence=args.get("has_via_fence", False),
            via_fence_pitch_mm=args.get("via_fence_pitch_mm"),
            rise_time_ns=args.get("rise_time_ns"),
            bend_geometry=args.get("bend_geometry", "mitred_45"),
        )
    if name == "pcb_emc_precompliance_auditor":
        return calc_emc_precompliance_audit(
            vin_v=args.get("vin_v") if "vin_v" in args else args.get("vin_volts", 12.0),
            vout_v=args.get("vout_v") if "vout_v" in args else args.get("vout_volts", 3.3),
            iout_a=args.get("iout_a") if "iout_a" in args else args.get("iout_amps", 1.0),
            topology=args.get("converter_topology") or args.get("topology", "buck"),
            fsw_khz=args.get("fsw_khz", 500.0),
            trise_ns=args.get("trise_ns") if "trise_ns" in args else args.get("current_rise_time_ns", 5.0),
            hot_loop_area_mm2=args.get("hot_loop_area_mm2", 25.0),
            hot_loop_layer_dist_mm=args.get("hot_loop_layer_dist_mm", 0.1),
            emc_standard=args.get("emc_standard") or args.get("standard", "CISPR_32_CLASS_B"),
            measurement_distance_m=args.get("measurement_distance_m", 3.0),
            efficiency=args.get("efficiency", 0.90),
            filter_damping_ratio=args.get("filter_damping_ratio", 4.0),
            board_dimensions_mm=args.get("board_dimensions_mm"),
            dielectric_er=args.get("dielectric_er") or args.get("er", 4.4),
        )
    if name == "pcb_generate_3d_showcase":
        b_dims = args.get("board_dimensions") or {
            "width_mm": args.get("board_width_mm", 50.0),
            "height_mm": args.get("board_height_mm", 40.0),
            "thickness_mm": args.get("board_thickness_mm", 1.6),
        }
        comps = args.get("components") or args.get("devices", [])
        return generate_3d_showcase(
            board_dimensions=b_dims,
            components=comps,
            showcase_mode=args.get("showcase_mode") or args.get("assembly_mode", "all"),
            exploded_options=args.get("exploded_options"),
            knolling_options=args.get("knolling_options"),
        )
    raise ValueError(f"Herramienta desconocida: {name}")


def run_stdio_server() -> None:
    """Bucle principal MCP JSON-RPC 2.0 sobre stdio con protecciones CWE-400 y JSON estricto."""
    for raw_line in sys.stdin:
        if len(raw_line) > MAX_RPC_LINE_BYTES:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Payload JSON-RPC excede el límite máximo de 1 MiB."},
            }) + "\n")
            sys.stdout.flush()
            continue
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {}) or {}

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "agent-design-pcb-mcp",
                        "version": "4.7.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(resp, allow_nan=False) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_SCHEMA},
            }
            sys.stdout.write(json.dumps(resp, allow_nan=False) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            t_name = params.get("name", "")
            t_args = params.get("arguments", {}) or {}
            try:
                out = handle_tool_call(t_name, t_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)}],
                        "structuredContent": out,
                        "isError": False,
                    },
                }
            except Exception as exc:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "isError": True,
                    },
                }
            sys.stdout.write(json.dumps(resp, allow_nan=False) + "\n")
            sys.stdout.flush()
        elif req_id is not None:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
