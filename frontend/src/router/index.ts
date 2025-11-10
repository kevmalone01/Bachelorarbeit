import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'
import Dashboard from '@/pages/Dashboard.vue'
import ClientCreationView from '../views/ClientCreationView.vue'
import Clients from '@/pages/Clients.vue'
import ClientDetail from '@/pages/ClientDetail.vue'
import Templates from '@/pages/Templates.vue'
import DocumentCreationView from '../views/DocumentCreationView.vue'
import DocumentFillingView from '../views/DocumentFillingView.vue'
import WorkflowDetailView from '../views/WorkflowDetailView.vue'
import WorkflowDocumentsView from '../views/WorkflowDocumentsView.vue'
import IntelligentDocumentProcessingView from '../views/IntelligentDocumentProcessingView.vue'
import AccountSettingsView from '../views/AccountSettingsView.vue'
import AIAgentView from '../views/AIAgentView.vue'
import store from '@/store/store'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/dashboard',
        },
        {
            path: '/auth',
            name: 'auth',
            component: AuthView,
            meta: { requiresAuth: false },
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: Dashboard,
            meta: { requiresAuth: true },
        },
        {
            path: '/workflow/:id',
            name: 'workflow-detail',
            component: WorkflowDetailView,
            meta: { requiresAuth: true },
        },
        {
            path: '/workflow/:id/documents',
            name: 'workflow-documents',
            component: WorkflowDocumentsView,
            meta: { requiresAuth: true },
        },
        {
            path: '/workflow/:workflowId/intelligent-processing',
            name: 'intelligent-document-processing',
            component: IntelligentDocumentProcessingView,
            meta: { requiresAuth: true },
        },
        {
            path: '/client-creation',
            name: 'client-creation',
            component: ClientCreationView,
            meta: { requiresAuth: true },
        },
        {
            path: '/clients',
            name: 'clients',
            component: Clients,
            meta: { requiresAuth: true },
        },
        {
            path: '/clients/:id',
            name: 'client-detail',
            component: ClientDetail,
            meta: { requiresAuth: true },
        },
        {
            path: '/templates',
            name: 'templates',
            component: Templates,
            meta: { requiresAuth: true },
        },
        {
            path: '/document-creation',
            name: 'document-creation',
            component: DocumentCreationView,
            meta: { requiresAuth: true },
        },
        {
            path: '/documents/filling',
            name: 'document-filling',
            component: DocumentFillingView,
            meta: { requiresAuth: true },
        },
        {
            path: '/account-settings',
            name: 'account-settings',
            component: AccountSettingsView,
            meta: { requiresAuth: true },
        },
        {
            path: '/ai-agent',
            name: 'ai-agent',
            component: AIAgentView,
            meta: { requiresAuth: true },
        }
    ],
});

router.beforeEach((to, from, next) => {
    next();
});

export default router;