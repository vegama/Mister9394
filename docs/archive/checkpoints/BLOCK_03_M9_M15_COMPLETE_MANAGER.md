# Míster 93/94 — Cierre M9–M15

Checkpoint objetivo: **0.5.0**.

Este bloque cierra el plan maestro de producto desde la presión del consejo hasta el gate longitudinal de diez temporadas. El criterio no es acumular pantallas, sino que una carrera iniciada en 1993-94 siga siendo comprensible, ágil y futbolísticamente coherente cuando el mundo ya ha cambiado varios años después.

## M9 · Consejo, objetivos y riesgo

- Expectativas derivadas de fuerza deportiva y estatus del club.
- Confianza explicable por posición, forma y salud económica.
- Inercia: un mal resultado aislado no provoca un despido.
- Dos revisiones críticas consecutivas, y suficiente temporada disputada, son necesarias antes de una destitución.
- La Bandeja del Míster muestra el motivo principal cuando el puesto entra en riesgo.

## M10 · Noticias causales

- Las noticias nacen de hechos persistidos: resultados, mercado, títulos, rollover, consejo y mundo.
- Dedupe por evento causal: navegar o recargar no vuelve a publicar una noticia.
- Hemeroteca compacta con retención de 800 entradas y contador monotónico independiente.
- Las noticias enlazan entidades del juego en lugar de usar texto de relleno.

## M11 · Competiciones navegables

- Directorio único para ligas y torneos activos del mundo.
- Clasificación, resultados, calendario, participantes, formato, reglas y palmarés según proceda.
- Las competiciones especiales se abren desde la misma superficie que las ligas regulares.
- Los clubes necesarios para historia/continental permanecen en el universo aunque no sean seleccionables al crear carrera.

## M12 · Cierre, verano y pretemporada

- Recap persistente de cada temporada controlada.
- Palmarés, clasificación, movimientos de categoría y plazas continentales archivados.
- El 1 de julio abre la nueva temporada sin borrar la anterior.
- Pretemporada real como fase de calendario, con cuatro amistosos generados para el club controlado.
- En pretemporada `Continuar` avanza en pulsos cortos de hasta tres días; durante la competición el flujo busca el siguiente partido o incidencia relevante.
- Las reglas de inscripción son de época: se distingue entre datos históricos explícitos y fechas normalizadas de simulación cuando la MDB no aporta precisión suficiente.

## M13 · IA de clubes y realismo estructural

### Puestos especializados

El modelo ya no reduce una plantilla a POR/DEF/MED/DEL. Conserva los puestos históricos de la fuente y los traduce a trabajos compatibles de plantilla: portero, lateral derecho, lateral izquierdo, central, mediocentro, centrocampista/interior, mediapunta, bandas y delantero, incluyendo lateralidad y compatibilidades.

La IA compra, renueva y protege jugadores por necesidades reales de puesto. Un club no puede vender a su único portero ni desprenderse de una pieza si la salida rompe una cobertura estructural mínima.

### Plantilla mínima frente a once legal

Son dos conceptos distintos:

- **18 futbolistas sénior**: suelo operativo de plantilla.
- **20–24 futbolistas**: objetivo dinámico de profundidad según estatus del club; 22 es la referencia general.
- **11 futbolistas**: únicamente el número necesario para formar un once.

Tener 18 jugadores no garantiza poder jugar: después se valida por separado que exista un XI compatible con puestos y reglas de extranjeros.

La reparación de verano trabaja en dos pasadas: primero asegura necesidades duras de todos los clubes y después permite que clubes financieramente sanos consuman agentes libres para profundidad. Esto evita que los clubes ricos agoten el mercado antes de que los demás alcancen su suelo operativo.

### Reglas de extranjeros

- Cada partido consulta la regla de su propia competición.
- Los valores `Ex11` y `ExPlantilla` de la MDB son la fuente principal.
- Usuario e IA usan la misma validación.
- El mercado comprueba la posibilidad de inscripción antes de cerrar un fichaje.
- La APSL tiene tratamiento transfronterizo EE. UU./Canadá y no hereda ciegamente una regla europea genérica.
- En competición continental la nacionalidad se evalúa con el contexto continental de esa competición.

### Emergencias reales

Una lesión nunca autoriza a saltarse el cupo de extranjeros. Si una IA tiene una plantilla sénior válida pero todas las combinaciones sanas son imposibles, puede arriesgar excepcionalmente a un jugador real lesionado de su plantilla con una penalización severa. Si todos los porteros naturales están lesionados, un futbolista real de campo puede actuar como portero de emergencia con atributos fuertemente penalizados. No se inventan jugadores para tapar el problema.

### Renovaciones

La cola mensual se construye sólo con clubes activos. Todos reciben turno; los IDs bajos ya no pueden consumir un límite global antes de que llegue un club de ID alto. Las renovaciones protegen primero puestos estructurales y después valor deportivo.

## Jerarquía dinámica de clubes

Grande, medio o pequeño no es una etiqueta permanente. El estatus parte del contexto histórico y evoluciona según:

- resultados relativos a la competición que se disputa;
- títulos;
- presencia europea;
- fuerza de plantilla;
- economía;
- reputación histórica como inercia.

El prestigio es relativo: el sistema centra el movimiento global para evitar inflación de reputación y pondera el éxito por nivel/prestigio de la liga. Un título de una categoría inferior importa, pero no equivale a ganar una gran primera división. El cambio anual está limitado y los extremos tienen rendimientos decrecientes, de modo que un pequeño necesita años de éxito para convertirse en grande y un gigante puede decaer sin desaparecer por una mala temporada.

## Economía longitudinal

Los campos económicos históricos tienen escalas heterogéneas por país. Por ello los ingresos ordinarios y de partido usan curvas comprimidas en vez de multiplicar linealmente socios/presupuesto. Se conserva la ventaja estructural de un club grande, evitando que esa ventaja se convierta en miles de millones nuevos cada temporada.

La insolvencia reduce calidad y profundidad de plantilla, pero no puede impedir que un club reconstruya el mínimo operativo con agentes libres.

## M14 · Ritmo y UX

- Continuar es contextual.
- Pretemporada: pulsos cortos para dar tiempo a mercado, contratos, amistosos y decisiones.
- Temporada oficial: avance hacia partido o acontecimiento que requiera al usuario.
- Las lesiones del XI no se corrigen silenciosamente: aparecen como decisión de alineación; el generador de mejor XI permite resolverla en una acción.
- Consejo, mercado, competición, noticias, economía e historia comparten el estado de la misma carrera y no recalculan hechos al navegar.

## M15 · Gates de producto

El bloque deja tests permanentes para:

- puestos especializados;
- cupos de extranjeros y construcción de XI legal;
- APSL EE. UU./Canadá;
- periodos de inscripción de época;
- pretemporada y ritmo corto;
- 18 como mínimo de plantilla y no como XI;
- objetivo dinámico de 20–24 jugadores;
- reparación de verano incluso con insolvencia;
- protección del único portero;
- equidad de la cola de renovaciones;
- economía con extremos comprimidos;
- jerarquía de clubes gradual pero mutable;
- tres temporadas consecutivas;
- diez temporadas 1993-94 → 2003-04.

El gate longitudinal no se limita a comprobar que el calendario llega al final. Cada verano exige para todos los clubes activos:

1. al menos 18 jugadores sénior;
2. al menos un portero natural en plantilla;
3. un XI de 11 futbolistas legal por puestos y cupo de extranjeros;
4. siguiente partido disponible;
5. historia y noticias persistentes.

Al final de diez temporadas también aplica guardarraíles de balance: la mediana de plantilla debe quedar por encima del suelo, menos del 20 % del mundo puede terminar con caja negativa, no se permiten acumulaciones económicas explosivas y la reputación debe mostrar movilidad real sin teletransportar un club varias categorías de estatus en una sola década.

### Resultado del gate longitudinal de balance

En el seed de producto usado para el gate 1993-94 → 2003-04, con persistencia/reconstrucción a mitad de carrera:

- 374 clubes activos;
- plantilla mínima observada: 18; mediana: 22; máximo: 25;
- 0 clubes sin portero natural en plantilla;
- 27/374 clubes con caja negativa (~7,2 %);
- caja máxima observada: ~1.096 millones de ptas.;
- 24 gigantes en la jerarquía inicial y 35 tras diez temporadas;
- 15 clubes con desplazamientos de al menos 8 puntos de estatus;
- desplazamiento máximo en diez años: 11,3 puntos.

Esto permite movilidad real sin inflación masiva de prestigio: un club puede crecer o entrar en decadencia, pero los éxitos de categorías inferiores se ponderan por nivel y prestigio de competición y no equivalen automáticamente a triunfos en una gran primera división.

## Resultado del bloque

Con M9–M15 el plan maestro está implementado de M0 a M15. El siguiente trabajo ya no debe abrir una “M16” de sistemas grandes: debe ser **jugar, observar, calibrar y pulir** el mismo juego, corrigiendo cualquier punto que reduzca diversión, claridad, velocidad o credibilidad histórica.

## Resultado observado del stress gate de diez años

Con seed determinista `159394`, cierre sintético controlado y el código de este checkpoint:

- 10 temporadas archivadas: 1993-94 → 2003-04;
- 250 campeonatos/palmarés persistidos en el stress world gate;
- 373 clubes IA auditados en el último verano;
- tamaño de plantilla IA final: mínimo 18, mediana 22, máximo 24;
- ningún club auditado por debajo del suelo y ninguno sin portero natural;
- 27 de 374 clubes del mundo activo terminan con caja negativa (≈7,2 %), muy por debajo del guardarraíl del 20 %;
- mayor caja observada: ≈1.096 millones de pesetas, sin la explosión multibillonaria del modelo lineal anterior;
- 84 de 374 clubes cambian de banda de estatus durante la década;
- máximo desplazamiento absoluto de estatus observado: 11,3 puntos;
- gigantes: 24 al inicio y 35 al final del stress gate, mostrando movilidad sin inflación masiva;
- la hemeroteca conserva 800 noticias visibles mientras el contador causal supera las 12.000, confirmando que la retención no duplica IDs.

Estas cifras son un **stress test de estabilidad y balance**, no una predicción histórica: el gate fuerza resultados sintéticos para recorrer diez rollovers con rapidez.

## Playtest técnico por perfiles

Se deja también un gate permanente con cuatro carreras distintas: favorito (FC Barcelona), club fuerte/medio (Real Sociedad), modesto de Primera (UE Lleida) y club de categoría inferior (Deportivo Alavés). Cada carrera disputa diez partidos. Cuando una lesión invalida el XI, el test reproduce la decisión que ve el usuario y usa la acción de mejor XI antes de continuar. El objetivo es comprobar que los perfiles no dependen de un único club o liga y que las incidencias de alineación forman parte del juego en vez de convertirse en fallos técnicos.
