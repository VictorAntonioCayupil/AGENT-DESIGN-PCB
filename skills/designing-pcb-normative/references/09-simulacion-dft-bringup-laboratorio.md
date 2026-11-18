# Manual 09: Simulación SPICE, Diseño para Testabilidad (DFT) y Protocolo de *Bring-Up* en Laboratorio

> **Estándares aplicados:** Mejores Prácticas de Ingeniería de Prueba (DFT / DFX), Simulación de Punto de Operación y Transitorios en EasyEDA Pro, Protocolo de Energización Segura de Prototipos, ISO 24495-1 e ISO/IEC 82079-1.  
> **Autor:** S&D MMCALL — Proyecto Comunitario `AGENT-DESIGN-PCB`.

---

## 1. Simulación Previa del Circuito en EasyEDA Pro (`easyeda_simulate_*`)

Antes de sincronizar un circuito analógico, divisor de sensor, etapa MOSFET o filtro hacia el PCB, valide su comportamiento matemático mediante las herramientas nativas del conector MCP:

1. **Verificación de Punto de Operación DC (`easyeda_simulate_operating_point`):**
   * Úselo para comprobar las tensiones nodales en divisores resistivos de ADC, polarización de transistores, corrientes de polarización de diodos Zener y niveles de referencia.
2. **Verificación de Respuesta Transitoria en el Tiempo (`easyeda_simulate_transient`):**
   * Úselo para validar tiempos de retardo RC (como la red de arranque `EN`/`NRST`), respuesta de filtros pasa-bajos antialiasing, rizado de fuentes y picos de conmutación en cargas inductivas.

---

## 2. Diseño para Testabilidad en Laboratorio (DFT — *Design for Testability*)

> [!WARNING]
> **Placas imposibles de diagnosticar cuando algo falla:** Si ensambla una placa donde los reguladores alimentan directamente a todos los chips sin forma de seccionar los rieles ni puntos donde apoyar la punta del multímetro, un solo cortocircuito oculto impedirá saber qué componente está dañado.

### 2.1. Puntos de Prueba Obligatorios (*Test Points* — `TP`)

Coloque pads de prueba dedicados (de $1.0\,\text{mm}$ a $1.5\,\text{mm}$ de diámetro o *loops* THT en la cara superior `Top Layer`) claramente rotulados en la serigrafía (`Silkscreen`) para cada una de estas señales:

| Categoría | Puntos de Prueba (`TP`) Obligatorios | Recomendación de Ingeniería |
| :--- | :--- | :--- |
| **Referencia de Tierra** | **`TP_GND` (mínimo 2 en esquinas opuestas)** | Incluya al menos un agujero metalizado (THT) en `TP_GND` para enganchar cómodamente la pinza cocodrilo del multímetro o del osciloscopio sin que resbale. |
| **Rieles de Potencia** | `TP_VIN`, `TP_5V`, `TP_3V3`, `TP_VBAT` | Ubíquelos inmediatamente a la salida de cada regulador o fusible. |
| **Control del MCU** | `TP_RST` (`NRST`/`EN`), `TP_BOOT` | Permiten forzar reinicio o modo programación con una pinza si falla un pulsador. |
| **Buses y Señales** | `TP_SDA`, `TP_SCL`, `TP_TX`, `TP_RX`, `TP_ADC` | Permiten conectar un analizador lógico o multímetro sin tocar pines finos de un QFN/LQFP (evitando cortocircuitos accidentales con la punta de prueba). |

### 2.2. Seccionamiento de Rieles con Puentes de $0\,\Omega$ (*Isolation Jumpers*)

1. **Separe la fuente de la carga durante la primera prueba:** Coloque una resistencia SMD de **$0\,\Omega$** (paquete `0805` o `0603`) o un puente de soldadura abierto (*Solder Jumper* `SJ1`, `SJ2`) en serie a la salida de cada regulador de tensión antes de alimentar al microcontrolador y los periféricos.
2. **Ventaja en laboratorio:** Al recibir la placa fabricada, puede dejar sin montar esa resistencia de $0\,\Omega$, encender los reguladores en vacío, verificar con el multímetro que entregan exactamente $5.0\,\text{V}$ y $3.3\,\text{V}$ (y no $12\,\text{V}$ por un error de resistencia en el pin `FB`), y recién entonces soldar el puente de $0\,\Omega$ para alimentar al microcontrolador con total seguridad.

### 2.3. Indicadores Visuales de Diagnóstico (LEDs de Estado)

* Agregue un LED indicador (con resistencia limitadora de baja corriente, ej. $2.2\,\text{k}\Omega\text{–}4.7\,\text{k}\Omega$ para consumir apenas $\sim 0.5\text{–}1\,\text{mA}$) en el riel principal de $3.3\,\text{V}$ / $5\,\text{V}$ (con un puente deslizable o *jumper* para desconectarlo si el dispositivo operará a batería en modo *Deep Sleep*).

---

## 3. Protocolo de Puesta en Marcha en Laboratorio (*Board Bring-Up*)

> [!CAUTION]
> **Prohibido conectar un prototipo recién soldado directamente a una batería LiPo o cargador de alta corriente:** Una batería de litio o fuente de $5\,\text{A}$ puede entregar decenas de amperios ante un puente de soldadura oculto, vaporizando las pistas y quemando los integrados al instante.

Cuando el usuario termine de soldar o reciba su prototipo de fábrica, guíelo paso a paso con la lista de chequeo **[templates/BRINGUP-CHECKLIST.template.md](../templates/BRINGUP-CHECKLIST.template.md)** siguiendo estas 4 etapas:

### Etapa 1: Inspección Visual y Pruebas en Frío (Sin Energía)
1. **Inspección óptica con lupa o microscopio:** Revise orientación del Pin 1 en todos los circuitos integrados, polaridad de diodos/capacitores y ausencia de puentes de estaño entre pines de paso fino.
2. **Medición de resistencia en frío (Multímetro en modo Ohmios / Continuidad):**
   * Mida la resistencia entre cada punto de prueba de alimentación (`TP_VIN`, `TP_5V`, `TP_3V3`) y `TP_GND` **con la placa apagada**.
   * Si algún riel mide $< 50\,\Omega$ (o pita en continuidad directa a `GND`), **DETÉNGASE**: existe un cortocircuito de soldadura o un componente montado al revés. Localícelo antes de aplicar tensión.

### Etapa 2: Primer Encendido con Fuente de Laboratorio Limitada en Corriente
1. Configure la fuente de banco a la tensión nominal de entrada y ajuste el **límite de corriente máxima (*Current Limit / CC*) a un valor bajo y seguro** (por ejemplo, $50\,\text{mA}$ a $100\,\text{mA}$ para una placa con MCU sin actuadores activos).
2. Energice la etapa de alimentación (con los puentes de $0\,\Omega$ abiertos si aplica) y observe si la fuente cae en modo de corriente constante (CC).
3. Mida con el multímetro de precisión (si el entorno cuenta con el conector MCP del multímetro **`ut803`**, ejecute `ut803_esperar_estable` y `ut803_leer`) que cada riel se encuentre dentro del **$\pm 3\%$** de su tensión nominal:
   * Riel de $3.3\,\text{V}$: debe medir entre **$3.20\,\text{V}$ y $3.40\,\text{V}$**.
   * Riel de $5.0\,\text{V}$: debe medir entre **$4.85\,\text{V}$ y $5.15\,\text{V}$**.

### Etapa 3: Validación Térmica y de Relojes
1. Compruebe al tacto o con cámara térmica que ningún regulador, LDO o microcontrolador se caliente anormalmente en reposo ($\Delta T < 10\,^\circ\text{C}$ sin carga).
2. Cierre los puentes de $0\,\Omega$ hacia el microcontrolador, verifique que la tensión en `TP_RST` suba limpiamente a nivel lógico alto ($3.3\,\text{V}$) y compruebe el consumo base en reposo.

### Etapa 4: Detección por SWD/USB y Prueba Incremental de Periféricos
1. Conecte el programador SWD / ISP o cable USB-C y verifique que el microcontrolador responda con su ID de silicio (`Chip ID`).
2. Cargue un firmware mínimo de prueba (*Blink / Serial Heartbeat*), seguido de un escáner de bus I2C/SPI para confirmar que cada sensor responde en su dirección antes de activar etapas de potencia o relés.
