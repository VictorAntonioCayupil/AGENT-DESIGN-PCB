# Manual 06: Modo Co-Piloto en EasyEDA Pro y Asistente Cotizador Multicanal (LCSC/JLCPCB, AliExpress, Alibaba y Mercado Local)

> **Estándares aplicados:** Gestión de Calidad de Cadena de Suministro Electrónico, Auditoría contra Falsificación de Semiconductores, DFM para Ensamblaje PCBA (JLCPCB/LCSC), Optimización Logística de Importación vs. Compra Nacional, ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Modo Co-Piloto Seguro y Transaccional en EasyEDA Pro

> [!IMPORTANT]
> **Nunca modifique el diseño a ciegas:** El agente actúa como un co-piloto colaborativo. Antes de escribir un bloque grande en el esquemático o el PCB, verifique el espacio libre, envuelva los cambios en una transacción reversible y muestre una captura visual al usuario.

### Flujo Obligatorio de Escritura Segura (Paso a Paso)

1. **Planifique una región libre antes de colocar símbolos:**
   * Ejecute `easyeda_schematic_sheet_info` y `easyeda_schematic_plan_safe_region` para ubicar coordenadas vacías sin encimar componentes existentes.
2. **Abra una transacción segura:**
   * Ejecute `easyeda_project_begin_transaction` antes de realizar inserciones o cableados por lotes (`easyeda_schematic_batch_write` o `easyeda_pcb_place_batch`).
3. **Verifique colisiones y conecte:**
   * Ejecute `easyeda_schematic_check_collisions`, `easyeda_schematic_verify_write` y `easyeda_project_validate_transaction`.
4. **Capture y explique al usuario:**
   * Tome una imagen del estado actual mediante `easyeda_canvas_capture` o `easyeda_schematic_capture_full_page`.
   * Explique en 2 oraciones claras qué bloque armó y qué norma aplicó.
5. **Confirme o revierta:**
   * Si no hay colisiones ni errores: ejecute `easyeda_project_commit_transaction` y `easyeda_project_save` (y confirme con `PCB_Document.save` / `Ctrl+S` si reporta `persistence_unverified`).
   * Si detecta superposición o el usuario solicita otro arreglo: ejecute inmediatamente `easyeda_project_rollback_transaction`.

---

## 2. Asistente Cotizador de 4 Canales: ¿Dónde Comprar Cada Componente?

El agente actúa como un **Ingeniero de Abastecimiento y Cotizador Completo**, evaluando cada línea del BOM en **4 canales complementarios** mediante la herramienta determinista **`pcb_quote_bom_multichannel`** y registrando la decisión en `BOM-SOURCING.md`:

| Ruta de Compra | Cuándo Elegirla | Herramientas Reales que Usa el Agente |
| :--- | :--- | :--- |
| **Ruta A: EasyEDA Pro / LCSC / JLCPCB** | Cuando el usuario pedirá placas ensambladas (**PCBA**) o quiere traer todos los chips originales y pasivos SMD en un solo flete con los PCBs. | `easyeda_bom_generate`, `easyeda_schematic_search_device` (lee `JLCPCB Part Class` y `Datasheet`), `easyeda_catalog_verify_device`, `easyeda_jlcpcb_quote_workflow`, `search_web` (`lcsc.com`). |
| **Ruta B: AliExpress (Minorista Internacional / Prototipos)** | Para armado manual de 1 a 20 prototipos: módulos DevKit, pantallas OLED/TFT, sensores pre-montados, borneras THT, cables y accesorios sin urgencia inmediata (12–25 días). | `search_web` (`domain: "aliexpress.com"`) y/o subagente `browser` auditando reputación ($\ge 95\%$, $\ge 4.7\star$), pedidos reales y envío consolidado (*Choice*). |
| **Ruta C: Alibaba (Mayorista / Fábrica OEM / Lotes)** | Escalamiento a serie (50 a 1000+ uds), gabinetes plásticos personalizados, arneses de cables a medida, teclados de membrana o packs LiPo/18650 con transporte DDP. | `search_web` (`domain: "alibaba.com"`) y/o `browser` exigiendo **`Verified Supplier`** (SGS/TÜV) + **`Trade Assurance`** y evaluando MOQ. |
| **Ruta D: Mercado Local (Tiendas Nacionales / MercadoLibre / Distribuidor Local)** | **1)** Urgencia de prototipo o reparación en **24–72 horas**.<br>**2)** Restricciones aéreas IATA (**baterías 18650/LiPo/plomo**, flux, aerosoles, transformadores pesados, gabinetes grandes IP65/DIN).<br>**3)** Necesidad de **factura fiscal nacional** (IVA deducible) o garantía inmediata. | `search_web` / `browser` en tiendas electrónicas del país del usuario (ej. Chile: `mcielectronics.cl`, `afel.cl`, `mechatronicstore.cl`, `kowka.cl`, `mercadolibre.cl`; México: `agelectronica.com`, `steren.com.mx`; Colombia: `vistronica.com`; Argentina: `electrocomponentes.com`; España: `cetronic.es`, `rs-online.com`) + `pcb_quote_bom_multichannel`. |

---

## 3. Reglas Reales de Extracción y Optimización en EasyEDA Pro / LCSC (Ruta A)

> [!WARNING]
> **Dos trampas reales detectadas en EasyEDA Pro 3.2.x que el agente debe manejar siempre:**
> 1. **Códigos Comunitarios `C9900...` (*User Contributed*):** Si un componente en EasyEDA Pro tiene código `C9900xxxxxx` (ej. `C9900017044`), **NO existe en el almacén de LCSC ni puede montarse en JLCPCB PCBA**. Úselo solo como huella para comprar la pieza en **Mercado Local / AliExpress**, o cámbielo por un Device con código LCSC oficial (`C1xxxx`–`C2xxxxxxx`).
> 2. **Modo *Keyless* en `easyeda_bom_sourcing`:** Sin llaves API configuradas, `easyeda_bom_sourcing` puede devolver `sourcing: []` y `easyeda_bom_quality_report` marcar falsos `no_match`. **Solución nativa:** extraiga el BOM con `easyeda_bom_generate` (que funciona aunque esté enfocada la pestaña PCB) y consulte cada código `Cxxxx` con **`easyeda_schematic_search_device`**, el cual lee directamente del motor de EasyEDA Pro el campo `otherProperty["JLCPCB Part Class"]` (`Basic Part` vs `Extended Part`) y la URL oficial del `Datasheet`.

1. **Priorice *Basic Parts* sobre *Extended Parts*:** En JLCPCB PCBA, las **Basic Parts** tienen **$\$0$** de recargo de montaje, mientras cada **Extended Part** suma $\approx \$3.00\,\text{USD}$ por cambio de carrete (*feeder loading fee*).
2. **Unifique valores de pasivos:** Consolide resistencias y capacitores en valores estándar (`10k`, `4.7k`, `1k`, `100nF`, `10uF`) para minimizar líneas del BOM.
3. **Alinee el encapsulado con quien soldará:** Si el usuario suelda a mano en laboratorio (`manual_lab`), evite `0201`/`0402` (alerte si aparece alguno en el BOM y ofrezca `0805`/`0603` o THT disponible en Mercado Local).

---

## 4. Protocolo de Auditoría en AliExpress, Alibaba y Mercado Local (Rutas B, C y D)

> [!CAUTION]
> **Riesgo de semiconductores falsificados (*Fake / Relabeled ICs*):** Nunca compre MCUs críticos (STM32, ESP32 sueltos), MOSFETs de potencia, reguladores Buck o sensores de precisión en vendedores informales si cuestan **menos del $40\%$ de su precio oficial en LCSC/Mouser**.

### 4.1. Criterios Estrictos en AliExpress (Ruta B)
1. **Tienda:** $\ge 95\%$ valoraciones positivas (ideal $\ge 97\%$ / *Choice*) y $\ge 2$ años de antigüedad.
2. **Producto:** $\ge 4.7\star$ y órdenes reales comprobables.
3. **Filtro Anti-Clon:** Si `precio_unitario < 0.40 * precio_LCSC` en un IC crítico $\rightarrow$ **descartar automáticamente**.

### 4.2. Criterios Estrictos en Alibaba (Ruta C)
1. **Sellos obligatorios:** **`Verified Supplier`** (auditado por SGS / TÜV / Bureau Veritas) + **`Trade Assurance`** activo.
2. **Evaluación de MOQ real:** Si el proyecto requiere 10 piezas pero el MOQ es 100, el costo real del lote debe calcularse sobre las **100 unidades facturadas** más flete e impuestos (`pcb_quote_bom_multichannel` lo calcula automáticamente).
3. **Plano mecánico previo al Gerber:** Exigir plano 2D/STEP y datasheet antes de cerrar perforaciones o cortes en EasyEDA Pro.

### 4.3. Criterios Inteligentes en Mercado Local (Ruta D)
1. **Pregunte el país/ciudad del usuario** si aún no está definido (ej. Santiago de Chile, CDMX, Bogotá, Buenos Aires, Madrid) e impuestos locales (ej. IVA $19\%$ en Chile).
2. **Priorice Mercado Local automáticamente cuando:**
   * El usuario necesita armar o reparar el prototipo **esta misma semana** ($\le 3\text{–}5$ días).
   * El ítem tiene restricción aérea o alto peso volumétrico: **celdas 18650 / baterías LiPo / baterías 12V plomo-ácido**, cajas estancas IP65/IP67, rieles DIN, transformadores, cables por rollo o químicos de soldadura.
   * Para lotes muy pequeños (1–3 prototipos), donde pagar un envío internacional dedicado supera el sobreprecio de una tienda electrónica local con retiro en tienda o despacho en 24 h.
3. **Verifique disponibilidad de huella THT/Estándar:** En tiendas electrónicas locales abundan componentes clásicos (`1N4148`, `1N5822`, `P6KE15CA`, `LM2596`, borneras `5.08 mm`, conectores `DC-005`, `JST-XH`, resistencias `1/4W` o `0805`). Si el usuario quiere poder reparar la placa con repuestos locales, considere huellas duales (SMD + THT en paralelo, tal como en placas industriales de protección) o paquetes estándar.

---

## 5. Ecuación de Costo Total Puesto en Laboratorio (*Total Landed Cost*) y Canasta Híbrida

Nunca compare solo el "precio unitario del anuncio". Ejecute siempre **`pcb_quote_bom_multichannel`** para comparar el **Costo Total Puesto en Laboratorio**:

$$\text{Landed Cost}_{\text{Import}} = \Big(\max(Q_{\text{lote}}, \text{MOQ}) \times P_{\text{unit}} + \text{Envío} + \text{Fee}_{\text{Extended}}\Big) \times \left(1 + \frac{\text{Impuesto/IVA}_{\%}}{100}\right)$$

$$\text{Landed Cost}_{\text{Local}} = (Q_{\text{lote}} \times P_{\text{unit, local}}) + \text{Despacho Nacional}$$

### Entregable Obligatorio al Usuario (`BOM-SOURCING.md`)
Entregue siempre una recomendación de **Canasta Híbrida Óptima** dividida por canal:
1. **Pedido 1 — EasyEDA Pro / JLCPCB / LCSC:** PCB + pasivos SMD *Basic* + semiconductores críticos con trazabilidad 100 % original.
2. **Pedido 2 — AliExpress / Alibaba (si el plazo lo permite):** Módulos, pantallas, sensores externos, conectores especiales o carcasas en volumen.
3. **Pedido 3 — Mercado Local (Entrega 24–72 h con factura):** Baterías LiPo/18650, gabinetes IP65/DIN, borneras de potencia y repuestos urgentes para *Bring-Up* inmediato en laboratorio.
