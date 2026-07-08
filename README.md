# Technical Architecture & Developer Guide
---
This document explains the internal architecture, system design, data flow, deployment strategy, and implementation details of the SIAGE AI Document Intelligence Platform.

---

### Table of Contents
1. [Introduction](#1-introduction)
2. [Technology Stack](#2-technology-stack)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deployment Architecture](#4-deployment-architecture)
5. [Database Architecture](#5-database-architecture)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Knowledge Base Ingestion Pipeline](#7-knowledge-base-ingestion-pipeline)
8. [User Query Pipeline](#8-user-query-pipeline)
9. [AI Core & Prompt Processing Subsystem](#9-ai-core--prompt-processing-subsystem)
10. [API Architecture](#10-api-architecture)
11. [Backend Project Structure](#11-backend-project-structure)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Deployment & Infrastructure](#13-deployment--infrastructure)
14. [Security Considerations](#14-security-considerations)
15. [Performance Optimizations](#15-performance-optimizations)
16. [Future Enhancements](#16-future-enhancements)
17. [Developer Guidelines](#17-developer-guidelines)
18. [Development Environment Setup](#18-development-environment-setup)
19. [Docker Containerization](#19-docker-containerization)
20. [Building the Docker Image](#20-building-the-docker-image)
21. [Running the Docker Container](#21-running-the-docker-container)
22. [Docker Compose](#22-docker-compose)
23. [NGINX Reverse Proxy](#23-nginx-reverse-proxy)
24. [Production Deployment (AWS EC2)](#24-production-deployment-aws-ec2)
25. [Production Architecture & Request Flow](#25-production-architecture--request-flow)
26. [Summary & Conclusion](#26-summary--conclusion)

---

### 1. Introduction

#### Purpose
SIAGE AI is an enterprise-grade Retrieval-Augmented Generation (RAG) platform designed to provide intelligent access to organizational documentation through natural language conversations.
Unlike traditional chatbots, SIAGE AI separates knowledge management from knowledge consumption. Administrators are responsible for uploading and indexing technical documentation, structured data, and spreadsheets, while authenticated users interact only with the indexed knowledge base.
This architecture ensures that AI-generated responses remain grounded in approved organizational documents, improving accuracy, traceability, and maintainability.

---

### 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Angular | User Interface |
| **Reverse Proxy** | NGINX | Request Routing & SSE Optimization |
| **Backend** | FastAPI | REST APIs |
| **ASGI Server** | Uvicorn | Asynchronous Process Server |
| **AI Provider** | Anthropic Claude API (Sonnet 4.6) | Contextual Grounded Response Generation |
| **Embedding Model**| FastEmbed (`all-MiniLM-L6-v2`) | 384-Dimensional Semantic Embeddings |
| **Object Storage** | AWS S3 | Secure, Durable Storage of Raw PDFs, CSVs, and XLSX source files |
| **Database** | PostgreSQL | Relational Application Storage |
| **Vector Engine** | pgvector extension | Native Vector Spatial Similarity Search |
| **ORM** | SQLAlchemy | Database Access Layer |
| **Authentication** | JWT + OTP | Multi-stage Identity Validation |
| **Data Processing**| PyMuPDF, Pandas, OpenPyXL | Multi-format File Parsing Engine |

---

### 3. High-Level Architecture

#### Overview

SIAGE AI follows a layered client-server architecture built around a **Retrieval-Augmented Generation (RAG)** workflow. The system separates the presentation layer, application logic, AI processing, semantic retrieval, and storage services into independent components, allowing each layer to scale and evolve independently.

The architecture consists of five logical layers:

- Presentation Layer
- Reverse Proxy Layer
- Application Layer (FastAPI)
- AI Processing Layer (FastEmbed + Anthropic API)
- Data & Storage Layer (PostgreSQL + pgvector + AWS S3)

---

### High-Level Architecture Diagram

```mermaid
graph TD

    subgraph Presentation Layer
        A[Angular UI Client]
    end

    subgraph Reverse Proxy Layer
        B[NGINX Reverse Proxy]
    end

    subgraph Application Layer
        C[FastAPI Backend Server]
    end

    subgraph AI Processing Layer
        D[FastEmbed Vectorizer]
        E[Anthropic Claude 4.6 API]
    end

    subgraph Data & Storage Layer
        F[(PostgreSQL + pgvector)]
        G[AWS S3 File Storage]
    end

    A <--> |HTTPS / SSE Streaming| B
    B <--> |Internal Proxy Routing| C
    C <--> |Generate Embeddings| D
    C <--> |Context + Prompt| E
    C <--> |SQL Queries & Vector Search| F
    C <--> |File Uploads & Retrieval| G
```

---

### Layer Responsibilities

#### 1. Presentation Layer

The **Angular frontend** provides the primary user interface for both administrators and end users.

Its responsibilities include:

- User authentication and login
- Chat interface
- Real-time streaming response rendering (Server-Sent Events)
- Chat session management
- Document upload interface
- Administrative dashboard
- Analytics and reporting views
- User management

The frontend never communicates directly with databases or AI services. Every request is routed through the reverse proxy to the backend API.

---

### 2. Reverse Proxy Layer

**NGINX** acts as the application's public entry point.

Primary responsibilities include:

- Serving the production Angular build
- Reverse proxying API requests to FastAPI
- Supporting Server-Sent Events (SSE)
- Handling large document uploads (up to 100 MB)
- HTTPS termination
- Same-origin routing to eliminate Cross-Origin Resource Sharing (CORS) issues
- Static asset caching

This layer isolates backend services from direct internet exposure while improving overall application performance.

---

### 3. Application Layer

The **FastAPI backend** contains the core business logic of SIAGE AI.

Its responsibilities include:

- Authentication and authorization
- User session management
- Chat history persistence
- Document ingestion pipelines
- PDF parsing
- CSV processing
- Excel processing
- Embedding generation orchestration
- Vector similarity search
- Prompt construction
- Streaming AI responses
- Administrative APIs
- Analytics generation

The backend is implemented using asynchronous endpoints, enabling efficient handling of multiple concurrent users.

---

### 4. AI Processing Layer

The AI Processing Layer transforms enterprise documents into semantic vectors and generates grounded AI responses.

It consists of two primary components:

#### FastEmbed

FastEmbed is responsible for:

- Converting text chunks into vector embeddings
- Creating embeddings during document ingestion
- Generating query embeddings during user searches
- Performing lightweight and efficient embedding generation suitable for production deployments

#### Anthropic Claude API

The backend communicates with Anthropic Claude to generate natural language responses.

Claude receives:

- User query
- Retrieved document context
- Conversation history
- System prompt

Instead of relying solely on pretrained knowledge, Claude grounds its responses using enterprise documentation retrieved from the vector database.

This Retrieval-Augmented Generation (RAG) approach significantly reduces hallucinations while ensuring responses remain relevant to the uploaded knowledge base.

---

### 5. Data & Storage Layer

SIAGE AI uses a decoupled storage architecture to separate structured metadata from raw document storage.

#### PostgreSQL + pgvector

PostgreSQL stores:

- User accounts
- Authentication data
- Chat sessions
- Chat history
- Document metadata
- Text chunks
- Vector embeddings
- Analytics data
- Administrative records

The **pgvector** extension enables semantic similarity searches directly within PostgreSQL without requiring a separate vector database.

#### AWS S3

AWS S3 stores the original uploaded documents, including:

- PDF files
- CSV files
- Excel workbooks
- Other supported enterprise documents

Only metadata and extracted text are maintained within PostgreSQL, while raw binary files remain in S3. This design minimizes EC2 storage usage, improves scalability, and enables secure file retrieval using pre-signed URLs.

---

### Architectural Benefits

This layered architecture provides several advantages:

- Clear separation of concerns between frontend, backend, AI services, and storage
- Independent scalability of each layer
- Improved security through isolated service boundaries
- Efficient semantic search using pgvector
- Reduced infrastructure costs by offloading document storage to AWS S3
- Real-time streaming responses through Server-Sent Events (SSE)
- Simplified deployment using Docker and NGINX
- High maintainability through modular component design
- Enterprise-ready architecture suitable for production environments

### 4. Deployment Architecture

#### Overview

SIAGE AI is deployed on **Amazon Web Services (AWS)** using a containerized architecture designed for scalability, security, and maintainability. The application runs on an **AWS EC2** instance where the frontend, backend, and reverse proxy are orchestrated using Docker Compose.

A single **NGINX** reverse proxy serves as the public entry point, exposing the application over **HTTP (port 80)** and **HTTPS (port 443)**. NGINX routes frontend requests to the Angular application and securely proxies API requests to the FastAPI backend.

The backend communicates with multiple cloud services to support document processing, semantic search, and AI-powered responses:

- **AWS RDS PostgreSQL** stores relational data, chat history, metadata, and vector embeddings using the **pgvector** extension.
- **AWS S3** stores uploaded documents and other binary assets, reducing storage requirements on the EC2 instance.
- **Anthropic Claude API** is accessed over secure HTTPS connections to generate context-aware responses using enterprise knowledge retrieved through the RAG pipeline.

This deployment architecture separates compute, database, object storage, and AI services into independent components, improving scalability, reliability, and operational flexibility while minimizing infrastructure complexity.

### 5. Database Architecture

#### 5.1 Overview

SIAGE AI uses **PostgreSQL** as a unified database for both application data and semantic vector embeddings. By leveraging the **pgvector** extension, the system performs vector similarity searches directly within PostgreSQL, eliminating the need for a separate vector database.

This architecture provides several advantages:

- Single-source storage for structured and vector data
- ACID-compliant transactions for data consistency
- Native SQL joins between application tables and vector embeddings
- Simplified infrastructure and reduced operational costs
- Efficient semantic retrieval using pgvector indexes

---

### 5.2 Database Domains

The database schema is organized into two primary operational domains.

#### User Domain

The User Domain manages authentication, authorization, and conversational state.

#### `users`

Stores user account information, authentication credentials, roles, and OTP-related data.

#### `chat_sessions`

Maintains chat sessions belonging to individual users.

#### `messages`

Stores the complete conversation history, including user prompts, assistant responses, and source page references.

---

### Knowledge Base Domain

The Knowledge Base Domain manages enterprise documents and semantic search.

#### `manuals`

Stores metadata for uploaded documents, including storage locations and indexing status.

#### `manual_page_texts`

Stores extracted document content along with vector embeddings used for semantic retrieval.

---

### Entity Relationship Diagram

```mermaid
erDiagram

    USERS {
        VARCHAR id PK
        VARCHAR username UK
        VARCHAR email UK
        VARCHAR role
        VARCHAR current_otp
        TIMESTAMP otp_expires_at
    }

    CHAT_SESSIONS {
        VARCHAR id PK
        VARCHAR user_id FK
        VARCHAR title
        TIMESTAMP updated_at
    }

    MESSAGES {
        INT id PK
        VARCHAR session_id FK
        VARCHAR role
        TEXT content
        VARCHAR matched_pages_string
    }

    MANUALS {
        INT id PK
        VARCHAR file_id UK
        VARCHAR name
        VARCHAR file_type
        VARCHAR s3_bucket
        VARCHAR s3_key
        VARCHAR indexing_status
    }

    MANUAL_PAGE_TEXTS {
        INT id PK
        INT manual_id FK
        INT page_number
        TEXT page_text
        STRING embedding
    }

    USERS ||--o{ CHAT_SESSIONS : owns
    CHAT_SESSIONS ||--o{ MESSAGES : contains
    MANUALS ||--o{ MANUAL_PAGE_TEXTS : contains
```

---

### 5.3 Schema Reference

#### Table: `users`

| Column | Type | Description |
|----------|------|-------------|
| id | VARCHAR | Primary key. Unique user identifier. |
| username | VARCHAR | Unique username used for authentication. |
| full_name | VARCHAR | User's display name. |
| email | VARCHAR | Unique email address. |
| phone | VARCHAR | Contact phone number. |
| role | VARCHAR | User role (e.g., `user`, `admin`). |
| status | VARCHAR | Account status (`active`, `disabled`). |
| avatar_url | VARCHAR | Profile image URL or storage path. |
| created_at | TIMESTAMP | Account creation timestamp. |
| current_otp | VARCHAR | Active OTP value for authentication. |
| otp_expires_at | TIMESTAMP | OTP expiration timestamp. |

---

#### Table: `chat_sessions`

| Column | Type | Description |
|----------|------|-------------|
| id | VARCHAR | Primary key. Unique chat session identifier. |
| user_id | VARCHAR | Foreign key referencing `users.id`. |
| title | VARCHAR | Automatically generated chat title. |
| created_at | TIMESTAMP | Session creation timestamp. |
| updated_at | TIMESTAMP | Timestamp of the most recent activity. |

---

#### Table: `messages`

| Column | Type | Description |
|----------|------|-------------|
| id | SERIAL | Primary key. |
| session_id | VARCHAR | Foreign key referencing `chat_sessions.id`. |
| role | VARCHAR | Message author (`user` or `assistant`). |
| content | TEXT | Complete message content. |
| matched_pages_string | VARCHAR | Serialized list of matched document pages. |
| timestamp | TIMESTAMP | Message creation timestamp. |

---

#### Table: `manuals`

| Column | Type | Description |
|----------|------|-------------|
| id | SERIAL | Primary key. |
| file_id | VARCHAR | Public document identifier. |
| name | VARCHAR | Display name of the document. |
| filename | VARCHAR | Original uploaded filename. |
| s3_bucket | VARCHAR | AWS S3 bucket containing the document. |
| s3_key | VARCHAR | Object key within the S3 bucket. |
| file_type | VARCHAR | File format (`.pdf`, `.csv`, `.xlsx`). |
| uploaded_by | VARCHAR | Administrator who uploaded the document. |
| indexing_status | VARCHAR | Current indexing status (`uploading`, `processing`, `indexed`). |
| uploaded_at | TIMESTAMP | Upload timestamp. |

---

#### Table: `manual_page_texts`

| Column | Type | Description |
|----------|------|-------------|
| id | SERIAL | Primary key. |
| manual_id | INT | Foreign key referencing `manuals.id`. |
| page_number | INT | PDF page number or worksheet/chunk identifier. |
| page_text | TEXT | Extracted document text or structured table content. |
| embedding | VECTOR(384) | 384-dimensional vector embedding generated by FastEmbed. |

---

### 5.4 Page and Chunk-Level Indexing

To maximize retrieval accuracy while preserving document traceability, SIAGE AI indexes content at logical verification boundaries.

#### PDF Documents

Each embedding corresponds to a single physical page of the document. This allows the system to cite exact page numbers when generating responses.

#### CSV and Excel Documents

Structured datasets are divided into semantic chunks rather than individual rows.

Each chunk typically contains:

- 20–30 related rows
- Worksheet metadata
- Column headers
- Contextual schema information

Including header information within every chunk preserves the semantic meaning of tabular data and enables Claude to accurately interpret structured datasets during retrieval.

This strategy also allows the frontend to reconstruct and display the original table sections referenced by the AI.

---

### 5.5 Vector Indexing

To ensure high-performance semantic search as document collections grow, SIAGE AI uses PostgreSQL's **HNSW (Hierarchical Navigable Small World)** approximate nearest-neighbor index provided by the **pgvector** extension.

This index significantly reduces query latency by avoiding full-table sequential scans while maintaining high retrieval accuracy.

#### Create HNSW Index

```sql
CREATE INDEX IF NOT EXISTS hsnw_page_embedding_idx
ON manual_page_texts
USING hnsw (embedding vector_cosine_ops);
```

---

### 5.6 Semantic Search Query

The following query retrieves the most relevant document chunks by comparing the query embedding against stored vector embeddings using cosine distance.

```sql
SELECT
    manual_id,
    page_number,
    page_text,
    1 - (embedding <=> :query_embedding) AS similarity_score
FROM manual_page_texts
WHERE manual_id = ANY(:allowed_manual_ids)
ORDER BY embedding <=> :query_embedding
LIMIT :limit_count;
```

The query returns:

- Matching document identifier
- Source page or chunk number
- Retrieved document text
- Cosine similarity score

The retrieved context is then passed to the Retrieval-Augmented Generation (RAG) pipeline, where it is used to ground responses generated by the Anthropic Claude API.

### 6. Authentication & Authorization

#### Overview

SIAGE AI implements a secure **two-stage authentication mechanism** that combines credential validation with One-Time Password (OTP) verification. After successful authentication, the system issues a **JSON Web Token (JWT)**, which is required to access all protected API endpoints.

Role-Based Access Control (RBAC) is used to restrict access to administrative features while allowing standard users to interact with the chat application securely.

---

#### Authentication Flow

```mermaid
flowchart LR

    A[User Login]
    B[POST /api/v1/auth/login]
    C[Validate Username & Password]
    D[Generate & Send OTP]
    E[POST /api/v1/auth/verify-otp]
    F[Verify OTP]
    G[Generate JWT]
    H[Authenticated Session]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

---

#### Stage 1: Credential Validation

The authentication process begins when a user submits their username and password through the login endpoint.

**Endpoint**

```http
POST /api/v1/auth/login
```

The backend performs the following actions:

- Validates the supplied username and password.
- Confirms that the user account is active.
- Generates a One-Time Password (OTP).
- Stores the OTP and its expiration timestamp.
- Delivers the OTP through the configured authentication channel.

If the credentials are invalid, authentication is rejected immediately.

---

#### Stage 2: OTP Verification

After receiving the OTP, the client submits it for verification.

**Endpoint**

```http
POST /api/v1/auth/verify-otp
```

The backend:

- Verifies the OTP.
- Confirms that it has not expired.
- Invalidates the OTP after successful verification.
- Generates a signed JSON Web Token (JWT).
- Returns the JWT to the client.

The client securely stores this token and includes it in all subsequent authenticated requests.

---

### JWT Authorization

Protected endpoints require a valid JWT in the HTTP Authorization header.

```http
Authorization: Bearer <jwt_token>
```

For every protected request, the backend:

1. Validates the JWT signature.
2. Checks token expiration.
3. Extracts user identity and role.
4. Grants or denies access based on role permissions.

Requests with missing, invalid, or expired tokens are rejected with an authentication error.

---

### Role-Based Access Control (RBAC)

SIAGE AI defines two primary user roles.

#### User

Standard users can:

- Access the AI chat interface
- Create and manage chat sessions
- View conversation history
- Retrieve document citations and source pages
- Query indexed enterprise documents

#### Administrator

Administrators have all user permissions in addition to:

- Uploading documents
- Managing the knowledge base
- Monitoring document indexing
- Viewing analytics dashboards
- Managing user accounts
- Accessing administrative APIs

This separation ensures that sensitive management operations remain restricted to authorized personnel.

---

### 7. Knowledge Base Ingestion Pipeline

#### Overview

SIAGE AI supports automated ingestion of multiple enterprise document formats, including **PDF**, **CSV**, and **Microsoft Excel (.xlsx)** files.

The ingestion pipeline extracts document content, generates semantic vector embeddings, and stores both structured metadata and embeddings within PostgreSQL while offloading original files to AWS S3.

---

#### Ingestion Workflow

```mermaid
flowchart TD

    A[Administrator Uploads Document]
    B[Upload File to AWS S3]
    C[Create Database Metadata Record]
    D{Detect File Type}

    E[Extract PDF Text<br/>PyMuPDF]
    F[Parse CSV / Excel<br/>Pandas + OpenPyXL]

    G[Generate 384-Dimensional Embeddings<br/>FastEmbed]
    H[Store Text & Embeddings<br/>PostgreSQL + pgvector]
    I[Update Status to Indexed]

    A --> B
    B --> C
    C --> D
    D -->|PDF| E
    D -->|CSV / XLSX| F
    E --> G
    F --> G
    G --> H
    H --> I
```

---

#### Step 1: Document Upload

An administrator uploads a supported document through the document management interface.

**Endpoint**

```http
POST /admin/documents/upload
```

The FastAPI backend streams the uploaded file directly into the configured **AWS S3** bucket using the AWS SDK (`boto3`), minimizing local storage usage on the application server.

---

#### Step 2: Metadata Registration

After the upload completes, the backend creates a new record in the `manuals` table.

The record contains:

- Document identifier
- File name
- File type
- AWS S3 bucket name
- S3 object key
- Upload timestamp
- Current indexing status (`processing`)

This metadata enables the ingestion pipeline to track document processing independently from file storage.

---

#### Step 3: Document Parsing

The parser selected depends on the uploaded file type.

#### PDF Documents

PDF files are processed using **PyMuPDF**, which extracts text page by page while preserving page numbering for accurate source citations.

#### CSV and Excel Documents

Structured datasets are processed using **Pandas** and **OpenPyXL**.

The pipeline:

- Reads worksheets
- Extracts structured rows
- Divides data into semantic chunks
- Includes column headers within each chunk
- Converts each chunk into a structured Markdown representation

Embedding the schema within every chunk preserves contextual relationships during semantic retrieval.

---

### Step 4: Embedding Generation

Each extracted page or structured table chunk is converted into a **384-dimensional vector embedding** using **FastEmbed**.

These embeddings provide the semantic representation required for vector similarity search within the RAG pipeline.

---

### Step 5: Database Storage

After embedding generation, the backend stores:

- Extracted text
- Structured table content
- Page or chunk identifiers
- Vector embeddings

inside the `manual_page_texts` table.

The original document remains securely stored in **AWS S3**, while PostgreSQL contains only metadata, extracted content, and embeddings.

---

### Step 6: Index Activation

When ingestion completes successfully, the document status is updated from:

```
processing
```

to

```
indexed
```

Only documents marked as **indexed** become searchable through the semantic retrieval engine.

If an error occurs during parsing or embedding generation, the document status is changed to:

```
failed
```

Failed documents are excluded from production search results until they are reprocessed or replaced, ensuring that incomplete or corrupted data does not affect retrieval quality.

### 8. User Query Pipeline

#### Overview

The User Query Pipeline is the core Retrieval-Augmented Generation (RAG) workflow within SIAGE AI. It transforms a user's natural language question into a grounded AI response by retrieving relevant enterprise knowledge before invoking the Anthropic Claude API.

The pipeline performs authentication, semantic retrieval, prompt construction, response generation, real-time streaming, and conversation persistence.

---

#### Query Processing Sequence

```mermaid
sequenceDiagram
    autonumber

    participant U as User UI
    participant F as FastAPI Backend
    participant V as FastEmbed
    participant P as PostgreSQL (pgvector)
    participant S as AWS S3
    participant C as Anthropic Claude API

    U->>F: Question + JWT Token (SSE Request)

    F->>F: Validate JWT & Session

    F->>V: Generate Query Embedding
    V-->>F: 384-Dimensional Vector

    F->>P: HNSW Vector Similarity Search
    P-->>F: Top Matching Pages / Chunks

    F->>S: Generate Pre-signed URLs
    S-->>F: Temporary Secure URLs

    F->>F: Build RAG Prompt

    F->>C: Send Prompt + Context
    C-->>F: Streaming Response Tokens

    F-->>U: Server-Sent Events (SSE)

    F->>P: Save Chat History & Citations
```

---

### Query Processing Stages

#### 1. Session Validation

When a user submits a question, the FastAPI backend first validates the request.

The backend:

- Verifies the JWT signature.
- Confirms that the token has not expired.
- Identifies the authenticated user.
- Validates ownership of the requested chat session.
- Ensures the user has permission to access the requested resources.

Only authenticated requests continue through the retrieval pipeline.

---

#### 2. Query Embedding Generation

The user's natural language query is transformed into a semantic vector representation using the same embedding model employed during document ingestion.

**Embedding Model**

- FastEmbed
- `all-MiniLM-L6-v2`
- 384-dimensional embedding vector

Using the same embedding space for both documents and queries ensures meaningful similarity comparisons.

---

##### 3. Semantic Vector Search

The generated query embedding is compared against the indexed document embeddings stored within PostgreSQL.

Using the **pgvector** extension and an **HNSW** approximate nearest-neighbor index, the system retrieves the most semantically relevant document pages or structured data chunks.

Each result includes:

- Document identifier
- Page or chunk number
- Extracted text
- Similarity score

These retrieved results form the contextual knowledge used for AI response generation.

---

#### 4. Secure Citation Resolution

For each retrieved document, the backend generates temporary **AWS S3 pre-signed URLs**.

These URLs:

- Provide secure access to source documents
- Allow the frontend to display referenced pages or files
- Expire automatically after a configurable duration (typically 15 minutes)
- Prevent direct public access to the S3 bucket

This approach enables secure document viewing while maintaining strict access control.

---

#### 5. Prompt Construction

The backend assembles a Retrieval-Augmented Generation (RAG) prompt containing:

- System instructions
- User query
- Previous conversation history
- Retrieved document pages
- Structured table data
- Source metadata

This consolidated prompt provides Claude with the necessary context to generate grounded and accurate responses.

---

#### 6. AI Response Generation

The constructed prompt is sent to the Anthropic Claude API over a secure HTTPS connection.

Rather than relying solely on pretrained knowledge, Claude generates responses based on the retrieved enterprise documentation supplied by the backend.

This grounding process improves factual accuracy and reduces hallucinations.

---

#### 7. Real-Time Response Streaming

Claude returns its response as a continuous stream of tokens.

The FastAPI backend immediately forwards these tokens to the frontend using **Server-Sent Events (SSE)**, allowing users to see responses appear progressively in real time without waiting for the complete response.

The frontend simultaneously renders:

- Generated text
- Citation references
- Links to source documents

---

#### 8. Conversation Persistence

After the streaming response completes, the backend stores the interaction in PostgreSQL.

The following information is persisted:

- User question
- Assistant response
- Chat session identifier
- Retrieved document references
- Source page numbers
- Citation metadata
- Timestamp

This ensures that conversation history can be retrieved in future sessions and that every AI response remains traceable to its supporting source documents.

---

#### Pipeline Summary

The complete query lifecycle consists of the following stages:

1. User authentication and session validation
2. Query embedding generation using FastEmbed
3. Semantic similarity search with PostgreSQL and pgvector
4. Secure source document resolution through AWS S3
5. Retrieval-Augmented prompt construction
6. Response generation using Anthropic Claude
7. Real-time streaming via Server-Sent Events (SSE)
8. Persistent storage of conversation history and citations

### 9. AI Core & Prompt Processing Subsystem

#### 9.1 Overview

The AI Core is responsible for transforming retrieved enterprise knowledge into accurate, context-aware responses. It combines semantic retrieval with a Large Language Model (LLM) using a **Retrieval-Augmented Generation (RAG)** workflow.

The subsystem consists of two primary components:

- **FastEmbed** for semantic embedding generation
- **Anthropic Claude Sonnet 4.6** for grounded response generation

A Prompt Builder acts as the bridge between the retrieval engine and the LLM, ensuring that responses are generated only from verified enterprise documentation.

---

### 9.2 Prompt Builder

#### Overview

The Prompt Builder assembles all information required by the LLM before sending a request to the Anthropic Claude API.

Rather than forwarding only the user's question, it constructs a structured prompt containing system instructions, retrieved document context, conversation history, and the current query.

This approach ensures that responses remain grounded in enterprise knowledge while maintaining conversational continuity.

---

### Prompt Structure

#### 1. System Instructions

The system prompt defines the behavior expected from the language model.

It instructs Claude to:

- Answer only using the retrieved document context.
- Avoid generating unsupported information.
- Respond with **"Information not found in the provided documents."** when sufficient evidence is unavailable.
- Correctly interpret Markdown tables generated from CSV and Excel files.
- Preserve factual accuracy throughout the response.

These instructions help reduce hallucinations and ensure responses remain traceable to uploaded documentation.

---

#### 2. Retrieved Context

The backend injects the highest-ranking document pages or structured table chunks retrieved from the semantic search process.

Each context block may contain:

- PDF page text
- Markdown tables
- Spreadsheet data
- Document metadata
- Source page references

The retrieved context is ordered by semantic similarity score before being passed to the language model.

---

#### 3. Conversation History

To support multi-turn conversations, previous chat messages are included in the prompt.

This enables Claude to:

- Maintain conversational context
- Resolve follow-up questions
- Interpret references to earlier responses
- Generate coherent long-running conversations

---

#### 4. User Query

Finally, the user's current question is appended to the prompt.

Claude receives the complete prompt and generates a response based on:

- System instructions
- Retrieved enterprise knowledge
- Conversation history
- Current user query

---

### 9.3 AI Processing Workflow

```mermaid
graph LR

    A[User Query]
    B[FastEmbed<br/>all-MiniLM-L6-v2]
    C[(PostgreSQL<br/>pgvector)]
    D[Prompt Builder]
    E[Anthropic Claude Sonnet 4.6]
    F[Streaming Response]

    A -->|Generate Embedding| B
    B -->|Vector Search| C
    C -->|Retrieved Context| D
    D -->|Grounded Prompt| E
    E -->|Server-Sent Events| F
```

---

### 9.4 Embedding Model

#### FastEmbed (all-MiniLM-L6-v2)

FastEmbed is responsible for converting textual content into dense numerical vector representations used for semantic similarity search.

#### Model Characteristics

| Property | Value |
|-----------|-------|
| Model | all-MiniLM-L6-v2 |
| Framework | FastEmbed |
| Runtime | ONNX Runtime |
| Embedding Size | 384 Dimensions |
| Purpose | Semantic Text Embeddings |

---

#### Responsibilities

FastEmbed is used during two stages of the RAG pipeline:

#### Document Ingestion

During document indexing, every extracted page or structured table chunk is converted into a 384-dimensional embedding and stored within PostgreSQL.

#### Query Processing

When a user submits a question, the same model converts the query into a semantic embedding.

Because both documents and queries exist in the same vector space, PostgreSQL can efficiently retrieve the most relevant document sections using cosine similarity.

---

#### Deployment Strategy

FastEmbed runs locally inside the FastAPI backend using the optimized ONNX Runtime.

Benefits include:

- Low latency
- Reduced infrastructure cost
- No external embedding API calls
- Efficient CPU execution
- Simplified deployment

---

### 9.5 Conversational Generation Model

#### Anthropic Claude Sonnet 4.6

Claude Sonnet 4.6 is the primary Large Language Model (LLM) responsible for generating grounded responses based on the retrieved enterprise documentation.

Rather than relying solely on pretrained knowledge, Claude receives curated context from the retrieval engine, ensuring that responses remain accurate and relevant to the organization's knowledge base.

---

#### Model Characteristics

| Property | Value |
|-----------|-------|
| Model | Claude Sonnet 4.6 |
| Provider | Anthropic |
| Type | Large Language Model (LLM) |
| Context Window | Up to 1 Million Tokens* |
| Response Mode | Streaming (Server-Sent Events) |

> *Available subject to Anthropic model configuration and account capabilities.

---

#### Core Responsibilities

Claude is responsible for:

- Understanding user intent
- Interpreting retrieved document context
- Analyzing structured tables
- Performing technical reasoning
- Generating natural language responses
- Producing streaming output tokens

---

### Key Capabilities

#### Grounded Response Generation

Claude generates responses using only the retrieved document context supplied by the Prompt Builder, minimizing hallucinations and improving factual accuracy.

---

#### Multi-Turn Conversation Support

By incorporating conversation history into the prompt, Claude can understand follow-up questions and maintain context across extended chat sessions.

---

#### Structured Data Interpretation

Claude is capable of interpreting Markdown tables generated from CSV and Excel files, enabling accurate reasoning over structured datasets while preserving relationships between rows and columns.

---

#### Technical Document Understanding

The model is well suited for analyzing complex enterprise documentation, including:

- Technical manuals
- Standard operating procedures
- Engineering documentation
- Multi-page PDF reports
- Spreadsheet-based datasets

This capability enables SIAGE AI to provide precise, context-aware responses across a wide range of enterprise knowledge sources.

---

### 9.6 Summary

The AI Core combines semantic retrieval with large language generation to deliver accurate, grounded responses.

FastEmbed provides efficient vector representations for semantic search, while PostgreSQL retrieves the most relevant document context using pgvector. The Prompt Builder organizes retrieved knowledge into a structured prompt, which is then processed by Anthropic Claude Sonnet 4.6 to generate streamed, citation-backed responses through the Retrieval-Augmented Generation (RAG) pipeline.

### 10. API Architecture

#### Overview

SIAGE AI exposes a RESTful API organized into functional modules. Each module is responsible for a specific aspect of the application, including authentication, administration, chat services, and document asset management.

The backend follows a modular routing structure using FastAPI, making the API easy to maintain and extend.

---

#### 10.1 Authentication APIs

**Base Path**

```text
/api/v1/auth
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/register` | Register a new user account. |
| POST | `/login` | Validate user credentials and generate an OTP. |
| POST | `/verify-otp` | Verify the OTP and issue a JSON Web Token (JWT). |

---

#### 10.2 Administration APIs

**Base Path**

```text
/admin
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/documents/upload` | Upload and index enterprise documents. |
| GET | `/documents` | Retrieve metadata for all uploaded documents. |
| DELETE | `/documents/{id}` | Delete an indexed document and its associated records. |
| GET | `/users` | Retrieve and manage user accounts. |
| GET | `/analytics/queries-by-date` | Retrieve query analytics grouped by date. |

---

#### 10.3 Chat APIs

**Base Path**

```text
/api/v1/chat
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/sessions` | Retrieve all chat sessions for the authenticated user. |
| POST | `/sessions` | Create a new chat session. |
| GET | `/history/{session_id}` | Retrieve the complete conversation history for a session. |
| GET | `/query-stream` | Execute Retrieval-Augmented Generation (RAG) queries using Server-Sent Events (SSE). |

---

#### 10.4 Asset APIs

**Base Path**

```text
/api/v1/assets
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/page-image/{file}/{page}` | Retrieve document preview images or page assets. |

---

#### 10.5 API Design Principles

The API architecture follows several core principles:

- RESTful endpoint organization
- Modular routing by functional domain
- JWT-based authentication
- Role-Based Access Control (RBAC)
- Streaming responses using Server-Sent Events (SSE)
- Consistent JSON request and response formats
- Separation of administrative and user-facing operations

---

### 11. Backend Project Structure

The backend is organized into modular components that separate routing, business logic, database models, configuration, and infrastructure concerns.

```text
siage-ai-backend/
│
├── routes/
│   ├── auth.py              # User authentication and OTP verification
│   ├── admin.py             # Administrative APIs and analytics
│   ├── chat.py              # Chat sessions and RAG query pipeline
│   └── assets.py            # Document preview and asset endpoints
│
├── main.py                  # FastAPI application entry point
├── services.py              # Document ingestion, embedding, S3, and Claude integrations
├── models.py                # SQLAlchemy ORM models
├── schemas.py               # Pydantic request and response models
├── database.py              # PostgreSQL connection and session management
├── security.py              # JWT, password hashing, and authentication utilities
├── config.py                # Environment configuration and application settings
│
├── requirements.txt         # Python dependencies
├── Dockerfile               # Multi-stage Docker build configuration
├── docker-compose.yml       # Multi-container deployment configuration
│
└── README.md                # Project documentation
```

---

#### Module Responsibilities

| Module | Responsibility |
|---------|----------------|
| **main.py** | Initializes the FastAPI application, middleware, and route registration. |
| **routes/** | Defines all REST API endpoints grouped by functional domain. |
| **services.py** | Implements document ingestion, semantic retrieval, AWS S3 integration, and Anthropic Claude interactions. |
| **models.py** | Defines SQLAlchemy ORM models for database tables. |
| **schemas.py** | Defines request validation and response serialization using Pydantic. |
| **database.py** | Configures PostgreSQL connections and session management. |
| **security.py** | Handles password hashing, OTP validation, JWT generation, and authorization. |
| **config.py** | Loads environment variables and application configuration settings. |
| **Dockerfile** | Builds the production-ready backend container image. |
| **docker-compose.yml** | Orchestrates backend services and supporting infrastructure. |

---

#### Architectural Benefits

The modular backend architecture provides several advantages:

- Clear separation of concerns
- Improved maintainability and readability
- Simplified testing and debugging
- Independent development of functional modules
- Scalable service organization
- Production-ready containerized deployment
- Easy integration with cloud infrastructure such as AWS EC2, RDS, and S3

### 12. Deployment & Infrastructure

#### Overview
SIAGE AI is deployed using a containerized architecture on **AWS EC2**. The application components are packaged as Docker containers and orchestrated using Docker Compose.
An **NGINX** reverse proxy serves as the public entry point, routing incoming requests to the appropriate backend services while serving the production Angular application.

---

#### Deployment Architecture

```mermaid
graph TD

    User[Client Browser]

    User -->|HTTPS| NGINX

    subgraph AWS EC2
        NGINX[NGINX Reverse Proxy]
        ANGULAR[Angular Frontend]
        FASTAPI[FastAPI Backend]
    end

    NGINX --> ANGULAR
    NGINX --> FASTAPI

    FASTAPI --> RDS[(AWS RDS PostgreSQL)]
    FASTAPI --> S3[(AWS S3)]
    FASTAPI --> Claude[Anthropic Claude API]
```

---

#### Infrastructure Components

#### AWS EC2

Hosts the containerized application services, including:

- Angular frontend
- FastAPI backend
- NGINX reverse proxy

---

#### Docker

Docker packages each application component into isolated containers, ensuring consistent deployment across development, testing, and production environments.

---

#### Docker Compose

Docker Compose orchestrates the application stack by:

- Starting services
- Managing container networking
- Configuring environment variables
- Defining service dependencies

---

#### NGINX

NGINX acts as the application's gateway by:

- Serving the Angular production build
- Reverse proxying API requests
- Supporting Server-Sent Events (SSE)
- Handling HTTPS termination
- Routing frontend and backend traffic through a single origin

---

### 14. Security Considerations

#### Overview

Security is integrated throughout the SIAGE AI architecture to protect user data, enterprise documents, and backend services.

The platform follows industry best practices for authentication, authorization, secure storage, and cloud resource protection.

---

#### Input Validation

All user input is validated before processing.

The backend sanitizes incoming requests to:

- Prevent malformed input
- Reject invalid payloads
- Reduce the risk of command injection
- Ensure request integrity

---

#### Container Security

Application services run inside isolated Docker containers using a dedicated non-privileged user account (`appuser`) rather than the root user.

This minimizes the impact of potential container compromise and follows the principle of least privilege.

---

#### SQL Injection Protection

Database operations are performed exclusively through SQLAlchemy ORM and parameterized queries.

This approach prevents SQL injection attacks by separating SQL statements from user-supplied input.

---

#### JWT Authentication

Protected endpoints require a valid JSON Web Token (JWT).

The backend verifies:

- Token signature
- Token expiration
- User identity
- User role

Unauthorized requests are rejected before accessing protected resources.

---

#### Prompt Safety

Before invoking the language model, the Prompt Builder applies limits to:

- Maximum prompt size
- Retrieved context length
- Conversation history length
- Token allocation

These safeguards help prevent prompt overflow, excessive API usage, and token exhaustion.

---

#### Rate Limiting

High-cost endpoints, such as the streaming query endpoint (`/query-stream`), are protected using rate-limiting policies.

This helps:

- Prevent abuse
- Protect backend worker resources
- Control AI API consumption
- Improve overall system stability

---

#### Secure Document Access

Uploaded documents remain private within AWS S3.

Instead of exposing storage credentials or making objects publicly accessible, the backend generates temporary AWS S3 pre-signed URLs that:

- Grant time-limited access
- Restrict access to authorized users
- Prevent direct bucket exposure
- Protect enterprise documents from unauthorized access

---

#### Security Summary

SIAGE AI incorporates multiple layers of security, including:

- Input validation and sanitization
- JWT-based authentication
- Role-Based Access Control (RBAC)
- Parameterized database queries
- Non-root Docker containers
- Secure AWS S3 pre-signed URLs
- Prompt size controls
- Rate limiting for resource-intensive endpoints

Together, these measures provide a secure and production-ready environment for enterprise document intelligence.

### 15. Performance Optimizations

#### Overview

SIAGE AI incorporates several performance optimization techniques to ensure responsive user interactions, efficient document retrieval, and scalable AI processing. These optimizations minimize latency across the Retrieval-Augmented Generation (RAG) pipeline while supporting multiple concurrent users.

---

#### Asynchronous Processing

The FastAPI backend uses asynchronous request handlers (`async`/`await`) to prevent long-running operations from blocking the application.

Benefits include:

- Improved request concurrency
- Efficient handling of I/O-bound operations
- Better utilization of server resources
- Reduced response latency during AI interactions

Asynchronous execution is particularly beneficial for database queries, cloud storage operations, and external API communication.

---

#### Streaming Responses

AI-generated responses are delivered using **Server-Sent Events (SSE)**.

Instead of waiting for the complete response, tokens are streamed to the frontend as soon as they are generated.

Advantages include:

- Faster perceived response times
- Improved user experience
- Progressive rendering of long responses
- Reduced waiting time for users

---

#### Optimized Reverse Proxy

NGINX is configured to support low-latency streaming by forwarding Server-Sent Events without buffering.

This configuration enables:

- Immediate transmission of response tokens
- Reduced proxy latency
- Continuous streaming between the backend and frontend

---

#### High-Speed Vector Search

Semantic retrieval is accelerated using PostgreSQL with the **pgvector** extension and an **HNSW (Hierarchical Navigable Small World)** approximate nearest-neighbor index.

This provides:

- Sub-second semantic retrieval
- Efficient cosine similarity searches
- Scalable vector search performance for large document collections

---

#### Cloud Storage Offloading

Original document files are stored in **AWS S3**, while PostgreSQL maintains only metadata, extracted text, and vector embeddings.

This architecture:

- Reduces EC2 storage consumption
- Minimizes application server memory usage
- Improves scalability
- Enables efficient retrieval of large documents using pre-signed URLs

---

#### Modular Architecture

The application separates responsibilities across dedicated layers, including:

- Frontend presentation
- API services
- AI processing
- Database operations
- Cloud storage

This modular design simplifies scaling individual components as system demand increases.

---

## 16. Future Enhancements

The current architecture provides a strong foundation for enterprise document intelligence while allowing future expansion.

Planned enhancements include:

#### Hybrid Search

Combine dense vector retrieval with traditional keyword-based search (such as BM25) to improve retrieval accuracy, particularly for exact terminology, identifiers, and short queries.

---

#### Background Processing

Introduce distributed task processing using **Celery** to handle computationally intensive operations, including:

- Large-scale document ingestion
- Embedding generation
- Bulk indexing
- Scheduled maintenance tasks

This will improve responsiveness by moving long-running jobs outside the main application process.

---

#### Multi-Document Reasoning

Extend the Retrieval-Augmented Generation (RAG) pipeline to support simultaneous retrieval and comparison across multiple documents.

This capability will enable users to:

- Compare documents
- Identify differences between versions
- Correlate related information across multiple knowledge sources

---

#### Document Version Management

Implement document version control to support:

- Version history
- Change tracking
- Incremental re-indexing
- Rollback to previous document versions

This feature will improve knowledge management for frequently updated enterprise documentation.

---

#### Enhanced Analytics

Expand the administrative dashboard with:

- Retrieval quality metrics
- User activity analytics
- AI usage statistics
- Document indexing performance
- System health monitoring

---

## 17. Developer Guidelines

#### Code Organization

Business logic should remain isolated from API routing.

Recommended structure:

- `routes/` — API endpoint definitions
- `services.py` — Business logic and processing workflows
- `models.py` — Database models
- `schemas.py` — Request and response validation
- `security.py` — Authentication and authorization utilities

Keeping endpoints lightweight improves maintainability and simplifies testing.

---

#### Request Validation

All incoming requests should be validated using **Pydantic** models.

Validation should ensure:

- Required fields are present
- Data types are correct
- Input constraints are enforced
- Invalid requests are rejected before business logic execution

---

#### Coding Standards

Developers should follow the **PEP 8** Python style guide to maintain consistency across the codebase.

Recommended practices include:

- Meaningful variable and function names
- Consistent formatting
- Modular functions
- Clear documentation
- Proper exception handling

---

#### Type Hinting

All newly developed functions should include explicit Python type hints for:

- Function parameters
- Return values
- Class attributes

Type annotations improve readability, enable static analysis, and simplify long-term maintenance.

---

#### Documentation

New modules and major functions should include clear documentation describing:

- Purpose
- Inputs
- Outputs
- Exceptions
- Dependencies

Maintaining comprehensive documentation helps ensure the project remains accessible to future contributors.

---

#### Testing

Before deployment, developers should verify that:

- API endpoints function correctly
- Authentication and authorization rules are enforced
- Database operations behave as expected
- Document ingestion pipelines process supported file types
- Semantic retrieval produces relevant results
- Streaming responses function correctly
- Error handling remains consistent

---

#### Deployment Best Practices

For production deployments:

- Store secrets in environment variables
- Avoid hard-coded credentials
- Use Docker for consistent environments
- Enable HTTPS in production
- Monitor application logs and system metrics
- Regularly back up PostgreSQL databases and AWS S3 assets

Following these guidelines helps maintain a secure, scalable, and production-ready SIAGE AI platform.

## 18. Development Environment Setup

#### Prerequisites

Before running SIAGE AI locally, ensure the following software and services are installed:

#### Software

- Python 3.11 or later
- Node.js 20 or later
- Angular CLI
- PostgreSQL 16 or later
- pgvector extension enabled in PostgreSQL
- Docker Desktop (optional, for containerized development)
- Git

#### Cloud Services

- Anthropic API Key
- AWS IAM user with S3 read/write permissions
- AWS S3 bucket
- PostgreSQL database (local or AWS RDS)

---

#### 18.1 Clone the Repository

Clone the project repository and navigate to the project directory.

```bash
git clone <repository-url>
cd SiageAIChatBot
```

---

#### 18.2 Backend Setup

Navigate to the backend project.

```bash
cd siage-ai-backend
```

Create a virtual environment.

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

---

#### 18.3 Install Dependencies

Install the required Python packages.

```bash
pip install -r requirements.txt
```

The installation includes dependencies such as:

- FastAPI
- SQLAlchemy
- Pandas
- OpenPyXL
- FastEmbed
- boto3
- Anthropic SDK
- pgvector
- Uvicorn

---

#### 18.4 Environment Configuration

Create a `.env` file in the backend root directory.

```env
ENV_MODE=development

HOST=127.0.0.1
PORT=8000

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/manual_db

ANTHROPIC_API_KEY=your_anthropic_api_key

AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_REGION=ap-south-1

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
```

> **Note:** Never commit the `.env` file or any sensitive credentials to version control.

---

#### 18.5 Start the Development Server

Run the FastAPI development server using Uvicorn.

```bash
uvicorn main:app --reload
```

By default, the application is available at:

```
http://127.0.0.1:8000
```

Interactive API documentation is available at:

- `/docs` (Swagger UI)
- `/redoc` (ReDoc)

---

### 19. Docker Containerization

#### Overview

SIAGE AI is containerized using Docker to ensure consistent environments across development, testing, and production deployments.

A multi-stage Docker build is used to minimize image size while improving security and build efficiency.

---

#### 19.1 Dockerfile

```dockerfile
# -------------------------
# Build Stage
# -------------------------

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip wheel \
    --no-cache-dir \
    --no-deps \
    --wheel-dir /app/wheels \
    -r requirements.txt

# -------------------------
# Runtime Stage
# -------------------------

FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_MODE=production

RUN useradd -u 8888 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

USER appuser

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

ENV PATH="/home/appuser/.local/bin:${PATH}"

RUN pip install \
    --no-cache-dir \
    --user \
    /wheels/*

COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD [
    "uvicorn",
    "main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--workers",
    "4",
    "--proxy-headers",
    "--forwarded-allow-ips=*"
]
```

---

#### 19.2 `.dockerignore`

The `.dockerignore` file excludes unnecessary files from the Docker build context, reducing image size and improving build performance.

```text
__pycache__/
*.pyc
*.pyo
venv/
.env
.git
.gitignore
```

---

#### 19.3 Benefits of the Docker Configuration

The Docker setup provides several advantages:

- Multi-stage builds reduce final image size.
- Python dependencies are compiled during the build stage and reused in the runtime image.
- Containers run as a non-root user (`appuser`) to improve security.
- Environment variables configure application behavior without modifying the image.
- The application is exposed on port **8000** and served using **Uvicorn** with multiple worker processes for improved concurrency.
- The same container image can be deployed consistently across development, staging, and production environments.

### 20. Building the Docker Image

#### Overview

Once the backend has been configured, build the production Docker image using the project's `Dockerfile`.

Run the following command from the root of the backend project:

```bash
docker build -t siage-ai-backend:latest .
```

#### Command Explanation

| Option | Description |
|---------|-------------|
| `docker build` | Builds a Docker image from the Dockerfile. |
| `-t` | Assigns a tag to the image. |
| `siage-ai-backend:latest` | Image name and version tag. |
| `.` | Uses the current directory as the build context. |

After the build completes successfully, verify the image using:

```bash
docker images
```

---

### 21. Running the Docker Container

#### Overview

Run the backend as a detached Docker container while loading configuration values from the `.env` file.

```bash
docker run -d \
  --name siage-ai-backend-service \
  -p 8000:8000 \
  --env-file .env \
  siage-ai-backend:latest
```

#### Command Explanation

| Option | Description |
|---------|-------------|
| `-d` | Runs the container in detached mode. |
| `--name` | Assigns a name to the running container. |
| `-p 8000:8000` | Maps host port 8000 to the container port. |
| `--env-file` | Loads environment variables from the `.env` file. |
| `siage-ai-backend:latest` | Docker image to execute. |

#### Useful Docker Commands

View running containers:

```bash
docker ps
```

View application logs:

```bash
docker logs -f siage-ai-backend-service
```

Stop the container:

```bash
docker stop siage-ai-backend-service
```

Remove the container:

```bash
docker rm siage-ai-backend-service
```

---

### 22. Docker Compose

#### Overview

For local development and production deployments involving multiple services, SIAGE AI uses **Docker Compose** to orchestrate containers.

Docker Compose manages:

- FastAPI backend
- Angular frontend (optional)
- NGINX reverse proxy
- Supporting infrastructure

Start the complete application stack using:

```bash
docker compose up -d --build
```

#### Command Explanation

| Option | Description |
|---------|-------------|
| `up` | Creates and starts all configured services. |
| `-d` | Runs containers in detached mode. |
| `--build` | Rebuilds images before starting containers. |

#### Additional Commands

Stop all services:

```bash
docker compose down
```

Restart services:

```bash
docker compose restart
```

View container logs:

```bash
docker compose logs -f
```

List running services:

```bash
docker compose ps
```

---

### 23. NGINX Reverse Proxy

#### Overview

NGINX serves as the public entry point for SIAGE AI, routing incoming client requests to the appropriate backend services.

Its primary responsibilities include:

- Serving the Angular production build
- Reverse proxying API requests
- Supporting Server-Sent Events (SSE)
- Handling large document uploads
- Forwarding client request headers
- Providing a unified application endpoint

---

#### Example Production Configuration

```nginx
server {

    listen 80;
    server_name api.siageai.internal;

    client_max_body_size 100M;

    # -----------------------------
    # Streaming Endpoint (SSE)
    # -----------------------------

    location /api/v1/chat/query-stream {

        proxy_pass http://fastapi_backend:8000;

        proxy_http_version 1.1;

        proxy_set_header Connection "";

        proxy_buffering off;
        proxy_cache off;

        proxy_read_timeout 300s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # -----------------------------
    # General API Requests
    # -----------------------------

    location / {

        proxy_pass http://fastapi_backend:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

    }
}
```

---

#### Configuration Highlights

#### Reverse Proxy

NGINX forwards incoming HTTP requests to the FastAPI backend, allowing clients to communicate through a single public endpoint.

---

#### Server-Sent Events (SSE)

The streaming endpoint is configured specifically for Server-Sent Events.

The following directives are essential:

- `proxy_buffering off`
- `proxy_cache off`
- `proxy_http_version 1.1`
- `proxy_read_timeout 300s`

These settings ensure that AI-generated tokens are streamed immediately to the client without buffering.

---

#### Upload Support

The directive:

```nginx
client_max_body_size 100M;
```

allows users to upload enterprise documents up to **100 MB** in size.

---

#### Forwarded Headers

NGINX forwards client metadata to the backend using the following headers:

- `Host`
- `X-Real-IP`
- `X-Forwarded-For`
- `X-Forwarded-Proto`

These headers enable FastAPI to correctly identify client information, protocol details, and proxy routing.

---

#### Deployment Benefits

The NGINX reverse proxy provides several production advantages:

- Centralized request routing
- Efficient support for Server-Sent Events
- Reduced backend exposure
- Secure header forwarding
- Large file upload handling
- Improved scalability and maintainability
- Simplified integration with Docker and cloud infrastructure

### 24. Production Deployment (AWS EC2)

#### Overview

SIAGE AI is designed for production deployment on an **AWS EC2** instance using Docker and Docker Compose. The deployment architecture separates application services, database infrastructure, and object storage to provide a secure, scalable, and maintainable environment.

---

### Deployment Steps

#### 1. Connect to the EC2 Instance

Connect to the production EC2 instance using SSH.

```bash
ssh -i <private-key>.pem ubuntu@<ec2-public-ip>
```

---

#### 2. Clone the Repository

Clone the project repository and navigate to the application directory.

```bash
git clone <repository-url>

cd SiageAIChatBot
```

---

#### 3. Configure Production Environment

Create a production `.env` file containing the required configuration.

Typical production settings include:

- AWS RDS PostgreSQL connection
- AWS S3 bucket configuration
- Anthropic API key
- JWT secret
- Application environment variables

Example:

```env
ENV_MODE=production

DATABASE_URL=postgresql://<user>:<password>@<rds-endpoint>:5432/manual_db

ANTHROPIC_API_KEY=<anthropic_api_key>

AWS_ACCESS_KEY_ID=<access_key>
AWS_SECRET_ACCESS_KEY=<secret_key>
AWS_STORAGE_BUCKET_NAME=<bucket_name>
AWS_REGION=ap-south-1

JWT_SECRET_KEY=<jwt_secret>
JWT_ALGORITHM=HS256
```

---

#### 4. Build Docker Images

Build the required production images.

```bash
docker compose build
```

---

#### 5. Start the Application

Launch the production services in detached mode.

```bash
docker compose up -d
```

Verify that all services are running:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f
```

---

### 25. Production Architecture & Request Flow

#### Overview

The production request lifecycle illustrates how SIAGE AI processes authenticated user queries through the Retrieval-Augmented Generation (RAG) pipeline.

Each request flows through multiple infrastructure components before a grounded response is streamed back to the user.

---

#### Request Flow Diagram

```mermaid
flowchart LR

    A[User]
    B[Angular Frontend]
    C[NGINX]
    D[FastAPI Backend]
    E[FastEmbed]
    F[(PostgreSQL + pgvector)]
    G[(AWS S3)]
    H[Anthropic Claude API]

    A --> B
    B --> C
    C --> D

    D --> E
    E --> F

    F --> D

    D --> G
    G --> D

    D --> H
    H --> D

    D --> C
    C --> B
    B --> A
```

---

### Request Processing

#### 1. User Authentication

The user logs into the Angular application and authenticates using the two-stage login process.

After successful authentication, a JWT is issued and attached to subsequent requests.

---

#### 2. Streaming Query Request

The frontend submits the user's question to the FastAPI backend through the streaming endpoint:

```text
/api/v1/chat/query-stream
```

The request passes through the NGINX reverse proxy before reaching the backend.

---

#### 3. Query Embedding

FastAPI converts the user's question into a **384-dimensional semantic embedding** using FastEmbed.

This embedding represents the semantic meaning of the query rather than simple keyword matching.

---

#### 4. Semantic Retrieval

The generated embedding is compared against stored document embeddings in PostgreSQL using the **pgvector** extension and an **HNSW** approximate nearest-neighbor index.

The retrieval engine returns the most relevant document pages or structured data chunks.

---

#### 5. Source Resolution

For retrieved documents, the backend generates temporary **AWS S3 pre-signed URLs**.

These URLs allow the frontend to securely access referenced document pages without exposing the S3 bucket publicly.

---

#### 6. Prompt Construction

The Prompt Builder assembles:

- System instructions
- Retrieved document context
- Conversation history
- Current user query

This structured prompt is then sent to the Anthropic Claude API.

---

#### 7. AI Response Generation

Claude generates a grounded response using the supplied enterprise documentation.

Instead of relying solely on pretrained knowledge, the model bases its response on the retrieved context provided by the RAG pipeline.

---

#### 8. Real-Time Streaming

The generated response is streamed back to the frontend using **Server-Sent Events (SSE)**.

Users receive tokens progressively as they are generated, providing a responsive conversational experience.

---

### 26. Summary & Conclusion

SIAGE AI is an enterprise Retrieval-Augmented Generation (RAG) platform designed to deliver accurate, context-aware responses from organizational knowledge sources.

The platform integrates modern cloud infrastructure, semantic search, and large language models into a modular architecture that supports secure document management, intelligent retrieval, and scalable AI-powered conversations.

Key architectural features include:

- Multi-format document ingestion supporting PDF, CSV, and Excel files
- Semantic retrieval using PostgreSQL with the pgvector extension
- High-performance HNSW vector indexing
- Secure object storage through AWS S3
- Grounded response generation using Anthropic Claude Sonnet
- Real-time streaming responses via Server-Sent Events (SSE)
- JWT-based authentication with Role-Based Access Control (RBAC)
- Containerized deployment using Docker and Docker Compose
- Reverse proxy routing through NGINX
- Cloud-ready deployment on AWS EC2

The separation of presentation, application, AI processing, storage, and infrastructure layers enables SIAGE AI to remain scalable, maintainable, and adaptable to evolving enterprise requirements.
By combining efficient semantic retrieval, secure cloud storage, and Retrieval-Augmented Generation, the platform provides reliable document intelligence while preserving traceability, minimizing hallucinations, and supporting production-scale deployments.
