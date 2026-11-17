# Matriz de Abastecimiento y Auditoría de Componentes (`BOM-SOURCING.md`)

> **Generado por:** Agente Gestor de Hardware y PCB (`AGENT-DESIGN-PCB` — **S&D MMCALL**)  
> **Propósito:** Comparar y auditar costos, disponibilidad, calidad de proveedor y compatibilidad de huella entre el proveedor directo de EasyEDA Pro (**LCSC / JLCPCB**) y proveedores externos (**AliExpress / Alibaba**).

---

## 1. Resumen de Estrategia de Compra del Proyecto

* **Modalidad seleccionada:** `[Ensamblaje PCBA en JLCPCB / Soldadura Manual en Laboratorio / Híbrida]`
* **Cantidad de placas a armar (Lote):** `[Ej. 5 prototipos / 100 unidades de serie]`
* **Criterio de seguridad aplicado:** Semiconductores críticos y pasivos SMD cotizados en **LCSC** (trazabilidad original); módulos, conectores especiales, baterías y gabinetes auditados en **AliExpress / Alibaba** con verificación previa de huella mecánica.

---

## 2. Tabla Comparativa de Componentes y Proveedores

| Designador | Componente / MPN | Paquete / Footprint | Canal de Compra Elegido | Código LCSC (`Cxxxx`) / Categoría PCBA | Enlace y Tienda (AliExpress / Alibaba) | Auditoría de Proveedor ($\star$ / % / Antigüedad / Sello) | Costo Unitario + Envío (USD) | Riesgo de Falsificación / Notas de Huella |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| `R1..R10` | Resistencia $10\,\text{k}\Omega$ $1\%$ | `0805` / `0402` | **LCSC / JLCPCB** | `C17414` (**Basic Part**) | N/A | Distribuidor Oficial LCSC | $\$0.002$ | **Riesgo Nulo.** Sin recargo de carrete (*feeder fee*). |
| `U1` | MCU / Sensor Crítico | `QFN` / `LQFP` | **LCSC / JLCPCB** | `[Cxxxxxx]` (`Basic/Extended`) | `[Opcional si es módulo DevKit]` | Oficial / Tienda $\ge 97\%$ | `[$X.XX]` | **Priorizar LCSC** para evitar chips remarcados. |
| `MOD1` | Módulo / Pantalla / Sensor | `THT / Header` | **AliExpress** | No aplica (Montaje manual) | `[Nombre Tienda + URL]` | `Rating >= 4.8★, Tienda >= 95%` | `[$X.XX + Envío]` | Verificar distancia entre pines con calibre antes de cerrar PCB. |
| `J1 / BAT1` | Conector / Batería / Caja | `Custom / THT` | **Alibaba** | No aplica (Lote mayorista) | `[Proveedor + URL]` | `Verified Supplier + Trade Assurance` | `[$X.XX (MOQ: N)]` | Solicitar plano 2D/STEP al proveedor antes de fabricar Gerbers. |

---

## 3. Verificación de Reglas Anti-Sobrecosto y Anti-Falsificación

- [ ] Todos los pasivos SMD (`R`, `C`, `L`) para ensamblaje automático fueron consolidados en **Basic Parts** de JLCPCB para ahorrar cargos de cambio de carrete.
- [ ] Ningún circuito integrado crítico (MCU, ADC de precisión, MOSFET de potencia, regulador Buck) proviene de vendedores de AliExpress sin historial o con precios sospechosamente inferiores al $40\%$ de su valor en LCSC/Mouser.
- [ ] Todos los componentes comprados de forma independiente en **AliExpress** o **Alibaba** tienen sus dimensiones físicas (paso de pines, diámetro de perforación y altura máxima) validadas contra el *footprint* colocado en **EasyEDA Pro**.
