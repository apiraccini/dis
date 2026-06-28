## Part 2: The Practical Build, Document Intelligence Server

### 1. The Scenario

One of our enterprise clients, a financial services company, has accumulated hundreds of internal documents across teams: compliance policies, product manuals, onboarding guides, FAQ exports. Today, employees search for information using a shared drive with folders and filenames. It works, barely.

The client wants to connect this knowledge base to an AI assistant. Employees should be able to ask questions in natural language and get precise, grounded answers, with the agent knowing exactly which documents to search, when to filter by topic, and when to cast a wider net.

Your job is to build the backend infrastructure for this: a document ingestion pipeline, a simple management interface, and, the core of the project, an **MCP server** that exposes the knowledge base as a set of well-designed, agent-ready tools.

---

### 2. Functional Requirements

### A. Document Management (Frontend)

Build a minimal but functional web interface that allows a user to:

- **Upload documents** (PDF and plain text at minimum)
- **Assign one or more tags** to each document at upload time (e.g., `compliance`, `onboarding`, `product`, `hr`)
- **View the list of uploaded documents** with their associated tags
- **Delete a document** from the knowledge base

The frontend is free choice: use whatever framework or library you prefer. It does not need to be polished. It needs to work.

### B. Ingestion Pipeline (Backend)

When a document is uploaded, the backend must:

1. **Parse** the document and extract its text content
2. **Chunk** the text into meaningful segments (your choice of strategy: explain it in the README)
3. **Embed** each chunk using an embedding model of your choice (an OpenAI API key will be provided; you may use a different model, but document your choice)
4. **Store** the chunks and their embeddings in a vector store of your choice, local or third party
5. **Persist document metadata** (filename, tags, upload date, chunk count) in a relational or document store

The pipeline must be robust: re-uploading a document should not create duplicates.

### C. MCP Server: The Core

Build an MCP server in **Python** that exposes the knowledge base as a set of tools consumable by any MCP-compatible AI agent.

The server must use **Streamable HTTP** as the transport protocol.

The server must expose at least the following tools:

| Tool | Description |
| --- | --- |
| `list_documents` | Returns the names and metadata of all documents currently in the knowledge base |
| `list_tags` | Returns all unique tags that have been assigned to at least one document |
| `search` | Performs semantic search across the entire knowledge base, returning the top-k most relevant chunks with their source document |
| `search_by_tag` | Performs semantic search restricted to documents matching one or more specified tags |
| `search_by_document` | Performs semantic search restricted to one or more specific documents by name or ID |

**Tool interface design is part of the assignment.** We provide the tool names and high-level descriptions above, but you must decide:

- The input parameters each tool accepts (names, types, defaults, constraints)
- The output format and structure of each tool's response
- The tool descriptions that will help an LLM understand when and how to use each tool
- Whether to add additional tools beyond the five listed above

Think about it from the agent's perspective: your tool definitions (names, descriptions, input schemas) are what the LLM sees to decide when and how to call each tool. Design them accordingly.

Your tool interface design will be a key part of the evaluation. We want to see that you understand how LLMs consume tool definitions and that you can design an interface that makes it easy for an agent to make the right decisions.

**Authentication:** The MCP server endpoint must be protected with an authentication mechanism (e.g., API key header, Bearer token). Document how a client should authenticate.

---

### 3. Technical Constraints

- **Python** is required for the backend and MCP server.
- **Streamable HTTP** is required as the MCP transport protocol.
- Everything else is your choice: frontend framework, vector store, embedding model, database, libraries. Document and justify your decisions in the README.

---

### 5. Evaluation Criteria

We will evaluate your submission in this order of priority:

| Priority | Area | What we look at |
| --- | --- | --- |
| 1 | **MCP Tool Design** | Number of tools, names, descriptions, input schemas: would an LLM know when and how to use each tool correctly? |
| 2 | **RAG Architecture** | Chunking strategy and rationale, embedding choice, retrieval quality, deduplication |
| 3 | **Python Code Quality** | Structure, readability, error handling, type hints, separation of concerns |
| 4 | **Infrastructure & DevOps** | Dockerization, deployment strategy, secret management, reproducibility |
| 5 | **Frontend** | Functional and usable: we are not evaluating design |
| 6 | **Communication** | Can you explain your architectural decisions clearly to a non-technical stakeholder? |

Be prepared to walk through every choice during the review.

---

### 6. Deliverables

At submission, please provide:

1. **Git repository link:** `.env.example` included
2. **Live application URL** (preferred): frontend, backend and MCP server deployed and accessible via public URLs. If deployment is not feasible, provide one of the following alternatives:
    - A `docker-compose` setup that spins up the entire stack locally with a single command
    - A devcontainer configuration ready to use
    - Clear step-by-step instructions to run the application locally
3. **MCP server endpoint** (remote or local) with authentication, documented and working
4. **Demo video** (5-10 minutes): walk through the entire flow as if you were presenting to a client. Show document upload, document management, and then query the MCP server through a client of your choice (Claude Desktop, a custom agent, ChatGPT, or even Postman). Explain your architectural decisions along the way.
5. **README** covering:
    - Architecture overview (a diagram is welcome but not required)
    - Stack choices and their rationale (vector store, embedding model, chunking strategy, MCP transport)
    - MCP tool design rationale: why you chose these tools, these names, these parameters
    - How to run the project locally
    - How to connect an MCP-compatible client to your server
    - Known limitations and what you would improve with more time
6. **Part 1 written answers:** included in the README or as a separate document in the repository

---

## **Thank You**

We appreciate the effort you're putting into this assignment and look forward to learning more about you. If you have any questions or need clarification, don't hesitate to reach out.

Good luck!
