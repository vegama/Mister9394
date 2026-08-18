# Bloque 02 · M4–M8 · Fútbol, partido, jugadores, mercado y economía

Checkpoint objetivo: **0.4.0**.

Este bloque convierte la base de carrera del 0.3.1 en un bucle de mánager mucho más completo. La prioridad no es añadir menús, sino conseguir que las decisiones del usuario alteren lo que ocurre en el campo, en la plantilla y en la caja.

## M4 · Táctica pequeña pero profunda

Las nueve órdenes del plan maestro están validadas y consumidas por el motor: formación, mentalidad, ritmo, presión, tipo de pase, línea defensiva, anchura, marcaje y fuera de juego.

Cada control tiene una contrapartida. Por ejemplo, presión y ritmo altos generan más actividad pero más carga; línea alta y fuera de juego pueden cortar ataques pero aumentan el riesgo de ruptura; anchura abre producción ofensiva y córners a cambio de esfuerzo y espacios; marcaje al hombre aumenta contacto y coste físico. Las formaciones tienen sesgos modestos para que la plantilla siga siendo más importante que un desplegable.

La API expone una identidad táctica legible y la pantalla de Tácticas muestra sus consecuencias. Una táctica puede modificarse también durante un partido y sólo afecta a los minutos posteriores.

## M5 · Partido de texto realmente dirigible

Se añade un `LiveMatchEngine9394` serializable. El partido ya no es una animación de un resultado precalculado: avanza minuto a minuto desde el estado guardado.

Incluye previa en minuto 0, marcador, reloj, narración, posesión, tiros, tiros a puerta, córners, faltas, tarjetas y fueras de juego. El usuario ve condición de los futbolistas, puede hacer sustituciones, cambiar la táctica, detenerse en el descanso y continuar la segunda mitad.

El límite histórico es **dos sustituciones utilizadas**. El estado del directo se guarda dentro de la carrera, por lo que recargar a mitad del encuentro no lo reinicia. El resto de la jornada se resuelve al cerrar el partido y la clasificación sólo se actualiza entonces.

Controles del directo: ritmo x1, x2 y x4, avance hasta la siguiente ocasión/incidencia importante y resultado rápido desde Inicio. El texto es por pasos, por lo que entre pulsaciones el partido está efectivamente pausado.

El postpartido permanece visible con resultado, estadísticas y narración final hasta que el usuario decide cerrarlo.

## M6 · Rendimiento e identidad del futbolista

Los jugadores del club controlado acumulan historial detallado de los partidos de la carrera sin guardar ese volumen para los más de diez mil futbolistas del mundo.

Se registran apariciones, titularidades, minutos, goles, asistencias, amarillas, rojas, valoración media y últimos partidos. Las valoraciones van de 4,0 a 10,0 y reaccionan a resultado, goles, asistencias, portería a cero, tarjetas, lesión y condición de titular/suplente.

Al terminar la temporada, el resumen se archiva y sigue accesible. La ficha mantiene la decisión visual del bloque anterior: foto histórica pequeña arriba a la derecha, inspirada en la densidad de PC Fútbol 7 sin copiar su interfaz ni ampliar las fotos 40×55 como imagen principal.

## M7 · Mercado con tiempo y competencia

El mercado deja de depender de una respuesta instantánea. Ahora existen:

- búsqueda por nombre y posición;
- filtros de agentes libres y lista de seguimiento;
- seguimiento persistente;
- oferta de traspaso, salario y años;
- respuestas que tardan entre uno y tres días;
- contraofertas;
- interés rival que puede encarecer un objetivo;
- negociación de segunda ronda;
- jugadores propios transferibles;
- ofertas generadas por clubes IA según necesidad de posición, tamaño de plantilla y caja;
- ofertas de venta con caducidad y aceptación explícita;
- renovaciones y expiraciones ya integradas en el calendario de carrera.

Las contraofertas y ofertas por jugadores propios aparecen también en la Bandeja del Míster para que el usuario no tenga que vigilar manualmente la pantalla de mercado.

Las cesiones negociables quedan fuera de este checkpoint: la fuente 1993-94 no aporta términos históricos contractuales suficientes y no se inventa todavía una capa de préstamo que pueda romper propiedad, retorno de verano o reglas de inscripción. El estado de contrato ya soporta `loan`, pero sólo se abrirá la negociación de cesiones cuando exista un ciclo de retorno probado.

## M8 · Economía comprensible

Nueva pantalla Economía. Muestra caja, deuda, masa salarial mensual/anual, ingresos comerciales, costes de operación, servicio de deuda, balance mensual proyectado, reserva de seguridad y margen real disponible para traspasos.

El margen de fichajes no equivale a la caja: se descuenta una reserva para que una compra pueda tener consecuencias sin permitir gastar hasta la última peseta de forma absurda.

También se muestran las fichas más altas y el libro reciente de movimientos. Cuando la MDB no contiene un salario o contrato histórico utilizable, la interfaz lo identifica como dato generado por la carrera y no como hecho histórico.

## Persistencia y compatibilidad

El schema de carrera pasa a 6. Los saves anteriores 1–5 siguen admitidos y se completan con los nuevos estados al cargar. Partido en directo, seguimiento, negociaciones, transferibles, ofertas, historial de rendimiento y economía permanecen en el save.

## Gates ejecutados

- Motor + carrera + API + suite M4–M8: **38/38 PASS**.
- Mercado/economía/IA/desarrollo/torneos/competición: **13/13 PASS**.
- Mundo persistente, calendario de temporada, decisiones de cierre, mundo especial e internacional: **15/15 PASS**.
- Total de grupos dirigidos sin solapamiento funcional relevante: **66 pruebas PASS**.
- Smoke manual de **10 partidos consecutivos en directo**: completado; 10 partidos cerrados, jornada y fecha avanzan correctamente, con tácticas alternas y sustitución en descanso.
- `node tools/sfc-structure.mjs`: **PASS**.
- Script `<script setup>` de la aplicación: `node --check` **PASS**.
- Build Vite: **no certificado en este entorno**. La instalación `npm ci` no llegó a materializar dependencias antes del límite/entorno; no se presenta como PASS.

## Criterio de salida de este bloque

El usuario puede preparar un once, definir una táctica, dirigir el partido, intervenir durante el encuentro, revisar el rendimiento individual, negociar fichajes durante varios días, vender futbolistas y comprender cuánto puede gastar y por qué. El siguiente salto del plan maestro es M9–M12: presión del consejo, noticias nacidas del mundo, navegación completa de competiciones y cierre de temporada como momento de juego.
