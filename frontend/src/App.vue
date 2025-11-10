<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
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
          Dashboard
        </RouterLink>
        <RouterLink to="/client-creation">
          <span class="icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
              <path d="M5 20C5 16.134 8.13401 13 12 13C15.866 13 19 16.134 19 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </span>
          Mandate
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
</template>

<style scoped>
.nav-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1.25rem;
  background: linear-gradient(to right, #f8f9fa, #f1f3f5);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.nav-links {
  display: flex;
  justify-content: center;
  gap: 1rem;
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
  color: #444;
  font-weight: 500;
  padding: 0.5rem 0.75rem;
  position: relative;
  transition: all 0.25s ease;
  border-radius: 6px;
}

.nav-links a:hover {
  color: #94754a;
  background-color: #0d162714;
}

.nav-links a::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: 0;
  left: 50%;
  background-color: #94754a;
  transition: all 0.25s ease;
  transform: translateX(-50%);
}

.nav-links a:hover::after,
.nav-links a.router-link-active::after {
  width: 60%;
}

.nav-links a.router-link-active {
  color: #94754a;
  background-color: #94754a14;
}

.nav-links a svg {
  transition: transform 0.2s ease;
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
  color: #94754a;
}

.nav-actions a .settings-icon {
  color: #444;
  transition: transform 0.2s ease;
}

.nav-actions a:hover .settings-icon {
  color: #94754a;
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