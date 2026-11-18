# AGENT-DESIGN-PCB (v3.0) — Ingeniero Electrónico Integral, Co-Piloto de PCB y Gestor Multi-Agente de Hardware

> **Una iniciativa de S&D MMCALL para la comunidad.**  
> Creado con el afán de ayudar a ingenieros, estudiantes, *makers* y desarrolladores a formular, proteger, diseñar, cotizar, armar y poner en marcha placas electrónicas (PCB) de forma correcta, basándose en conceptos reales de la física electrónica, normas internacionales (**IPC**, **IEC**, **J-STD**, **ANSI/ESD**), co-diseño seguro con microcontroladores (**ESP32**, **STM32**, **RP2040**, **AVR**) y gestión inteligente de proveedores (**EasyEDA Pro / LCSC / JLCPCB**, **AliExpress** y **Alibaba**).

[![Versión: 3.0](https://img.shields.io/badge/Versión-3.0%20Full%20Electronic%20Engineer%20%2B%20Multi--Agent-brightgreen.svg)](#1-qué-hace-este-proyecto)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Norma de Redacción: ISO 24495-1](https://img.shields.io/badge/Documentación-ISO%2024495--1%20%7C%20ISO%2FIEC%2082079--1-success.svg)](#3-estructura-del-repositorio)
[![Conector MCP: easyeda-mcp-pro](https://img.shields.io/badge/MCP-easyeda--mcp--pro-orange.svg)](https://github.com/oaslananka/easyeda-mcp-pro)

---

## 1. ¿Qué hace este proyecto?

**AGENT-DESIGN-PCB v3.0** convierte a tu agente de Inteligencia Artificial (o equipo de sub-agentes en Antigravity, Claude Code, Cursor, Gemini CLI o Codex) en un **Ingeniero Electrónico Senior de Armado de PCB** que te acompaña de principio a fin:

1. **Entiende qué quieres y cómo lo quieres (Fase 0):** Antes de trazar un cable, realiza una entrevista inteligente (o inspecciona tu avance actual en EasyEDA Pro) para saber cómo se alimentará la placa, si la soldarás a mano en laboratorio (**IPC-7351 Nivel A**, paquetes `0805`/`SOIC`) o en fábrica PCBA (**Nivel B**, paquetes `0402`/`QFN`) y dónde comprarás las piezas.
2. **Conserva la memoria viva del proyecto en 3 documentos:** Mantiene actualizados `HARDWARE-SPEC.md` (arquitectura y cálculos), `BOM-SOURCING.md` (auditoría de compras) y `BRINGUP-CHECKLIST.md` (protocolo de encendido en laboratorio).
3. **Domina Microcontroladores (Co-Diseño HW/FW) y Antenas RF:** Evita pines trampa de arranque (*Strapping Pins* en **ESP32/S3/C3**, bloqueo de `ADC2` con Wi-Fi, polarización de `BOOT0`/`VDDA` en **STM32**, resistencias USB en **RP2040** y protección de `AREF` en **AVR**), e impone zonas libres de cobre (*Keep-Out*) y redes $\pi$ en antenas Wi-Fi/BLE/LoRa.
4. **Blinda y Protege tus Circuitos contra Fallas Reales:** Diseña protecciones contra inversión de polaridad (MOSFET canal P como diodo ideal + Zener de compuerta), sobrecorriente (fusibles PPTC con *thermal derating* y *eFuses*), transitorios pesados (**IEC 61000-4-2 ESD**, **IEC 61000-4-4 EFT** e **IEC 61000-4-5 Surge** con coordinación MOV + TVS), filtros EMI ($\pi$ y modo común) y aislamiento galvánico.
5. **Aplica todas las normas IPC e IEC con rigor matemático:** Calcula impedancia objetivo de PDN ($Z_{\text{target}}$), desacoplo en 3 décadas ($f_{\text{SRF}}$), anchos de pista (**IPC-2221 / IPC-2152**), vías térmicas ($R_{\text{th}}$), *Clearance* y *Creepage* por tensión pico (**IPC-2221C / IEC 60664-1** + ranuras fresadas $>1\,\text{mm}$), planos **GND continuos**, impedancia $Z_0$ (**IPC-2141A**) y reglas $3W / 5W$.
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
| **Manual 08 — Microcontroladores y Antenas RF** | Pines trampa de arranque en **ESP32/S3/C3** (`ADC2`, `EN`), **STM32** (`BOOT0`, `VDDA`, SWD), **RP2040** y **AVR** (`AREF`), zonas *Keep-Out* sin cobre para antenas y red de adaptación en $\pi$. | [08-microcontroladores-rf-pinout-seguro.md](skills/designing-pcb-normative/references/08-microcontroladores-rf-pinout-seguro.md) |
| **Manual 09 — Simulación, DFT y *Bring-Up*** | Simulación SPICE en EasyEDA Pro, puntos de prueba (`TP`) obligatorios, puentes de aislamiento de $0\,\Omega$ y protocolo de encendido seguro en laboratorio. | [09-simulacion-dft-bringup-laboratorio.md](skills/designing-pcb-normative/references/09-simulacion-dft-bringup-laboratorio.md) |
| **Manual 10 — Arquitectura Multi-Agente** | Orquestación de 4 roles especialistas (Arquitecto de Circuito/MCU, Gestor de Compras, Ingeniero de Layout/EMC y Auditor DFM/Laboratorio). | [10-arquitectura-multiagente-pcb.md](skills/designing-pcb-normative/references/10-arquitectura-multiagente-pcb.md) |
| **Plantilla 1 — Ficha Técnica Viva** | Documento persistente de arquitectura, árbol de potencia, *pinout*, *stackup* y estado de avance del proyecto. | [HARDWARE-SPEC.template.md](skills/designing-pcb-normative/templates/HARDWARE-SPEC.template.md) |
| **Plantilla 2 — Matriz de Compras y Proveedores** | Comparativa de componentes entre LCSC (`Basic/Extended`), AliExpress y Alibaba con evaluación de rating, envío, MOQ y riesgo de falsificación. | [BOM-SOURCING.template.md](skills/designing-pcb-normative/templates/BOM-SOURCING.template.md) |
| **Plantilla 3 — Checklist de *Bring-Up* en Banco** | Registro paso a paso de pruebas en frío ($\Omega$), primer encendido con fuente limitada, medición de rieles y validación de periféricos. | [BRINGUP-CHECKLIST.template.md](skills/designing-pcb-normative/templates/BRINGUP-CHECKLIST.template.md) |

---

## 3. Estructura del Repositorio

```text
AGENT-DESIGN-PCB/
├── README.md                                           # Manual principal de instalación y uso (ISO/IEC 82079-1)
├── LICENSE                                             # Licencia MIT (S&D MMCALL)
├── NOTICE.md                                           # Reconocimiento legal a easyeda-mcp-pro y normas técnicas
├── mcp-config.example.json                             # Configuración lista para el servidor MCP de EasyEDA Pro
└── skills/
    └── designing-pcb-normative/
        ├── SKILL.md                                    # Contrato operativo v3.0 del Agente PCB (Fase 0 a Fase 5)
        ├── templates/
        │   ├── HARDWARE-SPEC.template.md               # Plantilla de memoria viva del proyecto electrónico
        │   ├── BOM-SOURCING.template.md                # Plantilla de auditoría de compras (LCSC / AliExpress / Alibaba)
        │   └── BRINGUP-CHECKLIST.template.md           # Plantilla de pruebas y puesta en marcha en laboratorio
        └── references/
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
            └── 10-arquitectura-multiagente-pcb.md
```

---

## 4. Instalación Paso a Paso

> [!IMPORTANT]
> Antes de iniciar, instale **Node.js (v18 o superior)** y abra **EasyEDA Pro** con su puente local activo si desea que el agente opere sobre sus diseños en tiempo real.

### Paso 1: Instalar la Skill en su Agente de IA

1. Clone este repositorio en su equipo:
   ```bash
   git clone https://github.com/VictorAntonioCayupil/AGENT-DESIGN-PCB.git
   ```
2. Copie la carpeta `skills/designing-pcb-normative` al directorio de skills de su entorno:
   * **Antigravity / Gemini:** `~/.gemini/config/skills/designing-pcb-normative`
   * **Claude Code:** `~/.claude/skills/designing-pcb-normative`
   * **Multi-agente estándar:** `~/.agents/skills/designing-pcb-normative`

### Paso 2: Conectar el Servidor MCP de EasyEDA Pro

1. Abra el archivo de configuración MCP de su agente (por ejemplo, `mcp_config.json`).
2. Agregue el bloque incluido en [mcp-config.example.json](mcp-config.example.json):
   ```json
   {
     "mcpServers": {
       "easyeda-mcp-pro": {
         "command": "npx",
         "args": [
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
   *(En Windows, si su entorno requiere invocar `cmd`, utilice `"command": "cmd"` con `"args": ["/c", "npx", "-y", "easyeda-mcp-pro@1.15.6"]`).*

---

## 5. Créditos, Derechos de Autor y Licencias

* **Autoría de la Skill, Plantillas y Manuales Normativos:** Desarrollado por **S&D MMCALL** con el afán de apoyar a la comunidad hispanohablante e internacional a diseñar, proteger y fabricar hardware confiable. Distribuido bajo licencia **[MIT](LICENSE)**.
* **Créditos del Conector MCP (`easyeda-mcp-pro`):** El servidor MCP utilizado para interactuar con EasyEDA Pro es obra de **[oaslananka](https://github.com/oaslananka/easyeda-mcp-pro)** y se distribuye bajo licencia **`AGPL-3.0-only`**. Este repositorio no incluye ni modifica su código fuente; únicamente documenta e invoca su paquete oficial público. Consulte **[NOTICE.md](NOTICE.md)** para más detalles.
