# Matriz de Abastecimiento y Cotización Multicanal (`BOM-SOURCING.md`)

> **Generado por:** Agente Ingeniero de Hardware y Cotizador (`AGENT-DESIGN-PCB` v4.4 — **S&D MMCALL**)  
> **Propósito:** Cotizar, comparar y auditar costos reales puestos en laboratorio (*Landed Cost*), plazos de entrega, autenticidad y compatibilidad de huella entre **EasyEDA Pro (LCSC / JLCPCB)**, **AliExpress**, **Alibaba** y **Mercado Local** (tiendas nacionales con entrega 24–72 h y factura fiscal).

---

## 1. Parámetros Logísticos y de Armado del Proyecto

* **País / Ciudad de destino:** `[Ej. Chile (IVA 19%) / México (IVA 16%) / España (IVA 21%)]`
* **Plazo máximo requerido (*Lead Time*):** `[Ej. Urgente <= 3 días (Mercado Local) / Normal 18-25 días (Híbrido Importación + Local)]`
* **Modalidad de armado:** `[Ensamblaje PCBA en JLCPCB / Soldadura Manual en Laboratorio / Híbrida SMD+THT]`
* **Cantidad de placas a armar (Lote):** `[Ej. 5 prototipos / 100 unidades de serie]`
* **Resumen Calculado (`pcb_quote_bom_multichannel`):**
  * **Costo Total Canasta Híbrida Óptima:** **`[$XX.XX USD]`** (`[$X.XX USD / placa]`)
  * **Piezas Extended JLCPCB detectadas:** `[N]` | **Huellas Comunitarias `C9900...` detectadas:** `[N]`

---

## 2. Tabla Comparativa Multicanal por Componente

| Designador | Componente / MPN | Footprint | Cant. Total | LCSC (`Cxxxx` / Clase) | AliExpress / Alibaba (Tienda + Rating / MOQ) | Mercado Local (Proveedor + Plazo + Factura) | Canal Óptimo Elegido | Costo Total Lote (USD) | Notas de Calidad / Huella / IATA |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| `R1..R10` | Resistor $4.7\,\text{k}\Omega$ $1\%$ | `0805` | `10` | `C17673` (**Basic**) | N/A | Tienda Local (`$0.05`, 24h) | **LCSC / JLCPCB** | `\$0.03` | $\$0$ fee de carrete. Trazabilidad original. |
| `D1` | TVS `SMBJ15CA` $600\,\text{W}$ | `SMB` | `5` | `C8829` (*Extended*) | Choice $\ge 97\%$ (`4.9★`, 18d) | Distribuidor Local (`P6KE15CA` THT, 24h) | **LCSC** *(o Local si urgente)* | `\$0.48` *(+\$3 si PCBA)* | Si suelda a mano o usa huella dual (`D1`/`D11`), evita fee Extended. |
| `J1 / J3` | Conector `DC-005` / Bornera `5.08mm` | `THT` | `5` | `C9900...` *(Huella Comunitaria)* | Tienda $\ge 96\%$ (`4.8★`, 18d) | Tienda Electrónica Local (Stock inmediato, 24h, Factura) | **Mercado Local** *(o AliExpress)* | `\$2.50` | `C9900...` no existe en almacén LCSC. Validar paso de pines en mm. |
| `BAT1 / CAJA` | Celda `18650` / Gabinete `IP65` | `Externo` | `5` | Restricción aérea IATA | Alibaba `Verified + Trade Assurance` (MOQ 50, DDP) | **Proveedor Local** (Entrega 24–48h con IVA) | **Mercado Local** *(Prototipo)* / **Alibaba** *(Serie)* | `\$22.00` | Evita bloqueo aduanero/IATA en baterías de litio y flete volumétrico. |

---

## 3. Checklist de Auditoría Anti-Sobrecosto, Anti-Falsificación y Logística

- [ ] Se verificaron todos los códigos `Cxxxx` con `easyeda_schematic_search_device`: cualquier código `C9900...` fue reasignado a compra en **Mercado Local / AliExpress** o reemplazado por un Device LCSC real.
- [ ] Todos los pasivos SMD (`R`, `C`, `L`) para PCBA fueron consolidados en **JLCPCB Basic Parts** ($\$0$ fee de carrete) y se eliminaron paquetes `0201`/`0402` si el armado es manual en laboratorio.
- [ ] Ningún circuito integrado crítico (MCU, TVS de precisión, MOSFET, regulador) proviene de anuncios con precio $<40\%$ del valor oficial LCSC/Mouser.
- [ ] Baterías de litio, químicos, transformadores pesados y componentes de urgencia ($\le 72\,\text{h}$) fueron asignados a **Mercado Local** con verificación de stock y factura nacional.
