# 0.21 · Studio pass · USA 94 y selecciones funcionales

Esta pasada nace después de cerrar P1–P10. No abre un P11: reúne desarrollo, diseño y datos para mejorar una superficie ya existente, la carrera internacional, y para aumentar la densidad histórica utilizable de 1993-94.

## Criterio de producto

Una selección ya no se considera funcional por acumular nombres. Debe poder construir una convocatoria de 22 con un mínimo de 2 porteros, 5 defensas, 5 centrocampistas y 3 delanteros. El resto de plazas mantiene flexibilidad táctica. Esta definición evita exponer países aparentemente disponibles que luego no pueden producir una convocatoria razonable.

## Datos USA 94

- 24 participantes históricos.
- 22 convocados por selección.
- 528 plazas históricas y 528 identidades runtime únicas.
- 251 identidades se reconcilian con jugadores ya utilizables del snapshot.
- 277 identidades no reconciliables con seguridad se incorporan a la capa utilizable.
- 12 de esas altas tienen una asignación a club jugable 1993-94 verificada.
- 265 altas quedan en 19 contenedores `Otros-País` porque su club real no participa en una competición jugable del universo.
- Los atributos detallados de altas derivadas se marcan como estimados; no se reescriben las valoraciones de jugadores fuente ya existentes.

Las asignaciones a club jugable se contrastan con el club declarado para la convocatoria a 16 de junio de 1994. Entre las correcciones de esta pasada están Dmitri Popov → Racing Santander, John Sheridan → Sheffield Wednesday y Alan Kelly → Sheffield United. La reconciliación es deliberadamente conservadora: se prefiere crear una identidad internacional marcada y trazable antes que fusionar por apellido con un jugador incorrecto. El importador `backend/tools/enrich_world_cup_1994.py` es idempotente y conserva `resolved_source_id` en la capa de convocatoria.

## Mercado y regla de extranjeros

`Otros-País` es un propietario contractual, no una liga paralela. Sus clubes:

- no son seleccionables;
- no se admiten en ligas ni copas;
- no compran jugadores;
- sí pueden vender a clubes activos;
- no convierten a sus futbolistas en agentes libres ni en oportunidades protegidas artificialmente.

El jugador conserva su nacionalidad internacional real. Si un club español, italiano u otro intenta ficharlo, se aplica el límite de extranjeros de la competición congelada en 1993-94 exactamente igual que a cualquier otro fichaje.

## Mundial 1994

El Mundial de 1994 usa los 24 participantes reales, los seis grupos A–F y las 22 identidades históricas de cada selección. Los resultados siguen perteneciendo a la simulación: el juego reconstruye el punto de partida, no fuerza el desenlace histórico. Las ediciones futuras usan el universo alternativo de la carrera.

## Usabilidad

La pantalla Selecciones incorpora dos alcances: `USA 94` y `Todas funcionales`. La ficha de una selección clasificada muestra grupo, completitud 22/22 y seleccionador histórico. La convocatoria tiene dos vistas separadas:

- `Convocatoria actual`: los 22 de la carrera, incluyendo exactamente los guardados por el usuario cuando es seleccionador.
- `USA 94 · 22 históricos`: referencia inmutable del torneo, que no modifica la convocatoria actual.

La ficha de jugador muestra el sello USA 94 y dorsal cuando corresponde.

## Cobertura tras la pasada

Con la definición estricta hay 39 selecciones funcionales. Las 24 participantes de USA 94 están completas. Países con masa de datos cercana pero aún insuficiente no se promocionan artificialmente como funcionales: se convierten en candidatos de futuras pasadas de datos.

## Fuentes y trazabilidad

La identidad/posición/dorsal de las convocatorias se basa en Fjelstul World Cup Database (CC BY-SA 4.0). Clubes y contexto de convocatoria se contrastan con la relación de squads de 1994. Véase `CREDITS_SOURCES.md`.

## Gates de cierre

- USA 94 / mercado / extranjería: 10/10 PASS.
- Regresión focal internacional, mercado, API y P5–P10: 49/49 PASS.
- Catálogo fuente y coaching: 12/12 PASS.
- Importador: idempotencia SHA-256 confirmada sobre snapshot, convocatorias y reporte.
- Frontend: SFC PASS, contrato UI/legibilidad PASS, sintaxis Vue 23/23.
- `vite build`: no certificado en este entorno porque falta el binario `vite`; el propio comando ejecuta antes los tres gates frontend y esos sí pasan.
