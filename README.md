# AGENT-DESIGN-PCB (v4.3) — Ingeniero Electrónico Acoplado a EasyEDA Pro, Servidor MCP Normativo y Co-Piloto de Hardware

> **Una iniciativa de S&D MMCALL para la comunidad.**  
> Creado con el afán de ayudar a ingenieros, estudiantes, *makers* y desarrolladores a formular, proteger, diseñar, cotizar, armar y poner en marcha placas electrónicas (PCB) de forma correcta, acoplado nativamente a **EasyEDA Pro (Device-First + LCSC/JLCPCB + Stackups Oficiales + SPICE + Transacciones seguras)**, basándose en física real, normas internacionales (**IPC**, **IEC**, **J-STD**, **ANSI/ESD**), política de **Cero Invención (*Datasheet-First*)**, un **servidor MCP nativo con 8 motores deterministas** y gestión inteligente de proveedores (**EasyEDA Pro / LCSC / JLCPCB**, **AliExpress** y **Alibaba**).

[![Versión: 4.3](https://img.shields.io/badge/Versión-4.3%20EasyEDA%20Pro%20Native%20%2B%20Datasheet--First-brightgreen.svg)](#1-qué-hace-este-proyecto)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Norma de Redacción: ISO 24495-1](https://img.shields.io/badge/Documentación-ISO%2024495--1%20%7C%20ISO%2FIEC%2082079--1-success.svg)](#3-estructura-del-repositorio)
[![Servidor MCP: agent-design-pcb-mcp](https://img.shields.io/badge/MCP-agent--design--pcb--mcp%20(v4.3)-blueviolet.svg)](mcp-server/)
[![Conector CAD: easyeda-mcp-pro](https://img.shields.io/badge/CAD%20Bridge-easyeda--mcp--pro-orange.svg)](https://github.com/oaslananka/easyeda-mcp-pro)

---

## 1. ¿Qué hace este proyecto?

**AGENT-DESIGN-PCB v4.0** convierte a tu agente de Inteligencia Artificial (o equipo de sub-agentes en Antigravity, Claude Code, Cursor, Gemini CLI o Codex) en un **Ingeniero Electrónico Senior de Armado de PCB** respaldado por un servidor MCP nativo con motores de cálculo matemático y auditoría física:

1. **Servidor MCP Nativo Determinista (`agent-design-pcb-mcp`):** Expone 7 herramientas estándar JSON-RPC 2.0 sobre `stdio` para calcular anchos de pista (**IPC-2221 / IPC-2152**), *Clearance/Creepage* con detección de ranuras fresadas (**IPC-2221C / IEC 60664-1**), impedancia y diafonía (**IPC-2141A** y reglas $3W/5W$), desacoplo de PDN en 3 décadas ($Z_{\text{target}}$ y $f_{\text{SRF}}$), matrices de vías térmicas (conducción de Fourier y relación de aspecto), validación de *pinout* de MCU (evita conflictos de strapping pins y `ADC2` con Wi-Fi) y auditoría 2D de *courtyards* y chaflanes de placa.
2. **Entiende qué quieres y cómo lo quieres (Fase 0):** Antes de trazar un cable, realiza una entrevista inteligente (o inspecciona tu avance actual en EasyEDA Pro) para saber cómo se alimentará la placa, si la soldarás a mano en laboratorio (**IPC-7351 Nivel A**, paquetes `0805`/`SOIC`) o en fábrica PCBA (**Nivel B**, paquetes `0402`/`QFN`) y dónde comprarás las piezas.
3. **Conserva la memoria viva del proyecto en 3 documentos:** Mantiene actualizados `HARDWARE-SPEC.md` (arquitectura y cálculos), `BOM-SOURCING.md` (auditoría de compras) y `BRINGUP-CHECKLIST.md` (protocolo de encendido en laboratorio).
4. **Domina Microcontroladores (Co-Diseño HW/FW) y Antenas RF:** Evita pines trampa de arranque (*Strapping Pins* en **ESP32/S3/C3/C6**, bloqueo de `ADC2` con Wi-Fi, polarización de `BOOT0`/`VDDA` en **STM32**, resistencias USB en **RP2040** y protección de `AREF` en **AVR**), e impone zonas libres de cobre (*Keep-Out*) y redes $\pi$ en antenas Wi-Fi/BLE/LoRa.
5. **Blinda y Protege tus Circuitos contra Fallas Reales:** Diseña protecciones contra inversión de polaridad (MOSFET canal P como diodo ideal + Zener de compuerta), sobrecorriente (fusibles PPTC con *thermal derating* y *eFuses*), transitorios pesados (**IEC 61000-4-2 ESD**, **IEC 61000-4-4 EFT** e **IEC 61000-4-5 Surge** con coordinación MOV + TVS), filtros EMI ($\pi$ y modo común) y aislamiento galvánico.
6. **Gestiona y Audita tus Compras en LCSC, AliExpress y Alibaba:**
   * **EasyEDA Pro / LCSC / JLCPCB:** Verifica stock real, valida huellas y prioriza **Basic Parts** para eliminar recargos de montaje.
   * **AliExpress y Alibaba:** Busca componentes, audita reputación ($\ge 95\%$, $\ge 4.7\star$, *Verified Supplier*, *Trade Assurance*), calcula costo con envío, detecta chips falsificados/remarcados ($<40\%$ del valor oficial) y valida medidas físicas antes de cerrar el *footprint*.
7. **Prepara la Placa para el Laboratorio (Simulación SPICE, DFT y *Bring-Up*):** Simula en EasyEDA Pro, inserta puntos de prueba (`TP`) y puentes de aislamiento de $0\,\Omega$ por etapa, y guía el primer encendido seguro con fuente limitada y multímetro de banco (compatible con el conector MCP **`ut803`**).

---

## 2. Manuales Normativos y Plantillas de Ingeniería Incluidas

| Manual / Plantilla | Estándares y Capacidades Cubiertas | Archivo |
| :--- | :--- | :--- |
| **Manual 00 — Entrevista y Contexto** | Descubrimiento guiado del proyecto, adaptación a soldadura manual (**Nivel A**) vs. PCBA (**Nivel B**) y memoria persistente. | [00-entrevista-y-contexto-proyecto.md](skills/designing-pcb-normative/references/00-entrevista-y-contexto-proyecto.md) |
| **Manual 01 — Esquemático, PDN y ESD** | MCU (**AN2586 / AN2867**), impedancia objetivo ($Z_{\text{target}}$), desacoplo en 3 décadas ($f_{\text{SRF}}$), terminación serie ($R_s$, $\Gamma$) e inmunidad **IEC 61000-4-2** (TVS). | [01-esquematico-pdn-esd.md](skills/designing-pcb-normative/references/01-esquematico-pdn-esd.md) |
| **Manual 02 — Térmica, Aislamiento y Sustrato** | Capacidad de corriente (**IPC-2221 / IPC-2152**), vías térmicas ($R_{\text{th}}$), *Clearance* y *Creepage* (**IPC-2221C**, **IEC 60664-1**, **IEC 62368-1**) y laminados **IPC-4101** (`/21`, `/99`, `/126`, `/129`). | [02-termica-aislamiento-materiales.md](skills/designing-pcb-normative/references/02-termica-aislamiento-materiales.md) |
| **Manual 03 — Integridad de Señal, GND y Ruteo** | Planos **GND continuos**, ecuaciones Microstrip y Stripline (**IPC-2141A**), pares diferenciales (*skew* $\le 5\,\text{mils}$), reglas **$3W$ / $5W$**, HDI (**IPC-2226**) y Flex (**IPC-2223E**). | [03-integridad-senal-gnd-ruteo.md](skills/designing-pcb-normative/references/03-integridad-senal-gnd-ruteo.md) |
| **Manual 04 — DFM, Ensamblaje y Auditoría MCP** | Densidad de pads (**IPC-7351B / IPC-7352**), DFM Clase 2 vs. Clase 3 (**IPC-6012**), criterios de soldadura y vacíos BGA (**IPC-A-610J**, **J-STD-001J**, **IPC-7095**), **IPC-TM-650** y **ANSI/ESD S20.20**. | [04-dfm-ensamblaje-easyeda-mcp.md](skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md) |
| **Manual 05 — Bloques Electrónicos Prácticos** | Topologías listas para usar: USB-C UFP ($2\times 5.1\,\text{k}\Omega$), reguladores LDO vs. Buck (*Hot Loop*), baterías LiPo (*Power Path*), I2C, RS-485 industrial, relés/MOSFETs y filtros ADC. | [05-bloques-electronicos-practicos.md](skills/designing-pcb-normative/references/05-bloques-electronicos-practicos.md) |
| **Manual 06 — Co-Piloto EasyEDA y Gestor de Compras** | Transacciones seguras con *rollback* en EasyEDA Pro, optimización PCBA (**LCSC / JLCPCB**) y protocolo de auditoría de proveedores en **AliExpress y Alibaba**. | [06-copiloto-easyeda-sourcing-global.md](skills/designing-pcb-normative/references/06-copiloto-easyeda-sourcing-global.md) |
| **Manual 07 — Protección Integral de Circuitos** | Inversión de polaridad (MOSFET ideal + Zener), sobrecorriente (PPTC con *derating* y eFuse), coordinación Surge (**IEC 61000-4-5** MOV+TVS), filtros EMI ($\pi$/modo común) y aislamiento galvánico. | [07-proteccion-integral-circuitos.md](skills/designing-pcb-normative/references/07-proteccion-integral-circuitos.md) |
| **Manual 08 — Microcontroladores y Antenas RF** | Pines trampa de arranque en **ESP32/S3/C3/C6** (`ADC2`, `EN`), **STM32** (`BOOT0`, `VDDA`, SWD), **RP2040** y **AVR** (`AREF`), zonas *Keep-Out* sin cobre para antenas y red de adaptación en $\pi$. | [08-microcontroladores-rf-pinout-seguro.md](skills/designing-pcb-normative/references/08-microcontroladores-rf-pinout-seguro.md) |
| **Manual 09 — Simulación, DFT y *Bring-Up*** | Simulación SPICE en EasyEDA Pro, puntos de prueba (`TP`) obligatorios, puentes de aislamiento de $0\,\Omega$ y protocolo de encendido seguro en laboratorio. | [09-simulacion-dft-bringup-laboratorio.md](skills/designing-pcb-normative/references/09-simulacion-dft-bringup-laboratorio.md) |
| **Manual 10 — Arquitectura Multi-Agente** | Orquestación de 4 roles especialistas (Arquitecto de Circuito/MCU, Gestor de Compras, Ingeniero de Layout/EMC y Auditor DFM/Laboratorio). | [10-arquitectura-multiagente-pcb.md](skills/designing-pcb-normative/references/10-arquitectura-multiagente-pcb.md) |
| **Manual 11 — Guía Operativa Oficial del Editor EasyEDA** | Reglas oficiales del lienzo EasyEDA (eje $Y$ invertido, errores de *Convert to PCB*, correspondencia Pin/Pad `1,2` vs `A,C`, regiones `No Solid` y `Board Cutout`, reconstrucción de cobre `Shift+B` y anatomía de archivos Gerber `.GKO`/`.DRL`). | [11-guia-operativa-editor-easyeda.md](skills/designing-pcb-normative/references/11-guia-operativa-editor-easyeda.md) |
| **Manual 12 — Servidor MCP Normativo del Agente** | Especificación técnica de las 8 herramientas MCP del agente (`pcb_normative_*` y `pcb_verify_connection_board`), compuerta *Datasheet-First* y resolución atómica de DRC en EasyEDA Pro. | [12-servidor-mcp-normativo-agente.md](skills/designing-pcb-normative/references/12-servidor-mcp-normativo-agente.md) |
| **Manual 13 — Del Protoboard al PCB Profesional** | Metodología de co-diseño: política de cero invención (*Datasheet-First*), PCB de Conexión Interactivo con posicionamiento Drag & Drop, simulación real y promoción a EasyEDA Pro. | [13-del-protoboard-fisico-y-virtual-al-pcb.md](skills/designing-pcb-normative/references/13-del-protoboard-fisico-y-virtual-al-pcb.md) |
| **Manual 14 — Maestría EasyEDA Pro y Ecosistema JLCPCB** | Explotación nativa de EasyEDA Pro: arquitectura *Device-First* (Símbolo+Footprint+3D+LCSC), workflows inteligentes, SPICE, stackups oficiales JLCPCB (`JLC04161H-3313/7628`), *Auto-Fix* y manejo real del puente 3.2.x. | [14-maestria-easyeda-pro-y-ecosistema-jlcpcb.md](skills/designing-pcb-normative/references/14-maestria-easyeda-pro-y-ecosistema-jlcpcb.md) |
| **Plantilla 1 — Ficha Técnica Viva** | Documento persistente de arquitectura, árbol de potencia, *pinout*, *stackup* y estado de avance del proyecto. | [HARDWARE-SPEC.template.md](skills/designing-pcb-normative/templates/HARDWARE-SPEC.template.md) |
| **Plantilla 2 — Matriz de Compras y Proveedores** | Comparativa de componentes entre LCSC (`Basic/Extended`), AliExpress y Alibaba con evaluación de rating, envío, MOQ y riesgo de falsificación. | [BOM-SOURCING.template.md](skills/designing-pcb-normative/templates/BOM-SOURCING.template.md) |
| **Plantilla 3 — Checklist de *Bring-Up* en Banco** | Registro paso a paso de pruebas en frío ($\Omega$), primer encendido con fuente limitada, medición de rieles y validación de periféricos. | [BRINGUP-CHECKLIST.template.md](skills/designing-pcb-normative/templates/BRINGUP-CHECKLIST.template.md) |
| **Plantilla 4 — Contexto y Condiciones de Entorno** | Registro normativo de ubicación (IP rating), rango térmico, vibración (**IEC 60068-2-6**), transitorios vehiculares (**ISO 7637**) y cables largos. | [ENVIRONMENT-CONDITIONS.template.md](skills/designing-pcb-normative/templates/ENVIRONMENT-CONDITIONS.template.md) |
| **Plantilla 5 — Protoboard Virtual Interactivo** | Visualizador de protoboard preliminar en HTML5/Tailwind para prototipado rápido en banco. | [VIRTUAL-BREADBOARD.template.html](skills/designing-pcb-normative/templates/VIRTUAL-BREADBOARD.template.html) |
| **Plantilla 6 — PCB de Conexión Interactivo (v4.2)** | Workbench PCB interactivo: dibujo de pinouts verificados, posicionamiento Drag & Drop en mm/mils, simulación eléctrica con valores reales, bloqueo por falta de datasheet y exportación JSON para EasyEDA Pro. | [PCB-CONNECTION-WORKBENCH.template.html](skills/designing-pcb-normative/templates/PCB-CONNECTION-WORKBENCH.template.html) |

---

## 3. Estructura del Repositorio

```text
AGENT-DESIGN-PCB/
├── README.md                                           # Manual principal de instalación y uso (ISO/IEC 82079-1)
├── LICENSE                                             # Licencia MIT (S&D MMCALL)
├── NOTICE.md                                           # Reconocimiento legal a easyeda-mcp-pro y normas técnicas
├── mcp-config.example.json                             # Configuración lista para los servidores MCP
├── easyeda-extension/                                  # Extensión empaquetada para EasyEDA Pro
│   ├── README.md                                       # Guía de instalación en 1 minuto con capturas
│   ├── easyeda-bridge-extension.eext                   # Paquete oficial .eext para importar en EasyEDA Pro
│   └── easyeda-bridge-extension.checksums.json         # Checksums SHA-256 de verificación
├── mcp-server/                                         # Servidor MCP Normativo Desarrollado por S&D MMCALL
│   ├── agent_design_pcb_mcp.py                         # Servidor stdio JSON-RPC 2.0 con 8 herramientas IPC/IEC
│   └── test_mcp_and_easyeda_live.py                    # Suite de pruebas automatizadas y diagnóstico de placa
└── skills/
    └── designing-pcb-normative/                        # Skill para el agente de IA
        ├── SKILL.md                                    # Instrucciones maestras de la skill (v4.3)
        ├── templates/                                  # Plantillas Markdown y HTML interactivas
        │   ├── HARDWARE-SPEC.template.md               # Memoria viva del hardware
        │   ├── BOM-SOURCING.template.md                # Matriz de compras (LCSC / AliExpress / Alibaba)
        │   ├── BRINGUP-CHECKLIST.template.md           # Puesta en marcha en banco de pruebas
        │   ├── ENVIRONMENT-CONDITIONS.template.md      # Contexto y condiciones de entorno (IP, temperatura, cables)
        │   ├── VIRTUAL-BREADBOARD.template.html        # Protoboard Virtual preliminar (HTML5)
        │   └── PCB-CONNECTION-WORKBENCH.template.html  # PCB de Conexión Interactivo con Pinouts & EasyEDA JSON
        └── references/                                 # 15 Manuales técnicos normativos (00 a 14)
            ├── 00-entrevista-y-contexto-proyecto.md
            ├── 01-esquematico-pdn-esd.md
            ├── 02-termica-aislamiento-materiales.md
            ├── 03-integridad-senal-gnd-ruteo.md
            ├── 04-dfm-ensamblaje-easyeda-mcp.md
            ├── 05-bloques-electronicos-practicos.md
            ├── 06-copiloto-easyeda-sourcing-global.md
            ├── 07-proteccion-integral-circuitos.md
            ├── 08-microcontroladores-rf-pinout-seguro.md
            ├── 09-simulacion-dft-bringup-laboratorio.md
            ├── 10-arquitectura-multiagente-pcb.md
            ├── 11-guia-operativa-editor-easyeda.md
            ├── 12-servidor-mcp-normativo-agente.md
            ├── 13-del-protoboard-fisico-y-virtual-al-pcb.md
            └── 14-maestria-easyeda-pro-y-ecosistema-jlcpcb.md
```

---

## 4. Instalación Paso a Paso

### Paso 0: Instalar la Extensión en EasyEDA Pro (Paquete `.eext`)

1. Abra **EasyEDA Pro** (v3.2.x Desktop).
2. Vaya al menú superior: **`Avanzado` $\rightarrow$ `Gestor de Extensiones...`** (*Advanced $\rightarrow$ Extensions Manager...*).
3. Haga clic en **`Importar Extensión`** (*Import Extension*) y seleccione el archivo [`easyeda-extension/easyeda-bridge-extension.eext`](easyeda-extension/easyeda-bridge-extension.eext).
4. Asegúrese de activar la casilla **`Permitir Interacción Externa`** (*Allow External Interaction*).
5. **Cierre completamente EasyEDA Pro y vuelva a abrirlo.**
6. En la barra de menú verá el nuevo menú **`MCP Bridge`** $\rightarrow$ haga clic en **`Connect`**.

### Paso 1: Instalar la Skill en su Agente de IA

1. Clone este repositorio en su equipo:
   ```bash
   git clone https://github.com/VictorAntonioCayupil/AGENT-DESIGN-PCB.git
   ```
2. Copie la carpeta `skills/designing-pcb-normative` al directorio de skills de su entorno:
   * **Antigravity / Gemini:** `~/.gemini/config/skills/designing-pcb-normative`
   * **Claude Code:** `~/.claude/skills/designing-pcb-normative`
   * **Multi-agente estándar:** `~/.agents/skills/designing-pcb-normative`

### Paso 2: Conectar los Servidores MCP

1. Abra el archivo de configuración MCP de su agente (por ejemplo, `mcp_config.json`).
2. Agregue el bloque incluido en [mcp-config.example.json](mcp-config.example.json):
   ```json
   {
     "mcpServers": {
       "agent-design-pcb": {
         "command": "python",
         "args": [
           "c:/Users/vcayu/Documents/SKILL/DESIGN-PCB/mcp-server/agent_design_pcb_mcp.py"
         ]
       },
       "easyeda-mcp-pro": {
         "command": "cmd",
         "args": [
           "/c",
           "npx",
           "-y",
           "easyeda-mcp-pro@1.15.6"
         ],
         "env": {
           "TOOL_PROFILE": "full",
           "TRANSPORT": "stdio",
           "BRIDGE_HOST": "127.0.0.1"
         }
       }
     }
   }
   ```

### Paso 3: Ejecutar la Suite de Pruebas Automatizadas

Para validar que todas las calculadoras normativas IPC/IEC y el protocolo JSON-RPC estén 100 % operativos en su entorno:

```bash
cd mcp-server
python test_mcp_and_easyeda_live.py
```

---

## 5. Créditos, Derechos de Autor y Licencias

* **Autoría de la Skill, Plantillas y Manuales Normativos:** Desarrollado por **S&D MMCALL** con el afán de apoyar a la comunidad hispanohablante e internacional a diseñar, proteger y fabricar hardware confiable. Distribuido bajo licencia **[MIT](LICENSE)**.
* **Créditos del Conector MCP (`easyeda-mcp-pro`):** El servidor MCP utilizado para interactuar con EasyEDA Pro es obra de **[oaslananka](https://github.com/oaslananka/easyeda-mcp-pro)** y se distribuye bajo licencia **`AGPL-3.0-only`**. Este repositorio no incluye ni modifica su código fuente; únicamente documenta e invoca su paquete oficial público. Consulte **[NOTICE.md](NOTICE.md)** para más detalles.
