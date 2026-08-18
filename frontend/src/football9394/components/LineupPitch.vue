<script setup>
import { computed } from 'vue'

const props = defineProps({
  formation: { type: String, default: '4-4-2' },
  players: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  interactive: { type: Boolean, default: false },
  selectedPlayerId: { type: Number, default: 0 },
})

const emit = defineEmits(['select-player'])

const layouts = {
  '4-4-2': [
    ['GK', 50, 89],
    ['DEF', 14, 70], ['DEF', 38, 70], ['DEF', 62, 70], ['DEF', 86, 70],
    ['MID', 14, 45], ['MID', 38, 45], ['MID', 62, 45], ['MID', 86, 45],
    ['FWD', 38, 18], ['FWD', 62, 18],
  ],
  '4-3-3': [
    ['GK', 50, 89],
    ['DEF', 14, 70], ['DEF', 38, 70], ['DEF', 62, 70], ['DEF', 86, 70],
    ['MID', 25, 45], ['MID', 50, 42], ['MID', 75, 45],
    ['FWD', 20, 18], ['FWD', 50, 14], ['FWD', 80, 18],
  ],
  '3-5-2': [
    ['GK', 50, 89],
    ['DEF', 24, 68], ['DEF', 50, 72], ['DEF', 76, 68],
    ['MID', 10, 44], ['MID', 30, 43], ['MID', 50, 39], ['MID', 70, 43], ['MID', 90, 44],
    ['FWD', 37, 16], ['FWD', 63, 16],
  ],
  '5-3-2': [
    ['GK', 50, 89],
    ['DEF', 9, 66], ['DEF', 29, 70], ['DEF', 50, 73], ['DEF', 71, 70], ['DEF', 91, 66],
    ['MID', 25, 42], ['MID', 50, 39], ['MID', 75, 42],
    ['FWD', 37, 16], ['FWD', 63, 16],
  ],
  '4-2-3-1': [
    ['GK',50,89], ['DEF',14,70],['DEF',38,70],['DEF',62,70],['DEF',86,70],
    ['MID',38,53],['MID',62,53],['MID',18,32],['MID',50,29],['MID',82,32],['FWD',50,13],
  ],
  '4-5-1': [
    ['GK',50,89], ['DEF',14,70],['DEF',38,70],['DEF',62,70],['DEF',86,70],
    ['MID',10,43],['MID',30,45],['MID',50,40],['MID',70,45],['MID',90,43],['FWD',50,15],
  ],
  '4-4-1-1': [
    ['GK',50,89], ['DEF',14,70],['DEF',38,70],['DEF',62,70],['DEF',86,70],
    ['MID',14,46],['MID',38,46],['MID',62,46],['MID',86,46],['FWD',50,29],['FWD',50,13],
  ],
  '4-3-1-2': [
    ['GK',50,89], ['DEF',14,70],['DEF',38,70],['DEF',62,70],['DEF',86,70],
    ['MID',25,48],['MID',50,44],['MID',75,48],['MID',50,29],['FWD',37,14],['FWD',63,14],
  ],
  '4-2-4': [
    ['GK',50,89], ['DEF',14,70],['DEF',38,70],['DEF',62,70],['DEF',86,70],
    ['MID',38,45],['MID',62,45],['FWD',12,19],['FWD',38,14],['FWD',62,14],['FWD',88,19],
  ],
  '3-4-3': [
    ['GK',50,89], ['DEF',24,70],['DEF',50,73],['DEF',76,70],
    ['MID',12,47],['MID',38,45],['MID',62,45],['MID',88,47],
    ['FWD',18,18],['FWD',50,13],['FWD',82,18],
  ],
  '3-4-1-2': [
    ['GK',50,89], ['DEF',24,70],['DEF',50,73],['DEF',76,70],
    ['MID',12,48],['MID',38,47],['MID',62,47],['MID',88,48],['MID',50,29],
    ['FWD',37,14],['FWD',63,14],
  ],
  '5-4-1': [
    ['GK',50,89], ['DEF',9,66],['DEF',29,70],['DEF',50,73],['DEF',71,70],['DEF',91,66],
    ['MID',16,43],['MID',39,45],['MID',61,45],['MID',84,43],['FWD',50,15],
  ],
  '5-2-3': [
    ['GK',50,89], ['DEF',9,66],['DEF',29,70],['DEF',50,73],['DEF',71,70],['DEF',91,66],
    ['MID',38,45],['MID',62,45],['FWD',20,18],['FWD',50,13],['FWD',80,18],
  ],
}

function family(player) {
  const pos = String(player?.pos || player?.position || '').toUpperCase()
  if (pos === 'POR' || pos.includes('PORT')) return 'GK'
  if (['LD','LI','CB','DFC','DF','CENTRAL','LIB'].some(token => pos === token || pos.includes(token))) return 'DEF'
  if (['MCD','MC','MP','MD','MI','MED','MCO'].some(token => pos === token || pos.includes(token))) return 'MID'
  return 'FWD'
}

const placedPlayers = computed(() => {
  const pool = [...props.players]
  const slots = layouts[props.formation] || layouts['4-4-2']
  return slots.map(([type, x, y], index) => {
    let playerIndex = pool.findIndex(player => family(player) === type)
    if (playerIndex < 0) playerIndex = 0
    const player = pool.length ? pool.splice(playerIndex, 1)[0] : null
    return { type, x, y, player, key: `${type}-${index}` }
  })
})

const photo = player => player?.id ? `/historical9394/players/${Number(player.id)}.jpg` : null

function shortName(player) {
  const name = String(player?.name || player?.display_name || 'Vacante').trim()
  const parts = name.split(/\s+/)
  return parts.length > 1 ? parts.at(-1) : name
}
</script>

<template>
  <div class="lineup-pitch" :class="{ compact }" :aria-label="`Once en formación ${formation}`">
    <div class="pitch-markings" aria-hidden="true"><i class="pitch-half"></i><i class="pitch-circle"></i><i class="pitch-box top"></i><i class="pitch-box bottom"></i></div>
    <div
      v-for="slot in placedPlayers"
      :key="slot.key"
      class="pitch-player"
      :class="[`role-${slot.type.toLowerCase()}`, { empty: !slot.player, interactive: interactive && !!slot.player, selected: Number(selectedPlayerId) === Number(slot.player?.id || 0) }]"
      :style="{ left: `${slot.x}%`, top: `${slot.y}%` }"
      :role="interactive && slot.player ? 'button' : undefined"
      :tabindex="interactive && slot.player ? 0 : undefined"
      :aria-label="interactive && slot.player ? `Seleccionar a ${slot.player.name || slot.player.display_name} para sustituir o quitar` : undefined"
      @click="interactive && slot.player && emit('select-player', slot.player)"
      @keydown.enter.prevent="interactive && slot.player && emit('select-player', slot.player)"
      @keydown.space.prevent="interactive && slot.player && emit('select-player', slot.player)"
    >
      <span class="pitch-player-visual">
        <img v-if="slot.player" :src="photo(slot.player)" alt="" @error="$event.currentTarget.style.display='none'">
        <i>{{ slot.player?.n || slot.player?.shirt_number || '•' }}</i>
      </span>
      <strong>{{ shortName(slot.player) }}</strong>
      <small v-if="!compact">{{ slot.player?.pos || slot.player?.position || slot.type }}<template v-if="slot.player?.overall"> · {{ slot.player.overall }}</template></small>
    </div>
    <span class="pitch-formation">{{ formation }}</span>
  </div>
</template>
