-- --- INSERÇÃO DE DADOS  ---

-- 1. Inserindo Usuários
-- Usuário 1: Um Produtor Rural (Dona Maria)
INSERT INTO Usuarios (nome, email, telefone, endereco, senha, tipo, cpf) 
VALUES ('Maria da Silva', 'maria.produtora@email.com', '91999999999', 'Sítio Esperança, Zona Rural', 'senha123', 'produtor', '12345678900');

-- Usuário 2: Uma Empresa Compradora (Mercado Natural Ltda)
INSERT INTO Usuarios (nome, email, telefone, endereco, senha, tipo, cnpj) 
VALUES ('Mercado Natural', 'contato@mercadonatural.com', '91888888888', 'Av. Central, 500, Belém', 'senha123', 'empresa', '12345678000199');

-- Usuário 3: O Administrador do Sistema 
INSERT INTO Usuarios (nome, email, telefone, endereco, senha, tipo, matricula) 
VALUES ('Carlos Auditor', 'admin@amazonia.com', '91777777777', 'Escritório Central', 'admin123', 'admin', 'ADM2025');

-- 2. Inserindo Produtos (Associados ao Produtor Maria - ID 1)
INSERT INTO Produtos (nome, categoria, descricao, preco, status_estoque, usuario_id, imagem) 
VALUES 
('Mel de Abelha Nativa', 'Alimentos', 'Mel puro produzido na região do Baixo Amazonas.', 45.00, 'disponivel', 1),
('Cesto de Palha', 'Artesanato', 'Cesto trançado manualmente com fibra natural.', 30.00, 'disponivel', 1);

-- 3. Inserindo uma Certificação (Solicitação de Selo para o Mel - Produto ID 1)
INSERT INTO Certificacoes (texto_autodeclaracao, documento, status_certificacao, data_envio, produto_id) 
VALUES ('Declaro que o mel é extraído sem aditivos químicos conforme normas.', 'laudo_mel_2025.pdf', 'pendente', '2025-12-13', 1);

-- 4. Inserindo um Anúncio no Marketplace
INSERT INTO Marketplace (plataforma, conteudo_gerado, data_geracao, produto_id)
VALUES ('Mercado Livre', 'Anuncio gerado automaticamente: Mel de Abelha Nativa - 45 reais', '2025-12-13', 1);

-- --- CONSULTA DE DADOS  ---

SELECT id_usuario, nome, tipo, email FROM Usuarios;

-- Consulta: Relatório de Produtos com Nome do Produtor (Teste de Foreign Key)
SELECT 
    p.nome AS Nome_Produto, 
    p.categoria, 
    p.preco, 
    u.nome AS Nome_Produtor, 
    u.tipo AS Tipo_Usuario
FROM Produtos p
INNER JOIN Usuarios u ON p.usuario_id = u.id_usuario;

-- Consulta: Verificar status da Certificação do Produto
SELECT 
    c.id_certificacao,
    p.nome AS Produto,
    c.status_certificacao,
    c.data_envio
FROM Certificacoes c
JOIN Produtos p ON c.produto_id = p.id_produto;