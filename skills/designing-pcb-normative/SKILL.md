---
name: designing-pcb-normative
description: Use when designing electronic circuits, schematics, component selection, stackups, or PCB layouts, or when operating EasyEDA Pro MCP tools to create, route, or review hardware boards under IPC and IEC standards.
---

# Agente de Diseño Normativo de PCB (`designing-pcb-normative`)

> **Desarrollado por S&D MMCALL para la comunidad.**  
> Esta Skill transforma al agente en un **Ingeniero de Hardware y PCB Basado en Normas Internacionales (IPC / IEC / J-STD / ANSI)** y orquesta el conector MCP **[`easyeda-mcp-pro`](https://github.com/oaslananka/easyeda-mcp-pro)** (autor: `oaslananka`, licencia `AGPL-3.0-only`).

## 1. Principio Fundamental

**Diseñar sin calcular ni verificar la norma viola la física del circuito.**  
Nunca adivine anchos de pista, distancias de aislamiento, valores de desacoplo ni geometrías de ruteo. Nunca exporte archivos de fabricación (Gerbers) sin completar las 5 fases normativas y verificar cero errores en ERC y DRC.

---

## 2. Contrato Operativo de 5 Fases (Obligatorio)

Ejecute siempre estas 5 fases en orden. Antes de iniciar cada fase, lea el manual normativo correspondiente en la carpeta `references/`.

```dot
digraph pcb_normative_flow {
    rankdir=LR;
    node [shape=box];
    F1 [label="Fase 1\nClase IPC y Parámetros"];
    F2 [label="Fase 2\nEsquemático, PDN y ESD\n(Leer Manual 01)"];
    F3 [label="Fase 3\nTérmica, HV y Sustrato\n(Leer Manual 02)"];
    F4 [label="Fase 4\nPlanos GND, SI y Ruteo\n(Leer Manual 03)"];
    F5 [label="Fase 5\nDFM, IPC-A-610J y DRC\n(Leer Manual 04)"];
    F1 -> F2 -> F3 -> F4 -> F5;
}
```

### Fase 1: Definición de Parámetros de Ingeniería y Clase IPC
1. Defina la clase de producto según **IPC-6012**:
   * **Clase 2:** Electrónica industrial o comercial dedicada.
   * **Clase 3:** Alta confiabilidad crítica (cero vacíos en barriles PTH, cero *breakout* en anillos anulares).
2. Liste explícitamente:
   * Tensión máxima **pico** ($V_{\text{peak}}$, recordando que $V_{\text{peak}} = V_{\text{RMS}} \times \sqrt{2}$ en AC).
   * Corriente continua y transitoria ($\Delta I_{\text{transient}}$) de cada riel de potencia.
   * Frecuencia máxima de reloj y tiempos de subida ($t_r$).
3. **Herramientas MCP:** Ejecute `easyeda_health_check`, `easyeda_project_open` y `easyeda_power_tree_analyze`.

### Fase 2: Esquemático, Red de Potencia (PDN), Terminaciones y Protección ESD
1. **Lea obligatoriamente:** [references/01-esquematico-pdn-esd.md](references/01-esquematico-pdn-esd.md).
2. **Calcule y aplique:**
   * **Desacoplo MCU (AN2586 / AN2867):** $100\,\text{nF}\text{–}1\,\mu\text{F}$ a $< 2\,\text{mm}$ de cada pin $V_{DD}$ y cristal aislado sin trazas digitales debajo.
   * **Impedancia objetivo PDN:** $Z_{\text{target}} = \frac{\Delta V_{\text{allowed}}}{\Delta I_{\text{transient}}}$ y desacoplo en **3 décadas** ($10\,\mu\text{F} + 100\,\text{nF} + 10\,\text{nF}$) respetando $f_{\text{SRF}} = \frac{1}{2\pi\sqrt{\text{ESL}\cdot C}}$.
   * **Terminación serie en relojes/SPI rápidos:** $R_s = Z_{\text{trace}} - Z_{\text{source}}$ colocada en el pin transmisor para lograr $\Gamma = 0$.
   * **Inmunidad ESD (IEC 61000-4-2):** Diodos TVS ultrarrápidos (respuesta $< 0.8\,\text{ns}$, hasta $30\,\text{A}$ en Nivel 4 / $\pm 8\,\text{kV}$ contacto) en cada conector externo.
3. **Herramientas MCP:** `easyeda_design_rules_lookup` (`decoupling`, `bulk-capacitance`), `easyeda_workflow_power_rail`, `easyeda_workflow_decouple_ic`, `easyeda_workflow_connector_breakout`, `easyeda_schematic_validate_netlist`, `easyeda_semantic_erc_auto` y `easyeda_erc_run`.

### Fase 3: Termodinámica de Conductores, Aislamiento (Clearance/Creepage) y Materiales
1. **Lea obligatoriamente:** [references/02-termica-aislamiento-materiales.md](references/02-termica-aislamiento-materiales.md).
2. **Calcule y aplique:**
   * **Ancho de pista por corriente (IPC-2221 / IPC-2152):** $I = k \cdot \Delta T^{0.44} \cdot A_c^{0.725}$ ($k=0.048$ externa, $k=0.024$ interna; ej. para $5\,\text{A}$ a $1\,\text{oz}$ y $\Delta T=10\,^\circ\text{C}$: **$2.770\,\text{mm}$ externa** / **$7.190\,\text{mm}$ interna**) y corrección **IPC-2152** por planos disipadores.
   * **Arreglo de vías térmicas:** $R_{\text{th}} = \frac{L}{k \cdot A}$ ($k = 385\,\text{W/m}\cdot\text{K}$), $R_{\text{total}} = R_{\text{single}}/N$, perforación $0.2\text{–}0.3\,\text{mm}$ y paso $0.5\,\text{mm}$.
   * **Clearance y Creepage (IPC-2221C Tabla 6-1, IEC 60664-1, IEC 62368-1):** Evalúe con **$V_{\text{peak}}$** y columna **B2** en capas externas (la máscara antisoldante normal no es recubrimiento permanente B4). Para $230\,\text{V}_{\text{RMS}}$ ($325\,\text{V}_{\text{peak}}$), exija mínimo $2.50\,\text{mm}$ (IPC-2221C B2), considere el índice CTI del FR-4 (**Grupo IIIa**, $175 \le \text{CTI} < 400\,\text{V}$) y agregue **ranuras fresadas (*milled slots* $> 1.0\,\text{mm}$)** cuando falte distancia superficial.
   * **Laminado base (IPC-4101):** Especifique hoja de datos exacta (ej. **`IPC-4101/126`** con $T_g \ge 150\text{–}170\,^\circ\text{C}$ y $T_d \ge 340\,^\circ\text{C}$ para soldadura sin plomo SAC305 a $260\,^\circ\text{C}$, o **`IPC-4101/129`** libre de halógenos).
3. **Herramientas MCP:** `easyeda_design_rules_lookup` (`trace-width`, `max-current`, `clearance`, `isolation-emc-review`), `easyeda_board_stackup`, `easyeda_board_design_rules` y `easyeda_schematic_sync_to_pcb`.

### Fase 4: Planos GND Continuos, Integridad de Señal (SI) y Ruteo
1. **Lea obligatoriamente:** [references/03-integridad-senal-gnd-ruteo.md](references/03-integridad-senal-gnd-ruteo.md).
2. **Calcule y aplique:**
   * **Continuidad del plano GND:** Mantenga un plano GND sólido debajo de toda señal de alta velocidad. **Prohibido cruzar divisiones de plano (*split planes*)**. Coloque vías de retorno a GND junto a cada vía de cambio de capa y vías dobles en los pads de capacitores de desacoplo.
   * **Impedancia controlada (IPC-2141A):** Calcule geometría Microstrip o Stripline ($W/H \le 7.5$) y pares diferenciales ($85\text{–}100\,\Omega$, desfase intra-par *skew* $\le 5\,\text{mils} / 0.127\,\text{mm}$).
   * **Control de diafonía (*Crosstalk*):** Aplique la regla **$3W$** (separación centro a centro $\ge 3W$) en señales generales y **$5W$** en relojes y líneas críticas.
   * **HDI y Flex (IPC-2226 / IPC-2223E):** En BGA $\le 0.5\,\text{mm}$, priorice microvías escalonadas (*staggered*) sobre apiladas. En flexibles, trace a $90^\circ$ de la línea de doblez y respete radios de $6\times$ (estático) a $150\times$ (dinámico bicapa).
3. **Herramientas MCP:** `easyeda_design_rules_lookup` (`protocol-routing`), `easyeda_pcb_floorplan`, `easyeda_pcb_place_component_group`, `easyeda_pcb_add_zone`, `easyeda_pcb_route_path_plan`, `easyeda_pcb_add_track`, `easyeda_pcb_add_via` y `easyeda_pcb_rebuild_copper`.

### Fase 5: Verificación DFM, Ensamblaje y Auditoría de Producción
1. **Lea obligatoriamente:** [references/04-dfm-ensamblaje-easyeda-mcp.md](references/04-dfm-ensamblaje-easyeda-mcp.md).
2. **Verifique:**
   * **Footprints (IPC-7351B / IPC-7352):** Densidad Nivel A (manual/vibración), Nivel B (reflujo nominal) o Nivel C (ultradenso).
   * **DFM Rígido (IPC-6012):** Anillo anular intacto en Clase 3 ($\ge 1\,\text{mil}$ interno, $\ge 2\,\text{mils}$ externo), cobre en barril PTH ($\ge 20\,\mu\text{m}$ Clase 2, $\ge 25\,\mu\text{m}$ Clase 3 sin vacíos), distancia taladro-cobre $\ge 8\,\text{mils}$ ($0.20\,\text{mm}$) y relación de aspecto $\le 10:1$ en PTH ($\le 1:1$ en microvías).
   * **Criterios de ensamblaje (IPC-A-610J / J-STD-001J / IPC-7095):** Llenado THT $\ge 75\%$, vacíos BGA (*macrovoids*) $\le 25\%$, cero *champagne voids* en Clase 3, contaminación iónica $\le 1.56\,\mu\text{g/cm}^2$ NaCl y control EPA **ANSI/ESD S20.20** ($\le 35\,\text{M}\Omega$).
3. **Herramientas MCP:** Ejecute `easyeda_design_rules_lookup` (`dfm-checklist`), `easyeda_drc_run`, `easyeda_pcb_constraint_check`, `easyeda_pcb_route_geometry_review`, `easyeda_engineering_review` y `easyeda_pcb_production_review` **antes** de ejecutar `easyeda_production_qa_artifacts` o `easyeda_export_gerbers`.

---

## 3. Tabla contra Racionalizaciones (Prohibido Saltar Reglas bajo Presión)

| Excusa del Usuario o del Agente | Realidad Física y Normativa (Respuesta Obligatoria) |
| :--- | :--- |
| *"Estoy apurado, dime un valor rápido sin calcular"* | Los cálculos toman 10 segundos y evitan que la placa se queme o falle por EMI. Entregue el valor exacto calculado con su norma IPC/IEC. |
| *"La máscara antisoldante protege los 230 V AC"* | Falso. Según **IPC-2221C**, la máscara antisoldante normal no es un recubrimiento permanente certificado (B4). Debe usar la columna **B2** ($2.50\,\text{mm}$ para $325\,\text{V}_{\text{peak}}$) y **IEC 60664-1**. |
| *"Con un capacitor de 100 nF basta para todo el riel"* | Por encima de su $f_{\text{SRF}}$, un solo capacitor se vuelve inductivo. Debe calcular $Z_{\text{target}}$ y aplicar desacoplo en **3 décadas** con vías directas al plano. |
| *"Exporta los Gerbers directo con `easyeda_export_gerbers`"* | Prohibido exportar sin ejecutar antes `easyeda_erc_run`, `easyeda_drc_run`, `easyeda_pcb_route_geometry_review` y `easyeda_engineering_review`. |

---

## 4. Banderas Rojas — DETÉNGASE y Corrija Inmediatamente

- Evaluar aislamiento eléctrico en AC usando tensión RMS en lugar de tensión pico ($V_{\text{peak}}$).
- Omitir el cálculo de ancho de pista (**IPC-2221 / IPC-2152**) en rieles de potencia.
- Trazar relojes o buses rápidos (SPI, USB, Ethernet) cruzando cortes en el plano de retorno GND.
- Omitir diodos TVS (**IEC 61000-4-2**) en conectores externos o resistencias serie ($R_s$) en líneas rápidas.
- Especificar "FR-4 genérico" sin indicar la hoja **IPC-4101** (`/126` o `/129` para reflujo sin plomo SAC305).
