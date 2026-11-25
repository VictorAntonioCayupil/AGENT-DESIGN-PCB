# Manual 03: Integridad de Señal (SI), Planos GND Continuos, Diafonía y Ruteo HDI/Flex

> **Estándares aplicados:** IPC-2141A (Control de impedancia y líneas de transmisión), Reglas de Ruteo de Retorno GND y Diafonía (3W/5W), IPC-2226 (HDI), IPC-2223E (Circuitos Flexibles), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Arquitectura del Plano de Retorno GND (Regla Crítica de Ruteo)

> [!CAUTION]
> **Emisión electromagnética severa (EMI) y pérdida de integridad de señal:** En frecuencias altas, la corriente de retorno no regresa por el camino de menor resistencia DC, sino por el camino de **menor inductancia**, fluyendo por el plano de tierra exactamente debajo de la traza de señal. Si cruza un corte o ranura en el plano GND (*split plane*), abrirá el lazo de retorno, multiplicará la inductancia y convertirá la pista en una antena radiante.

### Procedimiento Obligatorio para el Plano GND

1. **Dedique un plano GND continuo:** En placas de 2 capas, reserve toda la cara inferior como plano de referencia GND lo más sólido posible; en placas de 4 o más capas, asigne al menos una capa interna completa e ininterrumpida a GND.
2. **Prohíba cruzar cortes de plano (*Split Planes*):** Nunca trace señales de reloj, buses rápidos (SPI, USB, Ethernet, I2S) ni líneas analógicas sensibles por encima de una división del plano de referencia.
3. **Añada vías de retorno al cambiar de capa:** Si una señal de alta velocidad cambia de capa mediante una vía, coloque una vía conectada a GND a menos de $1.0\,\text{mm}$ de distancia para dar continuidad vertical a la corriente de retorno.
4. **Costura de planos (*Via Stitching*):**Cosa los bordes del PCB y las islas de cobre con vías a GND cada $\lambda / 20$ (o cada $5\text{–}10\,\text{mm}$ en diseños generales) para suprimir modos resonantes de cavidad.

---

## 2. Control Geométrico de Impedancia Característica ($Z_0$ — IPC-2141A)

Cuando el tiempo de subida de una señal es sub-nanosegundo, la geometría física de la pista y su distancia al plano GND determinan su impedancia característica ($Z_0$).

### 2.1. Topología Microstrip (Capa Externa sobre un Plano de Referencia)

Calcule la impedancia característica ($Z_0$) en función del ancho de pista ($W$), espesor del dieléctrico ($H$), espesor del cobre ($T$) y constante dieléctrica ($\epsilon_r$):

$$Z_0 = \frac{87}{\sqrt{\epsilon_r + 1.41}} \ln \left( \frac{5.98 \cdot H}{0.8 \cdot W + T} \right)$$

### 2.2. Topología Stripline (Capa Interna Confinada entre Dos Planos de Referencia)

Para trazas embebidas simétricamente en un dieléctrico de espesor total $B$ entre dos planos de referencia:

$$Z_0 = \frac{60}{\sqrt{\epsilon_r}} \ln \left( \frac{1.9 \cdot B}{0.8 \cdot W + T} \right)$$

> [!NOTE]
> **Límite matemático del modelo IPC-2141A:** Las ecuaciones logarítmicas de **IPC-2141A** pierden precisión o arrojan valores erráticos cuando la relación geométrica supera $W / H > 7.5$. Para producción crítica de RF o enlaces multigigabit, solicite al fabricante el ajuste mediante un solucionador de campos 2D (*2D Field Solver*) que compense el grabado trapezoidal (*undercut*) y el recubrimiento de máscara antisoldante.

---

## 3. Ruteo de Pares Diferenciales Críticos de Alta Velocidad y Prevención de Diafonía

> **Estándares de Referencia:** IPC-2141A, IPC-2251, IEEE 802.3 (Ethernet), USB-IF (USB 2.0 / USB 3.2), ISO 11898-2 (CAN-FD) y MIPI Alliance D-PHY v1.2/v2.0.

### 3.1. Matriz de Parámetros Normativos por Protocolo

| Protocolo | Estándar | $Z_{diff}$ Objetivo | Tolerancia | Flanco $t_r$ | Skew Máx. ($\Delta L$) | Requerimiento Especial de Ruteo |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **USB 2.0 (High-Speed)** | USB 2.0 Spec | $90\,\Omega$ | $\pm 10\%$ ($81\text{–}99\,\Omega$) | $0.5\,\text{ns}$ | $< 0.127\,\text{mm}$ ($5\,\text{mil}$) | D+/D- simétricos; plano GND continuo en L2 sin cortes. |
| **USB 3.0 (SuperSpeed)** | USB 3.2 Spec | $90\,\Omega$ | $\pm 10\%$ ($\pm 7\,\Omega$ rec.) | $0.07\,\text{ns}$ | $< 0.127\,\text{mm}$ ($5\,\text{mil}$) | Caps AC de $100\,\text{nF}$ (0402) simétricos en TX; Stripline o Via Fence. |
| **Fast Ethernet (100M)** | IEEE 802.3u | $100\,\Omega$ | $\pm 10\%$ ($90\text{–}110\,\Omega$)| $3.0\,\text{ns}$ | $< 0.150\,\text{mm}$ ($6\,\text{mil}$) | Transformador Magnetics 1:1; corte de chasis ($2\,\text{mm}$) en RJ45. |
| **Gigabit Ethernet (1G)**| IEEE 802.3ab | $100\,\Omega$ | $\pm 10\%$ ($90\text{–}110\,\Omega$)| $1.0\,\text{ns}$ | $< 0.127\,\text{mm}$ ($5\,\text{mil}$) | 4 pares (TRD0..3); matching par-a-par $< 1.0\,\text{mm}$. |
| **CAN-Bus / CAN-FD** | ISO 11898-2 | $120\,\Omega$ | $\pm 10\%$ ($108\text{–}132\,\Omega$)| $5.0\,\text{ns}$ | $< 0.150\,\text{mm}$ ($6\,\text{mil}$) | Split Termination ($2 \times 60\,\Omega + 4.7\,\text{nF}$ a GND) en extremos. |
| **MIPI CSI-2 / DSI** | MIPI D-PHY | $100\,\Omega$ | $\pm 10\%$ ($90\text{–}110\,\Omega$)| $0.2\,\text{ns}$ | $< 0.100\,\text{mm}$ ($4\,\text{mil}$) | Reloj y Datos HS; Skew Clock-to-Data $< 1.0\,\text{mm}$; sin stubs. |

### 3.2. Topologías de Ruteo: Microstrip vs. Stripline
- **Edge-Coupled Microstrip (Capas Externas - Top/Bottom):** Adecuado para USB 2.0, Ethernet 100M y CAN-Bus. Sin vías metalizadas requeridas desde conectores SMD.
- **Edge-Coupled Symmetric Stripline (Capas Internas confinadas):** Obligatorio o recomendado para USB 3.0 SuperSpeed (5-10 Gbps) y MIPI D-PHY. Confinamiento electromagnético total entre planos GND, eliminando la radiación externa.

### 3.3. Acoplamiento Estrecho (*Tight*) vs. Holgado (*Loose*)
- **Acoplamiento Estrecho ($S \le 2W$):** Fuerte acoplamiento capacitivo e inductivo mutuo ($k_c > 0.15$). Menor susceptibilidad a ruido externo; sensible a discontinuidades en conectores.
- **Acoplamiento Holgado ($S > 2W$):** Las trazas se comportan como dos líneas independientes de $Z_0 \approx Z_{diff} / 2$. Ideal con componentes en serie intermedios (capacitores AC, ferritas) e inmune a tolerancias de grabado químico.

### 3.4. Regla Cardinal de Retorno: Prohibición de Cruce de Planos Divididos (*Split Planes*)
> [!CAUTION]
> **Pérdida Catastrófica de Integridad de Señal y Emisión EMI:** La corriente de retorno fluye por el plano de tierra directamente bajo la traza diferencial ($I \propto 1 / (1 + (x/H)^2)$). Si el par cruza un corte de plano (*split plane*), la inductancia de bucle se multiplica ($5\text{–}15\,\text{nH}$), se genera un salto de impedancia diferencial de más de $150\,\Omega$ y el corte actúa como antena de ranura irradiando armónicos destructivos.
> **Regla Mandataria:** Rutee siempre sobre plano GND 100% continuo. Si el par debe cambiar de capa, coloque dos vías de costura GND (*ground stitching vias*) a menos de $0.8\,\text{mm}$ de las vías diferenciales.

### 3.5. Geometría de Curvas, Mitrado y Compensación de Skew
1. **Prohibición de Esquinas a 90°:** Causan exceso capacitivo ($C_{corner} \approx 0.03\,\text{pF}$) y degradan flancos ultra-rápidos.
2. **Geometrías Válidas:** Arcos circulares suaves con radio $R \ge 3 \times W$ o chaflanes a 45° con biselado estándar del 50–60%.
3. **Compensación de Skew por Curva:** En cada curva, la traza exterior recorre mayor longitud ($\Delta L_{90^\circ} = 1.57 \cdot (W + S)$). Incorpore un meandro tipo trombón en la traza interior inmediatamente al salir de la curva (amplitud $\le 3W$, paso $\ge 3W$).

### 3.6. Apantallamiento Lateral con Vías (*GND Via Fence*)
Para proteger pares de alta velocidad contra interferencias de fuentes conmutadas (DC-DC) o transmisores RF:
1. Frecuencia de rodilla: $f_{knee} = 0.35 / t_r$.
2. Longitud de onda en el dieléctrico: $\lambda = v_{prop} / f_{knee}$.
3. Paso máximo entre vías de costura: $p_{via} \le \lambda / 20$.
4. Distancia de aislamiento lateral: $d_{fence} \ge \max(3 \times W, 2 \times H)$ para no alterar la impedancia diferencial.

### 3.7. Reglas de Separación contra Diafonía ($3W$ y $5W$)
1. **Regla $3W$ en señales digitales generales:** Distancia centro a centro $\ge 3 \times W$ (espacio libre borde a borde $\ge 2 \times W$), reduciendo la diafonía a menos del 5%.
2. **Regla $5W$ en relojes y señales críticas:** En líneas de reloj (`CLK`), señales analógicas de alta impedancia o pares diferenciales, aumente la separación a cinco veces el ancho ($5 \times W$).

---

## 4. Interconexión de Alta Densidad (HDI — IPC-2226) y Circuitos Flexibles (IPC-2223E)

### 4.1. Arquitecturas HDI (`X+N+X`) para Encapsulados BGA de Paso Fino ($\le 0.5\,\text{mm}$)

Cuando el paso de las esferas BGA desciende a $0.5\,\text{mm}$ o $0.4\,\text{mm}$, sustituya las vías mecánicas por microvías perforadas por láser (diámetro $< 0.15\,\text{mm}$) bajo la norma **IPC-2226**:

| Arquitectura IPC-2226 | Nomenclatura | Estructura de Vías | Recomendación de Confiabilidad |
| :---: | :---: | :--- | :--- |
| **HDI Tipo I** | `1+N+1` | 1 capa de microvías ciegas por cara + vías pasantes (PTH) de lado a lado. | Opción más económica para BGA de paso $0.5\,\text{mm}$. |
| **HDI Tipo II** | `1+N+1` con enterradas | Microvías ciegas en superficie + vías mecánicas enterradas (*buried*) en el núcleo central. | Óptima densidad y ruteabilidad para SoC industriales. |
| **HDI Tipo III** | `2+N+2` o superior | Dos o más laminaciones secuenciales láser por cara. | **Prefiera microvías escalonadas (*Staggered*)** sobre apiladas (*Stacked*). |

> [!CAUTION]
> **Fractura interfacial en microvías apiladas (*Stacked Microvias*):** Si utiliza arquitectura HDI Tipo III, evite apilar más de 2 niveles de microvías una sobre otra. Apilar 3 o más niveles concentra el esfuerzo termomecánico del eje Z y dispara la tasa de fractura. Priorice siempre microvías escalonadas (*staggered*) que distribuyen la tensión en el plano XY.

### 4.2. Reglas de Diseño para Circuitos Flexibles y Rígido-Flexibles (IPC-2223E)

1. **Respete el radio mínimo de curvatura:** Multiplique el espesor total del sustrato flexible por el factor normativo de **IPC-2223E**:
   * **Flexión estática (*flex-to-install*, 1 capa):** Radio mínimo $\ge 6 \times$ el espesor.
   * **Flexión dinámica continua (1 capa):** Radio mínimo $\ge 100 \times$ el espesor.
   * **Flexión dinámica continua (2 capas):** Radio mínimo $\ge 150 \times$ el espesor.
2. **Trace a $90^\circ$ respecto a la línea de doblez:** Todas las pistas que crucen una zona de flexión deben entrar y salir de forma perfectamente perpendicular ($90^\circ$) al eje de plegado.
3. **Elimine vías y componentes en la zona de doblez:** No coloque nunca vías metalizadas, pads ni cambios bruscos de ancho dentro de la región de curvatura.

---

## 5. Herramientas de `easyeda-mcp-pro` para esta Fase

1. `easyeda_design_rules_lookup` con `topic: "protocol-routing"` (soporta `usb2`, `usb3`, `rs485`, `i2c`, `spi`, `uart`, `ethernet-10-100`, `ethernet-1000`).
2. `easyeda_pcb_floorplan` y `easyeda_pcb_place_component_group` para agrupar bloques funcionales antes de trazar.
3. `easyeda_pcb_zone_preflight` y `easyeda_pcb_add_zone` para crear los planos continuos de retorno GND.
4. `easyeda_pcb_route_path_plan`, `easyeda_pcb_add_track`, `easyeda_pcb_add_via` y `easyeda_pcb_rebuild_copper` para ejecutar el ruteo respetando la continuidad de planos y las reglas $3W/5W$.
