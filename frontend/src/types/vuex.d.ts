declare module 'vuex' {
    import { Component } from 'vue'
    export function createStore<S>(options: any): Store<S>
    export * from 'vuex/types/index'
}
