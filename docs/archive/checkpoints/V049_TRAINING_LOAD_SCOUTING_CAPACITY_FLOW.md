# Míster 93/94 — 0.49.0 · entrenamiento, carga, scouting y flujo de plantilla

Fecha: 17/08/2026  
Checkpoint: **0.49.0-training-load-scouting-capacity-flow**

## Objetivo de la pasada

Profundizar varias piezas a la vez sin añadir superficies aisladas. Esta entrega conecta **NF1 Scouting**, **NF2 Planificación de plantilla** y **NF3 Entrenamiento/médico** con la arquitectura de responsabilidades NF0, de forma que las decisiones del usuario y la calidad/carga del staff alteren información y riesgo reales de la carrera.

## 1. Entrenamiento semanal jugable

Se añade un estado persistente de entrenamiento por club con:

- plan de siete días;
- sesiones compactas: recuperación, físico, táctica, ataque, defensa, balón parado, preparación de partido y descanso;
- intensidad baja, normal o alta;
- foco individual por futbolista;
- responsable real de `first_team_training` y su eficacia operativa;
- historial de sesiones procesadas.

No se pretende reproducir una agenda moderna de micro-sesiones. El objetivo es que el usuario controle las decisiones que importan y que la experiencia siga siendo compatible con un club de 1993-94.

## 2. Cadena carga → condición → lesión → partido

El entrenamiento ya no es decorativo. Cada día puede modificar:

- `training_load`;
- fatiga acumulada;
- condición;
- riesgo estimado de lesión;
- evidencia lenta de mejora en atributos coherentes con el foco individual.

Los minutos de partido también generan carga y fatiga, mientras que los días posteriores permiten recuperación progresiva. La capa que materializa al futbolista para el motor aplica penalizaciones físicas temporales cuando la condición/fatiga lo justifican y puede elevar moderadamente su propensión efectiva a lesionarse.

El área médica consume exactamente ese mismo estado. Por tanto, un jugador cargado puede aparecer como apto pero con una recomendación de dosificación o con advertencia de riesgo, en lugar de existir dos verdades independientes entre entrenamiento y medicina.

### Incidencia encontrada y corregida

La regresión detectó un caso real de integración: una lesión sufrida durante el entrenamiento podía dejar al lesionado dentro de la convocatoria guardada y bloquear el siguiente partido. La carrera ahora repara automáticamente una convocatoria que haya quedado ilegal por esa baja y genera una nota explicativa. Si la plantilla no permite formar once, el usuario recibe el problema en vez de un crash opaco.

## 3. Scouting con capacidad real

Los informes ya no pueden encargarse sin límite. La capacidad simultánea depende de:

- número de ojeadores/jefe de ojeadores activos;
- estructura del club;
- conocimiento de mercado del jefe de ojeadores;
- si el usuario asume personalmente la responsabilidad de reclutamiento.

La interfaz muestra `ocupados / capacidad / disponibles` y bloquea encargos adicionales cuando no queda capacidad.

## 4. Geografía y tiempo de desplazamiento

El encargo distingue, de forma deliberadamente compacta:

- mercado doméstico;
- desplazamiento europeo;
- seguimiento de larga distancia.

La geografía añade días al informe. No intenta fingir una base de datos global moderna: la información tarda porque alguien tiene que conseguirla u observar al futbolista.

## 5. Informes que envejecen

Cada conocimiento tiene fecha. Al consultar un jugador meses después:

- baja la confianza efectiva;
- aparece un estado de frescura (`Actual`, `Envejeciendo`, `Desactualizado`, `Antiguo`);
- después de periodos largos puede caer el nivel efectivo de conocimiento;
- el usuario conserva el hecho de haber observado al jugador, pero no una precisión eterna.

La calidad del informe que termina queda vinculada a la calidad del responsable en el momento de iniciar el trabajo. Cambiar de ojeador a mitad del encargo no reescribe mágicamente el pasado.

## 6. Planificador → mercado

Las prioridades de plantilla incluyen ahora la demarcación de mercado equivalente. Desde el planificador el usuario puede abrir directamente el mercado filtrado por la necesidad seleccionada.

El flujo visible queda más cerca del objetivo rector:

`problema de plantilla → búsqueda → capacidad de scouting → informe → decisión de mercado`

La IA y el usuario siguen compartiendo la misma lectura base de cobertura, evitando dos lógicas contradictorias de plantilla.

## 7. Interfaz

Nueva superficie **Entrenamiento** con:

- sesión del día;
- intensidad;
- plan semanal editable;
- condición/carga/riesgo agregados;
- lista de jugadores a vigilar;
- tabla individual con foco de entrenamiento.

Mercado muestra ahora capacidad de scouting, alcance/desplazamiento, informes envejecidos y acceso directo desde prioridades del plan de plantilla.

## Validación

Pruebas ejecutadas y verdes en esta pasada:

- lote v0.49 + v0.48 + NF0 + desarrollo + motor + mercado: **28/28**;
- profundidad histórica F1–F8: **14/14**;
- gameplay M4–M8: **9/9**;
- M9–M14 y regresiones IA/noticias/economía seleccionadas: **10/10**;
- gate M15 de cuatro perfiles / diez partidos: **1/1**;
- web API + movilidad de mánager: **23/23**.

Total de pruebas ejecutadas en los grupos anteriores: **85/85 PASS**.

El gate `test_m15_three_season_product_gate_preserves_history_world_and_playability` **no se recertifica** en esta ejecución: supera la ventana de 180 segundos antes de producir un resultado. No se interpreta el timeout como PASS ni como fallo funcional.

Frontend:

- `check:sfc`: **PASS**;
- `check:ui`: **PASS**;
- `check:vue`: **PASS 25/25 SFC**.

`vite build` permanece sin certificar porque este checkpoint no trae `frontend/node_modules/.bin/vite` materializado.

## Estado NF0–NF3 tras 0.49

- **NF0** sigue activo: la infraestructura y efectos de responsabilidad existen; falta seguir extendiendo consecuencias a más decisiones.
- **NF1** tiene ya conocimiento imperfecto, tiempo, capacidad, geografía y obsolescencia. Sigue pendiente una capa territorial/por competición más profunda y mejores comparaciones de candidatos.
- **NF2** tiene plan de plantilla y enlace directo a mercado; siguen pendientes decisiones persistentes por jugador y comparación A/B/C.
- **NF3** tiene ya una vertical jugable de entrenamiento + carga + condición + medicina + lesión. Quedan por profundizar familiaridad táctica, recuperación específica, preparación rival dentro del plan y efectos longitudinales de staff/moral.

## Siguiente frente recomendado

Con el nuevo P0 cada vez más conectado, el siguiente bloque de alto retorno es continuar NF3 y empezar NF4/NF5 de forma transversal:

1. familiaridad táctica y preparación específica del rival;
2. feedback semanal del segundo entrenador/preparador basado en datos reales;
3. comparación A/B/C de objetivos desde una necesidad concreta;
4. decisiones persistentes de plantilla (mantener/renovar/vender/ceder/sustituir);
5. ampliar efectos del staff sin convertirlos en bonificaciones invisibles.
