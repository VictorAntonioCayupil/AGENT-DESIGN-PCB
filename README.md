# AGENT-DESIGN-PCB — Agente y Skill de Diseño Normativo de PCB

> **Una iniciativa de S&D MMCALL para la comunidad.**  
> Creado con el afán de ayudar a ingenieros, estudiantes y desarrolladores a formular, diseñar y armar placas electrónicas (PCB) de forma correcta, basándose en conceptos reales de la física electrónica y en normas internacionales (**IPC**, **IEC**, **J-STD** y **ANSI/ESD**).

[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Norma de Redacción: ISO 24495-1](https://img.shields.io/badge/Documentación-ISO%2024495--1%20%7C%20ISO%2FIEC%2082079--1-success.svg)](#estructura-del-repositorio)
[![Conector MCP: easyeda-mcp-pro](https://img.shields.io/badge/MCP-easyeda--mcp--pro-orange.svg)](https://github.com/oaslananka/easyeda-mcp-pro)

---

## 1. ¿Qué hace este proyecto?

**AGENT-DESIGN-PCB** convierte a tu agente de Inteligencia Artificial (Antigravity, Claude Code, Cursor, Gemini CLI o Codex) en un **Ingeniero Experto en Diseño de Hardware y PCB**.

En lugar de conectar componentes al azar o trazar pistas por intuición, este agente:
1. **Calcula y justifica** cada decisión técnica con ecuaciones reales (termorregulación por efecto Joule, impedancia objetivo de PDN, líneas de transmisión Microstrip/Stripline, coeficiente de reflexión y vías térmicas).
2. **Exige el cumplimiento** de las normas **IPC** e **IEC** antes de aprobar un esquemático o un *layout*.
3. **Se conecta a EasyEDA Pro** a través del servidor MCP [`easyeda-mcp-pro`](https://github.com/oaslananka/easyeda-mcp-pro) para inspeccionar, colocar, rutear y auditar tu placa paso a paso.

---

## 2. Normas e Ingeniería Cubiertas

| Área de Ingeniería | Normas y Conceptos Aplicados | Manual de Referencia |
| :--- | :--- | :--- |
| **Esquemático, MCU, PDN y ESD** | AN2586 / AN2867, impedancia objetivo ($Z_{\text{target}}$), desacoplo en 3 décadas ($f_{\text{SRF}}$), terminación serie ($R_s$, $\Gamma$) e inmunidad **IEC 61000-4-2** (TVS). | [01-esquematico-pdn-esd.md](skills/designing-pcb-normative/references/01-esquematico-pdn-esd.md) |
| **Térmica, Aislamiento y Sustrato** | Capacidad de corriente (**IPC-2221 / IPC-2152**), vías térmicas ($R_{\text{th}}$), *Clearance* y *Creepage* (**IPC-2221C**, **IEC 60664-1**, **IEC 62368-1**) y laminados **IPC-4101** (`/21`, `/99`, `/126`, `/129`). | [02-termica-aislamiento-materiales.md](skills/designing-pcb-normative/references/02-termica-aislamiento-materiales.md) |
| **Integridad de Señal, GND y Ruteo** | Impedancia controlada Microstrip y Stripline (**IPC-2141A**), pares diferenciales, reglas **$3W$ / $5W$**, planos **GND ininterrumpidos**, HDI (**IPC-2226**) y Flex (**IPC-2223E**). | [03-integridad-senal-gnd-ruteo.md](skills/designing-pcb-normative/references/03-integridad-senal-gnd-ruteo.md) |
| **DFM, Footprints y Ensamblaje** | Densidad de pads (**IPC-7351B / IPC-7352** Niveles A/B/C), reglas rígidas Clase 2 y Clase 3 (**IPC-6012**), criterios de soldadura y vacíos BGA (**IPC-A-610J**, **J-STD-001J**, **IPC-7095**), confiabilidad (**IPC-TM-650**) y control **ANSI/ESD S20.20**. | [04-dfm-ensamblaje-easyeda-mcp.md](skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md) |

---

## 3. Estructura del Repositorio

```text
AGENT-DESIGN-PCB/
├── README.md                  # Manual principal de instalación y uso (ISO/IEC 82079-1)
├── LICENSE                    # Licencia MIT (S&D MMCALL)
├── NOTICE.md                  # Reconocimiento legal a easyeda-mcp-pro y normas técnicas
├── mcp-config.example.json    # Configuración de ejemplo para el servidor MCP de EasyEDA Pro
└── skills/
    └── designing-pcb-normative/
        ├── SKILL.md           # Contrato operativo del Agente PCB (flujo de 5 fases)
        └── references/
            ├── 01-esquematico-pdn-esd.md
            ├── 02-termica-aislamiento-materiales.md
            ├── 03-integridad-senal-gnd-ruteo.md
            └── 04-dfm-ensamblaje-easyeda-mcp.md
```

---

## 4. Instalación Paso a Paso

> [!IMPORTANT]
> Antes de iniciar, instale **Node.js (v18 o superior)** y abra **EasyEDA Pro** con su extensión de puente local activa si desea que el agente opere sobre sus diseños en vivo.

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

## 5. Cómo Usar el Agente PCB

1. Abra su proyecto en **EasyEDA Pro** (o pida al agente formular un diseño nuevo desde cero).
2. Indique al agente los requisitos eléctricos de su placa (tensión de entrada, corriente máxima por riel, microcontrolador, interfaces de comunicación y entorno de operación).
3. El agente ejecutará automáticamente su contrato de **5 fases normativas**:
   * **Fase 1:** Clasificación IPC (Clase 2 o Clase 3) y auditoría inicial del árbol de potencia.
   * **Fase 2:** Diseño de esquemático, cálculo de PDN ($Z_{\text{target}}$), desacoplo en 3 décadas, resistencias de terminación serie y protección ESD (**IEC 61000-4-2**).
   * **Fase 3:** Cálculo térmico de pistas (**IPC-2221 / IPC-2152**), matrices de vías térmicas, aislamiento eléctrico (**IPC-2221C / IEC 60664-1**) y selección de sustrato (**IPC-4101**).
   * **Fase 4:** *Floorplanning*, planos de retorno **GND continuos**, control de impedancia (**IPC-2141A**) y reglas de diafonía **$3W$ / $5W$**.
   * **Fase 5:** Verificación DFM (**IPC-6012**), densidad de *footprints* (**IPC-7351B/7352**) y criterios de ensamblaje (**IPC-A-610J / J-STD-001J / IPC-7095**).

---

## 6. Créditos, Derechos de Autor y Licencias

* **Autoría de la Skill y Manuales Normativos:** Desarrollado por **S&D MMCALL** para la comunidad global de hardware y diseño electrónico, distribuido bajo licencia **[MIT](LICENSE)**.
* **Créditos del Conector MCP (`easyeda-mcp-pro`):** El servidor MCP utilizado para interactuar con EasyEDA Pro es obra de **[oaslananka](https://github.com/oaslananka/easyeda-mcp-pro)** y se distribuye bajo licencia **`AGPL-3.0-only`**. Este repositorio no empaqueta ni modifica su código fuente; únicamente documenta e invoca su paquete oficial público. Consulte el archivo **[NOTICE.md](NOTICE.md)** para más detalles.
