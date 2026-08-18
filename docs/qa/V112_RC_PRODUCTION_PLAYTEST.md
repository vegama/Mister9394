# v1.1.2 — RC production bundle + persona playtest

Fecha: 18-08-2026

## Estado

**CANDIDATO RC JUGABLE sobre bundle compilado real.** El repositorio aporta `deploy_dist` y la pasada ejecuta ese JS/CSS compilado contra el backend real. No se reconstruye con piezas externas ni se sustituye por un DOM ficticio.

## Evidencia ejecutada

- `backend/tools/rc_production_browser_gate.py --policy-safe`: **58/58 PASS**.
- `backend/tools/rc_persona_playtest.py`: **18/18 PASS**.
- Frontend source: version PASS, SFC PASS, UI PASS, UX PASS, network **10/10**, Vue **38/38**.
- Release/refactor: H + M **13/13**.
- Launcher HTTP real: **6/6 PASS** (`health`, `index.html`, referencias de bundle, assets y MIME).
- El historial previo mantiene carrera longitudinal **14/14 segmentada**, incluidos 93/94→94/95→95/96.

## Producción / navegador

El gate de producción verifica sobre el bundle compilado:

- Nueva carrera completa con liga/club reales y contraste medido; ratios observados: título **16.46**, dato de club **16.02**, texto secundario **8.21**.
- 1920×1080, 1366×768, 1280×720 y 1024×768.
- Reflow equivalente a 200 % en 960×540, 683×384, 640×360 y 512×384.
- Sin overflow horizontal global y navegación móvil inferior de una sola fila.
- Ctrl+K → Mercado.
- Topbar sticky tras scroll profundo de Mercado (`scrollY=923`, topbar y=0).
- Atrás y Adelante reales mediante History API.
- `page.reload()` literal conservando ruta y carrera.
- feedback >500 ms, caída de conexión, recuperación y error no fatal.
- doble clic de mutación = una sola operación.
- sin `pageerror` ni errores de consola de aplicación.
- sólo el CTA primario se admite como superficie clara en Inicio; Mercado no contiene superficies claras heredadas.

## Playtest de personas

### Persona nueva

La ayuda de primer día explica que no necesita recorrer todos los menús. La acción principal lleva directamente a Tácticas, donde se muestra el proceso de preparación y el siguiente paso. Existe retorno visible a Inicio.

### Persona experta

Ctrl+K abre Mercado; una búsqueda y `Consultar` convierten el objetivo en un proceso visible. La tabla/resultados mantiene la gramática oscura y la topbar no desaparece al trabajar con scroll.

### Experiencia completa partido → consecuencia

La carrera avanza a día de partido; Inicio expone `Ir a la previa`; la cabecera cambia a `Partido · DÍA DE PARTIDO`; la previa permite revisar XI/táctica y deja claro que el reloj no corre; `Resultado` termina el encuentro; el postpartido explica lectura, momentos, diagnóstico y consecuencias; al cerrar vuelve a carrera y cambia el siguiente acontecimiento.

## P1/P2 encontrados en el render real y corregidos

1. **Nueva carrera casi ilegible** por fondos claros heredados con tokens oscuros → superficies de setup migradas a gramática oscura y contraste protegido.
2. **Topbar dejaba de ser sticky** porque `.manager-main { overflow-x:hidden }` creaba contenedor de scroll → `overflow-x:clip`, protegido por gate después de scroll profundo.
3. **Mercado mezclaba tabla/filtros blancos** con tema oscuro → filtros, resultados, estados de ventana, cupo y negociación normalizados.
4. **Previa/postpartido mezclaban tema claro** y la cabecera decía `Inicio` dentro de partido → superficies de matchday oscuras + orientación `Partido · DÍA DE PARTIDO`.
5. **Postpartido con media fila visual vacía** cuando el número de bloques era impar → último bloque ocupa ambas columnas.
6. **Estados vacíos de Inicio concatenaban título y explicación** → `display:grid` + separación explícita.
7. **Fila controlada y confianza del consejo excesivamente claras** → énfasis semántico oscuro sin perder identificación.

## Artefacto certificado

- JS: `index-94a754db.js` · SHA-256 `94a754db82a3550068cdd1863b1dfc5025f3b7fced488931977f4efb8bca4d27`
- CSS: `index-aed6cc31.css` · SHA-256 `aed6cc3114f4b18f170c41591f30012846e59ed6532a365116a5d66506a4fdb0`
- `deploy_dist/index.html` referencia únicamente esos assets principales.

## Limitación de entorno, no de producto

El Chromium gestionado tiene política `URLBlocklist=["*"]` y bloquea la navegación normal a `http://127.0.0.1`. Por ello `http_static_server_certified=false`. El gate `policy-safe` carga el **mismo bundle compilado**, proxýa sus llamadas al FastAPI real mediante Playwright y permite ejercer History API y reload literal.

El servidor HTTP local **sí se certifica por separado** con `rc_launcher_http_smoke.py` (6/6): el launcher arranca, health usa la versión canónica, `/` sirve el índice y JS/CSS responden 200 con MIME válidos. Lo que la política impide es que Chromium navegue directamente a ese localhost; esa capa de UI se certifica con el mismo bundle mediante policy-safe.

## Decisión RC

No quedan P0/P1 conocidos en los recorridos certificados. Este checkpoint puede tratarse como **RC candidate jugable**: launcher HTTP 6/6, bundle Chromium 58/58 y personas 18/18. Queda como limitación ambiental, no como P0/P1 conocido, la imposibilidad de unir Chromium gestionado y localhost en una sola navegación por `URLBlocklist`.
