import './assets/main.css';

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

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

app.use(router)
app.use(vuetify)

app.mount('#app')
