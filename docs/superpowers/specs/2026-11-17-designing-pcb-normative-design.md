# Especificación de Diseño: Agente y Skill de Diseño Normativo de PCB (`designing-pcb-normative`)

**Fecha:** 2026-11-17  
**Estado:** Validado para revisión  
**Normas de Redacción Aplicadas:** ISO 24495-1 (Lenguaje Claro) e ISO/IEC 82079-1 (Manuales e Instrucciones de Uso)  
**Conector MCP Externo Integrado:** [`easyeda-mcp-pro`](https://github.com/oaslananka/easyeda-mcp-pro) v1.15.6 (Autor: `oaslananka`, Licencia: `AGPL-3.0-only`)

---

## 1. Propósito del Sistema

Transformar a cualquier agente de IA en un **Ingeniero Experto en Diseño Electrónico y PCB Basado en Normas Internacionales (IPC / IEC / J-STD / ANSI)**.

El agente no diseña por intuición ni por ensayo y error. Antes de crear esquemáticos, seleccionar paquetes, definir el *stackup* (apilamiento de capas) o rutear pistas mediante las herramientas de `easyeda-mcp-pro`, el agente calcula, valida y aplica obligatoriamente las leyes físicas, ecuaciones de integridad de señal/potencia y tablas normativas contenidas en sus manuales de referencia.

---

## 2. Arquitectura del Repositorio Público (GitHub)

El repositorio se estructura en formato 100 % Markdown para garantizar portabilidad total entre entornos de agentes (Antigravity, Claude Code, Cursor, Gemini CLI, Codex) sin dependencias de código propietario ni infracción de derechos de autor:

```text
DESIGN-PCB/
├── README.md                  # Manual principal del repositorio (ISO/IEC 82079-1), instalación y créditos
├── LICENSE                    # Licencia MIT para la Skill y la documentación normativa propia
├── NOTICE.md                  # Aviso legal y atribución a easyeda-mcp-pro (oaslananka, AGPL-3.0-only)
├── mcp-config.example.json    # Configuración lista para conectar easyeda-mcp-pro vía npx
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-11-17-designing-pcb-normative-design.md
│       └── plans/             # Plan de implementación paso a paso
└── skills/
    └── designing-pcb-normative/
        ├── SKILL.md           # Contrato operativo del Agente PCB, reglas inquebrantables y flujo de 5 fases
        └── references/
            ├── 01-esquematico-pdn-esd.md
            ├── 02-termica-aislamiento-materiales.md
            ├── 03-integridad-senal-gnd-ruteo.md
            └── 04-dfm-ensamblaje-easyeda-mcp.md
```

---

## 3. Cumplimiento Legal y Derechos de Autor (`NOTICE.md` y `LICENSE`)

1. **Separación estricta de código:** Este repositorio no copia, modifica ni redistribuye ningún archivo fuente del paquete `easyeda-mcp-pro`.
2. **Invocación externa autorizada:** El archivo `mcp-config.example.json` y los manuales indican al usuario cómo ejecutar el servidor MCP oficial directamente desde npm mediante `npx -y easyeda-mcp-pro@1.15.6`.
3. **Reconocimiento explícito:** Tanto `README.md` como `NOTICE.md` otorgan crédito visible al autor original **oaslananka** ([github.com/oaslananka/easyeda-mcp-pro](https://github.com/oaslananka/easyeda-mcp-pro)) e informan que dicho conector se distribuye bajo licencia `AGPL-3.0-only`.
4. **Licencia propia del repositorio:** El contenido original de esta Skill y sus manuales normativos se publican bajo licencia **MIT**.

---

## 4. Diseño del Núcleo de la Skill (`SKILL.md`)

### 4.1. Metadatos de Descubrimiento (SDO)
```yaml
---
name: designing-pcb-normative
description: Use when designing electronic circuits, schematics, component selection, stackups, or PCB layouts, or when operating EasyEDA Pro MCP tools to create, route, or review hardware boards under IPC and IEC standards.
---
```

### 4.2. Comportamiento del Agente PCB (Contrato de 5 Fases)
El agente actúa como un revisor y ejecutor normativo en tiempo real. Ante cualquier solicitud de diseño electrónico o de placa (como el proyecto `Sensor-mini-v2` o cualquier circuito nuevo), el agente ejecuta las siguientes 5 fases en orden estricto:

1. **Fase 1 — Definición de Parámetros de Ingeniería y Clase IPC**
   * Determina la clase de confiabilidad según **IPC-6012**:
     * **Clase 2:** Electrónica industrial o comercial dedicada.
     * **Clase 3:** Alta confiabilidad crítica (cero tolerancia a vacíos en barriles y microvías).
   * Registra tensión máxima pico ($V_{\text{peak}}$), corriente máxima por riel ($I_{\text{max}}$), frecuencia máxima / tiempo de subida ($t_r$) y entorno térmico/contaminación.
   * **Herramientas MCP:** `easyeda_health_check`, `easyeda_project_open`, `easyeda_design_rules_lookup`.

2. **Fase 2 — Arquitectura de Esquemático, PDN y Protección ESD**
   * Consulta obligatoriamente `references/01-esquematico-pdn-esd.md`.
   * Aplica reglas de microcontroladores (**AN2586 / AN2867**), cálculo de impedancia objetivo de la red de potencia ($Z_{\text{target}}$), estrategia de capacitores de desacoplo en 3 décadas considerando su frecuencia autorresonante ($f_{\text{SRF}}$), resistencias de terminación serie ($R_s$) y diodos TVS en conectores externos según **IEC 61000-4-2**.
   * Define clases de red (*Net Classes*) en el esquemático antes de pasar al PCB.
   * **Herramientas MCP:** `easyeda_workflow_power_rail`, `easyeda_workflow_decouple_ic`, `easyeda_workflow_connector_breakout`, `easyeda_schematic_place_component`, `easyeda_schematic_connect_pins_by_net`, `easyeda_schematic_validate_netlist`, `easyeda_semantic_erc_auto`, `easyeda_erc_run`.

3. **Fase 3 — Dimensionamiento Térmico, Aislamiento y Selección de Materiales**
   * Consulta obligatoriamente `references/02-termica-aislamiento-materiales.md`.
   * Calcula el ancho mínimo de pista según **IPC-2221** e **IPC-2152** para un incremento térmico seguro ($\Delta T \le 10\,^\circ\text{C}$ o $20\,^\circ\text{C}$).
   * Diseña matrices de vías térmicas ($R_{\text{th}} = \frac{L}{k \cdot A}$) para disipación de paquetes QFN/MOSFET.
   * Verifica distancias de *Clearance* (aire) y *Creepage* (superficie) según **IPC-2221C (Tabla 6-1)**, **IEC 60664-1** e **IEC 62368-1** usando tensión pico, grupo de material (CTI) y grado de polución. Si el espacio superficial es insuficiente en alta tensión, exige ranuras fresadas (*milled slots* $> 1\,\text{mm}$).
   * Selecciona la hoja de especificación del laminado según **IPC-4101** (`/21`, `/99`, `/126`, `/129`) verificando $T_g$, $T_d \ge 340\,^\circ\text{C}$ para reflujo sin plomo SAC305 y factor de disipación ($\text{Df}$).
   * **Herramientas MCP:** `easyeda_board_stackup`, `easyeda_board_design_rules`, `easyeda_schematic_sync_to_pcb`.

4. **Fase 4 — Emplazamiento, Planos GND Continua e Integridad de Señal (Ruteo)**
   * Consulta obligatoriamente `references/03-integridad-senal-gnd-ruteo.md`.
   * **Regla de Oro de GND:** Garantiza un plano de referencia GND sólido e ininterrumpido debajo de toda pista de alta velocidad o reloj. Prohíbe cruzar cortes de plano (*split planes*).
   * Coloca capacitores de desacoplo a menos de $2\,\text{mm}$ de los pines de alimentación con múltiples vías directas al plano para minimizar la inductancia de lazo (ESL).
   * Calcula geometrías Microstrip y Stripline según **IPC-2141A**, mantiene simetría en pares diferenciales ($85\text{–}100\,\Omega$, *skew* $\le 5\,\text{mils}$) y aplica la regla de separación **$3W$** (general) o **$5W$** (relojes y señales críticas) para contener la diafonía (*crosstalk* $< 5\%$).
   * Si el diseño utiliza BGA de paso fino ($\le 0.5\,\text{mm}$) o circuitos flexibles, aplica las reglas **IPC-2226** (HDI tipos I, II, III con microvías escalonadas) o **IPC-2223E** (radios de curvatura y trazado ortogonal a $90^\circ$).
   * **Herramientas MCP:** `easyeda_pcb_floorplan`, `easyeda_pcb_place_component_group`, `easyeda_pcb_add_zone`, `easyeda_pcb_route_path_plan`, `easyeda_pcb_add_track`, `easyeda_pcb_add_via`, `easyeda_pcb_rebuild_copper`.

5. **Fase 5 — Verificación DFM, Ensamblaje y Auditoría Final**
   * Consulta obligatoriamente `references/04-dfm-ensamblaje-easyeda-mcp.md`.
   * Verifica niveles de densidad de *footprints* (**IPC-7351B / IPC-7352** Niveles A, B, C), anillo anular intacto, espaciamiento taladro-cobre ($\ge 8\,\text{mils}$ / $0.2\,\text{mm}$) y relación de aspecto ($\le 10:1$ en PTH, $\le 1:1$ en microvías) según **IPC-6012**.
   * Audita criterios de soldadura y ensamblaje según **IPC-A-610J**, **J-STD-001J** e **IPC-7095** (llenado THT $\ge 75\%$, vacíos en BGA $\le 25\%$, límite de contaminación iónica $\le 1.56\,\mu\text{g/cm}^2$ NaCl y protección de área EPA según **ANSI/ESD S20.20**).
   * **Herramientas MCP:** `easyeda_drc_run`, `easyeda_pcb_constraint_check`, `easyeda_pcb_route_geometry_review`, `easyeda_engineering_review`, `easyeda_pcb_production_review`, `easyeda_production_qa_artifacts`.

---

## 5. Especificación Detallada de los 4 Manuales Normativos (`references/`)

Todos los archivos de referencia aplicarán rigurosamente las normas **ISO 24495-1** e **ISO/IEC 82079-1**:
* Oraciones activas, imperativas y menores de 20 palabras.
* Orden lógico: **Condición $\rightarrow$ Acción**.
* Avisos de precaución (`> [!WARNING]` o `> [!CAUTION]`) colocados **antes** del paso donde ocurre el riesgo físico o eléctrico.
* Párrafos de máximo 3 a 4 líneas, apoyados en tablas de consulta directa y ecuaciones en LaTeX.

### 5.1. `references/01-esquematico-pdn-esd.md`
* **Implementación de MCU (AN2586 / AN2867):** Red de desacoplo por pin ($100\,\text{nF}$ a $1\,\mu\text{F}$), aislamiento del cristal oscilador y prohibición de rutear señales digitales bajo el cristal.
* **Impedancia Objetivo de PDN ($Z_{\text{target}}$):**
  $$Z_{\text{target}} = \frac{\Delta V_{\text{allowed}}}{\Delta I_{\text{transient}}}$$
* **Frecuencia Autorresonante ($f_{\text{SRF}}$) y Método de las 3 Décadas:**
  $$f_{\text{SRF}} = \frac{1}{2\pi \sqrt{\text{ESL} \cdot C}}$$
  Combinación de encapsulados compactos (ej. 0402/0201 para $100\,\text{MHz}\text{–}\text{GHz}$) y arreglo MLCC ($10\,\mu\text{F}$, $100\,\text{nF}$, $10\,\text{nF}$) con control de ESR contra picos de antirresonancia.
* **Adaptación de Impedancia en Serie y Coeficiente de Reflexión ($\Gamma$):**
  $$R_s = Z_{\text{trace}} - Z_{\text{source}} \quad ; \quad \Gamma = \frac{Z_{\text{load}} - Z_{\text{trace}}}{Z_{\text{load}} + Z_{\text{trace}}}$$
* **Inmunidad ESD (IEC 61000-4-2):** Tabla completa de Niveles 1 a 4 (Contacto $\pm 2\,\text{kV}$ a $\pm 8\,\text{kV}$, Aire $\pm 2\,\text{kV}$ a $\pm 15\,\text{kV}$, corriente pico de $7.5\,\text{A}$ a $30\,\text{A}$ con $t_r = 0.8\,\text{ns}$) y reglas de colocación de diodos TVS ultrarrápidos en la entrada del conector.

### 5.2. `references/02-termica-aislamiento-materiales.md`
* **Capacidad de Corriente y Efecto Joule:** Coeficiente térmico del cobre ($\text{TCR} \approx 0.393\%/^\circ\text{C}$).
* **Modelo IPC-2221 y Tabla de Anchos ($1\,\text{oz}$, $\Delta T = 10\,^\circ\text{C}$):**
  $$I = k \cdot \Delta T^{0.44} \cdot A_c^{0.725}$$
  ($k = 0.048$ externa, $k = 0.024$ interna; tabla para $1\,\text{A}$, $5\,\text{A}$, $10\,\text{A}$ y $15\,\text{A}$).
* **Optimización Paramétrica IPC-2152:** Ajuste por espesor de placa, conductividad del dieléctrico y proximidad a planos de cobre disipadores.
* **Arreglos de Vías Térmicas:**
  $$R_{\text{th}} = \frac{L}{k \cdot A} \quad ; \quad R_{\text{total}} = \frac{R_{\text{single}}}{N}$$
  Con $k = 385\,\text{W/m}\cdot\text{K}$, diámetro de perforación de $0.2\text{–}0.3\,\text{mm}$ y paso de $0.5\,\text{mm}$ para evitar drenaje capilar de soldadura.
* **Clearance y Creepage:**
  * Tabla completa **IPC-2221C (Tabla 6-1)** para categorías B1 (interna), B2 (externa sin recubrimiento) y B4 (externa con recubrimiento permanente) desde $0\text{–}15\,\text{V}$ hasta $>500\,\text{V}$ pico.
  * Reglas de seguridad **IEC 60664-1** e **IEC 62368-1**: Grado de polución, índice CTI (Grupos I, II y IIIa) y fresado de ranuras (*slots* $> 1\,\text{mm}$).
* **Selección de Laminados (IPC-4101):** Tabla comparativa de *Slash Sheets* `/21`, `/99`, `/126` y `/129` ($T_g$, $T_d$, CTE en eje Z) y sustratos de baja pérdida ($\text{Df} \approx 0.0037$, ej. Rogers RO4350B) frente a FR-4 estándar ($\text{Df} \approx 0.020$).

### 5.3. `references/03-integridad-senal-gnd-ruteo.md`
* **Modelos de Línea de Transmisión (IPC-2141A):**
  * Ecuación **Microstrip**:
    $$Z_0 = \frac{87}{\sqrt{\epsilon_r + 1.41}} \ln \left( \frac{5.98 \cdot H}{0.8 \cdot W + T} \right)$$
  * Ecuación **Stripline**:
    $$Z_0 = \frac{60}{\sqrt{\epsilon_r}} \ln \left( \frac{1.9 \cdot B}{0.8 \cdot W + T} \right)$$
  * Restricción de validez geométrica ($W/H \le 7.5$) y compensación por grabado ácido (*undercut*) y máscara antisoldante.
* **Pares Diferenciales y Diafonía (*Crosstalk*):** Impedancia diferencial ($85\text{–}100\,\Omega$), igualación de longitud intra-par (*skew* $\le 5\,\text{mils}$ / $0.127\,\text{mm}$), regla **$3W$** y regla **$5W$**.
* **Arquitectura de Retorno GND:** Continuidad absoluta del plano de referencia bajo trazas críticas, colocación de vías de retorno junto a vías de cambio de capa y vías dobles en pads de capacitores.
* **Interconexión de Alta Densidad (IPC-2226) y Flexibles (IPC-2223E):** Arquitecturas HDI Tipo I, II y III (`X+N+X`), preferencia por microvías escalonadas (*staggered*) sobre apiladas (*stacked* $\le 2$ niveles) y multiplicadores de radio de curvatura ($6\times$ estático a $150\times$ dinámico bicapa con ruteo a $90^\circ$).

### 5.4. `references/04-dfm-ensamblaje-easyeda-mcp.md`
* **Geometría de Pads (IPC-7351B e IPC-7352):** Criterios de filete (*Toe, Heel, Side*) por suma estadística RMS y selección de densidad Nivel A, Nivel B y Nivel C.
* **Reglas DFM Rígidas (IPC-6012 Clase 2 vs Clase 3):** Tabla de anillo anular interno/externo, espesor de cobre en barril PTH ($20\,\mu\text{m}$ vs $25\,\mu\text{m}$ sin vacíos), *Copper Wrap Plating*, distancia taladro-cobre ($8\text{–}10\,\text{mils}$) y relación de aspecto.
* **Criterios de Aceptación de Ensamblaje (IPC-A-610J, J-STD-001J, IPC-7095):**
  * Eliminación del criterio *Target* (solo *Acceptable*, *Process Indicator*, *Defect*).
  * Mojado de talón en SMT gull-wing y llenado vertical $\ge 75\%$ en barriles THT con ángulo de contacto $< 90^\circ$.
  * Control de vacíos en BGA/BTC por rayos X (AXI): *Macrovoids* $\le 25\%$ del área de la esfera, tolerancia cero a *Planar Microvoids (Champagne Voids)* en Clase 3 y prevención de *Head-in-Pillow (HiP)*.
  * Límite de limpieza iónica ($\le 1.56\,\mu\text{g/cm}^2$ equivalente NaCl) y resistencia a tierra en área EPA ($\le 3.5 \times 10^7\,\Omega$ según **ANSI/ESD S20.20**).
* **Pruebas de Confiabilidad Termomecánica (IPC-TM-650):** Choque térmico por flotación en soldadura a $288\,^\circ\text{C}$ por $10\,\text{s}$ (Método 2.6.8) y ciclado térmico / prueba IST de $-55\,^\circ\text{C}$ a $125\,^\circ\text{C}$ (Métodos 2.6.7.2C y 2.6.26A, umbral de fallo $\Delta R > 5\text{–}10\%$).
* **Guía de Orquestación con `easyeda-mcp-pro`:** Mapa operativo de qué herramientas MCP invocar en cada verificación y cómo interpretar sus reportes sin asumir certificaciones de seguridad cuando faltan mediciones físicas.

---

## 6. Criterios de Verificación y Prueba (TDD de Skills)

De acuerdo con la metodología `writing-skills`:
1. Se verificará que todas las fórmulas, tablas y umbrales de los dos informes estén presentes sin omisiones.
2. Se comprobará el cumplimiento de las normas **ISO 24495-1** e **ISO/IEC 82079-1** (oraciones concisas, voz activa, avisos de advertencia antes de la acción y tablas escaneables).
3. Se validará mediante un escenario de prueba que un agente utilizando la Skill aplique las normas IPC/IEC y seleccione las herramientas correctas de `easyeda-mcp-pro` antes de dar por bueno un diseño de placa.
