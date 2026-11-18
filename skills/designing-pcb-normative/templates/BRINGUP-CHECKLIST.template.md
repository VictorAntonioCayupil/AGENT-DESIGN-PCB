# Protocolo de Puesta en Marcha y Pruebas en Laboratorio (`BRINGUP-CHECKLIST.md`)

> **Generado por:** Agente Auditor de Ingeniería y Laboratorio (`AGENT-DESIGN-PCB` — **S&D MMCALL**)  
> **Normas aplicadas:** IPC-A-610J (Inspección Visual de Soldadura), ANSI/ESD S20.20 (Área Protegida EPA $\le 35\,\text{M}\Omega$), Protocolo de Energización Incremental.

---

## 1. Preparación del Banco de Trabajo (Antes de Conectar Energía)

- [ ] **Protección ESD activa (ANSI/ESD S20.20):** Tapete antiestático y pulsera conectada a tierra ($\le 3.5 \times 10^7\,\Omega$).
- [ ] **Puentes de aislamiento ($0\,\Omega$ / *Solder Jumpers*) abiertos:** Las etapas de regulación están desconectadas de la carga del microcontrolador para la primera prueba en vacío.
- [ ] **Inspección óptica bajo lupa/microscopio (IPC-A-610J):**
  - [ ] Pin 1 verificado en MCU (`U1`), reguladores y memorias.
  - [ ] Polaridad verificada en diodos TVS, diodos *Flyback*, LEDs y capacitores electrolíticos/tantalio.
  - [ ] Ausencia de puentes de soldadura (*solder bridges*) en pines de USB-C y encapsulados QFN/LQFP.

---

## 2. Prueba en Frío de Cortocircuitos (Placa Apagada — Multímetro en $\Omega$)

> [!CAUTION]
> **Si cualquier medición en frío marca $< 50\,\Omega$ o continuidad directa a `GND`, NO CONECTE LA FUENTE.** Localice y elimine el cortocircuito primero.

| Punto de Prueba Medido (vs. `TP_GND`) | Resistencia Mínima Esperada | Valor Medido en Banco ($\Omega$) | Estado (`OK` / `CORTO`) |
| :--- | :---: | :---: | :---: |
| **`TP_VIN` vs. `TP_GND`** | $> 1\,\text{k}\Omega$ | `[     Ω]` | `[ ]` |
| **`TP_5V` vs. `TP_GND`** | $> 500\,\Omega$ | `[     Ω]` | `[ ]` |
| **`TP_3V3` vs. `TP_GND`** | $> 500\,\Omega$ | `[     Ω]` | `[ ]` |

---

## 3. Primer Encendido Controlado (Fuente Limitada en Corriente + Multímetro / `ut803`)

1. Configure la fuente de laboratorio a la tensión nominal de entrada y limite la corriente a **$50\,\text{mA}\text{–}100\,\text{mA}$**.
2. Encienda la fuente y verifique que no caiga en modo de protección por corriente constante (*CC*).
3. Mida y registre cada riel (con multímetro manual o ejecutando `ut803_esperar_estable` / `ut803_leer`):

| Riel / Punto de Prueba | Tensión Nominal | Rango Aceptable ($\pm 3\%$) | Tensión Medida ($\text{V}_{\text{DC}}$) | Rizado Medido ($\text{mV}_{\text{pp}}$) | Temperatura ($\Delta T < 10\,^\circ\text{C}$) | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`TP_VIN`** | `[Ej. 12.00 V]` | `[11.64 V – 12.36 V]` | `[     V]` | `[   mV]` | `[OK]` | `[ ]` |
| **`TP_5V`** | `5.00 V` | `4.85 V – 5.15 V` | `[     V]` | `< 50 mV` | `[OK]` | `[ ]` |
| **`TP_3V3`** | `3.30 V` | `3.20 V – 3.40 V` | `[     V]` | `< 30 mV` | `[OK]` | `[ ]` |
| **`TP_RST` (`NRST`/`EN`)** | `3.30 V` | `3.00 V – 3.40 V` | `[     V]` | `Limpio` | `N/A` | `[ ]` |

---

## 4. Cierre de Puentes de $0\,\Omega$, Programación y Periféricos

- [ ] **Soldar puentes de $0\,\Omega$:** Apagar la fuente, soldar los puentes que alimentan al MCU y volver a encender con límite de corriente de $150\,\text{mA}$.
- [ ] **Consumo base en reposo:** Corriente medida sin actuadores = `[     mA]` (dentro de lo esperado).
- [ ] **Detección del Microcontrolador:** Reconocido correctamente por puerto SWD / USB nativo / ISP (`Chip ID` leído sin errores).
- [ ] **Escaneo de Buses (`I2C` / `SPI` / `UART`):** Todos los sensores soldados responden en su dirección hexadecimal esperada.
- [ ] **Prueba de Actuadores y Protecciones:** Disparo de relés/MOSFETs sin caídas de tensión ni reinicios del MCU.
