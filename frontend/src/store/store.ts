import { createStore } from 'vuex'
import user from './modules/user'
import workflow from './modules/workflow'
import document from './modules/document'
import client from './modules/client'

export const store = createStore({
  modules: {
    user,
    client,
    workflow,
    document,
  },
})

export default store
