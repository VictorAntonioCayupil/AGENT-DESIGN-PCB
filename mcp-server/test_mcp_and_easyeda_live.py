#!/usr/bin/env python3
"""
Suite de Pruebas Automatizadas para AGENT-DESIGN-PCB MCP Server (v4.0)
y Diagnóstico en Vivo de EasyEDA Pro (Sensor-mini-V2).
"""

import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_design_pcb_mcp as mcp


def test_normative_calculators() -> None:
    print("=== 1. Probando Calculadoras Normativas Deterministas (IPC / IEC) ===")

    # 1.1 IPC-2221 / IPC-2152 Trace Width (5A, 1oz, dT=10°C)
    t_res = mcp.calc_trace_width_ipc(current_a=5.0, temp_rise_c=10.0, copper_oz=1.0, layer="external", length_mm=80.0)
    assert 2.75 <= t_res["ipc_2221_width_mm"] <= 2.80, f"IPC-2221 5A esperado ~2.77 mm, obtenido {t_res['ipc_2221_width_mm']}"
    print(f"  [OK] IPC-2221/2152 (5A, 1oz): ancho={t_res['ipc_2221_width_mm']} mm, dV={t_res['electrical_thermal']['voltage_drop_mv']} mV")

    # 1.2 IPC-2221C + IEC 60664-1 Clearance & Creepage (230V AC RMS -> 325.27V Peak -> B2 = 2.50 mm)
    c_res = mcp.calc_clearance_creepage(voltage_val=230.0, is_ac_rms=True, location="external_uncoated_B2")
    assert c_res["ipc_2221c_clearance_mm"] == 2.50, f"Esperado 2.50 mm para 230Vrms (325Vpk), obtenido {c_res['ipc_2221c_clearance_mm']}"
    assert c_res["milled_slot_recommendation"]["required"] is True
    print(f"  [OK] IPC-2221C / IEC 60664-1 (230Vrms -> {c_res['evaluated_v_peak']}Vpk): Clearance B2={c_res['ipc_2221c_clearance_mm']} mm, Slot={c_res['milled_slot_recommendation']['min_slot_width_mm']} mm")

    # 1.3 IPC-2141A Microstrip & Termination (50 Ohm target, Z_source = 20 Ohm)
    si_res = mcp.calc_impedance_si(topology="microstrip", trace_width_mm=0.35, dielectric_h_mm=0.20, copper_oz=1.0, er=4.4, driver_z_source_ohm=20.0)
    assert si_res["ipc_2141a_formula_valid"] is True
    assert si_res["crosstalk_and_gnd_rules"]["rule_3w_center_to_center_mm"] == 1.05
    print(f"  [OK] IPC-2141A Microstrip: Z0={si_res['z0_characteristic_ohm']} Ω, Rs={si_res['termination']['series_resistor_rs_ohm']} Ω, 3W={si_res['crosstalk_and_gnd_rules']['rule_3w_center_to_center_mm']} mm")

    # 1.4 PDN Z_target & 3-Decade SRF (3.3V, 5% ripple, 0.4A transient)
    pdn_res = mcp.calc_pdn_decoupling(voltage_nominal_v=3.3, ripple_percent=5.0, transient_current_a=0.4, package="0805")
    assert abs(pdn_res["z_target_ohm"] - 0.4125) < 1e-4
    print(f"  [OK] PDN Z_target (3.3V, 0.4A): Z_target={pdn_res['z_target_ohm']} Ω, 100nF f_SRF={pdn_res['three_decade_network'][1]['f_srf_mhz']} MHz")

    # 1.5 Fourier Thermal Via Array (2W, 9 vias, 0.25mm drill)
    tv_res = mcp.calc_thermal_vias(power_dissipation_w=2.0, via_drill_mm=0.25, via_count=9)
    assert tv_res["ipc_6012_aspect_ratio_ok"] is True
    assert tv_res["capillary_solder_wicking_ok"] is True
    print(f"  [OK] Thermal Vias (9x 0.25mm): R_th_array={tv_res['r_th_array_c_per_w']} °C/W, dT={tv_res['temp_delta_across_vias_c']} °C")

    # 1.6 MCU Pinout Co-Design Validator (ESP32 ADC2 conflict & XIAO-ESP32-C6 LP-IO wake check)
    mcu_bad = mcp.validate_mcu_pinout(
        mcu_family="XIAO-ESP32-C6",
        pin_assignments={"GPIO0": "Sensor_Wake_Ext1", "GPIO21": "Button_Wake_DeepSleep"},
        uses_wifi=True,
    )
    assert mcu_bad["passed"] is False, "Debería detectar que GPIO21 en ESP32-C6 no es LP-IO para despertar de Deep Sleep"
    print(f"  [OK] MCU Validator (XIAO-ESP32-C6): detectó correctamente error LP-IO -> {mcu_bad['blocking_errors'][0]}")

    # 1.7 Connection Board Datasheet-First Gate (Bloqueo sin ficha técnica y aprobación con ficha verificada)
    dev_u1 = {
        "designator": "U1",
        "name": "XIAO ESP32-C6",
        "datasheet_verified": True,
        "datasheet_source": "Seeed XIAO ESP32-C6 Official Datasheet",
        "x_mm": 25.0,
        "y_mm": 40.0,
        "width_mm": 21.0,
        "height_mm": 30.0,
        "pins": [
            {"number": "1", "name": "3V3", "type": "power_out", "voltage_v": 3.3, "max_current_ma": 500},
            {"number": "2", "name": "GND", "type": "gnd", "voltage_v": 0.0, "max_current_ma": 1000},
            {"number": "3", "name": "D4", "type": "i2c", "voltage_v": 3.3, "max_current_ma": 20, "tolerant_5v": False},
        ],
    }
    dev_missing_ds = {
        "designator": "M2",
        "name": "Modulo Sin Datasheet",
        "datasheet_verified": False,
        "datasheet_source": "",
        "x_mm": 75.0,
        "y_mm": 40.0,
        "width_mm": 20.0,
        "height_mm": 20.0,
        "pins": [{"number": "1", "name": "VCC", "type": "power_in", "voltage_v": 3.3}],
    }
    gate_blocked = mcp.verify_connection_board(
        board_width_mm=120.0,
        board_height_mm=84.0,
        devices=[dev_u1, dev_missing_ds],
        connections=[],
    )
    assert gate_blocked["can_proceed_to_easyeda"] is False
    assert len(gate_blocked["missing_datasheets"]) == 1
    print("  [OK] Datasheet-First Gate: bloqueó correctamente equipo sin ficha técnica verificada.")

    dev_m1_ok = {
        "designator": "M1",
        "name": "BME280",
        "datasheet_verified": True,
        "datasheet_source": "Bosch BST-BME280-DS002",
        "x_mm": 75.0,
        "y_mm": 40.0,
        "width_mm": 18.0,
        "height_mm": 18.0,
        "pins": [
            {"number": "1", "name": "VIN", "type": "power_in", "voltage_v": 3.3, "max_current_ma": 10},
            {"number": "2", "name": "GND", "type": "gnd", "voltage_v": 0.0, "max_current_ma": 10},
            {"number": "3", "name": "SDA", "type": "i2c", "voltage_v": 3.3, "max_current_ma": 5},
        ],
    }
    gate_ok = mcp.verify_connection_board(
        board_width_mm=120.0,
        board_height_mm=84.0,
        devices=[dev_u1, dev_m1_ok],
        connections=[
            {"net": "+3V3", "from_device": "U1", "from_pin": "1", "to_device": "M1", "to_pin": "1"},
            {"net": "GND", "from_device": "U1", "from_pin": "2", "to_device": "M1", "to_pin": "2"},
            {"net": "I2C_SDA", "from_device": "U1", "from_pin": "3", "to_device": "M1", "to_pin": "3"},
        ],
    )
    assert gate_ok["can_proceed_to_easyeda"] is True
    assert gate_ok["status"] == "APPROVED_FOR_EASYEDA"
    assert len(gate_ok["easyeda_integration_pipeline"]) == 7
    print("  [OK] Datasheet-First Gate: aprobó tablero verificado y emitió pipeline nativo de 7 pasos para EasyEDA Pro.")

    # 1.8 Stackup oficial JLCPCB en IPC-2141A (JLC04161H-3313 para 50 Ohm / USB 90 Ohm)
    si_jlc = mcp.calc_impedance_si(topology="microstrip", trace_width_mm=0.16, jlcpcb_stackup="JLC04161H-3313", diff_spacing_mm=0.15)
    assert si_jlc["jlcpcb_stackup"]["name"] == "JLC04161H-3313"
    assert 48.0 <= si_jlc["z0_characteristic_ohm"] <= 58.0
    print(f"  [OK] Stackup JLCPCB (JLC04161H-3313, W=0.16mm): Z0={si_jlc['z0_characteristic_ohm']} Ω, Zdiff={si_jlc['z_differential_ohm']} Ω")

    # 1.9 Asistente Cotizador Multicanal (LCSC, AliExpress, Alibaba y Mercado Local sobre MMCALL-PROT-12V)
    sample_bom = [
        {
            "reference": "J1",
            "mpn": "DC-005-5.5*2.1",
            "footprint": "DC-IN-TH",
            "lcsc": "C9900017044",  # Huella comunitaria -> no comprable en LCSC
            "qty_per_board": 1,
            "lcsc_quote": {"unit_usd": 0.08, "shipping_share_usd": 0.5, "in_stock": True, "lead_days": 12},
            "aliexpress_quote": {"unit_usd": 0.06, "shipping_usd": 1.80, "store_rating_pct": 97.4, "item_stars": 4.8, "lead_days": 18},
            "local_market_quote": {"unit_usd": 0.45, "shipping_usd": 1.50, "vendor_name": "MCI/AFEL Local", "has_tax_invoice": True, "lead_days": 1},
        },
        {
            "reference": "D1",
            "mpn": "SMBJ15CA",
            "footprint": "SMB",
            "lcsc": "C8829",
            "qty_per_board": 1,
            "is_critical_ic": True,
            "jlcpcb_class": "Extended Part",
            "lcsc_quote": {"unit_usd": 0.075, "shipping_share_usd": 0.8, "in_stock": True, "lead_days": 10},
            "aliexpress_quote": {"unit_usd": 0.020, "shipping_usd": 1.50, "store_rating_pct": 96.2, "item_stars": 4.8, "lead_days": 19},  # <40% -> Clon!
            "local_market_quote": {"unit_usd": 0.55, "shipping_usd": 1.00, "vendor_name": "Local", "has_tax_invoice": True, "lead_days": 2},
        },
        {
            "reference": "ENC1",
            "mpn": "Gabinete IP65 + Bateria",
            "footprint": "EXT",
            "lcsc": "",
            "qty_per_board": 1,
            "category": "battery_hazmat",
            "alibaba_quote": {"unit_usd": 2.90, "shipping_usd": 65.0, "moq": 50, "verified_supplier": True, "trade_assurance": True, "lead_days": 32},
            "local_market_quote": {"unit_usd": 7.20, "shipping_usd": 3.50, "vendor_name": "Distribuidor Local", "has_tax_invoice": True, "lead_days": 2},
        },
    ]
    q_normal = mcp.quote_bom_multichannel(bom_items=sample_bom, board_qty=5, assembly_mode="manual_lab", country_code="CL", import_tax_percent=19.0, urgency_days=20)
    assert q_normal["summary"]["easyeda_community_c9900_parts_count"] == 1
    # J1 (C9900) no puede elegir LCSC; D1 en AliExpress (<40%) debe ser bloqueado por clon y elegir LCSC; ENC1 elige MERCADO_LOCAL
    assert q_normal["items"][0]["recommended_channel"] in ("ALIEXPRESS", "MERCADO_LOCAL")
    assert q_normal["items"][1]["recommended_channel"] == "LCSC_JLCPCB"
    assert q_normal["items"][2]["recommended_channel"] == "MERCADO_LOCAL"
    print(f"  [OK] Cotizador Multicanal (Normal 20d): Canasta Híbrida=${q_normal['summary']['optimal_hybrid_total_usd']} USD ({q_normal['summary']['channel_distribution']})")

    # Caso Urgencia Laboratorio <= 3 días -> todo debe ir a MERCADO_LOCAL
    q_urgent = mcp.quote_bom_multichannel(bom_items=sample_bom, board_qty=2, assembly_mode="manual_lab", country_code="CL", import_tax_percent=19.0, urgency_days=3)
    assert q_urgent["summary"]["channel_distribution"]["MERCADO_LOCAL"] == 3
    print(f"  [OK] Cotizador Multicanal (Urgencia <=3d): 100% redirigido a MERCADO_LOCAL (${q_urgent['summary']['optimal_hybrid_total_usd']} USD en 24-48h con factura).")

    # 1.10 Validación XIAO-ESP32-C5 (detecta D2 sin ADC y JTAG prohibidos) + Endurecimiento Seguridad CWE-20/369
    c5_bad = mcp.validate_mcu_pinout("XIAO-ESP32-C5", {"D2": "VBAT_ADC", "MTMS": "RTC_WAKE"})
    assert c5_bad["passed"] is False and len(c5_bad["blocking_errors"]) == 2
    c5_good = mcp.validate_mcu_pinout("XIAO-ESP32-C5", {"D0": "VBAT_ADC", "D1": "SENSOR_WAKE", "D4": "RTC_SDA", "D5": "RTC_SCL"})
    assert c5_good["passed"] is True
    try:
        mcp.calc_impedance_si(trace_width_mm=0.0, dielectric_h_mm=0.2)
        raise AssertionError("Debió rechazar trace_width_mm <= 0")
    except ValueError:
        pass
    print("  [OK] XIAO-ESP32-C5 Validator + Endurecimiento CWE-20/369 verificados.")

    # 1.11 Validación Matriz de 3 Niveles (v4.6): Bloqueo Flash, Octal PSRAM, Input-Only y Walter módem
    c5_flash_bad = mcp.validate_mcu_pinout("ESP32-C5", {"GPIO16": "RELAY_OUT"})
    assert c5_flash_bad["passed"] is False
    assert any("SPI Flash/PSRAM" in err for err in c5_flash_bad["blocking_errors"])

    s3_octal_bad = mcp.validate_mcu_pinout("ESP32-S3", {"GPIO35": "SPI_CLK"}, octal_flash_psram=True)
    assert s3_octal_bad["passed"] is False
    assert any("GPIO35" in err for err in s3_octal_bad["blocking_errors"])

    esp32_in_bad = mcp.validate_mcu_pinout("ESP32", {"GPIO34": "LED_OUT"})
    assert esp32_in_bad["passed"] is False
    assert any("SOLO ENTRADA" in err for err in esp32_in_bad["blocking_errors"])

    walter_bad = mcp.validate_mcu_pinout("WALTER-ESP32-S3", {"GPIO45": "USER_UART_TX"})
    assert walter_bad["passed"] is False
    assert any("módem interno" in err for err in walter_bad["blocking_errors"])

    ulp_backpower = mcp.validate_mcu_pinout("XIAO-ESP32-C5", {"D6": "MODEM_TX", "D7": "MODEM_RX", "D8": "LTE_EN"})
    assert any("Anti Back-Powering" in rec for rec in ulp_backpower["mandatory_hardware_checks"])
    print("  [OK] Matriz de Seguridad de Pines de 3 Niveles (v4.6) validada (Flash, Octal, Input-Only, Walter y Back-Powering).")


def test_stdio_jsonrpc_protocol() -> None:
    print("\n=== 2. Probando Protocolo MCP JSON-RPC 2.0 sobre STDIO ===")
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_design_pcb_mcp.py")
    proc = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # 1. initialize
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n")
        proc.stdin.flush()
        init_out = json.loads(proc.stdout.readline())
        assert init_out["result"]["serverInfo"]["name"] == "agent-design-pcb-mcp"

        # 2. tools/list
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n")
        proc.stdin.flush()
        list_out = json.loads(proc.stdout.readline())
        tools = list_out["result"]["tools"]
        assert len(tools) >= 7
        print(f"  [OK] MCP stdio server inicializado y expone {len(tools)} herramientas normativas.")

        # 3. tools/call
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "pcb_normative_clearance_creepage",
                "arguments": {"voltage_val": 230, "is_ac_rms": True},
            },
        }) + "\n")
        proc.stdin.flush()
        call_out = json.loads(proc.stdout.readline())
        assert call_out["result"]["isError"] is False
        assert call_out["result"]["structuredContent"]["ipc_2221c_clearance_mm"] == 2.50
        print("  [OK] Llamada JSON-RPC tools/call a pcb_normative_clearance_creepage verificada.")
    finally:
        proc.terminate()


def inspect_sensor_mini_v2_drc_geometry() -> None:
    print("\n=== 3. Analizando Geometría Real de Sensor-mini-V2 desde EasyEDA Pro ===")
    pads_path = r"C:\Users\vcayu\.gemini\antigravity\brain\2c85a191-d21f-4628-9634-80cec8d098bd\.system_generated\steps\230\output.txt"
    if not os.path.exists(pads_path):
        print("  [SKIP] No se encontró captura local de pads.")
        return

    pads = json.load(open(pads_path, encoding="utf-8"))["result"]
    gnd_pads = [p for p in pads if p.get("net") == "GND"]
    disc_ids = {
        "6cf1c4937e7d2498e15": "C1_2",
        "752e16636ad0765be15": "C2_2",
        "e89b2db085575348e15": "C3_2",
        "1b738ef2f9769dbee15": "C6_2",
        "7bc3dbd7455bc307e12": "R10_2",
        "f009bfc6b2c026d8e19": "C5_2",
    }
    conn_gnd = [p for p in gnd_pads if p.get("primitiveId") not in disc_ids]
    disc_gnd = [p for p in gnd_pads if p.get("primitiveId") in disc_ids]

    for dp in disc_gnd:
        name = disc_ids[dp["primitiveId"]]
        nearest = min(conn_gnd, key=lambda cp: math.hypot(cp["x"] - dp["x"], cp["y"] - dp["y"]))
        dist = math.hypot(nearest["x"] - dp["x"], nearest["y"] - dp["y"])
        print(
            f"  Pad desconectado {name:5s} ({dp['primitiveId']}) en ({dp['x']:6.1f}, {dp['y']:6.1f}) mil "
            f"-> GND conectado más cercano: {nearest['primitiveId']} (Layer {nearest['layer']}) "
            f"en ({nearest['x']:6.1f}, {nearest['y']:6.1f}) mil [dist={dist:5.1f} mil / {dist*0.0254:4.2f} mm]"
        )

    t1_path = r"C:\Users\vcayu\.gemini\antigravity\brain\2c85a191-d21f-4628-9634-80cec8d098bd\.system_generated\steps\301\output.txt"
    t2_path = r"C:\Users\vcayu\.gemini\antigravity\brain\2c85a191-d21f-4628-9634-80cec8d098bd\.system_generated\steps\307\output.txt"
    if os.path.exists(t1_path) and os.path.exists(t2_path):
        t1 = json.load(open(t1_path, encoding="utf-8"))["tracks"]
        t2 = json.load(open(t2_path, encoding="utf-8"))["tracks"]
        tracks = [t for t in (t1 + t2) if t["primitiveId"] != "7dd31be71e4b4eed" and t["layer"] == 1]
        for dp in disc_gnd:
            name = disc_ids[dp["primitiveId"]]
            px, py = dp["x"], dp["y"]
            print(f"  Pistas Layer 1 cerca de {name} ({px}, {py}):")
            for t in tracks:
                if min(t["startX"], t["endX"]) - 70 <= px <= max(t["startX"], t["endX"]) + 70 and min(t["startY"], t["endY"]) - 70 <= py <= max(t["startY"], t["endY"]) + 70:
                    print(f"    net={t['net']:12s} ({t['startX']:.1f},{t['startY']:.1f}) -> ({t['endX']:.1f},{t['endY']:.1f})")


if __name__ == "__main__":
    test_normative_calculators()
    test_stdio_jsonrpc_protocol()
    inspect_sensor_mini_v2_drc_geometry()
    print("\nTODAS LAS PRUEBAS PASARON EXITOSAMENTE.")
