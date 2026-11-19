# Manual 10: Arquitectura Multi-Agente para Ingeniería Electrónica y Armado de PCB

> **Estándares aplicados:** Ingeniería de Sistemas Concurrente, Despacho de Sub-Agentes Especializados, Gestión Transaccional sobre EasyEDA Pro MCP, ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. ¿Cómo Opera `AGENT-DESIGN-PCB` como un Equipo de Agentes?

En proyectos electrónicos completos (que combinan microcontroladores, etapas de potencia, sensores, compras en múltiples mercados y ruteo multicapa), un solo hilo de conversación puede saturarse si intenta hacer todo a la vez.

Esta Skill permite que el Agente Principal actúe de dos maneras según la complejidad del proyecto:
* **Modo Ingeniero Único Secuencial (Proyectos pequeños o medianos):** Un solo agente asume los 4 roles especializados en orden (Fase 0 a Fase 5).
* **Modo Escuadrón Multi-Agente (Proyectos complejos o auditorías paralelas):** El Agente Coordinador despacha hasta **4 Sub-Agentes Especialistas**, asignando a cada uno sus manuales normativos exclusivos y consolidando sus resultados en `HARDWARE-SPEC.md`, `BOM-SOURCING.md` y `BRINGUP-CHECKLIST.md`.

---

## 2. Los 4 Roles Especialistas del Equipo de Ingeniería

| Rol del Agente | Manuales Normativos que Domina | Responsabilidad y Entregable Exacto | Herramientas que Ejecuta |
| :--- | :---: | :--- | :--- |
| **1. Agente Arquitecto de Circuito, MCU y Protecciones** | **Manuales `00`, `01`, `05`, `07`, `08`** | Entrevista al usuario, define el árbol de potencia ($Z_{\text{target}}$), selecciona el MCU evitando pines trampa (*strapping* / `ADC2`), dimensiona bloques (USB-C, Buck/LDO, I2C, RS-485, relés) y blinda las entradas (inversión de polaridad, PPTC/eFuse, MOV+TVS **IEC 61000-4-2 / 4-5** y aislamiento galvánico). | `easyeda_project_open`, `easyeda_power_tree_analyze`, `easyeda_workflow_*`, `easyeda_simulate_*`, `easyeda_semantic_erc_auto`, `easyeda_erc_run`. |
| **2. Agente Gestor de Compras y Huellas (*Sourcing Manager*)** | **Manuales `06`, `04` (Sección 1)** | Audita la lista de materiales (BOM). Verifica stock y prioriza *Basic Parts* en **EasyEDA Pro / LCSC / JLCPCB**; busca módulos, conectores y baterías en **AliExpress** ($\ge 95\%$, $\ge 4.7\star$, detector de chips falsos) y **Alibaba** (*Verified Supplier*, *Trade Assurance*, MOQ) confirmando que las medidas físicas calcen con el *footprint* (**IPC-7351B Nivel A/B/C**). | `easyeda_catalog_verify_device`, `easyeda_bom_sourcing`, `easyeda_bom_quality_report`, `search_web` (`aliexpress.com`, `alibaba.com`), subagente `browser`. |
| **3. Agente Ingeniero de Layout, Térmica, SI/EMC y RF** | **Manuales `02`, `03`, `08` (Sección 3), `11`** | Define el *Stackup* (**IPC-4101/126**), calcula anchos de pista por corriente (**IPC-2221 / IPC-2152**), matrices de vías térmicas ($R_{\text{th}}$), distancias de *Clearance* y *Creepage* (**IPC-2221C / IEC 60664-1** + ranuras `Board Cutout` $>1\,\text{mm}$), planos **GND continuos** (`Keep Island = No`, `Shift+B`), impedancia $Z_0$ (**IPC-2141A**), reglas $3W/5W$ y zonas *Keep-Out* (`No Solid`) de antenas RF. | `easyeda_board_stackup`, `easyeda_board_design_rules`, `easyeda_pcb_floorplan`, `easyeda_pcb_add_zone`, `easyeda_pcb_add_region`, `easyeda_pcb_route_path_plan`, `easyeda_pcb_add_track`, `easyeda_pcb_add_via`, `easyeda_pcb_rebuild_copper`. |
| **4. Agente Auditor DFM, Ensamblaje y Laboratorio (*Bring-Up*)** | **Manuales `04`, `09`, `11` (Sección 4)** | Verifica anillos anulares y relación de aspecto (**IPC-6012** Clase 2/3), criterios de soldadura y vacíos BGA (**IPC-A-610J / IPC-7095**), inserta puntos de prueba (`TP`) y puentes de aislamiento de $0\,\Omega$ (DFT), corre DRC final, audita anatomía de archivos Gerber (`.GKO`, `.GTL/.GBL`, `.GTS/.GBS`, `.DRL`) y guía al usuario en el encendido en banco (*Bring-Up* con fuente limitada y multímetro **`ut803`**). | `easyeda_drc_run`, `easyeda_pcb_constraint_check`, `easyeda_pcb_route_geometry_review`, `easyeda_engineering_review`, `easyeda_production_qa_artifacts`, `ut803_*`. |

---

## 3. Regla de Sincronización para Evitar Conflictos en EasyEDA Pro

> [!IMPORTANT]
> **Un solo escritor a la vez sobre el lienzo de EasyEDA Pro:** Cuando utilice múltiples sub-agentes en paralelo, los sub-agentes de investigación (como el **Agente 2 de Compras en LCSC/AliExpress/Alibaba** y el **Agente de Cálculo Normativo Térmico/PDN**) pueden trabajar simultáneamente en paralelo, pero las escrituras sobre el archivo de EasyEDA Pro (`place_component`, `add_wire`, `add_track`) deben ejecutarse de forma secuencial y dentro de transacciones (`easyeda_project_begin_transaction` $\rightarrow$ `easyeda_project_commit_transaction`).

---

## 4. Plantilla de Prompt para Despachar Sub-Agentes Especialistas

Cuando el Agente Coordinador invoque a un sub-agente (mediante `invoke_subagent`), debe indicarle explícitamente qué manual leer y qué tabla devolver:

* **Ejemplo para el Sub-Agente Gestor de Compras (Agente 2):**
  > *"Lee `skills/designing-pcb-normative/references/06-copiloto-easyeda-sourcing-global.md` y la ficha `HARDWARE-SPEC.md`. Audita todos los componentes del proyecto: cotiza los pasivos e integrados críticos en LCSC (priorizando Basic Parts) y busca los módulos, conectores y carcasas en AliExpress/Alibaba cumpliendo los filtros de reputación ($\ge 95\%$, $\ge 4.7\star$, Verified Supplier) y anti-falsificación ($<40\%$ precio oficial). Devuelve la tabla completa siguiendo `templates/BOM-SOURCING.template.md`."*

* **Ejemplo para el Sub-Agente Auditor de Ingeniería y DFM (Agente 4):**
  > *"Lee `skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md` y `09-simulacion-dft-bringup-laboratorio.md`. Revisa el proyecto para verificar el cumplimiento de IPC-6012, IPC-2221C (tensión pico), continuidad del plano GND, presencia de puntos de prueba (`TP_GND`, `TP_3V3`, `TP_5V`) y puentes de $0\,\Omega$, y genera la lista de puesta en marcha siguiendo `templates/BRINGUP-CHECKLIST.template.md`."*
