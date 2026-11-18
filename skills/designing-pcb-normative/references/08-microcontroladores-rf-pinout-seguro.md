# Manual 08: Co-Diseño Hardware–Firmware de Microcontroladores, Pines Trampa y Antenas RF

> **Estándares aplicados:** Guías de Diseño de Hardware Espressif (ESP32/S3/C3), STMicroelectronics (AN2586/AN4488), Raspberry Pi (Hardware Design with RP2040/RP2350), Microchip AVR042, Diseño de Antenas en PCB ($2.4\,\text{GHz}$ / Sub-GHz), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Reglas Universales de Co-Diseño Hardware–Firmware

> [!CAUTION]
> **Placas que no entran en modo programación o activan salidas al encender:** Durante los primeros milisegundos del encendido, todo microcontrolador muestrea sus **pines de arranque (*Strapping / Boot Pins*)** y mantiene el resto de sus GPIO en alta impedancia o con *pull-ups* débiles internos. Si conecta un relé, MOSFET o sensor que fuerce un nivel lógico indebido en un pin de *strapping*, el chip jamás arrancará.

### Procedimiento Obligatorio antes de Cerrar el Esquemático del MCU

1. **Verifique la tabla de *Strapping Pins* de la familia elegida** (ver Sección 2).
2. **Coloque siempre un cabezal de programación y depuración nativo** (SWD, JTAG, ISP o USB/UART) accesible con puntos de prueba.
3. **Asegure un estado de reposo seguro (*Fail-Safe Default*) en todos los actuadores:** Coloque resistencias *Pull-Down* ($10\,\text{k}\Omega\text{–}100\,\text{k}\Omega$) en las compuertas de MOSFETs y entradas de *drivers* de motor/relé para que permanezcan apagados mientras el MCU inicializa su firmware.

---

## 2. Reglas Críticas y Pines Trampa por Familia de Microcontrolador

### 2.1. Familia Espressif: ESP32 / ESP32-S3 / ESP32-C3

| Regla Crítica en ESP32 / S3 / C3 | Acción Obligatoria en Esquemático y PCB |
| :--- | :--- |
| **Red de Retardo de Encendido (`EN` / `CHIP_PU`)** | Nunca deje el pin `EN` flotando. Conecte una resistencia **Pull-Up de $10\,\text{k}\Omega$ a `3V3`** y un **capacitor de $1\,\mu\text{F}$ (mínimo $100\,\text{nF}$) a `GND`** para garantizar que el pulso de *Reset* se libere después de que la fuente de $3.3\,\text{V}$ se haya estabilizado. |
| **Pines de Arranque (*Strapping Pins*)** | **En ESP32 clásico:** `GPIO0`, `GPIO2`, `GPIO5`, `GPIO12` (¡si `GPIO12` está en ALTO al arrancar, cambia la tensión interna de la Flash a $1.8\,\text{V}$ y bloquea el arranque!), `GPIO15`.<br>**En ESP32-S3:** `GPIO0` (Boot), `GPIO3`, `GPIO45` (tensión VDD_SPI), `GPIO46`.<br>**En ESP32-C3:** `GPIO2`, `GPIO8` (debe estar en ALTO para poder descargar por USB/Serie), `GPIO9` (Boot). |
| **Prohibición de `ADC2` con Wi-Fi Activo** | El periférico **`ADC2` queda bloqueado por hardware** cuando el módem Wi-Fi se enciende. Conecte todos los sensores analógicos y la medición de batería exclusivamente a pines del bloque **`ADC1`** (ej. `GPIO1..GPIO10` en ESP32-S3 o `GPIO32..GPIO39` en ESP32 clásico). |
| **Puerto USB Nativo (`GPIO19 = D-`, `GPIO20 = D+` en S3 / `GPIO18`, `GPIO19` en C3)** | Permite programar y depurar por JTAG sin chip conversor UART externo (`CH340`/`CP2102`). Trace `D+` y `D-` como par diferencial de $90\,\Omega$ directo al conector USB-C con protección TVS de baja capacitancia. |
| **Corriente pico de la fuente de $3.3\,\text{V}$** | Durante la calibración de RF Wi-Fi al arrancar, el ESP32 consume picos breves de **$500\,\text{mA}$ a $600\,\text{mA}$**. Dimensione el regulador para $\ge 600\,\text{mA}$ (ideal $800\,\text{mA}\text{–}1\,\text{A}$) y coloque un capacitor de reserva (*bulk*) de **$10\,\mu\text{F}$ a $22\,\mu\text{F}$** pegado al pin `3V3` del módulo. |

### 2.2. Familia STMicroelectronics: STM32 (F1 / F4 / G0 / L4 / H7)

1. **Pin `BOOT0`:** Conecte siempre una resistencia de **$10\,\text{k}\Omega$ desde `BOOT0` a `GND`** para arrancar desde la memoria Flash principal (con opción de botón o *jumper* a `3V3` para entrar al cargador DFU/ROM de fábrica).
2. **Pin `NRST`:** Los STM32 ya incluyen una resistencia *Pull-Up* interna ($\approx 40\,\text{k}\Omega$). Coloque únicamente un **capacitor cerámico de $100\,\text{nF}$ entre `NRST` y `GND`** muy cerca del pin.
3. **Aislamiento de Alimentación Analógica (`VDDA` / `VSSA`):**
   * Incluso si no usa el ADC, **`VDDA` debe estar alimentado** (alimenta el bloque de *Reset*, PLL y osciladores analógicos internos).
   * Si mide señales analógicas de precisión, filtre `VDDA` desde `VDD` a través de una **perla de ferrita** acompañada de capacitores de $10\,\text{nF} + 1\,\mu\text{F}$ directos a `VSSA`.
4. **Conector de Depuración SWD Estándar (4 o 5 pines):** Incluya siempre `3V3_REF`, `SWDIO`, `SWCLK`, `GND` y `NRST`.

### 2.3. Familia Raspberry Pi (RP2040 / RP2350) y Microchip AVR (ATmega328P)

* **RP2040 / RP2350:**
  * Coloque resistencias de terminación serie de **$27\,\Omega$** en las líneas `USB_DP` y `USB_DM` inmediatamente junto a los pines del microcontrolador.
  * Ubique la memoria Flash QSPI externa a menos de $5\,\text{mm}$ del chip, con una resistencia de $1\,\text{k}\Omega$ hacia el botón `BOOTSEL` en la línea `QSPI_SS`.
* **AVR (ATmega328P / Arduino Uno embebido):**
  * **¡Nunca conecte el pin `AREF` directamente a `VCC` ($5\,\text{V}$)!** Conecte `AREF` únicamente a un capacitor de **$100\,\text{nF}$ hacia `GND`** (si `AREF` se une a $5\,\text{V}$ y el código selecciona referencia interna de $1.1\,\text{V}$, se produce un cortocircuito interno).
  * Filtre el pin `AVCC` con un inductor/ferrita de $10\,\mu\text{H}$ y un capacitor de $100\,\text{nF}$ a `GND`, e incluya el cabezal **ICSP de 6 pines** (`MISO`, `VCC`, `SCK`, `MOSI`, `RESET`, `GND`) con resistencia Pull-Up de $10\,\text{k}\Omega$ en `RESET`.

---

## 3. Diseño de Antenas RF y Zonas de Exclusión de Cobre (*Keep-Out* — Wi-Fi / BLE / LoRa)

> [!CAUTION]
> **Pérdida del $80\text{–}95\%$ del alcance inalámbrico por apantallamiento de cobre:** Si vierte plano de tierra (`GND`) o traza pistas debajo de la antena impresa de un módulo ESP32, nRF52 o LoRa, desintonizará la antena y bloqueará la radiación electromagnética.

### 3.1. Reglas de Emplazamiento para Módulos con Antena en PCB (ESP32-WROOM / MINI)

1. **Ubique la antena en el borde exterior de la placa:** Lo ideal es que la sección de la antena impresa del módulo **sobresalga fuera del borde del sustrato principal** del PCB.
2. **Si la antena queda dentro del contorno del PCB, cree una Zona *Keep-Out* absoluta:**
   * Dibuje una región de prohibición (*Keep-Out / No Copper Pour*) en **TODAS las capas del PCB (Top, Internas y Bottom)** debajo de la antena.
   * Extienda dicha zona vacía al menos **$15\,\text{mm}$ hacia los lados** de la antena, sin componentes, sin planos GND, sin vías y sin tornillos metálicos ni paredes metálicas cerca.

### 3.2. Reglas para Trazas de Radiofrecuencia ($50\,\Omega$) hacia Conector SMA / IPEX (U.FL)

1. **Adapte la línea a $50\,\Omega$ (Coplanar Waveguide with Ground):** Trace una pista corta, recta y sin esquinas de $90^\circ$ (use línea recta o curva suave) desde el pin `ANT` hasta el conector coaxial, flanqueada a ambos lados por plano GND cosido con una cortina densa de vías (*Via Fence* cada $1.0\text{–}1.5\,\text{mm}$).
2. **Incluya una Red de Adaptación en $\pi$ (*Pi-Matching Network*):** Coloque siempre las huellas (`0402`) de tres componentes en topología $\pi$ (un elemento en serie entre dos elementos derivados a `GND`) entre el pin de RF y la antena. Esto permite ajustar la impedancia en laboratorio sin tener que refabricar el PCB (inicialmente se monta un capacitor/bobina de $0\,\Omega$ en serie y se dejan vacíos los dos pads a `GND`).
