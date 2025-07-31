# 🚀 Intelligent Teaching System V1

A distributed AI teaching system based on Kafka, integrated with variety LLM engines.
See the motivation and architecture diagram in the slides—view the PDF here: [View presentation](./agent-teach-introduce.pdf)
![](/docs/images/demo.gif)

## ✨ Beta version Key Features
**🎯 Beta version Goal: Build a functional, demonstrable, and extensible base system!**
- 🤖 **Multi-LLM Support**: Integrated Gemini & Ollama engines
- 🌍 **Dynamic question Routing**: Detect language and route to specialized agents
- 📊 **Real-Time Cost Tracking**: Detailed token usage and cost monitoring
- 💬 **Interactive CLI**: User-friendly command-line interface
- ⚡ **Distributed Architecture**: Scalable design powered by Kafka

## 🏗️ System Architecture (Target)
 ```
 ┌───────────────┐       ┌────────────────┐
│   Student     │  →    │ producer.py    │  (Student Producer)
│   Producer    │       │ +dynamic_assign│  (router)
└──────┬────────┘       └──────┬─────────┘
       │                        │
       ▼                        ▼
        ┌───────────────────────────┐
        │         Kafka             │  →  kafka_client.py 
        │ (分散式訊息總線，Topic 分類) │      Topic: chinese_teacher, english_teacher
        └──────┬─────────┬─────────┘
               │         │
               │         ▼
               │   ┌─────────────────┐
               │   │   Monitor       │  →  monitor.py (Monitor Consumer)
               │   └─────────────────┘
               │
      ┌────────┴─────────────┐
      │                      │
┌──────────────┐       ┌──────────────┐
│ ChineseAgent  │  →    │ EnglishAgent │  →  chinese_agent.py, english_agent.py, web_search.py
│  (Consumer)   │       │  (Consumer)  │      (Agent Consumer + LLM tools)
└──────┬────────┘       └──────┬────────┘
       │                       │
       ▼                       ▼
  ┌────────────────┐     ┌────────────────┐
  │ Gemini Engine  │  →  │ Gemini Engine  │  →  gemini_engine.py 
  │ + WebSearch    │     │ + WebSearch    │     
  └──────┬─────────┘     └──────┬─────────┘
         ▼                       ▼
   ┌─────────────────────────────────────┐
   │  (Response/Tools/Cost/Response)     │  
   └─────────────────────────────────────┘
 ```

## 📋 Quick Start

### Start & Stop

**Start the system** (Default: Interactive CLI)
    
    docker-compose up

**Stop the system**
    
    docker-compose down

**Enter CLI mode**
    
    docker-compose exec agentic-app python cli.py

---

## 🔧 Required Configuration

Before running, edit `docker-compose.yml` or `.env` to set up required parameters.

### 1. Kafka Configuration
    # # Zookeeper (if separate service)
    - KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'

    # Broker settings
    - KAFKA_BROKER_ID: 1
    - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT

    # Client endpoints
    - KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    - KAFKA_BOOTSTRAP_SERVERS: kafka:29092

    # Topic & group behavior
    - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    - KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
    - KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'

### 2. Gemini Configuration
> Get your [Gemini API Key](https://ai.google.dev/gemini-api/docs?hl=en) first.
    
    # Gemini API Configuration
    - GEMINI_API_KEY=${GEMINI_API_KEY}
    - GEMINI_MODEL=${GEMINI_MODEL:-gemini-1.5-flash}
    # Cost calculation (adjust to match actual pricing)
    - GEMINI_INPUT_COST_PER_1K_TOKENS=${GEMINI_INPUT_COST_PER_1K_TOKENS:-0.000125}
    - GEMINI_OUTPUT_COST_PER_1K_TOKENS=${GEMINI_OUTPUT_COST_PER_1K_TOKENS:-0.000375}

    # System settings
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
    - REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-30}
    - PREFERRED_ENGINE=gemini

### 3. Ollama Configuration
> Install & start [Ollama](https://github.com/ollama/ollama), then pull the model:
    
    ollama pull llama3.1:8b

    # Ollama API Configuration
    - OLLAMA_BASE_URL=http://ollama:11434
    - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.1:8b}

    # Cost calculation (customizable)
    - OLLAMA_INPUT_COST_PER_1K_TOKENS=${OLLAMA_INPUT_COST_PER_1K_TOKENS:-0.0}
    - OLLAMA_OUTPUT_COST_PER_1K_TOKENS=${OLLAMA_OUTPUT_COST_PER_1K_TOKENS:-0.0}

    # System settings
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
    - REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-30}
    - PREFERRED_ENGINE=ollama

---

## 🎯 CLI Usage

**Features:**
- 💬 Ask any question freely
- 🔄 Continuous conversation mode
- 📊 Real-time cost display
- 🌐 Automatic language detection & routing
- ⌨️ Type 'quit' or 'exit' to leave

**Example:**
    
    🤖 Intelligent Teaching System V1
    Enter your question ('quit' to exit): What is deep learning?

    🧑‍🏫 English Teacher Answer:
    Deep learning is a subset of machine learning...

    💰 Cost Info:
    - Input tokens: 15
    - Output tokens: 200
    - Total cost: $0.003

---

## 🛠️ Development Guide

### Project Structure
    
    agentic-teaching-kafka/
    ├── cli.py                    # Interactive CLI entry
    ├── requirements.txt          # Python dependencies
    ├── docker-compose.yml        # Kafka + Gemini environment
    ├── docker-compose-ollama.yml # Kafka + Ollama environment
    ├── .env                      # Environment config
    ├── src/
    │   ├── core/                 # Core components
    │   │   ├── models.py         # Data models
    │   │   ├── config.py         # Configuration management
    │   │   └── kafka_client.py   # Kafka client
    │   ├── llm/                  # LLM engines
    │   │   ├── base_engine.py    # Base interface
    │   │   ├── gemini_engine.py  # Gemini implementation
    │   │   └── ollama_engine.py  # Ollama implementation
    │   ├── agents/               # Agent system
    │   │   ├── base_agent.py     # Base agent
    │   │   ├── chinese_agent.py  # Chinese teacher
    │   │   └── english_agent.py  # English teacher
    │   ├── producer.py           # Message producer
    │   ├── consumer.py           # Consumer management
    │   └── monitor.py            # Cost monitor

---

## 🚀 Future Work

- **Tool integration**: Web search, calculator, and other external utilities for enhanced reasoning  
- **Access control**: API key management, user authentication, and role-based authorization  
- **Web interface**: Browser-based UI for Q&A interaction and system monitoring  
- **Advanced monitoring**: Detailed analytics including agent health, queue metrics, and cost reports  
- **Intelligent auto problem assigner**: Dynamic task routing to the most suitable agents based on problem type and complexity  
- **Multi-agent expansion**: Support for more domain-specific teachers (e.g., legal, medical, technical experts)  
- **Cross-teacher self-aggregation**: Combine insights from multiple agents into a single, coherent answer using a self-aggregation mechanism for improved response quality  


---

## 📄 License
MIT License

---


