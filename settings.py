INSTALLED_APPS = [
    # ... seus apps padrão
    'corsheaders', # Adicione esta linha
    # ... seus apps do projeto (ex: 'core', 'api')
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    'corsheaders.middleware.CorsMiddleware', # Adicione AQUI (antes do CommonMiddleware)
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# Configuração de CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]

# (Opcional) Se você estiver desenvolvendo localmente e tiver problemas constantes,
# pode usar essa configuração TEMPORÁRIA para permitir tudo (não use em produção):
# CORS_ALLOW_ALL_ORIGINS = True
# Se for usar autenticação via Session/Cookies futuramente, ative:

CORS_ALLOW_CREDENTIALS = True

# Para garantir que o Django 4.x+ aceite o CSRF de origens confiáveis:
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]