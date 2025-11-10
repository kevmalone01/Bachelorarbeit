<template>
    <div class="login-container">
        <div class="login-form">
            <h2>Login</h2>

            <form @submit.prevent="handleLogin">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" v-model="email" placeholder="Enter your email" required />
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" v-model="password" placeholder="Enter your password" required />
                </div>

                <button type="submit">Login</button>
            </form>

            <p class="register-link">
                Noch nicht registriert? <a href="registrieren">Registrieren</a>
            </p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const email = ref('');
const password = ref('');
const router = useRouter();

const handleLogin = () => {
    // TODO: Implement login logic

    // Nach erfolgreichem Login zur Dashboard-Seite navigieren
    router.push('/dashboard');
}
</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    padding: 20px;
}

.login-form {
    background-color: #fff;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

h2 {
    text-align: center;
    font-size: 24px;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

button {
    width: 100%;
    padding: 1rem;
    background-color: rgb(74, 127, 163);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    margin-top: 1rem;
}

button:hover {
    background-color: rgb(41, 82, 110);
}

.register-link {
    text-align: center;
    margin-top: 1rem;
}

.register-link a {
    color: rgb(74, 127, 163);
    text-decoration: none;
}

.register-link a:hover {
    text-decoration: underline;
}
</style>