import axios from 'axios';

// const API_BASE_URL = 'https://747b-103-105-234-210.ngrok-free.app/api/v1';
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        "ngrok-skip-browser-warning": "test"
    },
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle 403 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 403) {
            // Clear the token from localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            // Redirect to login page
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const authAPI = {
    login: async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('grant_type', 'password');
        const response = await api.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    register: async (email, username, password) => {
        const response = await api.post('/auth/register', {
            email,
            username,
            password
        });
        return response.data;
    },
    getUsers: async () => {
        const response = await api.get('/users');
        return response.data;
    },
};

export const chatAPI = {
    createChat: async (name, type = 'single', isActive = true, participantIds = []) => {
        const response = await api.post('/chats', {
            name,
            type,
            is_active: isActive,
            participant_ids: participantIds
        });
        return response.data;
    },
    getChats: async () => {
        const response = await api.get('/chats');
        return response.data;
    },
    getChat: async (chatId) => {
        const response = await api.get(`/chats/${chatId}`);
        return response.data;
    },
    updateChat: async (chatId, data) => {
        const response = await api.put(`/chats/${chatId}`, data);
        return response.data;
    },
    deleteChat: async (chatId) => {
        const response = await api.delete(`/chats/${chatId}`);
        return response.data;
    },
};

export const messageAPI = {
    getMessages: async (chatId) => {
        const response = await api.get(`/chats/${chatId}/messages`);
        return response.data;
    },
    addMessage: async (chatId, message) => {
        const response = await api.post(`/chats/${chatId}/messages`, message);
        return response.data;
    },
};

export const branchAPI = {
    getBranches: async (chatId, messageId) => {
        const response = await api.get(`/chats/${chatId}/messages/${messageId}/thread`);
        return response.data;
    },
    setActiveBranch: async (chatId) => {
        const response = await api.get(`/chats/${chatId}/branches`);
        return response.data;
    },
};

export default api; 