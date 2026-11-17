# Manual 02: Termodinámica de Conductores, Aislamiento Eléctrico y Materiales Base

> **Estándares aplicados:** IPC-2221 / IPC-2152 (Capacidad de corriente y térmica), IPC-2221C Tabla 6-1, IEC 60664-1 e IEC 62368-1 (Clearance y Creepage), IPC-4101 (Materiales base y laminados), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Termodinámica de Conductores y Capacidad de Corriente (IPC-2221 e IPC-2152)

> [!WARNING]
> **Delaminación y fusión de pistas por efecto Joule ($P = I^2 R$):** El coeficiente térmico de resistividad (TCR) del cobre es de $\approx 0.393\%$ por cada $1\,^\circ\text{C}$. Un aumento de $100\,^\circ\text{C}$ incrementa la resistencia de la pista en un $40\%$, acelerando el embalamiento térmico.

### 1.1. Cálculo de Ancho de Pista según IPC-2221

1. Defina la corriente máxima continua ($I$, en amperios) y la elevación térmica permitida ($\Delta T$, típicamente $10\,^\circ\text{C}$ o $20\,^\circ\text{C}$ sobre el ambiente).
2. Calcule el área transversal requerida ($A_c$, en $\text{mil}^2$) despejando de la fórmula empírica:

$$I = k \cdot \Delta T^{0.44} \cdot A_c^{0.725} \implies A_c = \left( \frac{I}{k \cdot \Delta T^{0.44}} \right)^{\frac{1}{0.725}}$$

* **Constante $k$:** Use $k = 0.048$ para capas externas y $k = 0.024$ para capas internas (criterio conservador IPC-2221).
3. Obtenga el ancho de pista ($W$) dividiendo el área entre el espesor de cobre ($1\,\text{oz/ft}^2 \approx 35.0\,\mu\text{m} \approx 1.378\,\text{mils}$):

$$W_{\text{mils}} = \frac{A_c}{\text{Espesor}_{\text{mils}}}$$

### 1.2. Tabla de Consulta Rápida IPC-2221 (Cobre $1\,\text{oz} / 35\,\mu\text{m}$, $\Delta T = 10\,^\circ\text{C}$)

| Corriente Continua ($I$) | Ancho Mínimo en Capa Externa ($k=0.048$) | Ancho Mínimo en Capa Interna ($k=0.024$) |
| :---: | :---: | :---: |
| **$1.0\,\text{A}$** | $0.300\,\text{mm}$ ($11.8\,\text{mils}$) | $0.781\,\text{mm}$ ($30.8\,\text{mils}$) |
| **$5.0\,\text{A}$** | $2.770\,\text{mm}$ ($109.0\,\text{mils}$) | $7.190\,\text{mm}$ ($283.0\,\text{mils}$) |
| **$10.0\,\text{A}$** | $7.190\,\text{mm}$ ($283.0\,\text{mils}$) | $18.70\,\text{mm}$ ($737.0\,\text{mils}$) |
| **$15.0\,\text{A}$** | $12.60\,\text{mm}$ ($495.0\,\text{mils}$) | $33.10\,\text{mm}$ ($1303.0\,\text{mils}$) |

### 1.3. Corrección Paramétrica Moderna según IPC-2152

* **Por qué actualizar a IPC-2152 en placas multicapa:** El estándar **IPC-2221** penaliza las pistas internas asumiendo aislamiento térmico en el vacío. La norma **IPC-2152** demuestra que el dieléctrico FR-4 y los planos de cobre adyacentes disipan el calor por conducción de manera más eficiente que el aire quieto.
* **Regla de diseño:** Si la pista de potencia corre paralela y próxima a un plano sólido de tierra o potencia en una placa multicapa, aplique las curvas de reducción de **IPC-2152** teniendo en cuenta el espesor de la placa y la distancia al plano disipador.

---

## 2. Arreglos de Vías Térmicas (*Thermal Via Arrays*)

> [!WARNING]
> **Sobrecalentamiento de encapsulados QFN/MOSFET y drenaje de soldadura (*Solder Wicking*):** Si no conecta el pad térmico expuesto a los planos internos, el componente fallará por temperatura. Si usa vías demasiado anchas sin obturar, la pasta de soldadura se escurrirá por el agujero dejando el pad sin contacto.

1. **Calcule la resistencia térmica de una vía individual ($R_{\text{single}}$):**

$$R_{\text{th}} = \frac{L}{k \cdot A}$$

* Donde $L$ es el espesor de la placa, $k = 385\,\text{W/m}\cdot\text{K}$ es la conductividad térmica del cobre y $A$ es el área de sección de la pared cilíndrica de cobre de la vía.
2. **Coloque $N$ vías en paralelo para reducir la resistencia total:**

$$R_{\text{total}} = \frac{R_{\text{single}}}{N}$$

3. **Dimensione la geometría para retención capilar:**
   * **Diámetro de perforación (*drill*):** Configure entre $0.20\,\text{mm}$ y $0.30\,\text{mm}$.
   * **Paso entre centros (*pitch*):** Configure una cuadrícula de $0.50\,\text{mm}$ a $1.00\,\text{mm}$.

---

## 3. Aislamiento Eléctrico: *Clearance* y *Creepage* (IPC-2221C, IEC 60664-1 e IEC 62368-1)

* **Clearance (Distancia en aire):** Distancia más corta en línea recta a través del aire entre dos conductores (previene el arco disruptivo).
* **Creepage (Distancia superficial):** Distancia más corta a lo largo de la superficie del aislante entre dos conductores (previene la carbonización o *tracking* superficial).

> [!CAUTION]
> **Riesgo de electrocución y arco eléctrico:** Evalúe siempre el aislamiento utilizando la **tensión pico máxima ($V_{\text{peak}}$)**, nunca el valor RMS. Una red de $230\,\text{V}_{\text{RMS}}$ alcanza $325\,\text{V}_{\text{peak}}$, ubicándose en el tramo de $301\text{–}500\,\text{V}$. Además, la máscara antisoldante convencional (*solder mask*) **no califica** como recubrimiento permanente certificado en alta tensión; use siempre la columna **B2** en capas externas salvo que aplique barniz dieléctrico certificado (*conformal coating*).

### 3.1. Tabla de Espaciamiento Mínimo según IPC-2221C (Tabla 6-1)

| Tensión Pico de Trabajo ($V_{\text{peak}}$) | B1: Capas Internas | B2: Capas Externas (Sin Recubrimiento / Solder Mask Normal) | B4: Capas Externas (Con Recubrimiento Polimérico Permanente) |
| :---: | :---: | :---: | :---: |
| **$0\text{–}15\,\text{V}$** | $0.05\,\text{mm}$ | $0.10\,\text{mm}$ | $0.05\,\text{mm}$ |
| **$16\text{–}30\,\text{V}$** | $0.05\,\text{mm}$ | $0.10\,\text{mm}$ | $0.05\,\text{mm}$ |
| **$31\text{–}50\,\text{V}$** | $0.10\,\text{mm}$ | $0.60\,\text{mm}$ | $0.13\,\text{mm}$ |
| **$51\text{–}100\,\text{V}$** | $0.10\,\text{mm}$ | $0.60\,\text{mm}$ | $0.13\,\text{mm}$ |
| **$101\text{–}150\,\text{V}$** | $0.20\,\text{mm}$ | $0.60\,\text{mm}$ | $0.40\,\text{mm}$ |
| **$151\text{–}300\,\text{V}$** | $0.20\,\text{mm}$ | $1.25\,\text{mm}$ | $0.40\,\text{mm}$ |
| **$301\text{–}500\,\text{V}$** | $0.25\,\text{mm}$ | $2.50\,\text{mm}$ | $0.80\,\text{mm}$ |
| **$> 500\,\text{V}$** | $+0.0025\,\text{mm/V}$ | $+0.0050\,\text{mm/V}$ | $+0.00305\,\text{mm/V}$ |

### 3.2. Reglas de Seguridad de Producto (IEC 60664-1 e IEC 62368-1)

1. **Determine el Grado de Polución:** Use **Grado 2** para entornos de oficina/laboratorio (condensación ocasional) o **Grado 3** para ambientes industriales conductores.
2. **Clasifique el Grupo de Material según su CTI (*Comparative Tracking Index*):**
   * **Grupo I:** $\text{CTI} \ge 600\,\text{V}$
   * **Grupo II:** $400\,\text{V} \le \text{CTI} < 600\,\text{V}$
   * **Grupo IIIa:** $175\,\text{V} \le \text{CTI} < 400\,\text{V}$ *(valor típico del FR-4 estándar; exige la mayor distancia de Creepage).*
3. **Aplique ranuras fresadas (*Milled Slots*) cuando falte espacio 2D:** Si la separación entre pines de un optoacoplador, relé o transformador no cumple la distancia de *Creepage*, ordene el fresado mecánico de una ranura pasante de **ancho $> 1.0\,\text{mm}$** (recomendado $1.5\text{–}2.0\,\text{mm}$) en el sustrato para interrumpir el camino superficial.

---

## 4. Selección de Materiales Base y Dieléctricos (IPC-4101)

> [!WARNING]
> **Fractura de barriles PTH durante el soldado libre de plomo:** Nunca especifique únicamente "FR-4 genérico". Los perfiles de reflujo RoHS (aleación SAC305) alcanzan picos de $260\,^\circ\text{C}$. Si la temperatura supera la transición vítrea ($T_g$) de un FR-4 básico, su expansión térmica en el eje Z ($\text{CTE}_Z$) salta de $\approx 50\,\text{ppm}/^\circ\text{C}$ a $250\text{–}300\,\text{ppm}/^\circ\text{C}$, rompiendo las vías metalizadas.

### 4.1. Tabla de Selección por Hoja de Especificación (*Slash Sheet* IPC-4101)

| Slash Sheet IPC-4101 | Tipo de Resina / Relleno | $T_g$ Mínima | $T_d$ Mínima ($5\%$ pérdida masa) | Aplicación Recomendada |
| :---: | :--- | :---: | :---: | :--- |
| **`IPC-4101/21`** | Epoxi FR-4 estándar (curado Dicy) | $110\text{–}130\,^\circ\text{C}$ | N/A | Electrónica de consumo de bajo costo, 1–2 capas, baja exigencia térmica. |
| **`IPC-4101/99`** | Epoxi FR-4 con relleno inorgánico | $150\,^\circ\text{C}$ | $325\,^\circ\text{C}$ | Automotriz moderado e industrial general multicapa. |
| **`IPC-4101/126`** | Epoxi FR-4 Alto-$T_g$ con relleno (curado fenólico) | $150\text{–}170\,^\circ\text{C}$ | $340\,^\circ\text{C}$ | **Estándar recomendado** para multicapa con reflujo sin plomo SAC305 ($260\,^\circ\text{C}$) y servidores. |
| **`IPC-4101/129`** | Epoxi FR-4 Alto-$T_g$, Libre de Halógenos | $170\text{–}200\,^\circ\text{C}$ | $340\text{–}360\,^\circ\text{C}$ | Aeroespacial, alta confiabilidad Clase 3 y ambientes de temperatura extrema. |

### 4.2. Pérdidas Dieléctricas en Alta Frecuencia ($\text{Df}$)

* Si diseña circuitos digitales estándar o de potencia, utilice laminados FR-4 (`IPC-4101/126`, $\text{Df} \approx 0.020$).
* Si diseña radiofrecuencia (RF) o enlaces seriados en el rango de varios $\text{GHz}$, especifique sustratos de hidrocarburo/cerámica o PTFE (por ejemplo, **Rogers RO4350B** con $\text{Df} \approx 0.0037$) para evitar la atenuación severa de la señal.

---

## 5. Herramientas de `easyeda-mcp-pro` para esta Fase

1. `easyeda_design_rules_lookup` con `topic: "trace-width"`, `topic: "max-current"`, `topic: "clearance"` y `topic: "isolation-emc-review"`.
2. `easyeda_board_stackup` y `easyeda_board_layers` para configurar espesores de cobre y dieléctrico.
3. `easyeda_board_design_rules` para registrar los anchos mínimos de potencia y reglas de espaciamiento por tensión antes de rutear.
