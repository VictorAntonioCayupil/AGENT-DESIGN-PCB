# Manual 16: Auditoría EMC/EMI Pre-Compliance, Conmutación de Alta Frecuencia y Filtros Industriales

> **Estándares aplicados:** CISPR 32 (Multimedia / ITE Clase B), CISPR 25 (Automotriz Clase 5), IEC 61000-4-4 (EFT/Burst), IEC 61000-4-6 (Inmunidad Conducida RF), Criterio de Estabilidad de Middlebrook, Regla 20-H e IPC-2152.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. El Lazo Caliente de Conmutación (*Hot Loop di/dt*)

En cualquier convertidor conmutado (Buck, Boost o Inversor), existe una malla cerrada por la que circulan pulsos de corriente con tiempos de transición de nanosegundos ($t_r \le 5\,\text{ns}$). Esta malla es la principal responsable de la **emisión radiada en campo cercano y lejano**.

### 1.1. Identificación Topológica del Hot Loop
- **Buck síncrono/asíncrono:** $C_{in} \to \text{MOSFET High-Side} \to \text{Diodo / Low-Side FET} \to C_{in}$. *(El inductor de salida y $C_{out}$ conducen corriente triangular suave, NO pertenecen al lazo caliente).*
- **Boost:** $\text{Switch Low-Side} \to \text{Diodo Rectificador / High-Side FET} \to C_{out} \to \text{Switch Low-Side}$. *(En Boost, el capacitor crítico es $C_{out}$).*
- **Inversor / Buck-Boost:** $C_{in} \to \text{Switch} \to \text{Diodo} \to C_{out}$.

### 1.2. Reglas de Ruteo de Cero Emisión para el Hot Loop
1. **Colocación Inmediata de $C_{in}$:** Coloque los capacitores cerámicos de desacoplo de alta frecuencia ($0.1\,\mu\text{F} + 10\,\mu\text{F}$) a menos de $1.5\,\text{mm}$ de los pines `VIN` y `PGND` del controlador.
2. **Plano GND Sólido Continuo en Capa 2:** Nunca interrumpa el plano de tierra directamente debajo del lazo caliente. La corriente de retorno de alta frecuencia viajará por efecto espejo inmediatamente debajo de la pista superior, reduciendo el área efectiva del lazo a $A \approx \text{longitud} \times h_{\text{dieléctrico}}$.
3. **Área Máxima Admisible:** Mantenga el área geométrica del lazo caliente por debajo de $25\,\text{mm}^2$ para cumplir **CISPR 32 Clase B**, o por debajo de $8\,\text{mm}^2$ para **CISPR 25 Clase 5**.

---

## 2. Espectro Conducido y Síntesis de Filtros en $\pi$

### 2.1. El Espectro Trapezoidal y la LISN
La medición de emisiones conducidas (150 kHz a 30 MHz) se realiza conectando el riel a una LISN de $50\,\Omega$. Los armónicos se extienden con pendientes de $-20\,\text{dB/dec}$ hasta $f_2 = \frac{1}{\pi t_r}$ y luego a $-40\,\text{dB/dec}$.

### 2.2. Dimensionamiento del Filtro $\pi$
Un filtro en $\pi$ ($C_1 - L_f - C_2$) proporciona hasta $40\text{--}60\,\text{dB/década}$ de atenuación:
1. Calcule la atenuación necesaria $\text{Att}_{\text{req}}$ en el armónico más desfavorable sumando un margen de seguridad de $6\,\text{dB}$.
2. Fije la frecuencia de corte $f_c \le 0.1 \cdot f_{sw}$.
3. Seleccione una inductancia de choque blindada $L_f$ con corriente de saturación $I_{\text{sat}} \ge 1.5 \cdot I_{in,\max}$ y baja capacitancia interbobinado.

---

## 3. Criterio de Impedancia de Middlebrook y Amortiguamiento

Un regulador conmutado con control en lazo cerrado mantiene potencia constante, lo que se traduce en una **resistencia incremental negativa**:
$$R_{in} = -\frac{V_{in}^2}{P_{in}}$$

Si el filtro de entrada LC presenta un pico de resonancia no amortiguado tal que $|Z_{out,\text{filter}}| \ge |R_{in}|$, se violan las condiciones de Nyquist y el circuito oscila violentamente.

### 3.1. Red de Amortiguamiento Óptima ($R_d - C_d$)
Para amortiguar el filtro sin disipar potencia en DC:
1. Conecte un capacitor de amortiguamiento $C_d = 4 \cdot C_2$ (típicamente electrolítico de aluminio o tantalio con ESR adecuada, o cerámico con resistor serie).
2. Agregue un resistor de amortiguamiento en serie con $C_d$:
   $$R_d \approx 0.6 \cdot \sqrt{\frac{L_f}{C_2}}$$
3. Compruebe mediante `pcb_emc_precompliance_auditor` que el margen de Middlebrook sea $\ge 9.5\,\text{dB}$.

---

## 4. Parásitos de Layout de Alta Frecuencia

### 4.1. Inductancia de Vías de Desacoplo
Cada vía pasante en un PCB estándar de $1.6\,\text{mm}$ introduce aproximadamente $0.7\text{--}1.0\,\text{nH}$ de inductancia parásita ($L_{via} \approx 0.2\,\text{nH/mm}$).
- Un capacitor de $100\,\text{nF}$ conectado con pistas largas y dos vías resonará a solo $12\text{--}15\,\text{MHz}$, perdiendo efectividad en el rango de conmutación rápida.
- **Regla:** Coloque los pares de vías (VCC y GND) lo más juntos posible ($<1\,\text{mm}$) para inducir acoplamiento mutuo cancelatorio y minimizar el área del bucle de vía.

### 4.2. Resonancias de Cavidad Plano-Plano y Contención
La cavidad formada por los planos de potencia y tierra actúa como un resonador de microondas con modos $TM_{mn}$:
1. **Regla 20-H:** Retraiga la frontera del plano de alimentación en $20 \times h$ respecto a la frontera del plano GND. Esto inclina las líneas de campo eléctrico hacia el plano GND reduciendo la radiación por los bordes en un $70\%$.
2. **Via Fence Perimetral:** Instale una hilera de vías GND cosiendo el perímetro de la placa con una distancia máxima:
   $$\Delta s \le \frac{\lambda_{\min}}{20} \approx 7.0\,\text{mm} \quad (\text{recomendado } 3\text{ a } 5\,\text{mm})$$
