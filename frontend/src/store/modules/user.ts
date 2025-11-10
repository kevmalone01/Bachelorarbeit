interface UserState {
    user: any
    isLoggedIn: boolean
}

const user = {
    state: (): UserState => ({
        user: null,
        isLoggedIn: false,
    }),
    mutations: {},
    actions: {},
    getters: {},
}

export default user
