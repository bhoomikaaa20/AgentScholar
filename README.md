# 🔎 Research Desk — Multi-Agent AI Research Assistant

Research Desk is a **Multi-Agent AI Research Assistant** that automatically searches the web, gathers detailed information from relevant sources, generates a structured research report, and reviews the report using a dedicated AI critic.

The project uses **LangChain, OpenAI, Tavily, web scraping, and Streamlit** to create a complete research workflow powered by multiple specialized AI agents.

---

## 🚀 Features

- 🔎 **AI Web Search Agent** — searches the web for recent and reliable information.
- 📖 **AI Reader Agent** — selects a relevant source and scrapes its webpage for deeper information.
- ✍️ **AI Writer** — combines the gathered research and generates a structured report.
- 🧐 **AI Critic** — reviews the generated report and provides a score, strengths, areas for improvement, and a final verdict.
- 🌐 **Real-time Web Research** using Tavily.
- 📄 **Source Extraction** — displays the URLs and content gathered during research.
- 📥 **Report Download** — download the generated report as a Markdown file.
- 🖥️ **Streamlit Interface** — simple and interactive research dashboard.
- 📊 **Progress Tracker** — shows the current research stage.
- 💡 **Example Topics** — predefined research topics are available for quick testing.

---

## 🧠 How It Works

Research Desk follows a sequential multi-agent workflow:

```text
                 User
                   │
                   ▼
            Enter Research Topic
                   │
                   ▼
        ┌─────────────────────┐
        │  1. Search Agent    │
        │                     │
        │  Searches the web   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  2. Reader Agent    │
        │                     │
        │  Scrapes a relevant │
        │  webpage for detail │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  3. Writer Agent    │
        │                     │
        │  Generates report   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  4. Critic Agent    │
        │                     │
        │  Reviews the report │
        └──────────┬──────────┘
                   │
                   ▼
          Final Reviewed Report
```

The same four-step pipeline is also available through the Python pipeline implementation. 

---

## 🤖 AI Agents

### 1. Web Search Agent

The Web Search Agent searches for recent and relevant information about the user's topic.

It uses a custom `web_search` tool powered by **Tavily**.

The search tool returns:

- Title
- URL
- Content snippet

The tool retrieves up to three search results for a query.

---

### 2. Reader Agent

The Reader Agent receives the search results and chooses a relevant URL for deeper analysis.

It then uses the custom `url_scrape` tool to retrieve webpage content.

The scraper:

- Sends an HTTP request to the webpage
- Parses the HTML using BeautifulSoup
- Removes unnecessary elements such as scripts, styles, navigation, and footer sections
- Extracts clean webpage text
- Limits the extracted content for further processing



---

### 3. Writer

The Writer combines the search results and scraped webpage content and generates a professional research report.

The generated report contains:

```text
Introduction
     ↓
Key Findings
     ↓
Conclusion
     ↓
Sources
```

The report prompt specifically requests at least three well-explained key findings and a list of URLs found during research.

---

### 4. Critic

The Critic Agent evaluates the generated report.

It provides:

```text
Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
...
```

This allows the user to understand both the quality of the generated report and what could be improved.

---

## 🖥️ User Interface

The application is built using **Streamlit**.

The interface provides four main sections:

### 📄 Report

Displays the final generated research report.

The report can also be downloaded as a `.md` file.

### 🧐 Critic Review

Displays:

- Report score
- Strengths
- Areas to improve
- Final verdict

### 🔗 Sources

Displays the sources discovered by the Web Search Agent, including:

- Source title
- URL
- Website/domain
- Content snippet

### 📖 Scraped Page

Displays the webpage selected and read by the Reader Agent.

The Streamlit application implements these four result tabs directly.

---

## 🛠️ Tech Stack

### AI / LLM

- Python
- LangChain
- LangChain OpenAI
- LangChain Core
- LangGraph
- OpenAI GPT-5-mini

The project initializes `ChatOpenAI` with the `gpt-5-mini` model and uses LangChain agents for the search and scraping stages.

### Web Research

- Tavily
- Requests
- BeautifulSoup4
- HTTPX

### Frontend

- Streamlit
- HTML
- CSS

### Environment Management

- python-dotenv

### Validation / Utilities

- Pydantic
- typing-extensions
- Rich

The project's dependency file includes these major frameworks and libraries.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/research-desk.git
cd research-desk
```

---

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project dependencies include LangChain, LangChain OpenAI, Tavily, BeautifulSoup, Streamlit, Pydantic, and other supporting libraries.

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

The project loads environment variables using `python-dotenv`.

---

## ▶️ Running the Application

### Streamlit Application

Run:

```bash
streamlit run main.py
```

Then open the Streamlit URL shown in your terminal.

You will see the Research Desk interface.

Enter a topic such as:

```text
Impact of artificial intelligence on healthcare
```

and click:

```text
Run research
```

---

## 💻 Running Without Streamlit

You can also run the research pipeline directly from the terminal.

```bash
python pipeline.py
```

The application will ask:

```text
Enter a research topic:
```

Enter your topic and the pipeline will execute the four stages sequentially.

---

## 🔄 Complete Workflow

When a user enters a topic:

### Step 1 — Search

The Search Agent receives:

```text
Find recent, reliable and detailed information about: <topic>
```

It calls the Tavily search tool and collects relevant sources.

### Step 2 — Read

The Reader Agent receives the search results and selects the most relevant URL.

It then scrapes that webpage for deeper information.

### Step 3 — Write

The Writer receives:

```text
Search Results
+
Detailed Scraped Content
```

and generates the research report.

### Step 4 — Review

The Critic receives the generated report and evaluates it.

Finally, the user receives:

```text
Research Report
+
Sources
+
Critic Score
+
Strengths
+
Areas for Improvement
+
Final Verdict
```

## 👩‍💻 Author

**Bhoomika Somavarapu**

MSc Artificial Intelligence Student

Interested in:

- Artificial Intelligence
- Generative AI
- LLM Applications
- Multi-Agent Systems
- Machine Learning
- Full-Stack Development

---

## ⭐ If You Find This Project Useful

If you found this project interesting or useful, consider giving the repository a ⭐ on GitHub.

---
