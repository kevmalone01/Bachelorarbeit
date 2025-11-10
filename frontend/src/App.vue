<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { NConfigProvider } from 'naive-ui'

// Naive UI Theme Overrides: set primary to blue #0077B6
const themeOverrides = {
  common: {
    primaryColor: '#0077B6',
    primaryColorHover: '#0a8ad2',
    primaryColorPressed: '#00639a',
    primaryColorSuppl: '#0090ea'
  },
  Button: {
    // make primary buttons use our blue shades
    textColorPrimary: '#ffffff'
  }
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
  <header>
    <nav class="nav-container">
      <div class="nav-links">
        <RouterLink to="/dashboard">
          <span class="icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="7" height="9" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="3" width="7" height="5" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="12" width="7" height="9" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="3" y="16" width="7" height="5" rx="2" stroke="currentColor" stroke-width="2"/>
            </svg>
          </span>
          Dokumente
        </RouterLink>
        <RouterLink to="/clients">
          <span class="icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
              <path d="M5 20C5 16.134 8.13401 13 12 13C15.866 13 19 16.134 19 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </span>
          Mandate
        </RouterLink>
        <RouterLink to="/templates">
          <span class="icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 3V7C14 7.55228 14.4477 8 15 8H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H14L19 8V19C19 20.1046 18.1046 21 17 21Z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </span>
          Vorlagen
        </RouterLink>
        <RouterLink to="/document-creation">
          <span class="icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 3V7C14 7.55228 14.4477 8 15 8H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H14L19 8V19C19 20.1046 18.1046 21 17 21Z" stroke="currentColor" stroke-width="2"/>
              <path d="M9 13H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M9 17H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </span>
          Dokumente
        </RouterLink>
      </div>
      
      <div class="nav-actions">
        <RouterLink to="/account-settings" class="settings-btn">
          <v-icon class="settings-icon" size="28">mdi-account-cog-outline</v-icon>
        </RouterLink>
      </div>
    </nav>
  </header>

  <RouterView />
  </n-config-provider>
</template>

<style scoped>
.nav-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 56px;
  padding: 0 0.75rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: saturate(180%) blur(8px);
  -webkit-backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.nav-links {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
}

.nav-links a {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-links a {
  margin: 0 0.75rem;
  text-decoration: none;
  color: #2b2f36;
  font-weight: 600;
  padding: 0.35rem 0.6rem;
  position: relative;
  transition: all 0.25s ease;
  border-radius: 9999px;
}

.nav-links a:hover {
  color: #0077B6;
  background-color: rgba(0, 119, 182, 0.08);
}

.nav-links a::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: 0;
  left: 50%;
  background-color: #0077B6;
  transition: all 0.25s ease;
  transform: translateX(-50%);
}

.nav-links a:hover::after,
.nav-links a.router-link-active::after {
  width: 50%;
}

.nav-links a.router-link-active {
  color: #0077B6;
  background-color: rgba(0, 119, 182, 0.08);
}

.nav-links a svg {
  transition: transform 0.2s ease;
  color: currentColor;
}

.nav-links a:hover svg {
  transform: translateY(-1px);
}

.nav-actions {
  position: absolute;
  right: 25px;
}

.nav-actions a {
  margin: 0 0.75rem;
}

.nav-actions a.router-link-active {
  color: #0077B6;
}

.nav-actions a .settings-icon {
  color: #2b2f36;
  transition: transform 0.2s ease;
}

.nav-actions a:hover .settings-icon {
  color: #0077B6;
  transform: translateY(-1px);
}

.icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1.25rem;
    padding: 0.5rem;
  }
  
  .nav-links {
    width: 100%;
    justify-content: space-between;
  }
}
</style>