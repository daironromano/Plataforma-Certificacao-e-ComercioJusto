-- Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS amazonia_marketing;
USE amazonia_marketing;

-- Guarda os dados comuns a todos os perfis.
CREATE TABLE Usuarios (
    -- Dados comuns
	id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    endereco VARCHAR(100) NOT NULL,
    senha VARCHAR(100) NOT NULL,
    -- Define quem é quem
    tipo ENUM('produtor', 'empresa', 'admin') NOT NULL,
    -- Dados específicos
    cpf VARCHAR(14) NULL,
    cnpj VARCHAR(18) NULL,
    matricula VARCHAR(12) NULL
    
);

-- 2. Tabela Produtos
CREATE TABLE Produtos (
	id_produto INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10, 2), 
    status_estoque ENUM('disponivel', 'esgotado') DEFAULT 'disponivel',
    -- Quem cadastrou o produtor
    usuario_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id_usuario)
);

-- 3. Tabela Certificações
CREATE TABLE Certificacoes (
	id_certificacao INT AUTO_INCREMENT PRIMARY KEY,
    -- Autodeclaração
    texto_autodeclaracao TEXT,
    documento VARCHAR(255) NOT NULL,
    status_certificacao ENUM('pendente', 'aprovado', 'reprovado') DEFAULT 'pendente',
    data_envio DATE,
    data_resposta DATE,
    produto_id INT NOT NULL,
    admin_responsavel_id INT,
    FOREIGN KEY (produto_id) REFERENCES Produtos(id_produto),
	FOREIGN KEY (admin_responsavel_id) REFERENCES Usuarios(id_usuario)
);

-- 5. Tabela Marketplace
CREATE TABLE Marketplace (
	id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
    plataforma VARCHAR(80) NOT NULL,
    conteudo_gerado TEXT,
    data_geracao DATE,
    produto_id INT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES Produtos(id_produto)
);

-- 6. Tabela Modificadas
ALTER TABLE usuarios
ADD COLUMN cpf VARCHAR(14) NULL,
ADD COLUMN cnpj VARCHAR(18) NULL,
ADD COLUMN matricula VARCHAR(12) NULL;
