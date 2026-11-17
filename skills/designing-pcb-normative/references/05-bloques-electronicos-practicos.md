# Manual 05: Bloques Electrónicos Prácticos y Formulación de Circuitos

> **Estándares aplicados:** Especificación USB Type-C, Diseño Térmico y de Conmutación SMPS, Especificación Bus I2C (NXP UM10204), Estándar TIA/EIA-485 (RS-485), ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Alimentación y Datos por USB Tipo-C (Receptor $5\,\text{V}$ / UFP)

> [!CAUTION]
> **La placa no enciende con cargadores USB-C a USB-C:** Si deja flotando los pines `CC1` y `CC2` o conecta ambos a una sola resistencia compartida, las fuentes USB-C modernas (PD) no detectarán el dispositivo y mantendrán apagados los $5\,\text{V}$ de `VBUS`.

### Procedimiento de Diseño Correcto para USB-C ($5\,\text{V}$ hasta $3\,\text{A}$)

1. **Instale dos resistencias independientes de $5.1\,\text{k}\Omega$ ($\pm 1\%$ o $\pm 5\%$):**
   * Conecte una resistencia de $5.1\,\text{k}\Omega$ desde el pin **`CC1`** a `GND`.
   * Conecte una segunda resistencia independiente de $5.1\,\text{k}\Omega$ desde el pin **`CC2`** a `GND`.
2. **Uno los pines simétricos del conector 16-Pin:**
   * Conecte todos los pines `VBUS` (`A4`, `A9`, `B4`, `B9`) entre sí.
   * Conecte todos los pines `GND` (`A1`, `A12`, `B1`, `B12`) directamente al plano GND.
   * Una `A6` con `B6` (`D+`) y `A7` con `B7` (`D-`) lo más cerca posible de los pads haciendo transición simétrica para mantener una impedancia diferencial de **$90\,\Omega$**.
3. **Agregue protección ESD dedicada:** Instale una matriz TVS de baja capacitancia (ej. **`USBLC6-2SC6`** o **`SRV05-4`**) inmediatamente a la salida del conector protegiendo `VBUS`, `D+` y `D-`.

---

## 2. Selección y Diseño de Reguladores: Lineal (LDO) vs. Conmutado (Buck Step-Down)

### 2.1. Criterio Termodinámico de Selección

1. Calcule la potencia disipada en calor si usara un regulador lineal (LDO):

$$P_{\text{loss}} = (V_{\text{in}} - V_{\text{out}}) \cdot I_{\text{load}}$$

2. **Regla de decisión rápida:**
   * **Si $P_{\text{loss}} \le 0.4\,\text{W}$** (o si alimenta sensores analógicos/RF sensibles al rizado con baja caída de tensión, ej. $3.7\,\text{V} \rightarrow 3.3\,\text{V}$): Utilice un **LDO de bajo ruido y baja corriente de reposo ($I_q$)** (ej. `AP2112K-3.3`, `XC6206`, `HT7333` — evite el antiguo `AMS1117` en baterías por su alto consumo en reposo de $\approx 5\,\text{mA}$ y su exigencia de ESR específica).
   * **Si $P_{\text{loss}} > 0.5\,\text{W}$** (ej. bajar de $12\,\text{V}$ o $24\,\text{V}$ a $3.3\,\text{V} / 5\,\text{V}$ con $I_{\text{load}} \ge 150\,\text{mA}$): Utilice obligatoriamente un **convertidor Buck síncrono (Step-Down)**.

### 2.2. Reglas Críticas de Layout para Convertidores Buck

> [!WARNING]
> **Ruido severo y fallo de regulación en fuentes conmutadas:** El lazo por donde circula la corriente pulsante de alta frecuencia ($di/dt$) se denomina **Lazo Caliente (*Hot Loop*)**. Si este lazo es largo, radiará EMI a toda la placa.

1. **Minimice el Lazo Caliente (*Hot Loop*):** Coloque el capacitor cerámico de entrada ($C_{\text{in}}$) pegado a los pines `VIN` y `GND` del chip Buck.
2. **Mantenga el nodo `SW` compacto:** Use un polígono corto y ancho entre el pin `SW`, el inductor blindado y el capacitor de *Bootstrap*, evitando extender ese cobre más de lo necesario para no crear acoplamiento capacitivo.
3. **Aísle la línea de realimentación (`FB`):** Ubique las resistencias del divisor de tensión `FB` pegadas al pin `FB` del integrado y tome la muestra de tensión *después* del último capacitor de salida ($C_{\text{out}}$), trazando la pista lejos del inductor y del nodo `SW`.

---

## 3. Gestión de Baterías Li-Ion / LiPo (3.7 V nominal / 4.2 V carga)

1. **Conmutación automática USB / Batería (*Power Path*):**
   * Coloque un transistor **MOSFET de canal P** (ej. `AO3401A`) entre la batería (`VBAT`) y la entrada del regulador (`VSYS`), con su compuerta conectada a `VBUS` ($5\,\text{V}$), una resistencia de $100\,\text{k}\Omega$ de compuerta a `GND` y un diodo Schottky de baja caída (ej. `SS14` / `MBR0520`) desde `VBUS` hacia `VSYS`.
   * Cuando se conecta el USB, el MOSFET corta la batería automáticamente; al desconectar el USB, la batería alimenta el sistema sin reinicios.
2. **Medición de tensión de batería por ADC sin drenaje:**
   * Utilice un divisor resistivo de alta impedancia (ej. dos resistencias de $100\,\text{k}\Omega$ a $470\,\text{k}\Omega$) acompañado en paralelo por un **capacitor cerámico de $100\,\text{nF}$** en el pin ADC. El capacitor entrega la carga instantánea que pide el muestreador interno (*Sample & Hold*) del ADC sin falsear la lectura.

---

## 4. Buses de Comunicación: I2C y RS-485 Industrial

### 4.1. Cálculo de Resistencias *Pull-Up* en Bus I2C (NXP UM10204)

1. Calcule el límite mínimo (por corriente de hundimiento máxima de $3\,\text{mA}$ en modo estándar/rápido) y máximo (por tiempo de subida $t_r$ y capacitancia total del bus $C_{\text{bus}}$):

$$R_{p(\min)} = \frac{V_{DD} - 0.4\,\text{V}}{3\,\text{mA}} \quad ; \quad R_{p(\max)} = \frac{t_r}{0.8473 \cdot C_{\text{bus}}}$$

2. **Valores prácticos probados a $3.3\,\text{V}$:**
   * Pistas cortas en la misma placa ($100\,\text{kHz}\text{–}400\,\text{kHz}$, $C_{\text{bus}} < 50\,\text{pF}$): **$4.7\,\text{k}\Omega$**.
   * Múltiples sensores o cables cortos ($400\,\text{kHz}$, $C_{\text{bus}} \approx 100\text{–}200\,\text{pF}$): **$2.2\,\text{k}\Omega$ a $3.3\,\text{k}\Omega$**.

### 4.2. Interfaz RS-485 Robusta para Entornos Industriales

1. **Terminación diferencial:** Coloque una resistencia de **$120\,\Omega$** ($\ge 0.25\,\text{W}$) entre las líneas `A` y `B` en los dos extremos físicos del bus (habilitable mediante *jumper*).
2. **Protección contra sobretensiones y modo común:** Instale un diodo TVS asimétrico específico para RS-485 (ej. **`SM712`**, que soporta $-7\,\text{V}$ a $+12\,\text{V}$) junto a la bornera y fusibles rearmables PTC o resistencias de pulso de $10\,\Omega$ en serie.

---

## 5. Control de Cargas Inductivas (Relés, Solenoides, Válvulas y Motores DC)

> [!CAUTION]
> **Destrucción del transistor y reinicio del MCU por pico inverso ($V = -L \frac{di}{dt}$):** Al cortar la corriente de una bobina, el campo magnético colapsa generando cientos de voltios en polaridad inversa.

1. **Instale siempre un diodo de rueda libre (*Flyback*):** Conecte un diodo (ej. `1N4148` para relés pequeños o `1N4007` / Schottky `SS14` para cargas mayores) en antiparalelo directamente sobre los terminales de la bobina (cátodo al positivo, ánodo al colector/drenador del transistor).
2. **Diseñe correctamente la etapa de disparo con MOSFET Canal N:**
   * Coloque una **resistencia en serie de compuerta ($R_g = 22\,\Omega\text{–}100\,\Omega$)** para limitar el pico de corriente de carga de la capacitancia $C_{gs}$ desde el pin del MCU.
   * Coloque una **resistencia de descarga (*Pull-Down*, $R_{gs} = 10\,\text{k}\Omega\text{–}100\,\text{k}\Omega$)** entre compuerta y fuente (`GND`) para evitar que el relé o motor se active solo mientras los pines del MCU están en alta impedancia durante el arranque.
3. **Elija MOSFETs de nivel lógico (*Logic-Level*):** Verifique que el datasheet especifique una baja resistencia $R_{DS(\text{on})}$ a $V_{GS} = 2.5\,\text{V}$ o $3.3\,\text{V}$ (ej. `AO3400A`), no solo a $V_{GS} = 10\,\text{V}$.

---

## 6. Entradas de Sensores Analógicos y Filtrado Antialiasing

1. **Coloque un filtro RC pasa-bajos antes del pin ADC:**
   * Calcule la frecuencia de corte ($f_c$) por debajo de la mitad de la frecuencia de muestreo ($f_s / 2$, criterio de Nyquist):

$$f_c = \frac{1}{2\pi \cdot R \cdot C}$$

   * Ejemplo para sensores de temperatura, presión o nivel: $R = 1\,\text{k}\Omega$ y $C = 100\,\text{nF}$ ($f_c \approx 1.59\,\text{kHz}$), ubicando el capacitor pegado al pin del microcontrolador.
2. **Proteja entradas analógicas expuestas:** Si la señal analógica viene desde un cable externo, agregue diodos de enclavamiento Schottky de baja fuga hacia `VDD` y `GND` o un TVS de baja capacitancia.
