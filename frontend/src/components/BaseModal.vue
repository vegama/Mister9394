<script setup>
/**
 * Modal base accesible (B5-06).
 *
 * `App.vue` tenía cada modal escrito a mano, sin foco atrapado, sin cierre
 * con Esc, sin devolver el foco al cerrar y sin `aria-modal`. Con el teclado
 * se podía tabular fuera del diálogo y seguir "usando" la pantalla de detrás.
 *
 * Además resuelve B8-15: un modal marcado como `dirty` (una negociación a
 * medias, un formulario con datos) no se cierra por un clic accidental en el
 * fondo. Se pide confirmación.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { claseDeCapa, entrarEnLaPila, salirDeLaPila } from '../composables/modalStack'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  /** Bloquea el cierre por backdrop y por Esc sin confirmar (B8-15). */
  dirty: { type: Boolean, default: false },
  /** Texto de la confirmación cuando está `dirty`. */
  dirtyPrompt: { type: String, default: '¿Descartar los cambios sin guardar?' },
  /** `panel` en escritorio; `full` fuerza pantalla completa (B10-05). */
  size: { type: String, default: 'panel' },
  closeLabel: { type: String, default: 'Cerrar' },
  /** Algunas superficies bloqueantes (avance o partido live) no se cierran como un diálogo normal. */
  closable: { type: Boolean, default: true },
  /** Nombre accesible cuando la cabecera se aporta mediante slot y no hay `title`. */
  ariaLabel: { type: String, default: '' },
  /**
   * Capa de apilado (B12-02). Una sola escala para todo el juego, en vez de
   * `z-index` sueltos por componente: con aquéllos, el modal de renovación
   * (50) se abría **por detrás** de la ficha del jugador desde la que se
   * invocaba (70). El orden es
   * `page-overlay < entity < action < confirmation < blocking < toast`.
   */
  layer: { type: String, default: 'action' },
  /** Clase opcional del panel para conservar layouts de feature al migrar. */
  panelClass: { type: [String, Array, Object], default: '' },
  /** Renderiza el mismo contenido como página canónica, sin backdrop ni semántica de diálogo. */
  embedded: { type: Boolean, default: false },
  /** Hook estable para recorridos E2E sin acoplar el runner a clases visuales. */
  e2e: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const dialogo = ref(null)
const discardGuard = ref(false)
const keepEditingButton = ref(null)
let focoPrevio = null

const capa = computed(() => claseDeCapa(props.layer))

const titleId = computed(() => `modal-title-${Math.random().toString(36).slice(2, 9)}`)

function intentarCerrar() {
  if (!props.closable) return
  if (props.dirty) {
    discardGuard.value = true
    nextTick(() => keepEditingButton.value?.focus())
    return
  }
  emit('close')
}
function descartarYCerrar() {
  discardGuard.value = false
  emit('close')
}
function seguirEditando() {
  discardGuard.value = false
  nextTick(() => dialogo.value?.focus())
}

function alPulsarTecla(evento) {
  if (evento.key === 'Escape') {
    evento.stopPropagation()
    if (discardGuard.value) seguirEditando()
    else intentarCerrar()
    return
  }
  if (evento.key !== 'Tab') return
  // Foco atrapado: Tab en el último elemento vuelve al primero y viceversa.
  const focusables = dialogo.value?.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  if (!focusables?.length) return
  const primero = focusables[0]
  const ultimo = focusables[focusables.length - 1]
  if (evento.shiftKey && document.activeElement === primero) {
    evento.preventDefault(); ultimo.focus()
  } else if (!evento.shiftKey && document.activeElement === ultimo) {
    evento.preventDefault(); primero.focus()
  }
}

onMounted(async () => {
  if (props.embedded) return
  focoPrevio = document.activeElement
  // Bloquea el scroll de la página de detrás mientras el diálogo está abierto.
  // B12-02 · Se cuentan los diálogos abiertos: con modales anidados, cerrar el
  // hijo restauraba el scroll aunque el padre siguiera abierto, y la página de
  // detrás volvía a moverse bajo un diálogo todavía visible.
  entrarEnLaPila()
  await nextTick()
  const primero = dialogo.value?.querySelector('[autofocus], button, input, select, textarea')
  ;(primero || dialogo.value)?.focus()
})

onBeforeUnmount(() => {
  if (props.embedded) return
  salirDeLaPila()
  // Devolver el foco a donde estaba es lo que hace que el teclado no se
  // pierda al cerrar; sin esto vuelve al principio del documento.
  if (focoPrevio instanceof HTMLElement) focoPrevio.focus()
})
</script>

<template>
  <section
    v-if="embedded"
    ref="dialogo"
    class="modal-panel entity-page-surface"
    :class="[`modal-${size}`, panelClass]"
    :aria-label="ariaLabel || undefined"
    :data-e2e="e2e || undefined"
    tabindex="-1"
  >
    <header v-if="title || $slots.header" class="modal-head entity-page-head">
      <slot name="header">
        <div>
          <h2 :id="titleId">{{ title }}</h2>
          <p v-if="subtitle" class="section-caption">{{ subtitle }}</p>
        </div>
      </slot>
      <button v-if="closable" type="button" class="ghost entity-page-back" :aria-label="closeLabel" @click="emit('close')">← Volver</button>
    </header>
    <div class="modal-body entity-page-body"><slot /></div>
    <footer v-if="$slots.footer" class="modal-foot entity-page-foot"><slot name="footer" /></footer>
  </section>

  <div v-else class="modal-backdrop" :class="capa" @click.self="intentarCerrar">
    <section
      ref="dialogo"
      class="modal-panel"
      :class="[`modal-${size}`, panelClass]"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="title ? titleId : undefined"
      :aria-label="!title && ariaLabel ? ariaLabel : undefined"
      :data-e2e="e2e || undefined"
      tabindex="-1"
      @keydown="alPulsarTecla"
    >
      <header v-if="title || $slots.header" class="modal-head">
        <slot name="header">
          <div>
            <h2 :id="titleId">{{ title }}</h2>
            <p v-if="subtitle" class="section-caption">{{ subtitle }}</p>
          </div>
        </slot>
        <button v-if="closable" type="button" class="ghost modal-close" :aria-label="closeLabel" @click="intentarCerrar">×</button>
      </header>

      <div class="modal-body"><slot /></div>

      <footer v-if="$slots.footer" class="modal-foot"><slot name="footer" /></footer>

      <div v-if="discardGuard" class="modal-discard-guard" role="alert" aria-live="assertive">
        <div><b>Hay cambios sin confirmar</b><span>{{ dirtyPrompt }}</span></div>
        <div class="button-row">
          <button ref="keepEditingButton" type="button" class="ghost" @click="seguirEditando">Seguir editando</button>
          <button type="button" class="primary danger" @click="descartarYCerrar">Descartar y cerrar</button>
        </div>
      </div>
    </section>
  </div>
</template>
