# DxP Bot Assistant POC

This project is a Proof of Concept (POC) for an AI-powered assistant that enables Q&A and semantic search over Confluence documents. It leverages OpenAI embeddings, LangChain, Milvus vector database, and Streamlit for the user interface.

## Features
- **Document Ingestion:** Fetches and preprocesses Confluence pages.
- **Embeddings:** Uses OpenAI's embedding models to vectorize document chunks.
- **Vector Store:** Stores embeddings in Milvus for efficient semantic search.
- **Q&A Interface:** Streamlit app for uploading files and asking questions about their content.

## Project Structure
```
app/                # Streamlit app and UI components
embeddings/         # Embedding service and Milvus client
ingestion/          # Confluence ingestion and update scripts
data/               # Raw and processed data storage
images/             # Project images (e.g., logos)
tests/              # Unit tests
```

## Setup

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd confluence_ai_poc
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root with the following variables:

   | Variable | Purpose | How to Obtain |
   |----------|---------|---------------|
   | `OPENAI_API_KEY` | Access Azure OpenAI for embeddings and GPT model queries. | Log in to the Azure Portal → Navigate to your deployed Azure OpenAI Service → Go to Keys and Endpoint → Copy the Primary Key. |
   | `AZURE_OPENAI_ENDPOINT` | Endpoint to access Azure OpenAI resources. | Log in to the Azure Portal → Navigate to your deployed Azure OpenAI Service → Copy the Endpoint URL from the resource overview (e.g., `https://your-resource-name.openai.azure.com`). |
   | `OPENAI_ADA_DEPLOYMENT_NAME` | Use text-embedding-ada-002 for embedding generation. | Log in to the Azure Portal → Ensure you’ve deployed the text-embedding-ada-002 model and copy its deployment name (e.g., `ada-embeddings`). |
   | `OPENAI_GPT_DEPLOYMENT_NAME` | Use gpt-4 for generating conversational answers. | Log in to the Azure Portal → Ensure you’ve deployed the gpt-4 model and copy its deployment name (e.g., `gpt-4`). |
   | `OPENAI_API_VERSION` | Specify the Azure OpenAI API version to use. | Use the latest supported version for Azure OpenAI. Example: `2023-05-15`. |
   | `MILVUS_HOST` | Access local Milvus vector database. | If using a local Milvus instance: Host will be `localhost`, and port will be `19530`. Ensure Milvus is running locally. |
   | `MILVUS_PORT` | Milvus connection port for the vector database. | Default `19530`. |
   | `MILVUS_URI` (Optional) | Access Zilliz Cloud (Managed Milvus). | Register or log in to Zilliz Cloud → Copy the Public Endpoint after creating an instance. |
   | `MILVUS_TOKEN` (Optional) | API Key for Zilliz Cloud (Managed Milvus). | In Zilliz Cloud, copy the API Key from the vector database instance settings. |
   | `CONFLUENCE_API_KEY` | Access Confluence REST API to fetch spaces, pages, etc. | - Go to Atlassian API Token page. <br> - Click Create API Token, name it (e.g. Knowledge Bot), and copy the generated token. <br> (For on-prem Confluence) Generate a Personal Access Token (PAT) using on-prem documentation: Personal Access Token Info. |
   | `CONFLUENCE_URL` | Base URL of your Confluence instance. | Look at your Confluence’s URL when logged in. For example: https://your-instance.atlassian.net/wiki. |
   | `CONFLUENCE_SPACE_KEY` | Identifier for the Confluence space to fetch data from. | Found in the Confluence URL when you navigate to a specific space (e.g., https://your-instance.atlassian.net/wiki/spaces/<SPACE>/pages/...). |

4. **Run the Streamlit app:**
   ```sh
   streamlit run app/ChatBot.py
   ```

5. **(Optional) Update Knowledge Base:**
   To ingest new Confluence data and update the vector store:
   ```sh
   python -m ingestion.update_knowledge_base
   ```

## Notes
- Make sure you have access to the required APIs (OpenAI, Azure, Confluence, etc.).
- The Milvus vector database is used for storing and searching embeddings. You may need to configure or run Milvus locally or use Milvus Lite.
- For development and testing, mock data and services are provided.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
