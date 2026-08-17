# 0.48.0 · Lote funcional: staff operativo, scouting, planificación y partes

Esta entrega encadena varias piezas del plan NF0–NF3 para que la nueva etapa no avance a base de pantallas aisladas. El objetivo es que el club empiece a funcionar como una red de personas, información imperfecta y decisiones conectadas.

## NF0 · Delegación con consecuencias

La matriz de responsabilidades de 0.47 pasa a producir una eficacia operativa común. La calidad depende de la competencia del responsable y de su carga; el control directo del mánager tiene una referencia propia y también puede sufrir sobrecarga. Esta eficacia ya es consumida por cuatro sistemas: scouting, informes del rival, área médica y negociación de mercado.

Una responsabilidad ya no significa sólo «quién aparece en el desplegable»: determina quién genera la información, con qué confianza y, cuando corresponde, con qué velocidad o precisión.

## NF1 · Primera vertical de scouting real

El mercado deja de ser una ventana directa a la verdad del motor para futbolistas externos. Se añade conocimiento persistente por jugador con cuatro niveles visibles: referencia básica, seguimiento inicial, informe fiable y conocimiento profundo.

En conocimiento bajo:

- la media mostrada es una estimación y se acompaña de rango;
- el valor y salario son estimaciones, no cifras canónicas;
- los atributos permanecen ocultos o aparecen como rangos;
- encargar un informe consume días de calendario;
- el responsable y su calidad afectan al tiempo y a la confianza;
- el jugador entra automáticamente en seguimiento;
- al completarse el informe se genera un evento/noticia y el conocimiento queda guardado.

Una segunda observación permite profundizar hasta conocimiento prácticamente completo. La incertidumbre es determinista para una misma partida/jugador: recargar no «rerrollea» la valoración estimada.

## NF2 · Planificación de plantilla

La lógica de necesidades que ya utilizaba la IA se expone ahora al mánager. El plan devuelve:

- cobertura y nivel medio por demarcación;
- déficit y prioridad;
- contratos próximos a terminar;
- piezas que requieren planificación de sucesión;
- posibles excedentes;
- una acción propuesta.

Si no existe una urgencia, el plan conserva una lectura de seguimiento de la posición más débil; nunca queda como panel vacío.

## NF3 · Parte médico filtrado por el staff

Los jugadores propios siguen siendo conocidos internamente, pero la medicina deja de comunicar automáticamente la verdad exacta del simulador. El responsable médico aporta un intervalo estimado de días/fecha de regreso, confianza y recomendación. Un especialista de gran nivel puede acotar mucho más el pronóstico.

## Preparación del rival

El informe previo al partido también consume la responsabilidad de análisis del rival. La calidad determina cuántos jugadores peligrosos se identifican, el margen de sus niveles estimados y cuántos aspectos tácticos se conocen. La interfaz indica quién realizó el informe y su confianza.

## Mercado y negociación

Cada negociación registra quién la dirige y su calidad. La competencia puede alterar modestamente los tiempos de respuesta y las exigencias de salario/contraoferta; se evita un bonus arcade grande, pero delegar en alguien competente tiene valor real.

## Contratos de producto

- Un jugador de la propia plantilla no genera dossier de mercado: su información vive en los sistemas internos del club.
- La BD conserva siempre la verdad canónica; scouting sólo controla cuánto conoce el usuario.
- Ninguna estimación sobrescribe datos históricos.
- Las superficies nuevas explican responsable, calidad/confianza y estado para que la incertidumbre sea comprensible, no ruido oculto.

## Estado al cerrar esta pasada

NF0 queda mucho más cerca del gate funcional, pero sigue abierto hasta extender sus consecuencias a entrenamiento y más procesos del club. NF1 y NF2 tienen ya una vertical jugable, no se declaran cerrados. NF3 tiene cerrada su primera rebanada médica; el entrenamiento semanal sigue siendo el siguiente gran bloque.

## Certificación de esta entrega

- nuevo bloque funcional: 6/6;
- regresión dirigida NF0/API/mercado/partido: 30/30;
- regresión histórica F1–F8: 14/14;
- gates frontend SFC/UI/Vue: PASS, 24/24 SFC;
- bundle Vite de producción: no certificado en este entorno porque `vite` no está materializado, después de pasar todos los gates previos.
