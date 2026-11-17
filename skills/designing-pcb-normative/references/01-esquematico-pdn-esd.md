# Manual 01: Esquemático, Microcontroladores, Red de Potencia (PDN) y Protección ESD

> **Estándares aplicados:** AN2586 / AN2867 (Hardware MCU), IPC-2141A (Terminaciones), IEC 61000-4-2 (Inmunidad ESD), ISO 24495-1 (Lenguaje Claro) e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Implementación de Microcontroladores y Relojes (AN2586 / AN2867)

> [!WARNING]
> **Riesgo de inestabilidad de reloj y reinicios por caída de tensión:** Si omite los capacitores de desacoplo locales o traza señales digitales bajo el cristal oscilador, el microcontrolador sufrirá bloqueos y corrupción de memoria.

### Procedimiento Obligatorio en Esquemático y Layout Inicial

1. **Desacople cada pin de energía ($V_{DD} / V_{CC}$):** Conecte un capacitor cerámico (MLCC) de $100\,\text{nF}$ a $1\,\mu\text{F}$ en cada pin de alimentación del microcontrolador.
2. **Ubique el capacitor junto al pin:** Coloque físicamente el capacitor a menos de $2\,\text{mm}$ del pin de alimentación para minimizar la inductancia de lazo.
3. **Aísle el cristal oscilador:** Ubique el cristal y sus capacitores de carga lo más cerca posible de los pines `OSC_IN` y `OSC_OUT`.
4. **Proteja el área del cristal:** No trace ninguna señal digital de alta velocidad debajo ni alrededor del cristal oscilador.
5. **Declare clases de red (*Net Classes*):** Etiquete en el esquemático las redes de potencia (`PWR`), relojes (`CLK`), pares diferenciales (`DIFF`) y alta tensión (`HV`) antes de transferir al PCB.

---

## 2. Integridad de Potencia (PDN) y Desacoplo en 3 Décadas

La conmutación rápida del silicio demanda picos de corriente transitoria ($\Delta I_{\text{transient}}$). Si la impedancia de la red de distribución de potencia supera el límite objetivo ($Z_{\text{target}}$), la tensión caerá fuera del margen operativo.

### 2.1. Cálculo de la Impedancia Objetivo ($Z_{\text{target}}$)

1. Determine la tensión nominal del riel ($V_{\text{nominal}}$) y el rizado máximo permitido (típicamente $5\%$).
2. Calcule la impedancia máxima admisible mediante la ecuación:

$$Z_{\text{target}} = \frac{\Delta V_{\text{allowed}}}{\Delta I_{\text{transient}}} = \frac{V_{\text{nominal}} \cdot \text{Ripple}_{\%}}{\Delta I_{\text{transient}}}$$

* **Ejemplo de verificación:** Si una CPU de $1.8\,\text{V}$ tolera un $5\%$ de rizado ($\Delta V = 0.09\,\text{V}$) ante un transitorio de $0.4\,\text{A}$, diseñe la red de potencia para mantener $Z_{\text{target}} < 0.225\,\Omega$.

### 2.2. Frecuencia Autorresonante ($f_{\text{SRF}}$) y Método de las 3 Décadas

> [!CAUTION]
> **Pérdida de filtrado en alta frecuencia:** Por encima de su frecuencia autorresonante ($f_{\text{SRF}}$), un capacitor real deja de comportarse como capacitor y actúa como un inductor ($X_L = 2\pi f \cdot \text{ESL}$).

$$f_{\text{SRF}} = \frac{1}{2\pi \sqrt{\text{ESL} \cdot C}}$$

Para mantener la impedancia por debajo de $Z_{\text{target}}$ en todo el espectro de frecuencias:

1. **Aplique el método de las 3 décadas:** Combine al menos tres órdenes de magnitud de capacitancia en paralelo (por ejemplo: $10\,\mu\text{F}$, $100\,\text{nF}$ y $10\,\text{nF}$).
2. **Seleccione encapsulados pequeños para alta frecuencia ($100\,\text{MHz}\text{–}\text{GHz}$):** Use paquetes compactos (`0402` o `0201`) que poseen menor inductancia serie equivalente ($\text{ESL}$).
3. **Controle la antirresonancia:** Combine valores con resistencia serie equivalente ($\text{ESR}$) controlada para amortiguar los picos de impedancia entre cruces inductivos y capacitivos.
4. **Conecte con vías dobles:** Coloque múltiples vías directamente en los pads de cada capacitor de desacoplo hacia los planos de referencia para no degradar su $f_{\text{SRF}}$.

---

## 3. Adaptación de Impedancia en Serie y Coeficiente de Reflexión ($\Gamma$)

> [!WARNING]
> **Sobreimpulsos (*Overshoot*) y falsos disparos lógicos:** Si el tiempo de subida de la señal ($t_r$) es comparable al retardo de propagación de la pista, la traza actúa como línea de transmisión y genera reflexiones destructivas.

### 3.1. Cálculo del Coeficiente de Reflexión ($\Gamma$)

Evalúe la proporción de onda reflejada hacia la fuente mediante:

$$\Gamma = \frac{Z_{\text{load}} - Z_{\text{trace}}}{Z_{\text{load}} + Z_{\text{trace}}}$$

* Cuando $Z_{\text{load}} = Z_{\text{trace}}$, el coeficiente es $\Gamma = 0$ (transferencia perfecta sin reflexiones).

### 3.2. Cálculo de la Resistencia de Terminación Serie ($R_s$)

En relojes rápidos y buses síncronos (SPI de alta velocidad, SDRAM, QSPI, I2S):

1. Identifique la impedancia de salida del pin controlador ($Z_{\text{source}}$, típicamente $15\,\Omega$ a $25\,\Omega$) y la impedancia característica de la pista ($Z_{\text{trace}}$, típicamente $50\,\Omega$).
2. Calcule la resistencia de terminación en serie:

$$R_s = Z_{\text{trace}} - Z_{\text{source}}$$

3. **Ejemplos prácticos:**
   * Si $Z_{\text{trace}} = 50\,\Omega$ y $Z_{\text{source}} = 20\,\Omega$, instale $R_s = 30\,\Omega$.
   * Si $Z_{\text{trace}} = 50\,\Omega$ y $Z_{\text{source}} = 22\,\Omega$, instale $R_s = 28\,\Omega$ (o valor comercial $27\,\Omega / 33\,\Omega$).
4. **Ubicación crítica:** Coloque la resistencia $R_s$ **inmediatamente a la salida del pin transmisor (*driver*)**, nunca en el extremo receptor.

---

## 4. Protección contra Transitorios Electrostáticos (ESD — IEC 61000-4-2)

> [!CAUTION]
> **Destrucción del núcleo digital por pulso ESD:** El modelo de nivel de sistema **IEC 61000-4-2** descarga $150\,\text{pF}$ a través de $330\,\Omega$ con un tiempo de subida letal de $t_r = 0.8\,\text{ns}$ ($10\%$ a $90\%$). Los diodos internos HBM del chip (que tardan $\approx 15\,\text{ns}$ en responder) no protegen contra los $30\,\text{A}$ de un pulso externo Nivel 4.

### 4.1. Tabla Normativa de Severidad IEC 61000-4-2

| Nivel de Severidad | Tensión de Descarga por Contacto | Tensión de Descarga por Aire | Corriente Pico Inicial (a $1\,\text{ns}$) |
| :---: | :---: | :---: | :---: |
| **Nivel 1** | $\pm 2\,\text{kV}$ | $\pm 2\,\text{kV}$ | $7.5\,\text{A}$ |
| **Nivel 2** | $\pm 4\,\text{kV}$ | $\pm 4\,\text{kV}$ | $15.0\,\text{A}$ |
| **Nivel 3** | $\pm 6\,\text{kV}$ | $\pm 8\,\text{kV}$ | $22.5\,\text{A}$ |
| **Nivel 4** | $\pm 8\,\text{kV}$ | $\pm 15\,\text{kV}$ | $30.0\,\text{A}$ |

### 4.2. Reglas de Diseño de Protección TVS

1. **Proteja toda interfaz externa:** Instale diodos supresores de tensión transitoria (**TVS**) de respuesta sub-nanosegundo en cada conector accesible al usuario (USB, Ethernet, RS-485, botones, entradas de sensores, alimentación).
2. **Ubique el TVS en el borde de entrada:** Coloque el diodo TVS inmediatamente junto a los pines del conector externo, antes de cualquier derivación hacia el microcontrolador.
3. **Trace una ruta directa:** La señal del conector debe atravesar primero el pad del diodo TVS y luego continuar hacia el circuito interno (topología *flow-through* sin ramificaciones o *stubs*).
4. **Descargue directo al plano GND:** Conecte el pin de tierra del TVS mediante vías cortas y múltiples directamente al plano de tierra o chasis para evitar caídas inductivas $V = L \frac{di}{dt}$.

---

## 5. Herramientas de `easyeda-mcp-pro` para esta Fase

Ejecute estas herramientas en orden al aplicar este manual:
1. `easyeda_design_rules_lookup` (con `topic: "decoupling"` y `topic: "bulk-capacitance"`).
2. `easyeda_workflow_power_rail` y `easyeda_workflow_decouple_ic` para estructurar alimentación y desacoplo local.
3. `easyeda_workflow_connector_breakout` para conectores externos con protección ESD.
4. `easyeda_schematic_validate_netlist`, `easyeda_semantic_erc_auto` y `easyeda_erc_run` para confirmar cero pines flotantes o conflictos eléctricos antes de pasar al PCB.
