# AGENT-DESIGN-PCB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir y publicar en GitHub el repositorio público `AGENT-DESIGN-PCB` (creado por **S&D MMCALL** para la comunidad) con la Skill normativa de diseño electrónico y PCB (`designing-pcb-normative`) y la integración atribuida de `easyeda-mcp-pro`.

**Architecture:** Repositorio 100 % Markdown estructurado bajo las normas ISO 24495-1 (Lenguaje Claro) e ISO/IEC 82079-1 (Manuales de Uso). Contiene archivos de licenciamiento y atribución (`LICENSE` MIT, `NOTICE.md` para `oaslananka/easyeda-mcp-pro` AGPL-3.0-only, `mcp-config.example.json`), un `README.md` institucional de **S&D MMCALL**, el archivo núcleo `skills/designing-pcb-normative/SKILL.md` (flujo obligatorio de 5 fases) y 4 manuales normativos en `skills/designing-pcb-normative/references/` que cubren las 15 secciones de los dos informes técnicos (IPC, IEC, J-STD, ANSI).

**Tech Stack:** Markdown (GitHub Flavored Markdown + KaTeX LaTeX), JSON (`mcp-config.example.json`), Git, GitHub CLI (`gh`).

**Spec:** `docs/superpowers/specs/2026-11-17-designing-pcb-normative-design.md`

## Global Constraints

- Autor institucional del repositorio y la Skill: **S&D MMCALL**, creado con el afán de ayudar a la comunidad a diseñar y armar placas PCB de forma correcta bajo normas reales de ingeniería electrónica.
- Cero copia de código fuente de `easyeda-mcp-pro`: invocación externa vía `npx -y easyeda-mcp-pro@1.15.6` y atribución explícita a `oaslananka` (`https://github.com/oaslananka/easyeda-mcp-pro`, licencia `AGPL-3.0-only`).
- Aplicación estricta de **ISO 24495-1** e **ISO/IEC 82079-1**: oraciones activas/imperativas de menos de 20 palabras, orden lógico Condición $\rightarrow$ Acción, advertencias (`> [!WARNING]` / `> [!CAUTION]`) antes del paso donde ocurre el riesgo, y tablas de consulta rápida.
- Cobertura total de las 15 secciones de los dos informes técnicos (AN2586/AN2867, IPC-2221, IPC-2152, IPC-2221C, IEC 60664-1, IEC 62368-1, IPC-2141A, IPC-7351B, IPC-7352, IPC-6012, IPC-2226, IPC-2223E, IPC-4101, IPC-A-610J, J-STD-001J, IPC-7095, IPC-TM-650, IEC 61000-4-2, ANSI/ESD S20.20, planos GND continuos y terminaciones).

---

### Task 1: Archivos Raíz de Licenciamiento, Atribución, Configuración MCP y Manual Principal (`README.md`)

**Files:**
- Create: `LICENSE`
- Create: `NOTICE.md`
- Create: `mcp-config.example.json`
- Create: `README.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-11-17-designing-pcb-normative-design.md`
- Produces: Estructura raíz del repositorio `AGENT-DESIGN-PCB` con créditos de **S&D MMCALL** y atribución legal a `oaslananka/easyeda-mcp-pro`.

- [ ] **Step 1: Crear `LICENSE` (MIT License a nombre de S&D MMCALL)**
- [ ] **Step 2: Crear `NOTICE.md` (Atribución formal a `easyeda-mcp-pro` de `oaslananka` bajo `AGPL-3.0-only`)**
- [ ] **Step 3: Crear `mcp-config.example.json` (Configuración lista para conectar `easyeda-mcp-pro@1.15.6` vía `npx`)**
- [ ] **Step 4: Crear `README.md` (Manual de usuario bajo ISO/IEC 82079-1 presentando la iniciativa de S&D MMCALL para la comunidad)**
- [ ] **Step 5: Verificar existencia de archivos y hacer commit en Git**

---

### Task 2: Manuales de Referencia Normativa 01 y 02 (`references/01-esquematico-pdn-esd.md` y `references/02-termica-aislamiento-materiales.md`)

**Files:**
- Create: `skills/designing-pcb-normative/references/01-esquematico-pdn-esd.md`
- Create: `skills/designing-pcb-normative/references/02-termica-aislamiento-materiales.md`

**Interfaces:**
- Consumes: Secciones 2, 3, 4, 6, 10, 13 y 14 (14.1, 14.2, 14.4) de los informes técnicos.
- Produces: Manuales normativos listos para consulta por fase en `SKILL.md`.

- [ ] **Step 1: Crear `skills/designing-pcb-normative/references/01-esquematico-pdn-esd.md` con reglas de MCU (AN2586/AN2867), $Z_{\text{target}}$, $f_{\text{SRF}}$, desacoplo en 3 décadas, terminación serie ($R_s$, $\Gamma$) y protección TVS (IEC 61000-4-2 Niveles 1–4)**
- [ ] **Step 2: Crear `skills/designing-pcb-normative/references/02-termica-aislamiento-materiales.md` con IPC-2221 (tabla 1 A a 15 A), IPC-2152, vías térmicas ($R_{\text{th}}$), IPC-2221C Tabla 6-1, IEC 60664-1 / 62368-1 (CTI y ranuras fresadas) e IPC-4101 (`/21`, `/99`, `/126`, `/129`)**
- [ ] **Step 3: Verificar formato ISO 24495-1 / ISO/IEC 82079-1 y hacer commit en Git**

---

### Task 3: Manuales de Referencia Normativa 03 y 04 (`references/03-integridad-senal-gnd-ruteo.md` y `references/04-dfm-ensamblaje-easyeda-mcp.md`)

**Files:**
- Create: `skills/designing-pcb-normative/references/03-integridad-senal-gnd-ruteo.md`
- Create: `skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md`

**Interfaces:**
- Consumes: Secciones 5, 7, 8, 9, 11, 12, 13.2 y 14.3 de los informes técnicos + catálogo de herramientas de `easyeda-mcp-pro`.
- Produces: Manuales de integridad de señal, planos GND, HDI/Flex, DFM, ensamblaje y orquestación MCP.

- [ ] **Step 1: Crear `skills/designing-pcb-normative/references/03-integridad-senal-gnd-ruteo.md` con ecuaciones Microstrip/Stripline (IPC-2141A), pares diferenciales, reglas $3W/5W$, planos GND ininterrumpidos (Sección 14.3), HDI (IPC-2226) y Flex (IPC-2223E)**
- [ ] **Step 2: Crear `skills/designing-pcb-normative/references/04-dfm-ensamblaje-easyeda-mcp.md` con footprints (IPC-7351B/7352 Niveles A/B/C), DFM Clase 2 vs Clase 3 (IPC-6012), ensamblaje/voids BGA (IPC-A-610J, J-STD-001J, IPC-7095), pruebas termomecánicas (IPC-TM-650), EPA (ANSI/ESD S20.20) y matriz de herramientas `easyeda-mcp-pro`**
- [ ] **Step 3: Verificar formato ISO 24495-1 / ISO/IEC 82079-1 y hacer commit en Git**

---

### Task 4: Archivo Principal de la Skill (`skills/designing-pcb-normative/SKILL.md`) y Validación TDD

**Files:**
- Create: `skills/designing-pcb-normative/SKILL.md`

**Interfaces:**
- Consumes: `references/01-esquematico-pdn-esd.md`, `references/02-termica-aislamiento-materiales.md`, `references/03-integridad-senal-gnd-ruteo.md`, `references/04-dfm-ensamblaje-easyeda-mcp.md`.
- Produces: Skill operativa con frontmatter YAML optimizado (SDO), flujo obligatorio de 5 fases, tabla de racionalizaciones y banderas rojas.

- [ ] **Step 1: Ejecutar prueba base (RED) verificando qué omite un agente sin la Skill al diseñar un circuito con MCU, 230 V AC, reloj SPI rápido y regulador de 5 A en EasyEDA Pro**
- [ ] **Step 2: Redactar `skills/designing-pcb-normative/SKILL.md` siguiendo `writing-skills` e `ISO 24495-1`**
- [ ] **Step 3: Ejecutar prueba de validación (GREEN) con subagente aplicando `SKILL.md` y sus referencias para verificar cumplimiento del 100 % de normas y herramientas MCP**
- [ ] **Step 4: Hacer commit en Git**

---

### Task 5: Creación y Publicación del Repositorio Público `AGENT-DESIGN-PCB` en GitHub

**Files:**
- Modify: Configuración remota de Git en `c:\Users\vcayu\Documents\SKILL\DESIGN-PCB`

**Interfaces:**
- Consumes: Todos los commits de las Tareas 1 a 4.
- Produces: Repositorio público `AGENT-DESIGN-PCB` publicado en GitHub.

- [ ] **Step 1: Verificar autenticación con `gh auth status`**
- [ ] **Step 2: Crear el repositorio público `AGENT-DESIGN-PCB` con `gh repo create AGENT-DESIGN-PCB --public --source=. --remote=origin --push`**
- [ ] **Step 3: Verificar URL pública y estado limpio del repositorio**
