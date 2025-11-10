import './assets/main.css';

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query';
import { createDiscreteApi } from 'naive-ui';

// Vuetify
import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

// Material Design Icons
import '@mdi/font/css/materialdesignicons.css';
import { aliases, mdi } from 'vuetify/iconsets/mdi';

// DynamicMask
import DynamicMask from '@/components/DynamicMask.vue'; // Pfad zur Komponente

const vuetify = createVuetify({
    components,
    directives,
    icons: {
        defaultSet: 'mdi',
        aliases,
        sets: {
            mdi,
        },
    },
    theme: {
        themes: {
            light: {
                colors: {
                    brown: '#94754a',
                    darkBlue: '#0d1627',
                },
            },
            dark: {
                colors: {
                    brown: '#94754a',
                    darkBlue: '#0d1627',
                },
            },
        },
    },
})

const app = createApp(App)

// Pinia
const pinia = createPinia();
app.use(pinia);

// Router
app.use(router);

// Vuetify (bestehendes UI bleibt nutzbar)
app.use(vuetify);

// Vue Query
const queryClient = new QueryClient();
app.use(VueQueryPlugin, { queryClient });

// Naive UI discrete API (Notification/Message optional global)
const { message, notification } = createDiscreteApi(['message', 'notification']);
app.provide('nMessage', message);
app.provide('nNotification', notification);

app.mount('#app')
