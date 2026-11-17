# Ficha Técnica Viva del Proyecto de Hardware (`HARDWARE-SPEC.md`)

> **Generado y mantenido por:** Agente de Diseño Normativo de PCB (`AGENT-DESIGN-PCB` — **S&D MMCALL**)  
> **Instrucción para el Agente:** Actualice este archivo al finalizar cada fase para conservar la memoria exacta del proyecto entre sesiones.

---

## 1. Resumen General del Proyecto

| Campo | Valor Definido |
| :--- | :--- |
| **Nombre del Proyecto** | `[Ej. Sensor-Mini-V2]` |
| **Objetivo Funcional** | `[Descripción breve de qué hace la placa]` |
| **Clase Normativa IPC-6012** | `[Clase 2 (Industrial/Comercial) / Clase 3 (Alta Confiabilidad)]` |
| **Método de Ensamblaje** | `[Soldadura Manual (IPC-7351 Nivel A, 0805/SOIC) / PCBA Reflujo (Nivel B, 0402/QFN) / Híbrido]` |
| **Estrategia de Compras (Sourcing)** | `[100% LCSC-JLCPCB / Híbrido (SMD en LCSC + Módulos/Conectores en AliExpress/Alibaba) / 100% Independiente]` |
| **Dimensiones y Gabinete** | `[Ancho x Largo mm, espesor 1.6 mm, restricciones de caja o agujeros de montaje M3]` |

---

## 2. Árbol de Alimentación y Parámetros Eléctricos (PDN)

| Riel de Potencia | Tensión Nominal / Pico ($V_{\text{peak}}$) | Corriente Máxima Continua ($I_{\max}$) | Transitorio ($\Delta I$) | Impedancia Objetivo ($Z_{\text{target}}$) | Ancho Mínimo de Pista (IPC-2221 / 2152) | Clearance Mínimo (IPC-2221C B2) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`VIN_AC / DC`** | `[Ej. 230 Vrms / 325 Vpk]` | `[Ej. 2.0 A]` | `[0.5 A]` | `N/A` | `[0.80 mm]` | `[2.50 mm + Slot > 1 mm]` |
| **`+5V_SYS`** | `[5.0 V]` | `[3.0 A]` | `[0.8 A]` | `[0.31 Ω]` | `[1.35 mm]` | `[0.10 mm]` |
| **`+3V3_MCU`** | `[3.3 V]` | `[0.5 A]` | `[0.3 A]` | `[0.55 Ω]` | `[0.30 mm]` | `[0.10 mm]` |

---

## 3. Mapa de Bloques, Interfaces y Asignación de Pines (*Pinout*)

| Bloque / Periférico | Componente Principal (MPN) | Pines Asignados en MCU | Clase de Red (*Net Class*) | Protección / Terminación Requerida |
| :--- | :--- | :--- | :---: | :--- |
| **Microcontrolador** | `[Ej. ESP32-S3 / STM32G0]` | `VDD, VSS, EN/NRST` | `PWR / SYS` | `100 nF (< 2 mm por pin) + 10 uF + 10 nF` |
| **Puerto USB-C** | `[Receptáculo USB-C 16P]` | `D+, D-, CC1, CC2` | `DIFF_90` | `2x 5.1 kΩ independientes en CC1/CC2 + TVS USBLC6` |
| **Bus Sensor (I2C/SPI)** | `[Ej. VL53L0X / Flash SPI]` | `SDA, SCL / SCK, MOSI, MISO` | `CLK / BUS` | `Pull-ups 4.7 kΩ (I2C) o Rs 27-33 Ω en origen (SPI)` |
| **Actuador / Salida** | `[Ej. Relé / MOSFET]` | `GPIO_OUT` | `PWR_SW` | `Diodo Flyback + Rg 100 Ω + Rgs 10 kΩ` |

---

## 4. Apilamiento de Capas (*Stackup*) y Sustrato

* **Número de capas:** `[2 capas / 4 capas]`
* **Hoja de material IPC-4101:** `[IPC-4101/126 (Tg >= 150-170 °C, Td >= 340 °C para reflujo RoHS SAC305)]`
* **Espesor de cobre:** `[1 oz (35 µm) externo / 0.5 oz o 1 oz interno]`
* **Asignación de capas:**
  * `L1 (Top)`: Señales críticas, componentes SMD y microstrip.
  * `L2 (Inner 1 / Bottom)`: Plano de retorno **GND continuo e ininterrumpido**.

---

## 5. Estado de Avance por Fases Normativas

- [ ] **Fase 0:** Entrevista de requerimientos, definición de proyecto y estrategia de compras.
- [ ] **Fase 1:** Clasificación IPC-6012 y auditoría inicial del árbol de potencia.
- [ ] **Fase 2:** Esquemático completo, cálculo PDN ($Z_{\text{target}}$), terminaciones serie, ESD (**IEC 61000-4-2**) y validación ERC (`0 errores`).
- [ ] **Fase 3:** Validación de abastecimiento (LCSC / AliExpress / Alibaba), confirmación de huellas físicas (*footprints*), cálculo térmico (**IPC-2221/2152**) y aislamiento (**IPC-2221C / IEC 60664-1**).
- [ ] **Fase 4:** *Floorplanning*, plano **GND continuo**, ruteo con reglas $3W/5W$ e impedancia controlada (**IPC-2141A**).
- [ ] **Fase 5:** Auditoría DFM (**IPC-6012**), criterios de soldadura (**IPC-A-610J**), DRC en EasyEDA Pro (`0 errores`) y exportación de Gerbers/BOM.
