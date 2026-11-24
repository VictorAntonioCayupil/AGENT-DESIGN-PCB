# Manual 14: Maestría en EasyEDA Pro, Beneficios Nativos y Acoplamiento Total con MCP

> **Propósito:** Explotar al 100 % las ventajas nativas de **EasyEDA Pro (v2.3 / v3.2.x)** —arquitectura *Device-First*, biblioteca LCSC con modelos 3D, simulación SPICE integrada, stackups oficiales JLCPCB, *Auto-Fix* de esquemático, transacciones seguras con *rollback* y flujo 1-Click a fabricación PCBA— acopladas con exactitud a las herramientas reales de **`easyeda-mcp-pro`** y **`agent-design-pcb-mcp`**.  
> **Estándares aplicados:** ISO 24495-1 (Lenguaje Claro), ISO/IEC 82079-1, IPC-2221C / IPC-2152 / IPC-7351B.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Por qué EasyEDA Pro Cambia las Reglas del Juego (y Cómo Debe Aprovecharlo el Agente)

A diferencia de flujos tradicionales fragmentados (donde el símbolo, el *footprint*, el modelo 3D y el stock de fábrica viven en sitios distintos), **EasyEDA Pro** unifica toda la ingeniería en un solo ecosistema nativo:

| Beneficio Nativo de EasyEDA Pro | Qué Hace el Agente para Explotarlo (Herramientas Reales) | Ventaja Directa para el Usuario |
| :--- | :--- | :--- |
| **1. Arquitectura *Device-First* (Símbolo + Footprint + 3D + LCSC ID en un solo objeto)** | Busca y verifica dispositivos reales con **`easyeda_schematic_search_device`**, **`easyeda_catalog_verify_device`** y **`easyeda_schematic_device_subparts`** antes de colocar nada. | Cero *footprints* huérfanos, cero desajustes Pin/Pad y modelo 3D automático desde el minuto 1. |
| **2. Catálogo Vivo LCSC + Optimización JLCPCB Basic vs. Extended** | Audita el BOM con **`easyeda_bom_generate`**, **`easyeda_bom_validate`**, **`easyeda_bom_sourcing`**, **`easyeda_bom_quality_report`** y **`easyeda_jlcpcb_quote_workflow`**. | Ahorra \$3 USD por cada pieza *Extended* reemplazada por una *Basic Part* en ensamblaje SMT JLCPCB. |
| **3. Flujos de Bloques Inteligentes y Limpieza Automática del Esquemático** | Usa **`easyeda_workflow_power_rail`**, **`easyeda_workflow_decouple_ic`**, **`easyeda_workflow_connector_breakout`**, **`easyeda_power_tree_analyze`**, **`easyeda_schematic_layout_qa`** y **`easyeda_schematic_layout_autofix`**. | Esquemáticos limpios, legibles, sin colisiones y con el árbol de potencia auditado automáticamente. |
| **4. Simulación SPICE Integrada en el Propio Esquemático** | Ejecuta **`easyeda_simulate_operating_point`** (DC) y **`easyeda_simulate_transient`** (tiempo) antes de pasar al PCB. | Valida divisores, corrientes de polarización, filtros RC y arranques antes de gastar en fabricar. |
| **5. Stackups Oficiales de Impedancia Controlada JLCPCB** | Consulta **`easyeda_board_stackup`**, **`easyeda_board_design_rules`** y **`easyeda_design_rules_lookup`** y cruza los parámetros exactos con **`pcb_normative_impedance_si`**. | Pistas USB ($90\,\Omega$ diferencial) y antenas RF ($50\,\Omega$) calculadas exactamente para la prensa de JLCPCB (`JLC04161H-7628` / `3313` / `2313`). |
| **6. Navegación Visual Activa y Capturas Quirúrgicas del Lienzo** | Enfoca cualquier error con **`easyeda_canvas_locate`** y captura evidencia con **`easyeda_canvas_capture`** / **`easyeda_canvas_capture_region`**. | El usuario ve exactamente qué componente o pista se revisó, sin buscar a ciegas en la placa. |
| **7. Transacciones Seguras + Verificación Matemática de Escritura** | Envuelve cada lote de cambios en **`easyeda_project_begin_transaction`** $\rightarrow$ **`easyeda_schematic_verify_write`** / **`easyeda_post_write_qa`** $\rightarrow$ **`easyeda_project_commit_transaction`** (o **`rollback`**). | Si una escritura rompe una red o genera colisiones, se revierte limpiamente sin dañar el proyecto. |
| **8. Exportación Completa 1-Click para Fábrica y Laboratorio 3D** | Genera paquete integral con **`easyeda_production_qa_artifacts`**, **`easyeda_export_gerbers`**, **`easyeda_export_pick_place`**, **`easyeda_bom_export`**, **`easyeda_export_pdf`** y vista 3D STEP (`PCB_ManufactureData.get3DFile`). | Archivos listos para subir a JLCPCB, JLCDFM y validar encaje mecánico en caja 3D. |

---

## 2. Flujo Maestro Acoplado a EasyEDA Pro (De Cero a Gerber en 7 Etapas)

### Etapa 1: Diagnóstico de Conexión y Contexto de Documento (Obligatorio al Iniciar)
1. Verificar puente y proyecto:
   * `easyeda_health_check` y `easyeda_bridge_status`.
   * `easyeda_project_list` $\rightarrow$ `easyeda_project_open` (si aplica).
2. **Regla de Foco de Documento en EasyEDA Pro:**
   * EasyEDA Pro separa las pestañas de **Esquemático** (`expectedSchematicPageUuid`) y **PCB** (`expectedPcbUuid`).
   * **Nunca** ejecute herramientas de PCB con el esquemático enfocado ni `easyeda_erc_run` con el PCB enfocado; pase siempre el UUID esperado para impedir escrituras accidentales en otro documento.
   * Si el usuario importó un diseño previo desde KiCad, Altium o EasyEDA Standard, ejecute primero **`easyeda_schematic_audit_imported_design`** y **`easyeda_schematic_preview_imported_normalization`**.

### Etapa 2: Selección *Device-First* (Acoplada a Política Cero Invención)
1. Para cada componente aprobado en el **PCB de Conexión Interactivo** (`pcb_verify_connection_board` = `APPROVED_FOR_EASYEDA`):
   * Busque el dispositivo real con **`easyeda_schematic_search_device`**.
   * Valide que el dispositivo exista, tenga stock y huella real con **`easyeda_catalog_verify_device`**.
   * Si el IC es multi-parte (ej. LM358, comparadores, MCU grande), inspeccione subpartes con **`easyeda_schematic_device_subparts`**.
   * **Regla de oro:** Si un componente no existe en LCSC/biblioteca o sus pines no coinciden con la ficha técnica oficial, **deténgase y solicite confirmación o datasheet al usuario**; nunca sustituya silenciosamente por un símbolo genérico.

### Etapa 3: Construcción Transaccional y Limpia del Esquemático
1. Obtenga una huella base de conectividad con **`easyeda_schematic_connectivity_fingerprint`** (si el esquemático ya tiene contenido) y planifique zonas libres con **`easyeda_schematic_plan_safe_region`** / **`easyeda_schematic_plan_layout`**.
2. Abra transacción segura: **`easyeda_project_begin_transaction`**.
3. Coloque bloques normativos aprovechando los flujos nativos de EasyEDA Pro:
   * **`easyeda_workflow_power_rail`**: rieles de alimentación regulados.
   * **`easyeda_workflow_decouple_ic`**: desacoplo local por cada par VDD/GND del IC.
   * **`easyeda_workflow_connector_breakout`**: conectores con etiquetas ordenadas y protección ESD.
   * **`easyeda_schematic_place_component`** + **`easyeda_schematic_connect_pins_by_net`** / **`easyeda_schematic_connect_pin_to_net`** / **`easyeda_schematic_create_net_flag`** / **`easyeda_schematic_create_net_port`**.
   * **`easyeda_schematic_set_pin_no_connect`**: obligatoria en todo pin no utilizado.
   * **`easyeda_schematic_set_title_block`**: rellenar cajetín con nombre del proyecto, autor, revisión y fecha.
4. Audite el esquemático ANTES de hacer commit:
   * **`easyeda_schematic_check_collisions`** y **`easyeda_schematic_layout_qa`** (aplicar **`easyeda_schematic_layout_autofix`** si hay solapamientos).
   * **`easyeda_power_tree_analyze`**: verificar que ningún regulador quede sobrecargado ni falte alimentación en algún riel.
   * **`easyeda_semantic_erc_auto`** + **`easyeda_erc_run`** + **`easyeda_schematic_validate_netlist`**.
   * **`easyeda_schematic_capture_full_page`** para inspección visual.
5. Cierre con **`easyeda_project_commit_transaction`** (o **`easyeda_project_rollback_transaction`** si hubo errores críticos).

### Etapa 4: Simulación SPICE y Auditoría de Compras JLCPCB/LCSC
1. En circuitos analógicos, divisores ADC, filtros RC o etapas de potencia: ejecute **`easyeda_simulate_operating_point`** y/o **`easyeda_simulate_transient`**.
2. Genere y audite el BOM integrado con LCSC:
   * **`easyeda_bom_generate`** $\rightarrow$ **`easyeda_bom_validate`** $\rightarrow$ **`easyeda_bom_sourcing`** $\rightarrow$ **`easyeda_bom_quality_report`**.
   * Identifique piezas *Extended* reemplazables por *Basic Parts* y muestre el ahorro exacto al usuario con **`easyeda_jlcpcb_quote_workflow`**.

### Etapa 5: Sincronización al PCB y Floorplan Basado en el PCB de Conexión
1. Sincronice hacia el PCB: **`easyeda_schematic_sync_to_pcb`**.
2. Inspeccione geometría y reglas reales del PCB:
   * **`easyeda_board_dimensions`**, **`easyeda_board_layers`**, **`easyeda_board_stackup`** y **`easyeda_board_design_rules`**.
3. Aplique el posicionamiento verificado del usuario:
   * Verifique cero colisiones con **`easyeda_floorplan_verifier`** (o `pcb_verify_connection_board`).
   * Ejecute **`easyeda_pcb_floorplan`** $\rightarrow$ **`easyeda_pcb_place_batch`** / **`easyeda_pcb_place_component_group`** (recordando que en EasyEDA Pro las coordenadas nativas están en **mils** y el eje **$Y$ crece hacia abajo**).
   * Capture evidencia visual con **`easyeda_canvas_capture`**.

### Etapa 6: Ruteo Normativo, Vías de Costura GND y Planos de Cobre
1. Calcule cada ancho crítico con **`pcb_normative_trace_calculator`**, cada aislamiento con **`pcb_normative_clearance_creepage`** y cada impedancia con **`pcb_normative_impedance_si`** usando los espesores reales de **`easyeda_board_stackup`**.
2. Planifique y trace rutas críticas manualmente antes de pensar en autoruteo:
   * **`easyeda_pcb_export_route_context`** $\rightarrow$ **`easyeda_pcb_route_path_plan`** $\rightarrow$ **`easyeda_pcb_add_track`** + **`easyeda_pcb_add_via`**.
   * Use **`easyeda_pcb_autoroute`** únicamente en redes digitales no críticas de baja velocidad, nunca en *Hot Loops* de Buck, cristal oscilador, pares diferenciales ni líneas de alta tensión.
3. Añada serigrafía clara (polaridad, voltaje de borneras, nombre del proyecto, revisión) con **`easyeda_pcb_add_text`** y **`easyeda_pcb_add_silkscreen_line`**.
4. **Planos de Cobre (`Pour`) y Zonas Keep-Out:**
   * Antes de crear o modificar zonas, revise con **`easyeda_pcb_pours`**, **`easyeda_pcb_regions`** y **`easyeda_pcb_zone_preflight`**.
   * Para antenas RF y aislamiento galvánico, use **`easyeda_pcb_add_region`** (`No Solid` / `Board Cutout`).

### Etapa 7: Revisión Integral de Producción y Exportación
Ejecute esta escalera de calidad **sin saltar ningún paso**:
1. **`easyeda_rule_check_summary`** (`easyeda_erc_run` + `easyeda_drc_run` $\rightarrow$ 0 errores).
2. **`easyeda_pcb_constraint_check`** + **`easyeda_pcb_constraint_report`**.
3. **`easyeda_pcb_route_geometry_review`** (detecta ángulos agudos, cuellos de botella, stubs y rutas subóptimas).
4. **`easyeda_pcb_production_review`** + **`easyeda_engineering_review`**.
5. Solo con todo en verde: **`easyeda_production_qa_artifacts`**, **`easyeda_export_gerbers`**, **`easyeda_export_pick_place`**, **`easyeda_bom_export`** y **`easyeda_export_pdf`**.

---

## 3. Stackups Reales de JLCPCB en EasyEDA Pro (Referencia Rápida para Impedancia)

Cuando el usuario fabrique en **JLCPCB** (el fabricante nativo integrado en EasyEDA Pro), utilice estos perfiles oficiales al calcular impedancias en `pcb_normative_impedance_si`:

| Stackup Oficial JLCPCB | Capas | Dieléctrico Top $\leftrightarrow$ L2 ($H$) | $\varepsilon_r$ Típico | Uso Recomendado |
| :--- | :---: | :---: | :---: | :--- |
| **Estándar 2 Capas ($1.6\,\text{mm}$)** | 2 | $1.53\,\text{mm}$ (FR-4 core) | $4.5$ | Baja velocidad, sensores IoT, módulos con antena integrada fuera del borde. *(No apto para $50\,\Omega$ fino: requeriría pista de $\approx 2.9\,\text{mm}$).* |
| **`JLC04161H-7628`** | 4 | $0.2104\,\text{mm}$ (Prepreg 7628) | $4.6$ | Placas 4 capas económicas (MCU + USB $90\,\Omega$ + planos GND/3V3 sólidos). |
| **`JLC04161H-3313`** *(Recomendado RF/USB)* | 4 | $0.0994\,\text{mm}$ (Prepreg 3313) | $4.05$ | **Ideal para impedancia controlada:** pista $50\,\Omega$ angosta ($\approx 0.16\,\text{mm}$) y par diferencial $90\,\Omega$ compacto para ESP32/STM32/USB-HS. |
| **`JLC04161H-2313`** | 4 | $0.10\,\text{mm}$ (Prepreg 2313) | $4.05$ | Alternativa de alta estabilidad dieléctrica para RF y señales rápidas. |

---

## 4. Manejo Real de Peculiaridades del Puente EasyEDA Pro 3.2.x + `easyeda-mcp-pro`

Estas reglas provienen de pruebas reales en vivo contra **EasyEDA Pro 3.2.209** y evitan bloqueos o falsas alarmas:

1. **Bloqueo de `easyeda_pcb_rebuild_copper` en múltiples capas:**
   * Si la placa tiene planos de cobre en Top (`POUR1`) y Bottom (`POUR4`) y `easyeda_pcb_rebuild_copper` reporta *rebuild source mismatch* o *reconciliation lock*, **no reintente en bucle**.
   * Guarde con `easyeda_api_call` (`PCB_Document.save`), solicite al usuario presionar **`Shift + B`** (Reconstruir Todo el Cobre) en la ventana de EasyEDA Pro, y vuelva a ejecutar `easyeda_drc_run`.
2. **Creación de Zonas (`easyeda_pcb_add_zone`):**
   * Si `easyeda_bridge_status` indica `native_zone_safety.publicApplyEnabled: false`, informe claramente al usuario en vez de fallar repetidamente; use `easyeda_pcb_zone_preflight` para validar el polígono y guíe al usuario a trazar el Copper Area (`Shift+E`) o use `easyeda_pcb_add_region` para regiones sólidas/keep-out.
3. **Verificación de Guardado (`easyeda_project_save`):**
   * Si `easyeda_project_save` devuelve `status: "persistence_unverified"` con `native_acknowledged: true`, ejecute `PCB_Document.save` y recuerde al usuario presionar **`Ctrl + S`** en EasyEDA Pro antes de cerrar la aplicación.
4. **Coordenadas Nativas de PCB:**
   * Todas las coordenadas de `easyeda_pcb_add_track`, `easyeda_pcb_add_via` y `easyeda_pcb_place_batch` se expresan en **mils** ($1\,\text{mm} = 39.3701\,\text{mil}$) con eje **$Y$ positivo hacia abajo**. Convierta siempre usando `easyeda_floorplan_verifier` o `pcb_verify_connection_board`.
5. **Diagnóstico de Errores DRC en Net `GND`:**
   * Cuando `easyeda_drc_run` reporte `"{obj1} is disconnected from other objects of the same network"` en `GND`, lea los pads con `easyeda_api_read` (`PCB_PrimitivePad.getAll`) y los tracks con `easyeda_pcb_tracks` (paginado) para identificar los pads SMD de Capa 1 aislados y conectarlos al plano GND de Capa 2 mediante vías de desacoplo dedicadas (`outerDiameter: 24`, `holeSize: 12`, clearance $\ge 8\,\text{mil}$).
