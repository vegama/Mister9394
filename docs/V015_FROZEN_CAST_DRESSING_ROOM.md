# 0.15 · Reparto eterno + vestuario profundo

## Decisión de producto

La edad congelada deja de ser una variante secundaria y pasa a ser la opción predeterminada de Nueva carrera.

En `frozen_attributes_dynamic`:

- ningún jugador envejece cronológicamente;
- no existe retirada por edad;
- no se promociona cantera ni se crean newgens;
- las decisiones que dependen de edad usan la edad histórica de 1993-94, no una edad oculta que siga avanzando;
- los atributos siguen siendo dinámicos y pueden mejorar o empeorar de forma específica.

El modo `dynamic_from_birth_date` sigue disponible para conservar la simulación cronológica tradicional y sus gates históricos.

## Evolución sin envejecimiento

El desarrollo ya acumula evidencia por atributo. Goles alimentan finalización/desmarque, asistencias visión/pase, la continuidad puede reforzar regularidad/trabajo y lesiones relevantes pueden erosionar resistencia/aceleración/velocidad. Los cambios son lentos y con umbrales: la intención es que el jugador siga siendo reconocible después de muchas temporadas.

## P4 · vestuario

La plantilla tiene ahora:

- capitán elegido y grupo de líderes;
- liderazgo capaz de amortiguar o amplificar una mala dinámica;
- competencia real por puestos basada en nivel y forma;
- tutelas entre jugadores del reparto histórico inicial;
- reacción colectiva a la marcha o lesión grave de figuras/líderes;
- regreso tras lesión larga, que reabre competencia sin restaurar automáticamente la titularidad;
- relaciones persistentes para futuros reencuentros;
- promesas explícitas de rol.

### Promesas de rol

`Figura`, `Titular`, `Rotación`, `Promesa` y `Fondo de plantilla` no son promesas automáticas. Sólo existe compromiso cuando el usuario lo acuerda expresamente en la ficha del jugador.

El juego observa ocho partidos oficiales. La frecuencia real de titularidad determina si la promesa va bien, entra en riesgo o termina cumplida/incumplida. Cumplir construye confianza y satisfacción; romperla las deteriora y puede empujar hacia una petición de salida. La valoración neutral y los atributos **no cambian como castigo o recompensa social**.

Una venta con una promesa activa cuenta como ruptura. Una destitución cierra el acuerdo sin culpar al mánager.

## Gates

- 10/10 tests específicos de edad congelada, vestuario, atributos, promesas y regresos de lesión.
- 64/64 regresión dirigida tras adaptar los antiguos tests de retirada/cantera para que activen explícitamente el modo cronológico.
- Rollover 1994-95 PASS y repetición 1995-96 PASS con cero retiradas y cero promociones de cantera en el modo predeterminado.
- Frontend: SFC, contrato UI y sintaxis Vue protegidos por gates Node.
