# Manual 11: Guía Operativa Oficial del Editor EasyEDA y Resolución de Errores CAD

> **Fuente técnica:** Documentación Oficial de EasyEDA ([Introduction to EasyEDA](https://docs.easyeda.com/en/Introduction/Introduction-to-EasyEDA/) y [Editor FAQ](https://docs.easyeda.com/en/FAQ/Editor/)).  
> **Estándares aplicados:** ISO 24495-1 (Lenguaje Claro) e ISO/IEC 82079-1 (Manuales de Uso).  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Sistema de Coordenadas y Unidades del Lienzo (*Canvas*)

> [!IMPORTANT]
> **Eje vertical $Y$ invertido en EasyEDA:** A diferencia del plano cartesiano tradicional, en el lienzo de EasyEDA la coordenada horizontal **$X$ crece hacia la derecha**, pero la coordenada vertical **$Y$ crece hacia ABAJO** (es positiva debajo del origen y negativa arriba).

1. **Al posicionar componentes mediante `easyeda-mcp-pro`:**
   * Sumar a $X$ desplaza el componente hacia la **derecha**.
   * Sumar a $Y$ desplaza el componente hacia **abajo**.
2. **Unidades y cuadrícula (*Grid / Snap*):**
   * En el **Esquemático**, la unidad base es el píxel ($1\,\text{píxel} \approx 10\,\text{mil} = 0.001\,\text{pulgadas}$). Mantenga la cuadrícula (*Snap Size*) alineada (por defecto $10\,\text{mil}$ o múltiplos) para evitar pines desconectados fuera de rejilla.
   * En el **PCB**, cambie la unidad del lienzo a milímetros (`mm`) o milésimas de pulgada (`mil`) según la norma que esté aplicando, y evite reglas de diseño con más de **2 decimales**.

---

## 2. Reglas Operativas de Esquemático y Sincronización (*Convert / Update to PCB*)

> [!CAUTION]
> **Conexiones falsas y bloqueos al pasar a PCB:** Nunca utilice las herramientas de dibujo (*Drawing Tools*: líneas, polilíneas o arcos gráficos) para unir pines; esas líneas son meros dibujos y **no crean conexión eléctrica**. Utilice exclusivamente las herramientas de cableado (*Wiring Tools* / `easyeda_schematic_add_wire` / `connect_pins_by_net`).

### 2.1. Convenciones Obligatorias del Esquemático en EasyEDA

1. **Pines sin usar (*No Connect Flag*):** Todo pin que quede libre por diseño debe marcarse con una bandera de *No Connect* (`X` / `easyeda_schematic_set_pin_no_connect`). De lo contrario, el *Design Manager* (ERC) reportará un error de red de un solo pin (*Single-Pin Net Error*).
2. **Señales activas en nivel bajo (*Active-Low*):** Agregue el carácter `#` al final del nombre del pin o etiqueta de red (por ejemplo, `RESET#` o `CS#`) para que EasyEDA dibuje automáticamente la barra superior de negación lógica.
3. **Nombres de red válidos (*Net Labels*):** Utilice únicamente letras inglesas (`A-Z`), números (`0-9`), guiones (`-`) y guiones bajos (`_`). **Prohibido** usar caracteres especiales como `; ~ \ / [ ] =` (provocan fallos en el enrutador y en el analizador de netlist).
4. **Múltiples etiquetas en un mismo cable:** Si un mismo cable tiene varias etiquetas (`NetLabel`), EasyEDA tomará la **primera etiqueta colocada** como nombre oficial de la red al convertir a PCB y unirá todas esas redes entre sí.
5. **Componentes multi-parte (*Subparts*, ej. amplificadores operacionales dobles o cuádruples):** Nombrar siempre los prefijos con formato de punto y número (**`U1.1`, `U1.2`, `U1.3`**), nunca con letras (`U1.A`, `U1.B`).
6. **Exclusión de elementos virtuales o mecánicos:**
   * Si un símbolo no debe existir físicamente en el PCB (ej. sonda de simulación), configure su propiedad `Convert to PCB = No`.
   * Si un elemento está en el PCB pero no debe comprarse (ej. agujero de montaje M3, punto de prueba `TP`, logotipo), configure `Add into BOM = No`.

### 2.2. Solución a los 3 Errores que Bloquean el Paso de Esquemático a PCB

| Error en *Convert/Update PCB* | Causa Raíz en EasyEDA | Solución Directa del Agente |
| :--- | :--- | :--- |
| **1. `Duplicate Prefix Error`** | Existen dos o más símbolos con el mismo designador (ej. dos resistencias llamadas `R1`). | Abra la lista de componentes (`easyeda_schematic_components`), localice el prefijo repetido y reasigne un designador único. |
| **2. `No footprint, please associate the footprint first`** | El símbolo del esquemático tiene el atributo *Footprint* vacío o apunta a una huella inexistente. | Asigne una huella válida verificada del catálogo (`easyeda_catalog_verify_device` / *Footprint Manager*). |
| **3. `Symbol and Footprint Pin Mismatch` / `Invalid Footprint`** | El número/nombre de pines del símbolo no coincide con los pads de la huella (sensible a mayúsculas/minúsculas). *Ejemplo clásico:* un diodo cuyos pines en el símbolo se llaman `1` y `2`, pero en la huella se llaman `A` y `C`. | Edite los números de pin del símbolo o elija una huella cuyos pads coincidan exactamente (`1, 2` con `1, 2` o `A, C` con `A, C`). La huella debe tener igual o mayor cantidad de pads que pines en el símbolo. |

> [!TIP]
> **Cómo reemplazar un componente en el esquemático sin perder las pistas ya trazadas en el PCB:** Sustituya el símbolo en el esquemático manteniendo el mismo prefijo, ejecute **Reset Component Unique ID** tanto en el Esquemático como en el PCB, y luego ejecute **Update PCB / Import Changes** (`easyeda_schematic_sync_to_pcb`).

---

## 3. Reglas Operativas del Editor PCB, Planos de Cobre (*Copper Pour*) y Cortes

### 3.1. Requisitos para que el Plano de Cobre (*Copper Area*) se Genere Correctamente

> [!WARNING]
> **El plano de cobre no aparece o queda desactualizado en los Gerbers:** Por rendimiento, EasyEDA **no reconstruye los planos de cobre en tiempo real** cuando usted mueve una pista o modifica una regla de separación.

1. **Verifique que el contorno de la placa (`BoardOutline`) esté 100 % cerrado:** Si el borde de la placa está abierto o tiene líneas superpuestas duplicadas, el vertido de cobre (*Copper Area*) no se dibujará.
2. **Asigne una red existente (`Net = GND`):** Un área de cobre solo se rellena si dentro de su perímetro toca al menos un pad o vía perteneciente a la misma red (de lo contrario, EasyEDA la considera una isla desconectada y la elimina).
3. **Configure los atributos normativos del *Copper Area*:**
   * `Keep Island = No` (elimina islas de cobre flotantes que actúan como antenas parásitas de EMI).
   * `Improve Fabrication = Yes` (suaviza esquinas agudas de cobre evitando trampas de ácido / *acid traps*).
   * `Pad Connection = Spoke` (alivio térmico en cruz para facilitar la soldadura manual) o `Direct` (en vías y disipadores de alta corriente).
4. **Reconstruya siempre el cobre antes de ejecutar DRC o exportar Gerbers:** Ejecute **`easyeda_pcb_rebuild_copper`** (equivalente al atajo **`Shift + B`**) después de cualquier cambio de trazado.
5. **Prioridad de planos superpuestos (*Copper Area Manager*):** Si coloca un polígono pequeño de `VCC` dentro de un plano general de `GND` en la misma capa, ordene que el polígono pequeño se vierta **primero** para que el plano `GND` lo rodee respetando el *Clearance*.

### 3.2. Cómo Crear Zonas Prohibidas de Cobre (*Keep-Out*), Ranuras (*Slots*) y Pistas Estañadas

| Operación Física Requerida | Procedimiento Exacto en EasyEDA / MCP |
| :--- | :--- |
| **Zona sin Cobre (*Copper Keep-Out* para Antenas RF o Aislamiento Galvánico)** | Coloque una **`Solid Region`** (`easyeda_pcb_add_region`) con atributo **`Type = No Solid`** y asígnele una red distinta a la del plano de cobre. Luego reconstruya el cobre (**`Shift + B`**). **No borre nunca la región `No Solid`**. |
| **Ranura Fresada Pasante (*Milled Slot* para *Creepage* $>1\,\text{mm}$ en 230 V AC)** | Dibuje una **`Solid Region`** con atributo **`Type = Board Cutout`** (o trace una línea del grosor deseado y conviértala en *Board Cutout*). Esta ranura se exportará automáticamente en el archivo de corte `Gerber_BoardOutline.GKO`. |
| **Agujero Pasante No Metalizado (*NPTH*)** | Coloque un pad o agujero y configure su propiedad **`Plated = No`** (la pared interna quedará libre de cobre). |
| **Pista de Potencia Desnuda para Refuerzo con Estaño (*Expose Copper*)** | Seleccione la pista de cobre y active **`Expose Copper`** (o dibuje una `Solid Region` en la capa `TopSolderMaskLayer` / `BottomSolderMaskLayer` **encima** de la pista de cobre existente). *Error común:* dibujar solo en la capa *SolderMask* sin haber trazado cobre debajo. |
| **Línea de Corte en V para Panelizado (*V-Cut*)** | Cambie a la capa `BoardOutline` y trace una polilínea recta que **sobresalga ligeramente fuera de los bordes** del contorno original de la placa. |

---

## 4. Anatomía de Archivos Gerber de EasyEDA y Auditoría Pre-Fábrica

Al generar el paquete ZIP de fabricación (`easyeda_export_gerbers` / `easyeda_production_qa_artifacts`), EasyEDA produce los siguientes archivos estándar que el agente debe conocer y validar:

| Nombre de Archivo en el ZIP | Capa / Función en Fábrica | Qué Verificar Antes de Ordenar |
| :--- | :--- | :--- |
| **`Gerber_BoardOutline.GKO`** | Contorno de corte mecánico y ranuras internas (*Slots / Cutouts*). | Perímetro cerrado, sin líneas dobles, ranuras de aislamiento presentes. |
| **`Gerber_TopLayer.GTL` / `BottomLayer.GBL`** | Cobre superior e inferior. | Planos de cobre reconstruidos (`Shift+B`), cero cortos, anchos IPC cumplidos. |
| **`Gerber_InnerLayer1.G1` / `InnerLayer2.GP2`** | Capas internas de señal (`.G1`) o planos eléctricos (`.GP2`). | Continuidad del plano `GND` sin cortes bajo señales rápidas. |
| **`Gerber_TopSolderMaskLayer.GTS` / `.GBS`** | Apertura de máscara antisoldante (*negativo*: lo dibujado aquí queda **sin** pintura verde). | Pads descubiertos, vías cubiertas (*tented*) o expuestas según diseño. |
| **`Gerber_TopPasteMaskLayer.GTP` / `.GBP`** | Aperturas para plantilla metálica (*Stencil* de pasta SMD). | Solo pads SMD; verificar reducción de apertura en pads térmicos QFN. |
| **`Gerber_TopSilkLayer.GTO` / `.GBO`** | Serigrafía de texto y contornos de componentes. | Ningún texto pisando pads soldables; indicadores de Pin 1 y polaridad claros. |
| **`Drill_PTH_Through.DRL` y `_Via.DRL`** | Perforaciones metalizadas (pads THT y vías). | Formato de coordenadas `3:3` (o `4:2` en placas muy grandes) alineado con el cobre. |
| **`Drill_NPTH_Through.DRL`** | Perforaciones mecánicas NO metalizadas. | Agujeros de centrado o tornillos sin conexión eléctrica. |

> [!IMPORTANT]
> **Verificación visual obligatoria antes de pagar la fabricación:** Antes de confirmar el pedido en JLCPCB o cualquier fabricante, recomiende siempre abrir el ZIP de Gerbers en el visor DFM gratuito **[JLCDFM](https://jlcdfm.com/)** o en **Gerbv** para confirmar que los taladros (`.DRL`), ranuras (`.GKO`) y planos de cobre estén perfectamente alineados.
