import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Login.css'; // Arquivo de estilos sugerido abaixo

const Login = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const navigate = useNavigate();

    // Atualiza o estado conforme o usuário digita
    const handleChange = (e) => {
        setCredentials({
            ...credentials,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(''); // Limpa erros anteriores

        try {
            // Nota: Certifique-se de ter configurado uma rota de auth no Django (ex: SimpleJWT ou Djoser)
            // Aqui assumo que o endpoint retorna o token e os dados do usuário (incluindo o 'type')
            const response = await axios.post('http://localhost:8000/api/token/', credentials);

            const { access, type } = response.data;

            // 1. Salvar o Token para uso futuro (sessão)
            localStorage.setItem('token', access);
            localStorage.setItem('userType', type);

            // 2. Redirecionamento Inteligente (Baseado na Ata de Reunião)
            if (type === 'ADMIN') {
                navigate('/admin-panel'); // Vai para a auditoria
            } else {
                navigate('/dashboard'); // Vai para o cadastro de produtos
            }

        } catch (err) {
            console.error("Erro no login:", err);
            setError('Usuário ou senha inválidos. Verifique suas credenciais.');
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h2>Amazônia Marketing</h2>
                <p className="subtitle">Acesso ao Sistema de Certificação</p>
                
                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="username">Usuário (CPF/CNPJ)</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
                            placeholder="Digite seu usuário"
                            value={credentials.username}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Senha</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            placeholder="Digite sua senha"
                            value={credentials.password}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <button type="submit" className="btn-login">
                        Entrar
                    </button>
                </form>
                
                <p className="footer-text">
                    Ainda não tem cadastro? <a href="/register">Solicite aqui</a>
                </p>
            </div>
        </div>
    );
};

export default Login;