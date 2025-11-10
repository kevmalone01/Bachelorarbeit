<template>
    <v-container fluid class="workflow-documents-view">
        <WorkflowDocumentsManager
            :workflow-id="workflowId"
            :title="'Workflow Dokumente'"
            :subtitle="workflow?.name"
            :show-header="true"
            :show-back-button="true"
            @back="goBack"
            @documents-loaded="onDocumentsLoaded"
        />
    </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { WorkflowAPI } from '@/services/api'
import WorkflowDocumentsManager from '@/components/WorkflowDocumentsManager.vue'

const router = useRouter()
const route = useRoute()

// Reactive data
const workflowId = ref<number>(Number(route.params.id))
const workflow = ref<any>(null)

// Navigation
const goBack = () => {
    router.push('/dashboard')
}

// Load workflow data
const loadWorkflow = async () => {
    try {
        const response = await WorkflowAPI.getWorkOrder(workflowId.value)
        workflow.value = response.data
    } catch (error) {
        console.error('Error loading workflow:', error)
    }
}

const onDocumentsLoaded = (documents: any[]) => {
    // Optional: Handle documents loaded event
    console.log('Documents loaded:', documents.length)
}

// Initialize
onMounted(() => {
    loadWorkflow()
})
</script>

<style scoped>
.workflow-documents-view {
    min-height: 100vh;
    padding: 0;
}
</style>