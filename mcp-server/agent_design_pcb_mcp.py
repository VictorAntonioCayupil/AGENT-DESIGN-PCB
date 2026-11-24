#!/usr/bin/env python3
"""
AGENT-DESIGN-PCB MCP Server (v4.0)
Desarrollado por S&D MMCALL para la comunidad.
Licencia: MIT (Atribución a oaslananka/easyeda-mcp-pro para el puente de bajo nivel de EasyEDA Pro).

Servidor MCP Agéntico de Ingeniería Electrónica, Cálculos Normativos (IPC/IEC)
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
) -> Dict[str, Any]:
    """
    Valida asignaciones de pines contra trampas de hardware-firmware (Strapping pins,
    conflicto ADC2+Wi-Fi, pines de reset/boot, AREF, etc.) según el Manual 08.
    """
    fam = mcu_family.upper()
    warnings: List[str] = []
    blocking_errors: List[str] = []
    recommendations: List[str] = []

    if "ESP32" in fam:
        # Reglas comunes ESP32 / S3 / C3 / C6
        if uses_wifi:
            adc2_pins = {
                "ESP32": {"GPIO0", "GPIO2", "GPIO4", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO25", "GPIO26", "GPIO27"},
                "ESP32-S3": {"GPIO11", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "GPIO19", "GPIO20"},
                "ESP32-C3": {"GPIO5"},
            }
            for k, pins in adc2_pins.items():
                if k in fam or (k == "ESP32" and fam == "ESP32"):
                    for p, func in pin_assignments.items():
                        if p.upper() in pins and "ADC" in func.upper():
                            blocking_errors.append(
                                f"{p} ({func}): Pertenece a ADC2, el cual queda bloqueado por hardware cuando el Wi-Fi está activo. Mueva la lectura analógica a ADC1."
                            )

        strapping = {
            "GPIO0": "Pin de Boot. No conecte cargas ni sensores que lo fuercen a GND al encender.",
            "GPIO12": "En ESP32 clásico define tensión VDD_SDIO (si está en ALTO al arrancar fuerza 1.8V y bloquea la Flash).",
            "GPIO45": "En ESP32-S3 define tensión VDD_SPI al arrancar.",
            "GPIO46": "En ESP32-S3 es pin de strapping (debe estar en BAJO o flotante al arrancar).",
            "GPIO8": "En ESP32-C3/C6 debe estar en ALTO (pull-up 10k) para permitir modo descarga.",
            "GPIO9": "En ESP32-C3/C6 es el pin de BOOT (pull-up interno; a GND entra en modo bootloader).",
        }
        for p, func in pin_assignments.items():
            pu = p.upper()
            if pu in strapping:
                warnings.append(f"Strapping Pin {pu} asignado a '{func}': {strapping[pu]}")

        if "C6" in fam:
            lp_io = {"GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "D0", "D1", "D2"}
            for p, func in pin_assignments.items():
                if ("WAKE" in func.upper() or "SLEEP" in func.upper()) and p.upper() not in lp_io:
                    blocking_errors.append(
                        f"{p} ({func}): En ESP32-C6 solo GPIO0..GPIO7 son LP-IO capaces de despertar al chip desde Deep Sleep (ext1)."
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
        "description": "Valida asignaciones de pines de microcontroladores (ESP32, ESP32-S3, ESP32-C3, XIAO-ESP32-C6, STM32, RP2040, ATmega328P) contra pines trampa de arranque (Strapping), bloqueo de ADC2 con Wi-Fi, pines LP-IO de Deep Sleep y cortocircuitos en AREF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mcu_family": {"type": "string", "description": "Ej. 'ESP32', 'ESP32-S3', 'ESP32-C3', 'XIAO-ESP32-C6', 'STM32G0', 'RP2040', 'ATmega328P'."},
                "pin_assignments": {"type": "object", "description": "Diccionario { 'GPIO0': 'Sensor_In', 'GPIO12': 'Relay_Out', ... }."},
                "uses_wifi": {"type": "boolean", "default": True},
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
    raise ValueError(f"Herramienta desconocida: {name}")


def run_stdio_server() -> None:
    """Bucle principal MCP JSON-RPC 2.0 sobre stdio."""
    for raw_line in sys.stdin:
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
                        "version": "4.3.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_SCHEMA},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
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
                        "content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2)}],
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
            sys.stdout.write(json.dumps(resp) + "\n")
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
