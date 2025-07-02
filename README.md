# Document Extraction Application

This is a full-stack application designed to extract structured data from documents like invoices. It uses a Next.js frontend, a Flask backend, and the Gemini LLM for AI-powered data extraction.

## How to Run Locally

Here's how you can get the project running on your local machine.

### Prerequisites

* Node.js (v18+) with `pnpm`
* Python (v3.9+) with `poetry`

### 1. Installation

First, install all the dependencies for both the frontend and backend.

```bash
pnpm run install:all
```

### 2. Setup the Environment

You'll need an API key for the Gemini LLM.

1. Navigate to the `backend/` directory.
2. Create a copy of the `.env.example` file and name it `.env`.
3. Open the new `.env` file and add your Google Gemini API key: (to get an API key easily just go to [text](https://aistudio.google.com/prompts/new_chat) click get API key in right top cornder and follow the instructions)

    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

    You can also enable a testing mode that bypasses the duplicate invoice check by adding `TESTING=true` to this file. This is super useful for uploading the same invoice multiple times without causing an error.

### 3. Initialize the Database

Before you run the app for the first time, you need to create and populate the SQLite database from the provided Excel data.

```bash
pnpm run db:init
```

### 4. Run the Application

Now you can start both the frontend and backend servers concurrently.

```bash
pnpm run dev
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:5000`.

---

## If I Had More Time: Thoughts on Scaling This Up

This project is a solid proof-of-concept and I'm pretty happy with how it turned out. It does the job. But if we were talking about taking this to production to handle serious volume, there are a few things I'd focus on to make it more robust and scalable. Here's my thinking on how I'd evolve the system.

### The First Fix: Don't Make The User Wait

The most immediate issue is that when a user uploads a file, the frontend just hangs until the entire process is done. The LLM call can be slow, and that's not great for the user experience.

My first move would be to make this whole process asynchronous. When a file is uploaded, the API should just grab it, maybe do a quick validation, and then fire off a job to a background worker queue. For Python, Celery with Redis is the go-to stack for this. The API would then instantly respond to the user with something like, "Okay, we got it. We're working on it!".

This makes the UI feel super responsive. To get the results back, we could have the frontend poll an API endpoint every few seconds to check if the job is done. Or, for a really slick solution, use WebSockets to have the backend push the data to the UI in real-time the moment it's ready.

### Getting Smarter About Documents & Actually Improving the AI

Right now, the prompt is tuned for one specific invoice format. It would likely struggle with different layouts or completely different documents like purchase orders or receipts.

To handle this, I'd build a sort of "classification" step. The first call to the LLM wouldn't be to extract data, but simply to ask, "What is this document?". Based on that answer, we could then use a different, more specialized prompt for that specific document type. It's like having a team of specialized assistants.

And for true accuracy, you have to create a feedback loop. The UI we built is actually perfect for this. When the LLM extracts data, especially if its a low-confidence result, we can flag it for a human to review. The human corrects the data, and we save that correction. This gives us a stream of high-quality training data to fine-tune our own model over time. It's a virtuous cycle: the model gets smarter, and the business gets a dataset thats all its own, which is a huge asset.

### Bullet-proofing the Infrastructure for Production

A few pieces of the current stack are great for getting started, but they wouldn't hold up under real production load.

* **Database:** SQLite is fantastic for local dev, but it falls over with concurrent users. I'd switch this out for a managed PostgreSQL instance, like AWS RDS. It's built for this kind of thing, gives you automated backups, and can scale up easily. The support for JSONB columns is also a huge plus for storing raw, semi-structured outputs from the LLM.
* **File Storage:** Storing uploads on the server's local disk is a non-starter for scaling. If you run more than one instance of your app for redundancy, the servers won't have access to each others files. The right way to do this is to have the frontend upload files directly to a cloud storage bucket, like Amazon S3. This decouples file storage from the application itself.
* **Deployment:** To make deployments reliable and repeatable, I'd containerize the Flask and Next.js apps using Docker. From there, we could get started with a service like AWS Fargate or Google Cloud Run, which are great for running containers without having to manage servers. If we needed more power and control down the road, we could move to a full Kubernetes setup for auto-scaling and orchestration.

### Knowing What's Going On: Observability

Finally, you can't run what you can't see. We'd need to add proper monitoring. I'm not just talking about CPU and memory here, but application-level metrics. I'd want to track API response times, error rates from the backend, and the length of our Celery queue. Most importantly, I'd want to monitor the LLM itself: how long are calls taking? How much is it costing us per document? How often does our JSON parsing fail?

Tools like Prometheus and Grafana would be great for the metrics, and something like Sentry would be invaluable for real-time error tracking and performance monitoring. Without this, your flying blind when problems happen.
