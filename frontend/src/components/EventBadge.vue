<script setup lang="ts">
import type { EventType } from '../types'
import { eventNames } from '../utils'
defineProps<{ type: EventType }>()
</script>
<template>
  <span class="event-badge" :class="type"><span />{{ eventNames[type] }}</span>
</template>
