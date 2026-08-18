# V1.0-G — Certificación de transición de temporada y carrera longitudinal

Fecha de certificación: 18-08-2026.

## Criterio de cierre

G no se considera cerrado porque el número de temporada avance. La transición real del 1 de julio debe mantener durante 3, 10, 20 y 30 temporadas: mundo jugable, XI legales, plantillas operativas, economía acotada, historia persistente, save controlado, jerarquía gradual y un verano comprensible para el usuario.

El soak usa el rollover real, mercado/contratos IA, economía, archivo de temporada, competiciones de fondo, reconstrucción de plantillas y posterior recarga del save. Los horizontes largos son reanudables para que una limitación del runner no convierta una prueba de carrera en una prueba de duración de proceso.

## Resultado con el código final

| Horizonte | Temporada | Clubes | XI IA ilegales | Plantillas min/med/max | Cajas negativas | Caja máxima | Archivo/recaps | Honores | Save | Salud |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 3 | 1996-97 | 444 | 0 | 20 / 22 / 25 | 0 | 737.092.711 | 3 / 3 | 87 | 16,08 MB | healthy |
| 10 | 2003-04 | 444 | 0 | 20 / 22 / 25 | 0 | 1.079.843.915 | 10 / 10 | 290 | 23,41 MB | healthy |
| 20 | 2013-14 | 444 | 0 | 20 / 22 / 25 | 0 | 1.633.819.644 | 20 / 20 | 580 | 29,17 MB | healthy |
| 30 | 2023-24 | 444 | 0 | 20 / 22 / 25 | 0 | 2.121.516.720 | 30 / 30 | 870 | 33,00 MB | healthy |

Los audits tácticos completos construyen los 443 XI de IA en los cuatro horizontes y no encuentran ningún club incapaz de presentar once legal. El audit tarda aproximadamente 1,6–1,9 s por horizonte.

No se generan futbolistas sintéticos: `generated_players` permanece vacío. El manager sigue activo, el feed visible queda limitado a 800 noticias y el historial canónico mantiene exactamente 29 campeones/honores por temporada (25 ligas + 4 torneos).

## Veranos y rendimiento

El coste de una temporada madura completa durante el soak final permanece aproximadamente entre 3,4 y 4,3 s en este entorno. El rollover de julio medido por la telemetría interna queda en torno a 2 s en los años finales, muy por debajo del umbral de aviso de 12 s.

Los dos únicos avisos iniciales son intencionadamente visibles: el primer verano detecta 129/444 plantillas por encima de 25 jugadores heredadas de la base inicial; el segundo detecta un crecimiento de save de 2,6 MB durante la normalización. Desde la tercera transición hasta la trigésima, los diagnósticos son `healthy`.

Tras la normalización las plantillas IA permanecen en 20–25 jugadores, mediana 22. La poda de plantillas sobredimensionadas ocurre mediante retención/expiración y no mediante miles de fichajes de emergencia.

## Persistencia y compactación

Las 12 temporadas más recientes conservan detalle completo. Las antiguas compactan tablas y payloads duplicados, pero retienen campeones, movimientos, trayectoria del manager y hechos canónicos. Los saves pre-G que habían perdido recaps visibles por el antiguo límite de 20 reconstruyen automáticamente esos resúmenes desde `season_archive`.

El crecimiento se desacelera cuando entra la compactación: 23,41 MB en la temporada 10, 29,17 MB en la 20 y 33,00 MB en la 30. Los logs operativos tienen límites explícitos para noticias, contratos IA, traspasos IA, economía y otros históricos de trabajo.

## Jerarquía y economía

La jerarquía cambia de forma gradual: el mayor cambio anual observado en los horizontes certificados es 2,6 puntos. El desplazamiento acumulado máximo aumenta con la carrera (4,9 a 3 años; 13,1 a 10; 19,7 a 20; 24,1 a 30), sin saltos anuales artificiales ni homogeneización completa de categorías.

A 30 años no hay clubes activos con caja negativa y la caja máxima (2.121,5 M ptas.) permanece por debajo del guardarraíl de 2.500 M. No se detecta colapso económico sistémico.

## UX de transición

El 1 de julio genera un `summer_briefing` persistente con: temporada archivada, estado de plantilla, contratos, economía, mercado y pretemporada. Los puntos que requieren intervención aparecen como prioridades y ofrecen destino directo; el resto queda resumido para evitar burocracia y cascadas de pop-ups.

El briefing se muestra tanto en el cierre de temporada como en el dashboard de pretemporada. La historia antigua se compacta internamente, pero no desaparece para el jugador.

## Regresión

Bloques de pruebas verdes durante el cierre:

- manager/rollover: 12/12, ejecutados en lotes por el límite duro del runner;
- snapshot: 8/8;
- economía + IA + mercado + F + G: 19/19;
- torneos + special world + decisiones de temporada + snapshot: 16/16;
- validadores frontend: estructura SFC, calidad UI y sintaxis Vue verdes en la pasada G.

El build completo de frontend no se certifica desde este ZIP porque no contiene `node_modules` y `vite` no está instalado. Esto es una limitación del paquete de trabajo, no un resultado verde de build.

## Reproducción

`backend/tools/v100_g_longitudinal_soak.py` permite ejecutar y reanudar el soak escribiendo un checkpoint JSON después de cada temporada. Para un horizonte canónico, usar `--audit-xi` al final para construir los XI de todos los clubes IA y verificar legalidad real.
