# Míster 93/94 — Plan de cierre funcional, UX y dirección visual

> **Prioridad de cierre v1.0.0:** este documento conserva el detalle del cierre funcional/visual previo. El orden de trabajo y los gates de release vigentes se gobiernan desde `docs/V100_STUDIO_RELEASE_PLAN.md`. Los assets continúan en paralelo con presupuesto limitado; no desplazan jugabilidad, UX, continuidad ni robustez.

## Objetivo de producto
Cerrar una versión funcional completa que sea atractiva, cómoda y muy fácil de entender sin reducir la profundidad de manager. Cada pantalla debe responder de inmediato a tres preguntas: **qué estoy viendo, qué importa ahora y qué puedo hacer**.

La interfaz no debe parecer una hoja de administración. La densidad de datos se mantiene, pero con jerarquía visual, contexto, fotos históricas, estados claros y acciones naturales.

## Estado de ejecución de esta pasada
- **P0 — muy avanzado:** ficha de jugador compactada, foto visible también en resoluciones pequeñas, retratos de club corregidos y selector de XI campo→sustituto integrado. Queda la ronda visual real a 1080p cuando el entorno pueda ejecutar Vite.
- **P1 — sistema aplicado:** Inicio, Club, ficha de jugador, Plantilla, selección de carrera y controles tácticos comparten ya la paleta grafito/azul tinta + superficies cálidas + cobalto para acción primaria. El verde queda reservado al césped y estados positivos; el dorado, a historia/decisiones especiales. Falta validación visual real a 1080p y ajustes finos.
- **P2 — implementado y cubierto por API:** previa con los dos onces verticales y fotos/fallback, más botones **Comenzar partido** y **Resultado**. Resultado termina y compromete el partido mediante el mismo motor vivo.
- **P3 — avanzado y probado:** el motor de Resultado usa sustituciones para ambos banquillos con contexto de marcador, fatiga y compatibilidad posicional; evita cambios absurdos de portero y conserva el máximo histórico de dos. La valoración 0–10 se calcula con una función compartida. Falta afinar la riqueza posicional de la nota.
- **P4 — implementado y cubierto por tests:** contadores archivados exclusivamente de liga, nota media liguera persistente y premios de liga calculados sobre todos los equipos con la misma escala, incluido XI de la temporada. La trayectoria del jugador muestra PJ, titularidades, minutos, goles, asistencias, tarjetas y media.
- **P5 — implementado en versión funcional:** fin de temporada muestra balance, premios, XI de la temporada con fotos y entrenador campeón; **Campeones** conserva una foto fija histórica del entrenador y plantilla ganadora para que fichajes posteriores no reescriban el pasado.
- **P6 — verificado como regla global de juego:** todas las ligas runtime de Míster 93/94 usan 2/1/0. Las evidencias históricas que documenten otro sistema permanecen sólo en los ficheros de auditoría y no alteran la puntuación de la partida.
- **P7 — activo en paralelo:** la matriz viva está en `data/football9394/assets_coverage_ux_closure.json`. Estado actual: **480/504 clubes reales con escudo**, **443/504 estadios con foto**, **388/426 entrenadores con retrato** y **10.195 fotos de jugadores** en runtime. Quedan 24 escudos, 61 estadios y 38 entrenadores; además 205 jugadores con referencia BDFutbol preparada siguen pendientes de materialización/reintento. Los agregados `Otros-País` quedan fuera del gate de escudos.
- **P8 — regresión parcial verde:** 28/28 SFC pasan estructura, calidad UI y sintaxis; los tests dirigidos de Resultado/API, estadísticas ligueras, cierre de temporada y reglas 2/1/0 están verdes. Falta el recorrido visual completo en navegador y la simulación longitudinal final. El bundle Vite no puede ejecutarse en este entorno porque no está instalado el binario/dependencias de Vite.

## Principios no negociables
1. Una acción importante debe ser localizable sin ensayo/error y resolverse en el mínimo número razonable de clics.
2. La pantalla debe tener una acción primaria evidente; las secundarias no compiten visualmente con ella.
3. Los datos históricos, fotos, escudos y estadios refuerzan orientación e inmersión, no son decoración opcional.
4. Nunca recortar rostros de forma agresiva. Retratos y tarjetas deben priorizar cabeza/cara y disponer de fallback digno.
5. Cabeceras compactas: identidad + contexto + 2–4 datos clave. El contenido útil debe entrar antes en pantalla.
6. El color sirve para jerarquía y estado, no para llenar superficies. Verde = fútbol/éxito; rojo = riesgo/error; ámbar = advertencia; azul/cobalto = navegación/acción primaria.
7. El juego debe conservar un carácter propio de 1993-94, pero con legibilidad y ergonomía modernas; no clonar Football Manager.
8. Estados vacíos, errores y procesos siempre explican qué ocurre y cuál es la siguiente acción.
9. Toda pantalla crítica debe funcionar bien a 1080p sin depender de scroll excesivo.
10. Las estadísticas de temporada de jugador mostradas/archivadas son exclusivamente de **liga**.

---

## P0 — Correcciones visuales y de uso que bloquean la experiencia

### Ficha de jugador
- Reducir la cabecera hero aproximadamente un 30–40 %.
- Foto siempre visible en escritorio/tablet y no eliminada en móvil; adaptar tamaño en vez de ocultarla.
- Foto con encuadre de retrato, `object-position` orientado al rostro y fallback integrado.
- Escudo más pequeño que la foto: el jugador es el protagonista.
- Nombre, posición, dorsal, nacionalidad, estado y nivel deben leerse en un primer vistazo.
- La tira de métricas no debe competir con el nombre ni ocupar una segunda cabecera completa.
- Tabs visibles y estables; no más de 6–7 secciones principales.

**Gate:** al abrir cualquier jugador, foto + nombre + posición + estado + nivel aparecen completos sin scroll y sin grandes zonas decorativas vacías.

### Club y tarjetas de jugadores
- Sustituir cajas de imagen demasiado bajas por ratios de retrato consistentes.
- Prohibir recortes que corten frente/barbilla; usar posición focal alta y fallback común.
- Plantilla destacada con 3–5 jugadores importantes, no mosaicos de miniaturas cortadas.
- Identidad de club: escudo, estadio, competición, posición y próximos hitos; sin hero sobredimensionado.

**Gate:** ningún rostro se percibe “cortado” en tarjetas de plantilla, inicio o club.

### Selección de alineación
Rehacer la elección del XI como una tarea futbolística, no como una columna de botones `+ / ✓`.

Flujo propuesto:
1. Campo táctico grande como superficie principal.
2. Lista/banquillo al lado o debajo con retrato, posición, media, forma, condición y estado.
3. Clic en un jugador libre → resalta posiciones compatibles/vacantes.
4. Clic en una posición del campo → coloca al jugador.
5. Clic en un jugador del campo → permite sustituirlo o devolverlo al banquillo.
6. Drag & drop opcional en escritorio, nunca obligatorio.
7. “Mejor once disponible” sigue existiendo como atajo.
8. Avisos de legalidad aparecen cerca del campo, explicando exactamente qué hay que corregir.
9. Guardar sólo es acción principal cuando el XI está legal.

**Gate:** un usuario nuevo puede formar y guardar un XI sin conocer la interfaz previamente y sin usar una columna de `+ / ✓`.

---

## P1 — Nueva dirección visual completa

### Paleta
- Base: grafito/azul tinta para navegación y cabeceras estructurales.
- Superficies: blanco roto/gris cálido, no blanco puro repetido en todas partes.
- Acción primaria: cobalto profundo.
- Verde de césped reservado a fútbol, disponibilidad y éxito.
- Ámbar para atención; rojo para error/lesión/sanción.
- Colores del club como acento contextual en perfiles, previa y club, sin romper contraste.

### Tipografía y jerarquía
- Títulos de pantalla 24–28 px, paneles 15–18 px, cuerpo 12–14 px.
- Menos mayúsculas sostenidas y menos microtexto de 10–11 px.
- Datos clave con números grandes sólo cuando realmente son KPI.
- Etiquetas cortas; explicación secundaria en texto suave.

### Componentes
- Sistema único para cards, chips de estado, botones, tabs, tablas, modales y banners.
- Botón primario único por bloque de decisión.
- Acciones destructivas separadas visualmente.
- Hover/focus/disabled coherentes.
- Tablas con primera columna de identidad más rica y columnas secundarias progresivamente menos prominentes.

**Gate:** las principales pantallas parecen pertenecer al mismo producto, sin mezcla de estilos “dashboard”, “tabla”, “hero” y “modal” incompatibles.

---

## P2 — Día de partido y previa

### Previa con los dos onces
Antes de cada partido debe existir una pantalla de previa dedicada:
- Cabecera compacta con competición, jornada/ronda, estadio y fecha.
- Local a la izquierda y visitante a la derecha.
- **Dos onces completos en vertical**, uno por equipo.
- Cada jugador con foto, dorsal, nombre y posición.
- Lesionados/sancionados relevantes en una franja secundaria.
- Árbitro y estadio visibles cuando existan datos.
- Botones principales: **Jugar partido** y **Resultado**.

### Botón Resultado
- “Resultado” simula el encuentro completo sin entrar al directo.
- Debe usar el mismo motor y reglas del partido normal.
- La IA realiza sustituciones realistas atendiendo a minuto, marcador, cansancio, lesión, posición y contexto táctico.
- Tras simular, ir directamente a postpartido con marcador, eventos, cambios y notas.

**Gate:** simular por Resultado y jugar hasta el final producen el mismo tipo de resultado persistente y las mismas consecuencias de carrera.

---

## P3 — Partido, sustituciones y postpartido

### Sustituciones IA realistas
- Ventanas normales de cambios por fatiga/rendimiento alrededor de 55'–80'.
- Cambios tempranos por lesión o expulsión.
- Con ventaja: más control/defensa y gestión física.
- En desventaja: más riesgo y perfiles ofensivos.
- Evitar cambios absurdos de portero salvo lesión/expulsión o contexto excepcional.
- Respetar límite histórico de sustituciones y posiciones compatibles.

### Nota individual 0–10
Calcular una nota para cada participante en cada partido a partir de:
- resultado/contexto;
- goles y asistencias;
- producción observable por posición;
- portería a cero para portero/defensas;
- errores que provocan goles, tarjetas/expulsión;
- participación, minutos y condición;
- impacto relativo a la posición.

La nota de partido existe en todas las competiciones, pero el **promedio histórico de temporada mostrado en la ficha se calcula sólo con partidos de liga**.

---

## P4 — Estadísticas históricas de jugador y premios

### Registro de temporada
En la ficha del jugador, el registro archivado por temporada debe ser exclusivamente liguero:
- PJ de liga.
- Titularidades de liga.
- Minutos de liga.
- Goles de liga.
- Asistencias de liga.
- Amarillas/rojas de liga.
- Nota media 0–10 de liga.

Ejemplo obligatorio: 25 partidos de liga + 5 de Champions = **25 PJ** en el histórico de esa temporada.

Copas/Europa/selección pueden tener vistas separadas de competición o historial de partidos, pero no contaminan la línea estadística principal de liga.

### Premios
Al final de temporada:
- Jugador del año de cada liga.
- Máximo goleador.
- Mejor portero cuando haya datos suficientes.
- Once de la temporada por posiciones.
- Mejor joven sólo si la definición histórica/funcional está bien establecida.
- Premios del club: jugador de la temporada y máximo goleador.

Premios basados en rendimiento real simulado, con umbral mínimo de partidos/minutos para evitar ganadores absurdos.

---

## P5 — Cierre de temporada

### Pantalla de fin de temporada
Debe aparecer como hito, no quedar enterrada en Historial:
- Resultado liguero y evolución respecto al objetivo.
- Campeón de liga y campeones de copas/Europa relevantes.
- Ascensos/descensos.
- Clasificados a competiciones europeas.
- Premios individuales.
- Mejores jugadores del club con foto y nota media.
- Máximo goleador con foto.
- Récords alcanzados.
- Balance del consejo y economía resumida.
- CTA claro para “Preparar nueva temporada”.

### Pantallas de campeones
Cuando se decide una competición importante:
- pantalla de campeón con escudo, nombre, trofeo/competición, rival/final cuando proceda;
- once o protagonistas destacados con fotos;
- enlace al cuadro/clasificación y al palmarés;
- persistencia en Historial.

**Gate:** ganar una competición o terminar una temporada se siente como un acontecimiento reconocible y queda registrado.

---

## P6 — Reglas y consistencia histórica

- Regla global de liga del proyecto: **2 puntos por victoria, 1 por empate, 0 por derrota**.
- Ningún formato moderno se aplica por defecto a 1993-94.
- Las reglas especiales deben estar declaradas en datos/código y cubiertas por test.

---

## P7 — Assets históricos

### Cobertura
Mantener una matriz por equipo/persona:
- escudo;
- foto de estadio;
- foto de jugador;
- foto de entrenador/mánager;
- fuente y confianza;
- estado `available / verified_missing / pending / fallback`.

### Prioridad de descarga
1. Club del usuario y próximo rival.
2. Todos los equipos de ligas jugables.
3. Jugadores de las plantillas jugables 1993-94.
4. Entrenadores/mánagers de esas plantillas.
5. Estadios de esas ligas.
6. Pool europeo/internacional.

### UX de fallback
- Jugador sin foto: camiseta/identidad visual del equipo, nunca hueco roto.
- Entrenador sin foto: avatar sobrio con iniciales.
- Club sin escudo: monograma consistente.
- Estadio sin foto: superficie neutra identificada como “imagen no disponible”; nunca una foto inventada.

### Fuentes
Priorizar fuentes históricas verificables y conservar atribución/procedencia. BDFutbol ofrece páginas de plantillas 1993-94, personas y clubes/estadios útiles para continuar la cobertura; cualquier segunda fuente se usa para contraste o huecos, no para sobrescribir identidades ya verificadas sin evidencia.

---

## P8 — Recorrido UX destructivo antes de etiquetar la versión

Recorridos mínimos:
- Inicio → Plantilla → XI → Táctica → Previa → Jugar → Postpartido.
- Inicio → Previa → Resultado → Postpartido.
- Ficha de jugador desde Plantilla, Mercado, Club, Noticias y previa.
- Club → jugadores → ficha → volver conservando posición/contexto.
- Fin de temporada → campeones/premios → nueva temporada.
- Back/Forward/F5 en pantallas críticas.
- 1080p, portátil estrecho y móvil/tablet para modales.
- Sin fotos, sin escudos o sin estadio.
- XI incompleto, lesionado, sancionado, límite de extranjeros.
- Simulación de varias temporadas para comprobar archivos de liga y medias 0–10.

---

## Orden de ejecución recomendado
1. P0 fotos/cabeceras + selección de XI.
2. P1 sistema visual completo.
3. P4 estadísticas ligueras + nota 0–10 (porque alimentan muchas pantallas).
4. P2 previa + botón Resultado.
5. P3 sustituciones IA/postpartido.
6. P5 campeones + fin de temporada + premios.
7. P7 assets en paralelo durante todos los bloques.
8. P8 ronda destructiva y cierre de versión.

## Definition of Done de la versión funcional
La versión se considera cerrada cuando un usuario puede iniciar carrera, entender el estado del club, gestionar plantilla y XI, preparar un partido, ver ambos onces con fotos, jugar o simular por Resultado, recibir cambios IA razonables, consultar postpartido, avanzar una temporada completa con 2/1/0 donde corresponda, recibir campeones/premios/fin de temporada, y revisar en cada jugador un histórico liguero correcto con nota media 0–10; todo ello con fotos/escudos/estadios razonablemente cubiertos y fallbacks sin roturas visuales.
