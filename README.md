# Celery - Sistema Distribuído com Django e Celery

Um sistema de processamento distribuído para consulta de preços de ações em tempo real utilizando Django, Celery e RabbitMQ.

## 📋 Sobre o Projeto

Este projeto implementa um sistema distribuído que utiliza tarefas assíncronas para consultar preços de ações na web. A arquitetura é baseada em:

- **Django**: Framework web para o backend e API REST
- **Celery**: Sistema de filas para processamento assíncrono de tarefas
- **RabbitMQ**: Message broker para gerenciamento de filas
- **Selenium**: Automação web para coleta de dados de preços de ações

## 🚀 Configuração do Ambiente

### Pré-requisitos

- Python 3.8+
- Docker
- Navegador Chrome (para o Selenium)

### Dependências Principais

O projeto utiliza as seguintes bibliotecas principais:
- Django 5.2.2
- Celery 5.5.3
- Django REST Framework 3.16.0
- Django Celery Beat 2.8.1
- Django Celery Results 2.6.0
- Selenium 4.33.0
- WebDriver Manager 4.0.2

Todas as dependências estão listadas no arquivo `requirements.txt`.

### Instalação

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd celery2
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Aplique as migrações:
   ```bash
   python manage.py migrate
   ```

5. Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```

## 🐇 Iniciando o RabbitMQ

Execute o RabbitMQ usando Docker:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

Após iniciar, o RabbitMQ estará disponível em:
- Interface de gerenciamento: http://localhost:15672 (usuário: guest, senha: guest)
- Porta AMQP: 5672

## 🔄 Iniciando o Celery

1. Inicie o worker do Celery:
   ```bash
   celery -A core worker -l INFO
   ```

2. Inicie o Celery Beat para tarefas agendadas:
   ```bash
   celery -A core beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

## 🌐 Iniciando o Servidor Django

```bash
python manage.py runserver
```

O servidor estará disponível em: http://127.0.0.1:8000/

## 📱 API REST

A API permite consultar preços de ações e disparar tarefas assíncronas:

### Consultar Preços de Ações
- **GET** `/stocks/`
  - Retorna a lista de todas as ações consultadas e seus preços

### Disparar Consulta de Preço
- **POST** `/stocks/`
  - Parâmetros (JSON):
    ```json
    {
        "stock_name": "PETR4"
    }
    ```
  - Dispara uma tarefa assíncrona para consultar o preço da ação especificada
  - Exemplo com curl:
    ```bash
    curl -X POST http://localhost:8000/stocks/ -H "Content-Type: application/json" -d '{"stock_name":"PETR4"}'
    ```

## 📊 Painel Administrativo

O painel administrativo está disponível em: http://127.0.0.1:8000/admin/

- Acesse com o superusuário criado anteriormente
- No painel, você pode:
  - Visualizar e gerenciar ações e preços registrados
  - Configurar tarefas periódicas pelo Django Celery Beat
  - Monitorar resultados de tarefas pelo Django Celery Results

## 🔄 Fluxo de Funcionamento

1. O usuário solicita a consulta de preço de uma ação via API
2. Django recebe a solicitação e envia uma tarefa para o Celery
3. RabbitMQ gerencia a fila de tarefas
4. O worker do Celery processa a tarefa:
   - Utiliza Selenium para consultar o preço da ação no Google Finance
   - Salva o resultado no banco de dados
5. Os resultados ficam disponíveis via API REST e painel administrativo

## 💡 Potencial e Versatilidade

Este projeto demonstra um exemplo simples de consulta de preços de ações, mas o poder do Django combinado com Celery vai muito além:

### Possibilidades de Tarefas Assíncronas

- **Processamento de Dados em Lote**: Tratamento de grandes volumes de dados sem impactar a experiência do usuário
- **Geração de Relatórios**: Criação de relatórios complexos em background
- **Integração com APIs Externas**: Comunicação com múltiplos serviços sem bloqueio
- **Envio de E-mails em Massa**: Notificações e campanhas de marketing
- **Processamento de Mídia**: Conversão, compressão e análise de imagens e vídeos
- **Machine Learning**: Execução de modelos de predição e classificação
- **Web Scraping em Escala**: Coleta automatizada de dados de múltiplas fontes
- **Sincronização com Sistemas Externos**: Integração com ERPs, CRMs e outros sistemas

### Benefícios do Agendamento

O sistema de agendamento do Celery Beat permite:
- Execução periódica de tarefas (minutos, horas, dias)
- Agendamento baseado em expressões cron
- Execução em horários específicos (fora do horário comercial)
- Distribuição de carga em horários de menor tráfego
- Tarefas recorrentes com diferentes prioridades

### Escalabilidade

A arquitetura distribuída permite:
- Executar workers em diferentes máquinas
- Escalar horizontalmente conforme a demanda
- Separar workers por tipos de tarefas
- Implementar balanceamento de carga
- Monitoramento e recuperação automática de falhas

Este exemplo simples demonstra os fundamentos da computação distribuída com Django e Celery, mas as possibilidades são praticamente ilimitadas para construir sistemas robustos, escaláveis e de alta performance.

## 📝 Tarefas Suportadas

- **get_stock_price**: Consulta o preço de uma ação específica usando Selenium
  - Aceita códigos de ações brasileiras como PETR4, VALE3, ITUB4, etc.
  - Utiliza web scraping com Selenium para obter os preços atualizados
  - Salva os resultados no banco de dados com timestamp

## 🛠️ Personalização

### Agendamento de Tarefas

Você pode configurar tarefas periódicas através do painel administrativo:

1. Acesse http://127.0.0.1:8000/admin/
2. Navegue até Django Celery Beat > Periodic Tasks
3. Adicione uma nova tarefa periódica, configurando:
   - Nome da tarefa
   - Tarefa a ser executada (ex: `stocks.tasks.get_stock_price`)
   - Argumentos (ex: `["PETR4"]`)
   - Intervalo de execução

### Adicionando Novas Ações

Para adicionar novas ações para monitoramento:
1. Use a API REST para disparar uma consulta para o código da ação desejada
2. Configure tarefas periódicas para atualizar automaticamente os preços

## ⚠️ Solução de Problemas

- **RabbitMQ não conecta**: Verifique se o container Docker está rodando corretamente
- **Celery não processa tarefas**: Verifique logs do Celery e conexão com RabbitMQ
- **Erro no Selenium**: Certifique-se que o ChromeDriver está instalado e compatível com sua versão do Chrome
- **Tarefas não executando**: Verifique se o worker e o beat do Celery estão rodando

## 📚 Recursos Adicionais

- [Documentação do Django](https://docs.djangoproject.com/)
- [Documentação do Celery](https://docs.celeryq.dev/)
- [Documentação do RabbitMQ](https://www.rabbitmq.com/documentation.html) 