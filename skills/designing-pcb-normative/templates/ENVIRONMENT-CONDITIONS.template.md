# Ficha de Contexto de Operación y Condiciones de Entorno (`ENVIRONMENT-CONDITIONS.md`)

> **Proyecto:** [Nombre del Proyecto]  
> **Revisión:** 1.0  
> **Fecha:** [YYYY-MM-DD]  
> **Diseñador / Usuario:** [Nombre]  
> **Agente Co-Piloto:** AGENT-DESIGN-PCB (S&D MMCALL)

---

## 1. Ubicación y Envolvente Física (*Enclosure*)

* **Ubicación de Operación:**
  - [ ] Interior residencial / oficina (Ambiente limpio y seco).
  - [ ] Interior industrial / taller (Polvo, vapores de aceite, interferencia de maquinaria).
  - [ ] Intemperie / Exterior (Lluvia directa, condensación, radiación solar UV).
  - [ ] Subterráneo / Sumergido / Confinado.
* **Gabinete o Carcasa Prevista:**
  - [ ] Caja plástica comercial estándar (ABS / Policarbonato).
  - [ ] Gabinete estanco con sello de goma (Grado **IP65** / **IP67** / **NEMA 4X**).
  - [ ] Riel DIN para tablero eléctrico industrial.
  - [ ] Caja impresa en 3D (PLA / PETG / ABS).
  - [ ] Sin gabinete (Placa desnuda para integración OEM).
* **Tratamiento de Protección de Placa:**
  - [ ] Estándar con máscara antisoldante (*Solder Mask*).
  - [ ] Tropicalizado con barniz protector (*Conformal Coating* según **IPC-CC-830**).
  - [ ] Encapsulado total en resina epoxi (*Potting*).

---

## 2. Condiciones Térmicas y Climáticas

* **Rango de Temperatura Ambiental:**
  - Temperatura mínima: `[ -40°C / -20°C / 0°C / 10°C ]`
  - Temperatura máxima: `[ 35°C / 50°C / 70°C / 85°C / 125°C ]`
* **Humedad Relativa Máxima:** `[ < 60% / 80% / 95% con condensación ]`
* **Grado de Contaminación (**IEC 60664-1**):**
  - [ ] Grado 1: Sin contaminación o solo seca y no conductora (sellado hermético).
  - [ ] Grado 2: Contaminación no conductora normal con condensación temporal ocasional (estándar comercial).
  - [ ] Grado 3: Contaminación conductora o polvo higroscópico pesado (ambiente industrial).

---

## 3. Esfuerzo Mecánico y Vibración

* **Exposición a Vibración / Impacto:**
  - [ ] Estacionario (Fijo en pared o banco sin movimiento).
  - [ ] Portátil / De mano (*Handheld* — riesgo de caída de 1 metro).
  - [ ] Vehicular / Móvil (Automóvil, camión, motocicleta, tractor, dron — vibración continua según **IEC 60068-2-6**).
  - [ ] Maquinaria Pesada / Vibratoria (Bombas industriales, compresores, motores de combustión).
* **Tipo de Conectores Requeridos:**
  - [ ] Pines header estándar $2.54\,\text{mm}$ (solo aceptable en laboratorio o prototipo).
  - [ ] Conectores con seguro de trabado positivo (JST-XH, Molex Micro-Fit, terminales tipo tornillo desenchufables).
  - [ ] Fijación de cables con prensaestopas (*cable glands*) en la caja.

---

## 4. Perfil de Energía y Ruido Eléctrico

* **Fuente Primaria:**
  - [ ] Batería recargable Li-ion / LiPo ($3.7\,\text{V}$ nominal, $4.2\,\text{V}$ máx).
  - [ ] Batería primaria no recargable (Pilas AA/AAA alcalinas o LiSOCl2 $3.6\,\text{V}$).
  - [ ] Puerto USB ($5\,\text{V}$ DC regulado).
  - [ ] Red eléctrica vehicular ($12\,\text{V}$ o $24\,\text{V}$ con alternador — transitorios **ISO 7637-2**).
  - [ ] Fuente industrial conmutada de $24\,\text{V}$ DC.
  - [ ] Tensión de red $110\text{--}230\,\text{V}$ AC (aislamiento reforzado **IEC 62368-1**).
* **Consumo y Autonomía:**
  - Consumo en reposo (*Sleep*): `[ < 15 µA / < 100 µA / Continuo ]`
  - Corriente pico en transmisión: `[ 0.1 A / 0.5 A / 2.0 A ]`
  - Tiempo de autonomía requerido: `[ Días / Meses / Años ]`

---

## 5. Longitud y Tendido de Cables Externos

* **Conexión a Sensores / Actuadores Externos:**
  - [ ] Todos los periféricos van soldados sobre el mismo PCB (longitud $\le 5\,\text{cm}$).
  - [ ] Cables cortos hacia la tapa del gabinete ($\le 30\,\text{cm}$).
  - [ ] Cables largos hacia el exterior ($> 1\,\text{metro}$ hasta $50\,\text{metros}$ — riesgo de inducción por rayos y ESD).
* **Blindaje Requerido para Cables Largos:**
  - Diodos supresores TVS dedicados en cada línea de entrada/salida (**IEC 61000-4-2** $\pm 8\,\text{kV}$ contacto / $\pm 15\,\text{kV}$ aire).
  - Resistencia serie limitadora ($22\text{--}100\,\Omega$) y condensador cerámico de $10\text{--}100\,\text{nF}$ a tierra.
