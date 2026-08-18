# V0.47 · NF0 — staff y responsabilidades: primera vertical funcional

Checkpoint: **0.47.0-nf0-staff-responsibilities-base**

Esta pasada abre el plan `FM_REFERENCE_FUNCTIONAL_PLAN.md` y comienza por NF0, la arquitectura humana del club.

## Implementado

- Nuevo estado persistente `club_staff` separado por club.
- Generación determinista de empleados cuando no existe una identidad histórica utilizable.
- Proveniencia explícita `generated_career_staff`: un empleado inventado por la carrera nunca se presenta como trabajador histórico real de 1993-94.
- Estructura escalada según dimensión del club y pistas de fuente disponibles (incluido el nivel de secretario técnico cuando existe).
- Roles base: segundo entrenador, entrenador de primer equipo, entrenador de porteros según estructura, fisioterapeuta, ojeador, jefe de ojeadores según estructura y secretario técnico según estructura/fuente.
- Competencias 1–20 por área: entrenamiento, táctica, disciplina, capacidad/potencial, conocimiento de mercado, negociación, fisioterapia, jóvenes y porteros.
- Matriz persistente de nueve responsabilidades: once/táctica, entrenamiento, preparación de partido, informes del rival, búsqueda de fichajes, negociación de traspasos, renovaciones, valoración médica y seguimiento de jóvenes.
- El usuario puede asumir directamente cualquier responsabilidad o delegarla sólo en empleados elegibles.
- Carga visible por empleado y calidad estimada por responsabilidad. NF0 todavía no aplica penalizaciones ocultas a resultados: las fases siguientes consumirán explícitamente esta competencia.
- Cambio de club conserva el staff del club anterior y materializa una estructura diferente para el nuevo club.
- Snapshot de carrera, GET específico y PUT de delegación conectados al guardado.
- Nueva superficie `Cuerpo técnico` en la navegación principal, con empleados, competencias, carga, proveniencia y reasignación inmediata.

## Gate ejecutado

Pruebas NF0 dedicadas: **5/5 PASS**.

Regresión API `test_football9394_webapp.py`: **16/16 PASS**, incluido el caso NF0 de delegación/persistencia/validación.

Frontend:

- `check:sfc`: PASS
- `check:ui`: PASS
- `check:vue`: PASS (24/24 SFC)

La suite completa del repositorio no se declara recertificada en esta pasada. Una ejecución combinada de regresión amplia superó la ventana de 30 s sin devolver fallo antes del corte. La regresión API completa sí se ejecutó después: 16/16 PASS. Además, los dos casos de movilidad de mánager directamente afectados por el nuevo staff por club pasaron 2/2.

## Pendiente de NF0 antes de darlo por cerrado

Esta es la infraestructura y la primera vertical de producto, no el cierre NF0. Queda hacer que las responsabilidades produzcan consecuencias en sistemas reales y completar la vida laboral del staff:

- contratación, salida y sustitución de empleados;
- coste salarial y límites/tamaño de estructura cuando el consejo lo aplique;
- consumo de competencia/carga por entrenamiento, scouting, médico y mercado;
- mensajes e informes emitidos por la persona responsable;
- continuidad de empleados y cambios de rol a largo plazo;
- gate de carrera controlador vs carrera altamente delegada.

El siguiente desarrollo recomendado dentro de NF0 es conectar **responsable → información/resultado** en los sistemas ya existentes, empezando por informes del rival, valoración médica y negociación, porque permiten comprobar que delegar cambia realmente cómo llega la información sin añadir burocracia.
