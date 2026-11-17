# Manual 06: Modo Co-Piloto en EasyEDA Pro y Gestor Global de Compras (LCSC, AliExpress y Alibaba)

> **Estándares aplicados:** Gestión de Calidad de Cadena de Suministro Electrónico, Auditoría contra Falsificación de Semiconductores, DFM para Ensamblaje PCBA (JLCPCB/LCSC), ISO 24495-1 e ISO/IEC 82079-1.  
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
   * Si no hay colisiones ni errores: ejecute `easyeda_project_commit_transaction` y `easyeda_project_save`.
   * Si detecta superposición o el usuario solicita otro arreglo: ejecute inmediatamente `easyeda_project_rollback_transaction`.

---

## 2. Gestor Completo de Abastecimiento: ¿Dónde Comprar Cada Componente?

El agente debe clasificar cada componente del proyecto según la preferencia del usuario en una de las **3 rutas de compra** y completar el archivo `BOM-SOURCING.md`:

| Ruta de Compra | Cuándo Elegirla | Herramientas que Usa el Agente |
| :--- | :--- | :--- |
| **Ruta A: Proveedor Nativo de EasyEDA Pro (LCSC / JLCPCB)** | Cuando el usuario pedirá las placas ya soldadas de fábrica (**PCBA**) o desea comprar todos los chips y pasivos SMD originales en un solo envío junto con el PCB. | `easyeda_schematic_search_device`, `easyeda_catalog_verify_device`, `easyeda_bom_sourcing`, `easyeda_bom_quality_report`, `easyeda_jlcpcb_quote_workflow`. |
| **Ruta B: Compra Independiente en AliExpress (Minorista / Prototipos)** | Cuando el usuario armará la placa a mano en su laboratorio y necesita módulos (ESP32, sensores láser, pantallas OLED), conectores THT, relés, cables o lotes de 1 a 20 unidades. | `search_web` (`domain: "aliexpress.com"`) y/o subagente `browser` para inspeccionar tiendas, estrellas, pedidos vendidos, costo de envío y reseñas reales. |
| **Ruta C: Compra Mayorista / Directa de Fábrica en Alibaba (Lotes y Piezas a Medida)** | Cuando el proyecto escala a producción (50 a 1000+ unidades) o requiere baterías LiPo/18650 con certificaciones, gabinetes plásticos, membranas o conectores directo del fabricante. | `search_web` (`domain: "alibaba.com"`) y/o subagente `browser` filtrando proveedores `Verified Supplier` y `Trade Assurance`. |

---

## 3. Reglas de Optimización cuando se Compra en EasyEDA Pro / LCSC / JLCPCB (Ruta A)

1. **Priorice *Basic Parts* sobre *Extended Parts*:** En el servicio PCBA de JLCPCB, los componentes catalogados como **Basic Parts** no cobran cargo adicional por cambio de carrete (*feeder loading fee*), mientras que cada **Extended Part** añade un costo fijo de preparación.
2. **Unifique valores de pasivos:** Reduzca la variedad de resistencias y capacitores del esquemático al mínimo necesario (por ejemplo, use $10\,\text{k}\Omega$, $4.7\,\text{k}\Omega$, $1\,\text{k}\Omega$ y $100\,\text{nF}$ en lugar de diez valores intermedios distintos).
3. **Verifique stock real antes de rutear:** Ejecute `easyeda_catalog_verify_device` y `easyeda_bom_sourcing`. Si un circuito integrado tiene stock `0` en LCSC, proponga un reemplazo compatible *pin-a-pin* antes de diseñar el PCB.

---

## 4. Protocolo de Búsqueda y Auditoría en AliExpress y Alibaba (Rutas B y C)

> [!CAUTION]
> **Riesgo de componentes falsificados (*Fake / Relabeled ICs*) e incompatibilidad mecánica:** En mercados abiertos existen chips remarcados (especialmente MCU STM32, MOSFETs de potencia, amplificadores operacionales de precisión y sensores) y conectores cuyas medidas difieren de las hojas de datos estándar.

### 4.1. Criterios Estrictos para Seleccionar un Producto en AliExpress

Cuando busque componentes o módulos en **AliExpress** para el usuario, verifique y reporte estos 5 filtros obligatorios:

1. **Reputación de la tienda:** Seleccione únicamente tiendas con **$\ge 95\%$ de valoraciones positivas** (idealmente $\ge 97\%$ y medalla *Top Brand* o *Choice*) y más de **2 años de antigüedad**.
2. **Calificación y volumen del ítem:** El producto debe tener una puntuación de **$\ge 4.7 / 5.0$ estrellas** y un volumen comprobable de órdenes vendidas con reseñas técnicas de compradores.
3. **Filtro Anti-Falsificación para Semiconductores Críticos:**
   * Si un circuito integrado desnudo (ej. STM32, sensor Bosch/Sensirion, transceptor aislado) cuesta en AliExpress **menos del $40\%$ de su precio oficial en LCSC/Mouser**, márquelo como **Riesgo Alto de Chip Remarcado/Clon**.
   * **Recomendación inteligente:** Aconseje comprar los chips SMD críticos en **LCSC** y dejar **AliExpress** para módulos de desarrollo, pantallas, carcasas, sensores pre-montados, borneras, botones, cables y accesorios.
4. **Cálculo de Costo Real Puesto en Destino (*Landed Cost*):**
   $$\text{Costo Total} = (\text{Precio Unitario} \times \text{Cantidad}) + \text{Costo de Envío}$$
   Compare si conviene comprar varias unidades en la misma tienda para unificar un solo envío (*AliExpress Choice* o *Standard Shipping*).
5. **Verificación de Huella Física (*Footprint Match*):** Antes de colocar el componente en el PCB de EasyEDA Pro, contraste las dimensiones en milímetros del anuncio (distancia entre pines, ancho del módulo, posición de agujeros M2/M3) con el *footprint* del diseño.

### 4.2. Criterios Estrictos para Seleccionar un Proveedor en Alibaba (Volumen y OEM)

Cuando busque proveedores mayoristas en **Alibaba**, aplique este filtro de auditoría industrial:

1. **Sello *Verified Supplier* obligatorio:** Priorice fabricantes cuya planta haya sido auditada presencialmente por entidades independientes (SGS, TÜV Rheinland, Bureau Veritas o Intertek).
2. **Protección *Trade Assurance* activa:** Asegure que el proveedor acepte pagos protegidos por *Alibaba Trade Assurance* para garantizar reembolso ante incumplimiento de calidad o plazos.
3. **Métricas operativas:** Verifique tasa de entrega a tiempo **$\ge 95\%$**, tiempo de respuesta $\le 4\,\text{h}$ y monto histórico de transacciones verificadas.
4. **Análisis de MOQ y Escalas de Precio:** Reporte al usuario el **MOQ** (*Minimum Order Quantity*, ej. $10\,\text{uds}$ vs. $500\,\text{uds}$) y los escalones de precio unitario.
5. **Solicitud de Plano Mecánico (2D DXF / 3D STEP) y Datasheet:** Indique al usuario que pida al proveedor de Alibaba el plano mecánico exacto y el datasheet antes de cerrar los archivos Gerber.

---

## 5. Formato de Entrega de la Propuesta de Compras al Usuario

Cada vez que el usuario pida buscar, cotizar o seleccionar los componentes de su placa, entréguele la tabla comparativa completa (basada en **[templates/BOM-SOURCING.template.md](../templates/BOM-SOURCING.template.md)**) indicando para cada pieza:
1. **Opción EasyEDA Pro / LCSC:** Código `Cxxxxxx`, tipo (`Basic` / `Extended`), stock y precio.
2. **Opción Independiente (AliExpress / Alibaba):** Nombre de la tienda verificada, enlace directo, calificación ($\star$ y % positivo), MOQ, precio unitario + envío y advertencias de calidad o huella física.
3. **Veredicto del Agente:** Cuál de las dos opciones le conviene más según su presupuesto, tiempo de entrega y método de soldadura.
