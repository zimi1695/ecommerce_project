<script setup lang="ts">
defineProps<{ title: string; eyebrow: string; description: string }>()
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}<span class="title-dot">.</span></h1>
      <p class="page-description">{{ description }}</p>
    </div>
    <div class="heading-actions"><slot /></div>
  </div>
</template>
