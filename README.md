# AGENT-DESIGN-PCB (v2.0) — Agente Co-Piloto de Diseño Normativo de PCB y Gestor Global de Componentes

> **Una iniciativa de S&D MMCALL para la comunidad.**  
> Creado con el afán de ayudar a ingenieros, estudiantes, *makers* y desarrolladores a formular, diseñar, cotizar y armar placas electrónicas (PCB) de forma correcta, basándose en conceptos reales de la física electrónica, normas internacionales (**IPC**, **IEC**, **J-STD**, **ANSI/ESD**) y gestión inteligente de proveedores (**EasyEDA Pro / LCSC / JLCPCB**, **AliExpress** y **Alibaba**).

[![Versión: 2.0](https://img.shields.io/badge/Versión-2.0%20Co--Pilot%20%2B%20Sourcing-brightgreen.svg)](#1-qué-hace-este-proyecto)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Norma de Redacción: ISO 24495-1](https://img.shields.io/badge/Documentación-ISO%2024495--1%20%7C%20ISO%2FIEC%2082079--1-success.svg)](#3-estructura-del-repositorio)
[![Conector MCP: easyeda-mcp-pro](https://img.shields.io/badge/MCP-easyeda--mcp--pro-orange.svg)](https://github.com/oaslananka/easyeda-mcp-pro)

---

## 1. ¿Qué hace este proyecto?

**AGENT-DESIGN-PCB v2.0** convierte a tu agente de Inteligencia Artificial (Antigravity, Claude Code, Cursor, Gemini CLI o Codex) en un **Ingeniero Co-Piloto de Hardware y Gestor Integral del Proyecto Electrónico**:

1. **Entiende qué quieres y cómo lo quieres (Fase 0):** Antes de tocar un cable, realiza una entrevista inteligente (o inspecciona tu avance actual en EasyEDA Pro) para saber si soldarás a mano en tu laboratorio o pedirás ensamblaje robotizado (PCBA), qué restricciones de espacio tienes y cómo prefieres comprar las piezas.
2. **Conserva la memoria viva de tu placa (`HARDWARE-SPEC.md` y `BOM-SOURCING.md`):** Documenta el árbol de potencia, mapa de pines (*Pinout*), *Net Classes* y lista de compras para no perder el hilo entre sesiones.
3. **Formula bloques electrónicos reales sin errores de principiante:** Calcula e implementa conectores USB-C ($2\times 5.1\,\text{k}\Omega$ en `CC1`/`CC2`), fuentes LDO vs. Buck (*Hot Loop*), cargadores y conmutación de baterías LiPo/18650, buses I2C/RS-485, disparo de relés/MOSFETs y filtros ADC.
4. **Aplica las normas IPC e IEC con rigor físico:** Calcula anchos de pista por corriente, matrices de vías térmicas, distancias de *Clearance* y *Creepage* por tensión pico, impedancia controlada Microstrip/Stripline, planos **GND ininterrumpidos** y criterios de soldadura e inspección BGA.
5. **Busca, audita y compara tus componentes en LCSC, AliExpress y Alibaba:**
   * Si compras directo en **EasyEDA Pro (LCSC / JLCPCB)**: verifica stock real, huellas y prioriza **Basic Parts** para ahorrarte cargos de montaje.
   * Si compras independiente en **AliExpress o Alibaba**: busca productos, audita la reputación de la tienda ($\ge 95\%$, $\ge 4.7\star$, *Verified Supplier*, *Trade Assurance*), calcula el costo con envío, detecta chips remarcados/falsos y verifica las medidas físicas antes de cerrar el *footprint* en tu PCB.

---

## 2. Manuales Normativos y Plantillas Incluidas

| Manual / Plantilla | Estándares y Capacidades Cubiertas | Archivo |
| :--- | :--- | :--- |
| **Manual 00 — Entrevista y Contexto** | Descubrimiento guiado del proyecto, adaptación a soldadura manual (**Nivel A**) vs. PCBA (**Nivel B**) y gestión de memoria entre sesiones. | [00-entrevista-y-contexto-proyecto.md](skills/designing-pcb-normative/references/00-entrevista-y-contexto-proyecto.md) |
| **Manual 01 — Esquemático, PDN y ESD** | MCU (**AN2586 / AN2867**), impedancia objetivo ($Z_{\text{target}}$), desacoplo en 3 décadas ($f_{\text{SRF}}$), terminación serie ($R_s$, $\Gamma$) e inmunidad **IEC 61000-4-2** (TVS). | [01-esquematico-pdn-esd.md](skills/designing-pcb-normative/references/01-esquematico-pdn-esd.md) |
| **Manual 02 — Térmica, Aislamiento y Sustrato** | Capacidad de corriente (**IPC-2221 / IPC-2152**), vías térmicas ($R_{\text{th}}$), *Clearance* y *Creepage* (**IPC-2221C**, **IEC 60664-1**, **IEC 62368-1**) y laminados **IPC-4101** (`/21`, `/99`, `/126`, `/129`). | [02-termica-aislamiento-materiales.md](skills/designing-pcb-normative/references/02-termica-aislamiento-materiales.md) |
| **Manual 03 — Integridad de Señal, GND y Ruteo** | Planos **GND continuos**, ecuaciones Microstrip y Stripline (**IPC-2141A**), pares diferenciales (*skew* $\le 5\,\text{mils}$), reglas **$3W$ / $5W$**, HDI (**IPC-2226**) y Flex (**IPC-2223E**). | [03-integridad-senal-gnd-ruteo.md](skills/designing-pcb-normative/references/03-integridad-senal-gnd-ruteo.md) |
| **Manual 04 — DFM, Ensamblaje y Auditoría MCP** | Densidad de pads (**IPC-7351B / IPC-7352**), DFM Clase 2 vs. Clase 3 (**IPC-6012**), criterios de soldadura y vacíos BGA (**IPC-A-610J**, **J-STD-001J**, **IPC-7095**), **IPC-TM-650** y **ANSI/ESD S20.20**. | [04-dfm-ensamblaje-easyeda-mcp.md](skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md) |
| **Manual 05 — Bloques Electrónicos Prácticos** | Topologías listas para usar: USB-C UFP, reguladores LDO vs. Buck (*Hot Loop*), baterías LiPo (*Power Path*), I2C, RS-485 industrial, relés/MOSFETs y filtros ADC. | [05-bloques-electronicos-practicos.md](skills/designing-pcb-normative/references/05-bloques-electronicos-practicos.md) |
| **Manual 06 — Co-Piloto EasyEDA y Gestor de Compras** | Transacciones seguras con *rollback* en EasyEDA Pro, optimización PCBA (**LCSC / JLCPCB**) y protocolo de auditoría de proveedores en **AliExpress y Alibaba**. | [06-copiloto-easyeda-sourcing-global.md](skills/designing-pcb-normative/references/06-copiloto-easyeda-sourcing-global.md) |
| **Plantilla 1 — Ficha Técnica Viva** | Documento persistente de arquitectura, árbol de potencia, *pinout*, *stackup* y estado de avance del proyecto. | [HARDWARE-SPEC.template.md](skills/designing-pcb-normative/templates/HARDWARE-SPEC.template.md) |
| **Plantilla 2 — Matriz de Compras y Proveedores** | Comparativa de componentes entre LCSC (`Basic/Extended`), AliExpress y Alibaba con evaluación de rating, envío, MOQ y riesgo de falsificación. | [BOM-SOURCING.template.md](skills/designing-pcb-normative/templates/BOM-SOURCING.template.md) |

---

## 3. Estructura del Repositorio

```text
AGENT-DESIGN-PCB/
├── README.md                                        # Manual principal de instalación y uso (ISO/IEC 82079-1)
├── LICENSE                                          # Licencia MIT (S&D MMCALL)
├── NOTICE.md                                        # Reconocimiento legal a easyeda-mcp-pro y normas técnicas
├── mcp-config.example.json                          # Configuración lista para el servidor MCP de EasyEDA Pro
└── skills/
    └── designing-pcb-normative/
        ├── SKILL.md                                 # Contrato operativo v2.0 del Agente PCB (Fase 0 a Fase 5)
        ├── templates/
        │   ├── HARDWARE-SPEC.template.md            # Plantilla de memoria viva del proyecto electrónico
        │   └── BOM-SOURCING.template.md             # Plantilla de auditoría de compras (LCSC / AliExpress / Alibaba)
        └── references/
            ├── 00-entrevista-y-contexto-proyecto.md
            ├── 01-esquematico-pdn-esd.md
            ├── 02-termica-aislamiento-materiales.md
            ├── 03-integridad-senal-gnd-ruteo.md
            ├── 04-dfm-ensamblaje-easyeda-mcp.md
            ├── 05-bloques-electronicos-practicos.md
            └── 06-copiloto-easyeda-sourcing-global.md
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

* **Autoría de la Skill, Plantillas y Manuales Normativos:** Desarrollado por **S&D MMCALL** con el afán de apoyar a la comunidad hispanohablante e internacional a diseñar y fabricar hardware confiable. Distribuido bajo licencia **[MIT](LICENSE)**.
* **Créditos del Conector MCP (`easyeda-mcp-pro`):** El servidor MCP utilizado para interactuar con EasyEDA Pro es obra de **[oaslananka](https://github.com/oaslananka/easyeda-mcp-pro)** y se distribuye bajo licencia **`AGPL-3.0-only`**. Este repositorio no incluye ni modifica su código fuente; únicamente documenta e invoca su paquete oficial público. Consulte **[NOTICE.md](NOTICE.md)** para más detalles.
