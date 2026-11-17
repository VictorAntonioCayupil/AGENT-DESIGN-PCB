# Manual 04: Footprints, DFM Rígido, Criterios de Ensamblaje y Orquestación con EasyEDA MCP

> **Estándares aplicados:** IPC-7351B / IPC-7352 (Geometría de Footprints), IPC-6012 (DFM Placas Rígidas Clase 2 y Clase 3), IPC-A-610J y J-STD-001J (Aceptación de Ensamblaje y Soldadura), IPC-7095 (Inspección BGA), IPC-TM-650 (Confiabilidad Termomecánica), ANSI/ESD S20.20 (Área EPA), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Modelado Geométrico de Footprints y Niveles de Densidad (IPC-7351B e IPC-7352)

Las normas **IPC-7351B** y su evolución **IPC-7352** dimensionan los pads de cobre calculando las metas de filete de soldadura (*Toe* en la punta, *Heel* en el talón y *Side* en los laterales) mediante suma estadística cuadrática media (**RMS**) de las tolerancias de componente, fabricación de PCB y colocación robótica.

### Tabla de Selección del Nivel de Densidad de Pads

| Nivel IPC-7351B / 7352 | Protrusión de Pads y Patio (*Courtyard*) | Aplicación Recomendada |
| :---: | :--- | :--- |
| **Nivel A (Densidad Mínima / Pads Máximos)** | Pads extendidos y amplio margen de patio. | Soldadura por ola, ensamblaje o retrabajo manual, equipos sometidos a alta vibración o choque mecánico. |
| **Nivel B (Densidad Nominal / Mediana)** | Dimensiones balanceadas para hornos de reflujo estándar. | **Estándar por defecto** para electrónica comercial, industrial y automotriz automatizada. |
| **Nivel C (Densidad Máxima / Pads Mínimos)** | Protrusiones reducidas al mínimo físico. | Dispositivos portátiles ultracompactos, implantes médicos y módulos HDI con restricción severa de área. |

---

## 2. Diseño para Manufacturabilidad (DFM) en Placas Rígidas (IPC-6012)

> [!WARNING]
> **Rechazo en fábrica o rotura de vías en campo:** Si diseña con anillos anulares insuficientes o perforaciones con relación de aspecto excesiva, la broca romperá la conexión interna (*breakout*) o el baño electrolítico no depositará cobre suficiente en el centro del barril.

### 2.1. Comparativa Normativa IPC-6012: Clase 2 vs. Clase 3

| Parámetro Geométrico / Metalúrgico | IPC-6012 Clase 2 (Electrónica Dedicada / Industrial) | IPC-6012 Clase 3 (Alta Confiabilidad / Crítica / Aeroespacial) |
| :--- | :--- | :--- |
| **Anillo Anular Interno (*Internal Annular Ring*)** | Se permite tangencia y rotura (*breakout*) de hasta $90^\circ$ en direcciones no críticas. | **Prohibido el *breakout***. Exige anillo intacto mínimo de $1\,\text{mil}$ ($25\,\mu\text{m}$). |
| **Anillo Anular Externo (*External Annular Ring*)** | Se permite tangencia; rotura máxima de $90^\circ$ si no afecta uniones. | **Prohibido el *breakout***. Exige anillo intacto mínimo de $2\,\text{mils}$ ($50\,\mu\text{m}$). |
| **Espesor de Cobre en Barril PTH** | Promedio $\ge 20\,\mu\text{m}$ (tolera 1 vacío microscópico bajo umbral). | Promedio $\ge 25\,\mu\text{m}$ (mínimo absoluto $\ge 20\,\mu\text{m}$ en cualquier punto; **cero vacíos permitidos**). |
| **Recubrimiento Envolvente (*Copper Wrap Plating*)** | Estándar de proceso. | Obligatorio en estructuras *Via-in-Pad* ($\ge 0.472\,\text{mils} / 12\,\mu\text{m}$) para evitar grietas de esquina. |
| **Distancia Taladro a Cobre (*Drill-to-Copper*)** | Mínimo seguro de $8\,\text{mils}$ ($\approx 0.20\,\text{mm}$). | Mínimo seguro de $8\,\text{mils}$ a $10\,\text{mils}$ ($0.20\text{–}0.25\,\text{mm}$). |

### 2.2. Relación de Aspecto de Perforación (*Aspect Ratio*)

$$\text{Aspect Ratio} = \frac{\text{Espesor Total del PCB}}{\text{Diámetro Final del Agujero}}$$

1. **Vías pasantes mecánicas (PTH):** Mantenga la relación de aspecto en **$\le 10:1$** (máximo absoluto industrial $12:1$). Por ejemplo, en una placa estándar de $1.6\,\text{mm}$ de espesor, no utilice perforaciones mecánicas menores de $0.16\,\text{mm}$ (recomendado $\ge 0.20\,\text{mm}$ para bajo costo).
2. **Microvías láser ciegas:** Mantenga la relación de aspecto entre **$0.75:1$ y $1:1$** para garantizar el llenado electrolítico completo sin bolsas de aire.

---

## 3. Criterios de Aceptación de Ensamblaje y Soldadura (IPC-A-610J, J-STD-001J e IPC-7095)

Las revisiones **J** de **IPC-A-610** y **J-STD-001** eliminaron la antigua categoría *"Target"*; toda inspección clasifica cada unión estrictamente como **Aceptable (*Acceptable*)**, **Indicador de Proceso (*Process Indicator*)** o **Defecto (*Defect*)**.

### 3.1. Criterios de Mojado SMT y Llenado Tubular THT

1. **Terminales SMT *Gull-Wing* (QFP, SOIC, SOP):** En Clase 3, verifique que la soldadura forme un menisco continuo y visible que ascienda por el talón (*heel fillet*) del pin.
2. **Llenado vertical de barriles THT:** En Clase 2 y Clase 3, exija un llenado vertical de soldadura de al menos el **$75\%$** de la altura del barril, con mojado circunferencial en el lado de inserción ($\ge 270^\circ$ en Clase 3).
3. **Ángulo de contacto de mojado:** Verifique que el ángulo entre la soldadura y el pad sea siempre **$< 90^\circ$**. Un ángulo $> 90^\circ$ indica soldadura fría o falta de desoxidación.

### 3.2. Control de Vacíos (*Voids*) en Encapsulados BGA y BTC (IPC-7095 e IPC-A-610J)

> [!CAUTION]
> **Fallo prematuro en esferas BGA:** Los componentes de terminación inferior (BGA, QFN, LGA) requieren inspección por rayos X (AXI 2.5D/3D). Distinga y controle las tres patologías críticas de vaciado:

| Patología en Esfera BGA | Descripción Física | Límite Normativo (IPC-A-610J / IPC-7095) |
| :--- | :--- | :--- |
| **1. *Macrovoids* (Vacíos Volumétricos)** | Burbujas de gases de fundente atrapadas dentro del cuerpo de la esfera durante el reflujo. | El área acumulada de vacíos **no debe superar el $25\%$** del área proyectada de la bola BGA. |
| **2. *Planar Microvoids* (*Champagne Voids*)** | Hilera de microburbujas planas en la interfaz intermetálica pad-esfera (asociada a *Black Pad* en acabados ENIG con exceso de fósforo). | **Tolerancia Cero en Clase 3** (fractura catastrófica ante vibración o caída). |
| **3. *Head-in-Pillow* (HiP)** | La esfera del BGA descansa sobre la pasta fundida sin fusionarse debido a alabeo térmico (*warpage*) durante el reflujo. | **Defecto crítico en todas las clases** (unión mecánicamente abierta). |

### 3.3. Limpieza Iónica (J-STD-001J) y Área Protegida ESD (ANSI/ESD S20.20)

1. **Límite de contaminación iónica:** Para prevenir el crecimiento de dendritas metálicas por migración electroquímica (ECM), los residuos iónicos extraídos tras la limpieza no deben superar **$1.56\,\mu\text{g/cm}^2$ ($10.06\,\mu\text{g/in}^2$)** de equivalente de cloruro de sodio ($\text{NaCl}$).
2. **Control de estación de ensamblaje (ANSI/ESD S20.20):** Todo operador que manipule la placa en un Área Protegida contra ESD (EPA) debe utilizar pulsera o calzado conductivo con resistencia total a tierra **$\le 3.5 \times 10^7\,\Omega$ ($35\,\text{M}\Omega$)**.

---

## 4. Validación Termomecánica Acelerada (IPC-TM-650)

Cuando el diseño requiera calificación estructural de lotes de fabricación, especifique en las notas de fabricación del plano (*Fab Notes*) los siguientes ensayos sobre cupones de prueba:
1. **Choque térmico por flotación en soldadura (`IPC-TM-650 Método 2.6.8`):** Horneado previo de $6\,\text{h}$, flotación en baño de soldadura fundida a **$288\,^\circ\text{C}$ durante $10\,\text{s}$** y microsección metalográfica a $100\times$ para verificar ausencia de grietas en el barril o levantamiento de pads.
2. **Ciclado térmico y prueba IST (`IPC-TM-650 Métodos 2.6.7.2C y 2.6.26A`):** Ciclado entre **$-55\,^\circ\text{C}$ y $+125\,^\circ\text{C}$** en redes *daisy-chain*; se considera fallo si la resistencia eléctrica de la red de vías aumenta más de un **$5\%$ a $10\%$**.

---

## 5. Matriz de Orquestación y Verificación con `easyeda-mcp-pro`

Al finalizar el diseño o auditar un proyecto existente en EasyEDA Pro, ejecute esta secuencia obligatoria de herramientas MCP:

| Paso | Herramienta de `easyeda-mcp-pro` | Objetivo de Verificación Normativa |
| :---: | :--- | :--- |
| **1** | `easyeda_design_rules_lookup` (`topic: "dfm-checklist"`) | Consultar la lista de chequeo DFM para cobre, taladros, máscara antisoldante, serigrafía y panelizado. |
| **2** | `easyeda_erc_run` y `easyeda_semantic_erc_auto` | Confirmar integridad lógica, polaridades y ausencia de redes sin fuente en el esquemático. |
| **3** | `easyeda_drc_run` y `easyeda_pcb_constraint_check` | Verificar el cumplimiento físico de *Clearance*, anchos mínimos de pista y anillos anulares en el PCB. |
| **4** | `easyeda_pcb_route_geometry_review` | Auditar cuellos de botella (*neck-downs*), ángulos agudos (*acid traps*) y retorno de pistas. |
| **5** | `easyeda_engineering_review` y `easyeda_pcb_production_review` | Generar el informe consolidado de ingeniería con hallazgos estables, procedencia de reglas e incógnitas explícitas. |
| **6** | `easyeda_production_qa_artifacts` / `easyeda_export_gerbers` / `easyeda_export_pick_place` | Exportar los archivos de fabricación (Gerber, BOM y Pick & Place) únicamente cuando `easyeda_drc_run` reporte **cero errores**. |

> [!IMPORTANT]
> **Regla de honestidad técnica:** Las herramientas `easyeda_design_rules_lookup` y `easyeda_engineering_review` reportan advertencias o estados `UNKNOWN` cuando una distancia de *Creepage* o ranura mecánica no puede medirse automáticamente desde las primitivas 2D. Nunca declare una placa como "Certificada en Seguridad IEC" sin verificar visual y dimensionalmente las ranuras y distancias físicas en el lienzo.
