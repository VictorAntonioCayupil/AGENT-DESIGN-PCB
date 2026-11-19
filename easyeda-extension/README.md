# Extensión Bridge de EasyEDA Pro para AGENT-DESIGN-PCB

> **Extensión oficial para EasyEDA Pro (v3.2.x Desktop / Web).**  
> Proporciona el puente de comunicación bidireccional vía WebSocket seguro (`127.0.0.1:49620`) entre el editor gráfico de EasyEDA Pro y los agentes de IA (Antigravity, Claude Code, Cursor, Gemini CLI, etc.).

---

## 1. Contenido de esta Carpeta

* **`easyeda-bridge-extension.eext`**: Paquete empaquetado de la extensión de EasyEDA Pro listo para importar.
* **`easyeda-bridge-extension.checksums.json`**: Sumas de verificación SHA-256 de integridad del paquete.

---

## 2. Instrucciones de Instalación en EasyEDA Pro (Paso a Paso)

### Paso 1: Abrir el Gestor de Extensiones en EasyEDA Pro
1. Abra su aplicación de escritorio **EasyEDA Pro** (versión 3.2.209 o superior).
2. En la barra de menú superior, haga clic en:
   * **En Español:** `Avanzado` $\rightarrow$ `Gestor de Extensiones...`
   * **En Inglés:** `Advanced` $\rightarrow$ `Extensions Manager...`  
   *(En compilaciones antiguas de EasyEDA Pro: `Configuración / Settings` $\rightarrow$ `Extensiones` $\rightarrow$ `Extension Manager`).*

### Paso 2: Importar la Extensión
1. En la ventana emergente del Gestor de Extensiones, haga clic en el botón **`Importar Extensión`** (*Import Extension*).
2. Navegue hasta la carpeta `easyeda-extension/` de este repositorio y seleccione el archivo:
   ```text
   easyeda-bridge-extension.eext
   ```
3. Haga clic en **Abrir** (*Open*).

### Paso 3: Habilitar Permisos de Interacción Externa
1. En la lista de extensiones instaladas, localice **EasyEDA MCP Bridge**.
2. Asegúrese de que el interruptor esté **Activado** (*Enabled*).
3. Marque la casilla obligatoria:
   > **`[x] Permitir Interacción Externa`** (*Allow External Interaction*).
4. Guarde y cierre el Gestor de Extensiones.

### Paso 4: Reiniciar EasyEDA Pro (Obligatorio)
> [!IMPORTANT]
> **Cierre completamente EasyEDA Pro y vuelva a abrirlo.**  
> El motor de dispatch de extensiones de EasyEDA solo inicializa los sockets en memoria durante el arranque en frío.

### Paso 5: Conectar el Bridge con el Agente
1. Con su proyecto abierto en EasyEDA Pro, observe la barra de menú superior. Verá un nuevo menú llamado **`MCP Bridge`**.
2. Haga clic en **`MCP Bridge` $\rightarrow$ `Connect`** (*Conectar*).
3. Para verificar la conexión, haga clic en **`MCP Bridge` $\rightarrow$ `Status`**. Verá:
   * **Estado:** `Connected (127.0.0.1:49620)`
   * **Dispatch Build ID:** Activo
   * **Latencia:** $< 2\,\text{ms}$

A partir de este momento, cualquier agente de IA o LLM que tenga configurado `agent-design-pcb` y `easyeda-mcp-pro` podrá leer el esquemático, ubicar componentes, rutear pistas y vías, y auditar el DRC en tiempo real.
