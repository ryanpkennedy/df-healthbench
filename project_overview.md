# AI Engineer Project - DF HealthBench

## Overview

In this assignment, you will build a small backend application that processes medical documents using LLM. The project is broken into 6 parts: setting up a backend, integrating an LLM API, implementing a RAG pipeline, building an agent for data extraction, converting data to a healthcare standard data format, and containerizing the app for deployment.

The goal is to automate workflows for medical documents processing. For document notes, we have provided some notes, you can find them in attachment 1. You are also welcome to create your own medical notes or mock examples if it helps demonstrate your solution more effectively.

**FHIR Standard:** FHIR (Fast Healthcare Interoperability Resources) is a standard for exchanging healthcare information electronically. In practice, FHIR defines structured data formats (resources) for health information (patients, conditions, medications, etc.). In this assignment, you will create a simplified FHIR-like output.

This assignment mirrors real use cases your team will work on. You may also use any LLM provider or open-source libraries that help you move faster.

**Expectation**: at the end of the assignment, you could present your solution as a public Github repo or a zipped file and it should include a `docker-compose.yml` that launches the service locally with all parts ready to be tested. You should include a description of how each part should be tested in `README.md`.

**Time Estimate:** We recommend spending no more than 4 hours on this exercise. Please aim to complete as many core tasks and stretch goals as you can within the time you have available. If you have any questions, don’t hesitate to reach out—we’re happy to help!

**Evaluation Criteria**: We’ll evaluate your submission based on:

- Correctness and completeness of each part
- Documentation and ease of local setup
- Creativity in problem-solving (especially in agent design and RAG)
- Let’s make sure your implementation is model agnostic; however, we will use OpenAI for testing and grading

---

## Part 1: FastAPI Backend Foundation

Set up a basic backend service using FastAPI with a relational database. This will serve as the foundation for the subsequent parts, providing endpoints and data storage.

**Tasks:**

1. Initialize a FastAPI application. Implement a simple health-check endpoint (e.g., `GET /health`) that returns a confirmation (such as `{"status": "ok"}`) to verify the server is running.
2. Set up a relational database. Define a simple schema for storing documents, for example a table `documents` with fields: `id` (int primary key), `title` (text), and `content` (text). You can use this to store sample medical documents or notes for later retrieval.
3. If using an ORM, create a model class for the document and handle database connections. If using raw SQL, ensure you have functions to add and query documents.
4. Create at least one endpoint (e.g., `GET /documents`) that fetches all documents from the database and returns a list of ids. This will test that your app can interact with the database.
5. **(Optional)** Implement a `POST /documents` endpoint to add a new document (with a JSON body containing `title` and `content`), storing it in the DB. Include basic error handling/validation (e.g., if `content` is missing).

**Input/Output Expectations:**

- **Input:** HTTP requests to your FastAPI server
- **Output:** JSON responses

**Stretch Goals:**

- Integrate **SQLAlchemy** to define the relational schema and models more elegantly, and implement full CRUD (Create, Read, Update, Delete) endpoints for documents.

---

## Part 2: LLM API Integration

Demonstrate integration with a LLM API in your backend. The goal is to call LLM to perform a simple task on medical text.

**Tasks:**

1. Choose an LLM provider (any). Set up your code to use this API. Typically, this means installing the SDK, configuring authentication (e.g., an API key via environment variable), and writing a small wrapper function to send a prompt and get a completion.
2. Implement an endpoint, for example `POST /summarize_note`, which accepts a medical document as input, calls the LLM API, and returns the LLM’s output. For instance, you could have the LLM summarize the note or extract key insights about the patient.
3. Parse the response from the LLM API and return it in the endpoint’s JSON response. Bonus point if you handle potential errors gracefully, perhaps returning an error message with appropriate HTTP status if the LLM call fails.
4. Do not hard-code API keys in code. Use configuration (like environment variables) for sensitive info. Document in a README or comments how to set the API key to run this part.

**Input/Output Expectations:**

- **Input:** A request to the new endpoint (e.g., `POST /summarize_note`) with the required input (e.g., a raw text of a medical note).
- **Output:** A JSON response containing the processed result from the LLM.

**Stretch Goals:**

- Instead of a simple summary, you could have the LLM perform a different task, such as paraphrasing the note in layperson terms or extracting specific info (like the patient’s chief complaint) in one shot.
- Use a framework to allow selection of multiple models via configuration
- Implement rudimentary caching of LLM responses in the DB to avoid repeat API calls (useful if the same note is processed multiple times).

---

## Part 3: Retrieval-Augmented Generation (RAG) Pipeline

Implement a basic RAG pipeline.

**Tasks:**

1. Take a set of sample documents (the “knowledge base”). These could be a few short text files or entries in the database you set up in Part 1. For example, you might create 2–3 mock policy documents or medical guidelines and insert them into the `documents` table. Each document should have enough content that certain questions can be answered from it.
2. For each document, prepare it for retrieval. In a real RAG setup, this involves splitting documents into chunks and computing embeddings for each chunk, then storing those vectors in a vector database. For simplicity, you can use an embedding model (OpenAI offers embedding endpoints, or use a library like SentenceTransformers) to vectorize documents, then find the most similar document or section for a given query. Implement a proper vector store for retrieval.
3. Implement an endpoint, e.g. `POST /answer_question`, that accepts a user’s question (query). The endpoint should receive a question, retrieve relevant document text and generate an answer using the LLM.
4. Return the LLM’s answer in the response JSON. Bonus point if you could also return which document (or document section) was used as context for transparency.

**Input/Output Expectations:**

- **Input:** A question from the user, typically via a query parameter or JSON field.
- **Output:** A JSON response with the answer. The answer should ideally be correct based on the provided documents. If you also return context info, you might include the document id or snippet in the response for verification.

**Stretch Goals:**

- Return source citations in the answer.

---

## Part 4: Agent for Structured Data Extraction from Medical Notes

Build an **agent-based system** (or agentic workflow) that can extract structured data from an unstructured medical note. This agent should be able to interact with public health APIs and extract diagnosis and medication codes.

**Tasks:**

1. Extract raw information from the text (e.g. patient, conditions, diagnoses, medications, treatments, important observations such as vital signs and lab results and plan actions (e.g., follow-up appointments, recommended tests). For simplicity, choose a few key pieces that make sense for your note.
2. Look up ICD codes for conditions, diagnosis, and treatments
3. Look up RxNorm codes for medications
4. Return the final validated python object. You might use a Pydantic model or manual checks to verify the format.
5. Create an endpoint that takes a medical note and provide the structured data, e.g., `POST /extract_structured.`

**Input/Output Expectations:**

- **Input:** A raw text
- **Output:** A structured JSON object with specific fields extracted and enriched with relevant codes. The output and structure are yours to define.

**Stretch Goals:**

- Write a unit test for each agent module and try to test edge cases

---

## Part 5: Convert to FHIR-Compatible Format

Take the structured data extracted in Part 4 and convert (map) it into a simplified FHIR representation. We are not expecting a full implementation of FHIR, but rather a basic transformation to show you understand key FHIR resource fields.

**Tasks:**

1. Based on what you extracted in Part 4, decide which FHIR resource(s) would represent that data. Common choices:
   - **Patient** – if you have patient demographics (name, ID, etc.) from the note.
   - **Condition** – for diagnoses or problems. (FHIR Condition has fields like `code`, `subject` (the patient), `onset`, etc; pick the sections as you see fit)
   - **MedicationRequest** or **MedicationStatement** – for medications that were prescribed or reported.
   - **Observation** – for objective findings like vital signs or lab results.
   - **Encounter/Procedure** – if the note implies a visit or procedure done.
   - **CarePlan** or **Appointment** – for follow-up plans.
     For the assignment, pick one or two resource types that make sense (e.g., Patient and Condition, or Condition and Medication).
2. Create a JSON output structure that follows the FHIR format for those resources in a simplified way. You do not need to include every FHIR field, just the most relevant ones. For example, for a Condition you might output:

   ```json
   {
     "resourceType": "Condition",
     "code": "Type 2 Diabetes Mellitus",
     "clinicalStatus": "active",
     "verificationStatus": "confirmed",
     "subject": { "reference": "Patient/123" }
   }
   ```

   And for a Patient:

   ```json
   {
     "resourceType": "Patient",
     "id": "123",
     "name": "John Doe",
     "gender": "male",
     "birthDate": "1980-05-01"
   }
   ```

   (These are just examples; you can assume some dummy patient info or take it from the note if available.)

3. Write a function or logic that takes the output of Part 4 (your structured data dict) and maps it to the FHIR-like JSON.
4. Provide an endpoint, e.g., `POST /to_fhir`, that accepts the structured data and returns the FHIR-formatted JSON.
5. Since you are not using a FHIR library, do a basic check that the output is valid JSON and contains the fields you intended.

**Input/Output Expectations:**

- **Input:** The structured data (from Part 4)
- **Output:** A JSON representation of one or more FHIR resources. This could be a single JSON object if you bundled everything as, say, a FHIR Bundle or just a dictionary with sub-entries. Or it could be an array of resource JSON objects. For example, your response might look like:
  ```json
  {
    "patient": { ... Patient resource ... },
    "conditions": [ ... list of Condition resources ... ],
    "medications": [ ... Medication resources ... ]
  }
  ```
  or simply a list of resources.

**Stretch Goals:**

- Use an actual FHIR library (like `fhir.resources` in Python) to create real FHIR resource objects and serialize them. This would ensure compliance with the spec and is a good exercise in using standard libraries.

---

## **Part 6: Containerization and Docker Compose Deployment**

Containerize the entire application and use `docker-compose` to orchestrate the different components to show production-readiness and good DevOps practices.

### **Tasks:**

1. Write a `Dockerfile` for the Application:
   - Use a suitable Python base image
   - Install all dependencies (use `requirements.txt` or `pyproject.toml`).
   - Copy in the application code.
   - Set the entrypoint to run the FastAPI app using `uvicorn`.
2. Create a `docker-compose.yaml` File to:
   - Define the FastAPI app service.
   - Mount the necessary volumes if needed (for persistent storage).
   - Pass environment variables (e.g., OpenAI API key) securely via `env_file` or inline `environment` section.
   - Expose the API on a public port (e.g., `http://localhost:8000`).
3. Optional Services (if applicable)**:**
   - If you used a vector store like Chroma or FAISS, or a Redis cache, include these as additional services in the `docker-compose.yml`.
   - Example: a separate service for a vector DB or shared volume.
4. Add an `.env` File:
   - Use this for storing credentials, e.g. LLM API keys, reference it in your `docker-compose.yml`.
5. Startup Script (Optional):
   - You may include a small `init.sh` script or FastAPI startup event to seed the database with sample medical documents for quick testing after boot.
6. README Instructions:
   - Include clear setup instructions in your README:
     - How to build the image: `docker-compose build`
     - How to start the services: `docker-compose up`
     - How to test the endpoints (e.g., example `curl` or Postman requests)

### **Input/Output Expectations:**

- **Input:** Docker Compose configuration and supporting files.
- **Output:** A fully working local deployment:
  - Running `docker-compose up` should bring up all services.
  - The FastAPI backend should be reachable at `http://localhost:8000`.
  - All endpoints from earlier parts (e.g., `/health`, `/summarize_note`, `/extract_structured`) should work as expected within the containerized environment.

### **Stretch Goals:**

- Add hot-reloading support (e.g., using `uvicorn --reload`) for local development.
- Use multi-stage builds to keep the Docker image lightweight and production-ready.
- Include a volume mount for relational DB so the DB persists across restarts.
- Write a `Makefile` to simplify common actions like `build`, `up`, `down`.

---

## Attachment 1 - Medical notes

For document notes, we have provided some notes in SOAP format. For your information, many types of medical notes are written in this format and it stands for Subjective, Objective, Assessment, and Plan.

- _Subjective_ – the patient’s reported symptoms and history
- _Objective_ – the clinician’s observations, exam findings, and test results
- _Assessment_ – the clinician’s diagnoses or summary of the case
- _Plan_ – the treatment plan or next steps for the patient

[soap_01.txt](attachment:18ce7198-d5d9-4e99-87f5-e608f66098a0:soap_01.txt)

[soap_02.txt](attachment:beed957a-3509-4377-a68f-b5e554b6966f:soap_02.txt)

[soap_03.txt](attachment:f3c227c4-ba6f-4880-a71e-ee330455358b:soap_03.txt)

[soap_04.txt](attachment:929dc74e-80d1-49c1-b2c7-b38e7f29a19d:soap_04.txt)

[soap_05.txt](attachment:6641346f-77a0-420c-80e2-dc980cab89d3:soap_05.txt)

[soap_06.txt](attachment:f9499f17-30e7-45c6-8a1d-0c9032e94c47:soap_06.txt)

Note you are not limited to these medical notes and you can create your own documents.
