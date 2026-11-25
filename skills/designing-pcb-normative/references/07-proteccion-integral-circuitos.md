# Manual 07: Blindaje y Protección Integral de Circuitos (Polaridad, Sobrecorriente, Surge, EMI y Aislamiento)

> **Estándares aplicados:** IEC 61000-4-4 (Transitorios Rápidos EFT), IEC 61000-4-5 (Ondas de Choque / Surge), IEC 60664-1 (Coordinación de Aislamiento), CISPR 32 / FCC Parte 15 (Filtros EMI), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Protección contra Inversión de Polaridad (*Reverse Polarity Protection*)

> [!CAUTION]
> **Destrucción instantánea por conexión invertida:** Si el usuario conecta la fuente o batería al revés y la placa carece de protección en la entrada, los reguladores y el microcontrolador se quemarán en milisegundos.

### 1.1. Regla de Selección de Topología según Corriente

| Corriente del Riel ($I_{\max}$) | Topología Recomendada | Pérdida de Tensión / Calor |
| :---: | :--- | :--- |
| **$I_{\max} \le 250\,\text{mA}$** | Diodo Schottky en serie (ej. `SS14`, `MBR0520`). | Caída de $0.25\,\text{V}$ a $0.40\,\text{V}$ ($P \approx 0.1\,\text{W}$). Simple y económico. |
| **$I_{\max} > 250\,\text{mA}$ (o Baterías)** | **MOSFET de Canal P en configuración de diodo ideal.** | Caída $< 0.05\,\text{V}$ ($P = I^2 \cdot R_{DS(\text{on})} \approx 0\,\text{W}$). Sin pérdida de autonomía. |

### 1.2. Diseño Correcto del MOSFET Canal P contra Inversión de Polaridad

1. **Orientación crítica del Drenador y la Fuente:**
   * Conecte el **Drenador (*Drain*)** hacia el conector de entrada (`VIN_RAW`).
   * Conecte la **Fuente (*Source*)** hacia la carga interna del circuito (`VIN_PROT`).
   * *(Al encender con polaridad correcta, el diodo parásito interno polariza la fuente y lleva $V_{GS}$ a conducción plena; si se invierte la tensión, $V_{GS} = 0\,\text{V}$ y el MOSFET bloquea el paso).*
2. **Protección obligatoria de compuerta en entradas $> 12\,\text{V}$ (Sistemas de $12\,\text{V} / 24\,\text{V}$):**
   * La mayoría de los MOSFETs tienen un límite máximo de ruptura de compuerta $V_{GS(\max)} = \pm 20\,\text{V}$ (o $\pm 12\,\text{V}$).
   *Si $V_{\text{in}}$ puede superar $12\,\text{V}$: conecte un **diodo Zener de $10\,\text{V}$ o $12\,\text{V}$** entre la Fuente (*Source*, cátodo) y la Compuerta (*Gate*, ánodo), y una **resistencia de $10\,\text{k}\Omega$ a $47\,\text{k}\Omega$** desde la Compuerta hacia `GND`.

---

## 2. Protección contra Sobrecorriente y Cortocircuito (PPTC vs. eFuse)

> [!WARNING]
> **Disparo prematuro de fusibles rearmables por calor ambiente:** La corriente de mantenimiento ($I_{\text{hold}}$) de un fusible polimérico PPTC disminuye drásticamente a medida que sube la temperatura dentro del gabinete.

### Procedimiento de Dimensionamiento de Fusibles

1. **Si utiliza Fusible Rearmable Polimérico (PPTC):**
   * Aplique reducción térmica (*thermal derating*): a $60\,^\circ\text{C}$, la capacidad de un PPTC cae a $\approx 70\%$ de su valor nominal a $25\,^\circ\text{C}$.
   * Calcule la corriente nominal a $25\,^\circ\text{C}$ mediante:

$$I_{\text{hold}(25\,^\circ\text{C})} \ge \frac{I_{\text{operación\_máx}}}{0.70}$$

   * Verifique siempre que la tensión máxima del PPTC ($V_{\max}$) supere al menos en un $25\%$ la tensión máxima de la fuente.
2. **Si protege circuitos sensibles o puertos de salida de alimentación ($5\,\text{V} / 12\,\text{V}$):**
   * Utilice un **Fusible Electrónico Integrado (*eFuse*, ej. `TPS2592`, `SY6280`)** que corta cortocircuitos en microsegundos (frente a los varios segundos que tarda un PPTC en calentarse), limita la corriente de irrupción (*inrush current*) y bloquea sobretensiones.

---

## 3. Coordinación contra Sobretensiones y Transitorios Pesados (IEC 61000-4-4 e IEC 61000-4-5)

Mientras que la norma **IEC 61000-4-2** (ESD) evalúa pulsos muy cortos ($0.8\,\text{ns}$) de baja energía total, la norma **IEC 61000-4-5 (*Surge* / Rayos e Inducción de Red)** inyecta ondas de choque de **$1.2/50\,\mu\text{s}$ (tensión) y $8/20\,\mu\text{s}$ (corriente)** con decenas o cientos de julios de energía.

### Reglas de Protección Escalonada en Entradas Industriales y de Red AC/DC

1. **Etapa Primaria (Absorción de Energía Bruta en Bornera):**
   * Instale un **Fusible lento o resistencia fusible** en serie a la entrada, seguido de un **Varistor de Óxido Metálico (MOV)** (y un Tubo de Descarga de Gas **GDT** a tierra de chasis en líneas exteriores expuestas a rayos).
2. **Etapa de Desacoplo (Impedancia en Serie):**
   * Coloque un inductor, bobina de choque o resistencia serie entre el MOV primario y el diodo TVS secundario para crear caída de tensión y evitar que el TVS intente absorber toda la corriente del rayo antes de que el MOV actúe.
3. **Etapa Secundaria (Enclavamiento Fino y Rápido):**
   * Instale un **Diodo TVS** dimensionado con tensión de trabajo ($V_{\text{RWM}}$) un $15\%$ superior a la tensión nominal máxima del riel, y cuya tensión de enclavamiento máxima ($V_{\text{clamp}}$) sea **estrictamente menor** que la tensión máxima absoluta ($V_{\text{abs\_max}}$) del regulador de entrada.

---

## 4. Filtrado de Interferencia Electromagnética (EMI) y Estabilidad de Middlebrook

1. **Filtro $\pi$ ($C_1 - L_f - C_2$) en Entradas de Fuentes Conmutadas:**
   * La frecuencia de corte del filtro debe ser al menos una década inferior a la frecuencia de conmutación:
     $$f_c = \frac{1}{2\pi \sqrt{L_f \cdot C_2}} \le 0.1 \cdot f_{sw}$$
   * La atenuación a $f_{sw}$ debe satisfacer el déficit espectral detectado contra **CISPR 32 Clase B** o **CISPR 25 Clase 5** con al menos $6\,\text{dB}$ de margen.
2. **Criterio de Estabilidad de Impedancia de Middlebrook:**
   * Las fuentes conmutadas presentan resistencia incremental de entrada negativa ($R_{in} \approx -V_{in}^2 / P_{in}$). Si el filtro de entrada presenta una impedancia de salida en resonancia $|Z_{out,\text{filter}}| \ge |R_{in}|$, el sistema entrará en oscilación espontánea y apagado cíclico.
   * **Regla obligatoria:** Agregue una rama amortiguadora en paralelo con $C_2$ consistente en $C_d = 4 \cdot C_2$ en serie con una resistencia $R_d \approx 0.6 \cdot \sqrt{L_f / C_2}$.
   * Verifique siempre que $|Z_{out,\text{filter}}|_{\max} \le \frac{1}{3} |R_{in}|$ (separación $\ge 9.5\,\text{dB}$).
3. **Auditoría Pre-Compliance Automatizada:**
   * Ejecute la herramienta MCP `pcb_emc_precompliance_auditor` antes de cerrar el esquemático para obtener los valores comerciales de $L_f$, $C_1$, $C_2$, $C_d$ y $R_d$.
   * Para diseño detallado de campos radiados, lazos calientes y resonancias de cavidad, consulte el **[Manual 16: Auditoría EMC/EMI Pre-Compliance y Filtros Industriales](16-auditoria-emc-emi-precompliance-y-filtros-industriales.md)**.
4. **Choque de Modo Común (*Common-Mode Choke*) en Cables Largos:**
   * En entradas DC por cable externo, puertos USB, CAN o RS-485, instale una bobina de choque de modo común junto al conector para presentar alta impedancia al ruido en fase sin atenuar la señal diferencial ni la corriente continua.

---

## 5. Aislamiento Galvánico de Señales y Potencia

> [!CAUTION]
> **Puenteo accidental de la barrera de aislamiento:** Si coloca un optoacoplador o aislador digital pero une los planos `GND` de ambos lados o traza pistas debajo del componente aislado, anulará por completo la protección galvánica.

1. **Separe físicamente las tierras:** Defina redes con nombres distintos en el esquemático (por ejemplo, `GND_FIELD` / `GND_HV` en el lado primario y `GND_MCU` en el lado lógico).
2. **Deje una franja vacía libre de cobre (*Isolation Moat*):** Debajo de todo optoacoplador (ej. `PC817`, `TLP291`), aislador digital (`ISO77xx`, `ADuM1201`) o convertidor DC-DC aislado (`B0505S`), prohíba cualquier traza o plano de cobre en **todas las capas del PCB**, manteniendo la distancia de *Clearance* y *Creepage* de **[references/02-termica-aislamiento-materiales.md](02-termica-aislamiento-materiales.md)**.
3. **Use capacitores de seguridad Clase Y cuando requiera retorno de alta frecuencia:** Si necesita desviar ruido EMI de modo común a través de la barrera de aislamiento o hacia chasis, utilice exclusivamente **capacitores cerámicos certificados Clase Y1 o Y2** ($1\,\text{nF}$ a $4.7\,\text{nF}$), diseñados para fallar en circuito abierto y nunca en cortocircuito.
