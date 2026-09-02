<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
:root {
  --bg-primary: #0A0E14;
  --bg-panel: #141A22;
  --bg-card: #1A2029;
  --bg-input: #0D1117;
  --bg-hover: #1E2530;
  --border: #252D38;
  --accent: #3B82F6;
  --up-color: #F23645;
  --down-color: #089981;
  --text-primary: #E6EDF3;
  --text-secondary: #8B95A5;
  --ma5: #E8C07D;
  --ma10: #5B8DEF;
  --ma20: #C792EA;
  --ma60: #7D8590;
  --font-mono: 'JetBrains Mono', 'Roboto Mono', 'DIN', 'Consolas', monospace;
  --font-sans: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: var(--font-sans);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

body {
  background: url('/bg-finance.jpg') center/cover no-repeat fixed;
}

#app {
  position: relative;
}

#app::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(10, 14, 20, 0.7);
  z-index: 0;
  pointer-events: none;
}

#app > * {
  position: relative;
  z-index: 1;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
  background: #2D333B;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #444C56;
}
</style>