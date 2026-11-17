# Manual 00: Entrevista Inteligente,Comprensión del Proyecto y Memoria de Contexto

> **Estándares aplicados:** ISO 24495-1 (Lenguaje Claro), ISO/IEC 82079-1 (Instrucciones de uso), Ingeniería de Requerimientos de Hardware.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Objetivo de la Fase 0 (Entender al Usuario Antes de Diseñar)

> [!IMPORTANT]
> **Prohibido diseñar a ciegas:** Un ingeniero experto nunca traza un esquemático ni elige componentes sin comprender primero **qué quiere lograr el usuario**, **cómo piensa fabricar y soldar la placa** y **dónde comprará los repuestos**.

Antes de calcular fórmulas IPC o invocar comandos de escritura en EasyEDA Pro, ejecute esta Fase 0 para alinear el diseño con la realidad técnica y económica del usuario.

---

## 2. Paso 1: Inspección Silenciosa del Proyecto Actual (Si ya existe en EasyEDA Pro)

No haga preguntas que usted mismo pueda responder inspeccionando el entorno. Si el usuario ya tiene un proyecto abierto en EasyEDA Pro:

1. Ejecute `easyeda_health_check` y `easyeda_project_list` / `easyeda_project_open`.
2. Lea los componentes y redes actuales con `easyeda_schematic_components` y `easyeda_schematic_nets`.
3. Si existe un PCB iniciado, consulte `easyeda_board_dimensions`, `easyeda_board_layers` y capture una vista con `easyeda_canvas_capture`.
4. Resuma al usuario en 3 líneas qué detectó en su proyecto (ej. *"Veo que ya tienes un ESP32-S3, un sensor VL53L0X y un conector USB-C en el esquemático, pero aún faltan los capacitores de desacoplo y las resistencias CC1/CC2"*).

---

## 3. Paso 2: Las 4 Preguntas Clave de Descubrimiento (Entrevista Guiada)

Si el proyecto comienza desde cero o faltan definiciones críticas, formule únicamente las preguntas necesarias (máximo 1 o 2 por turno, en lenguaje claro y ofreciendo opciones recomendadas):

### A. Propósito Funcional y Entorno
* **Qué averiguar:** ¿Qué sensores, actuadores o comunicaciones necesita la placa y en qué ambiente trabajará (interior limpio, exterior húmedo, industrial con ruido eléctrico)?
* **Impacto normativo:** Define la Clase **IPC-6012** (Clase 2 vs. Clase 3), el Grado de Polución (**IEC 60664-1**) y el nivel de protección ESD (**IEC 61000-4-2**).

### B. Fuente de Energía y Niveles de Tensión/Corriente
* **Qué averiguar:** ¿Cómo se alimentará el circuito (USB 5 V, batería LiPo/18650, fuente industrial 12 V / 24 V o red eléctrica 110 V / 220 V AC)? ¿Cuál es la carga de mayor consumo?
* **Impacto normativo:** Define la arquitectura de reguladores (LDO vs. Buck), el cálculo de ancho de pistas (**IPC-2221 / IPC-2152**) y las distancias de aislamiento por tensión pico (**IPC-2221C**).

### C. Método de Armado y Nivel de Experiencia en Soldadura
* **Qué averiguar:** ¿Soldará la placa usted mismo a mano en su banco de trabajo (cautín / aire caliente) o pedirá el servicio de ensamblaje automático en fábrica (PCBA)?
* **Impacto normativo directo en EasyEDA Pro:**
  * **Si suelda a mano en laboratorio:** Seleccione **IPC-7351B Nivel A** (pads extendidos) y encapsulados amigables como `0805` o `0603` para pasivos, y `SOIC`, `TSSOP` o módulos con pines castellados en lugar de BGA/QFN diminutos.
  * **Si pide ensamblaje robotizado (PCBA):** Seleccione **IPC-7351B Nivel B** y encapsulados compactos (`0402`, `0603`, `QFN`) priorizando el catálogo de *Basic Parts* del fabricante.

### D. Estrategia de Compra de Componentes (*Sourcing*)
* **Qué averiguar:** ¿Desea comprar todos los componentes directamente al proveedor integrado de EasyEDA Pro (**LCSC / JLCPCB**), comprarlos por su cuenta en **AliExpress / Alibaba**, o usar una **estrategia híbrida**?
* **Impacto en el flujo:** Activa el Gestor de Compras ([Manual 06](06-copiloto-easyeda-sourcing-global.md)) para auditar stock en LCSC y/o buscar vendedores confiables en AliExpress y Alibaba antes de fijar las huellas (*footprints*) en la placa.

---

## 4. Paso 3: Creación y Mantenimiento de la Ficha Viva (`HARDWARE-SPEC.md`)

Una vez acordados los puntos anteriores con el usuario:

1. Cree en el directorio del proyecto el archivo `HARDWARE-SPEC.md` basándose en la plantilla **[templates/HARDWARE-SPEC.template.md](../templates/HARDWARE-SPEC.template.md)**.
2. Cree la tabla de abastecimiento `BOM-SOURCING.md` basándose en **[templates/BOM-SOURCING.template.md](../templates/BOM-SOURCING.template.md)**.
3. **Regla de persistencia:** Cada vez que complete una etapa (esquemático, compras, stackup, ruteo o DRC), actualice las casillas de verificación en `HARDWARE-SPEC.md`. Al iniciar cualquier nueva conversación, lea primero `HARDWARE-SPEC.md` para retomar el proyecto sin perder contexto.
