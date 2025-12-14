-- 1. Cria o usuário genérico (O banco gera o ID, ex: 1)
INSERT INTO Usuarios (nome, email, telefone, endereco, senha)
VALUES ('João Produtor', 'joao@email.com', '(91) 1234_5678', ' Rua A', 'senha123');

-- 2. Cria o perfil específico usando o MESMO ID (1)
-- Se você tentar criar com ID 2 sem existir o usua´rio 2, dará erro. 
INSERT INTO Produtores (id_usuario, cpf, registro_rural)
VALUES (1, '123.456.789-00', 'CAF-1234');