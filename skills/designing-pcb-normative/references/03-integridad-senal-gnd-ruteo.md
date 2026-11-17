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

## 3. Pares Diferenciales y Prevención de Diafonía (*Crosstalk*)

### 3.1. Reglas para Pares Diferenciales (USB, Ethernet, HDMI, PCIe, RS-485)

1. **Configure la impedancia diferencial objetivo:** Diseñe para $90\,\Omega$ (USB), $100\,\Omega$ (Ethernet, HDMI, LVDS, RS-485) u $85\,\Omega$ (PCIe Gen 3+), según la especificación de la interfaz.
2. **Mantenga simetría geométrica:** Trace ambas líneas del par ($D+$ y $D-$) en la misma capa, con ancho y separación constantes en todo su recorrido.
3. **Iguale las longitudes dentro del par (*Intra-pair Skew*):** La diferencia de longitud entre la línea positiva y negativa no debe superar **$5\,\text{mils}$ ($\approx 0.127\,\text{mm}$)** (equivalente a un desfase temporal $< 5\,\text{ps}$) para evitar conversión de modo diferencial a ruido de modo común.
4. **Compense el desfase en el origen:** Si un pad o vía introduce asimetría, agregue los meandros de compensación (*trombone tuning*) inmediatamente cerca del punto donde se originó la diferencia de longitud.

### 3.2. Reglas de Separación contra Diafonía ($3W$ y $5W$)

> [!WARNING]
> **Acoplamiento inductivo y capacitivo entre pistas vecinas (*Crosstalk*):** Si traza pistas paralelas demasiado juntas, los campos electromagnéticos se solaparán e inducirán pulsos falsos en la pista víctima.

1. **Aplique la Regla $3W$ en señales digitales generales:** Mantenga una distancia centro a centro entre trazas adyacentes de al menos **tres veces el ancho de la pista ($3 \times W$)** (lo que equivale a un espacio libre borde a borde de $2 \times W$). Esto confina el $\approx 70\%$ del flujo electromagnético y reduce la diafonía a menos del $5\%$.
2. **Aplique la Regla $5W$ en relojes y señales críticas:** En líneas de reloj (`CLK`), señales analógicas de alta impedancia o pares diferenciales de alta velocidad, aumente la separación centro a centro a **cinco veces el ancho de la pista ($5 \times W$)**.

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
