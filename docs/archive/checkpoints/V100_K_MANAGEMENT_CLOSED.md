# V1.0-K — Mercado, staff y entrenamiento · cierre canónico

Fecha: 18-08-2026  
Checkpoint: `1.0.0-k-management-closed`

## Contrato cerrado

Mercado, staff y entrenamiento dejan de comportarse como pantallas aisladas y comparten una gramática única de proceso:

`necesidad → responsable → trabajo en curso → decisión → consecuencia`

El usuario puede saber qué se está haciendo, quién lo lleva, qué falta, cuándo se espera el siguiente paso, qué parte requiere su intervención y qué cambiará si el proceso termina. La actividad delegada no interrumpe `Continuar`; sólo lo hacen decisiones reales.

## Mercado

El flujo visible queda ampliado a:

`Necesidad → Búsqueda → Seguimiento → Informe → Consulta → Negociación → Decisión → Consecuencia`

- La vista expone propietario del scouting y de la negociación, esperas activas, decisiones pendientes y siguiente paso.
- La comparación A/B/C muestra nivel, encaje, certeza del conocimiento, valoración y coste de oportunidad antes de comprometer presupuesto.
- El presupuesto enseña compromisos de ofertas ya abiertas y el margen que quedaría si se aceptasen.
- Con el mercado de inscripciones cerrado siguen disponibles búsqueda, scouting, seguimiento y consultas; sólo se bloquean nuevas altas/ofertas que requieren una ventana abierta.
- Las negociaciones distinguen espera, contraoferta que exige decisión y bloqueo por ventana, con explicación de la acción posible.

## Staff y continuidad de responsabilidad

Cambiar quién lleva un área ya no reinicia trabajos activos ni oculta quién tomó el relevo.

- Scouting activo conserva `id`, fecha prevista y estado; cambia el responsable y registra el handoff.
- Negociaciones activas conservan su identidad, respuesta prevista y estado; el nuevo responsable hereda el expediente y el historial registra `handler_changed`.
- Staff muestra cuántos procesos vivos dependen de cada responsabilidad, el último traspaso y los procesos afectados.
- El cambio queda registrado también como evento de mundo para que Inicio pueda explicar la consecuencia reciente.

## Entrenamiento y médico

Entrenamiento expone el proceso semanal completo: necesidad, responsable, estado, siguiente paso y consecuencia. El bloque médico comparte la misma verdad de disponibilidad y diferencia explícitamente:

- **observado:** lesión/condición que existe en el estado de carrera;
- **estimado:** días de baja y riesgo, que pueden cambiar con evolución, carga o recaída;
- **acción:** recomendación concreta cuando lesión o riesgo justifican intervención.

Esto evita presentar una estimación médica como una certeza y mantiene conectado el trabajo semanal con disponibilidad y riesgo de partido.

## Continuar

Se elimina una interrupción falsa heredada: `advance_until_event` ya no trata actividad de plantilla por prioridad como una decisión urgente. El criterio es el contrato `blocking` del dashboard; seguimiento, scouting y trabajo delegado pueden avanzar sin fricción.

## Gates ejecutados

- V1.0-K específico: **6/6 PASS** (cinco recorridos funcionales + contrato frontend).
- continuidad V1.0 previa: **2/2 PASS**.
- entrenamiento/scouting v0.49: **7/7 PASS**.
- mercado de carrera: **3/3 PASS**.
- staff base: **5/5 PASS**.
- higiene/release V1.0-H: **7/7 PASS**.
- frontend: version metadata PASS; SFC structure PASS; UI quality PASS; Vue syntax **28/28 PASS**.
- la ejecución combinada de todos los bloques agotó el límite del entorno tras 14 tests sin fallo; por eso el cierre conserva resultados segmentados verificables.
- assets: 10.195 fotos conservadas; 4 intentos nuevos fallidos por DNS, trazados en `docs/v100_k_asset_microbatch_attempt.json` y no bloqueantes.

Siguiente frente canónico: **V1.0-L — Emoción e hitos**.
