# 🛠️ The Digital Forge: An Autonomous AI Software Development Crew

**The Digital Forge** is a fully autonomous software development pipeline powered by a crew of specialized AI agents. Give it a natural language request, and the crew will work together to understand the requirements, write the code, create tests, and even debug their own work to deliver a final, validated solution.

**Live Demo:** [**https://thedigitalforge.onrender.com/**](https://thedigitalforge.onrender.com/)

---

### A Note on Project Status (MVP)

This project is currently a Minimum Viable Product (MVP). It's a functional proof-of-concept demonstrating the power of a specialized AI agent crew. While I've worked hard to make the agents as robust as possible, the underlying nature of Large Language Models and the CrewAI framework means that occasional bugs or AI "hallucinations" can still occur, especially with complex or ambiguous requests. I am continuously working to improve the system's reliability.

---

## Core Concept & Philosophy

This project is built on my philosophy of **agent specialization**, mirroring a real-world agile development team. Instead of a single, monolithic AI trying to handle all tasks, The Digital Forge employs a crew of four distinct agents I designed, each with a unique role, personality, and set of instructions. This separation of duties creates a more robust and intelligent system capable of complex problem-solving and self-correction.

The entire process is designed to be **autonomous and iterative**. The crew operates in sprints, with a built-in debugging loop that allows them to analyze their own failures and attempt fixes, learning and adapting with each cycle.

---

## The AI Crew: Unit 734

The crew of AI agents, "Unit 734," is the heart of the operation. I modeled each agent after a figure from Greek mythology to reflect their specific role in the development pipeline.

| Agent       | Role                                    | Responsibilities                                                                                                                              |
| :---------- | :-------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| **Janus** | 👤 **Client Liaison** | Interprets the initial user request to create a formal technical brief. At the end of the process, compiles the final, client-facing report.    |
| **Athena** | 📝 **Strategic Team Lead** | Deconstructs the technical brief into a precise, actionable development plan. When tests fail, performs a root cause analysis to diagnose the bug. |
| **Hephaestus**| ⌨️ **Principal Software Developer** | Writes clean, efficient, and correct Python application code based strictly on the instructions from Athena.                                    |
| **Argus** | 🔎 **Quality Assurance Tester** | Writes and executes a `pytest` test suite to validate the code written by Hephaestus. Its tests must be a faithful reflection of the original task. |

---

## System Architecture & Design Decisions

I built The Digital Forge with a modern, decoupled architecture designed for scalability and robust error handling.

#### **Frontend: Streamlit**
* **Why Streamlit?** I chose Streamlit for its ability to create a beautiful, interactive user interface with pure Python. It allowed for rapid prototyping and provided a seamless way to display real-time progress and final reports without the complexity of traditional web frameworks.

#### **Backend: Flask & CrewAI**
* **Flask:** A lightweight Flask server acts as the API endpoint. It receives requests from the Streamlit front end and initiates the AI agent pipeline.
* **CrewAI:** This is the core framework that orchestrates the agents. It manages the flow of information, the assignment of tasks, and the execution of the overall workflow.

#### **Critical Design Decision: The In-Memory Workspace**
* **The Challenge:** Deploying an application that needs to write and read files to a platform with an ephemeral or read-only filesystem (like Render's free tier) is a major challenge. The agents need a "workspace" to save their code and tests, but can't rely on a persistent disk.
* **The Solution:** I implemented a **virtual, in-memory workspace** using a simple Python dictionary. All file operations (`save_file`, `read_file`) interact with this dictionary instead of the disk. The `run_tests` tool is engineered to use temporary files that are created just for the test run and are immediately deleted—a safe and standard practice for server environments. This makes the entire application stateless, scalable, and perfectly suited for modern cloud deployment.

#### **The Robust Debugging Loop**
* **The Goal:** A truly autonomous system must be able to fix its own mistakes.
* **The Implementation:** The pipeline operates in a loop for up to three "sprints." If tests fail, the log is passed back to **Athena**, my analyst agent. Athena performs a **differential diagnosis** to determine the root cause:
    1.  **Is the code buggy?** (A Hephaestus error)
    2.  **Is the test buggy?** (An Argus error)
* The main orchestration script then routes Athena's new, targeted task to the correct agent, allowing the crew to fix bugs in both the application code and their own test suites.

---

## Setbacks and Evolution: The Journey to Robustness

The development of The Digital Forge was an iterative process of identifying and fixing critical failures in the agents' logic.

1.  **The Contradiction Failure:**
    * **The Problem:** In early tests, the developer (Hephaestus) would correctly write code, but the tester (Argus) would write a faulty test expecting a different outcome. The team lead (Athena) would then incorrectly side with the bad test and instruct the developer to break the working code.
    * **The Solution:** I re-engineered Athena's `analyze_test_failure` task to perform the "differential diagnosis," forcing it to compare the test failure against the *original* developer task to determine the true source of the error.

2.  **The Hallucination Failure:**
    * **The Problem:** When faced with a confusing bug-fix task or an error reading a file, the agents would sometimes "hallucinate"—inventing completely new, unrelated code instead of using the context they were given. This led to the pipeline completely derailing.
    * **The Solution:** I added **CRITICAL, explicit instructions** to the agents' goals and task descriptions. Hephaestus was forbidden from writing test code, and Janus was commanded to *only* use the verbatim content provided for the final report.

3.  **The Orchestration Failure:**
    * **The Problem:** Even after Athena correctly diagnosed a bug in the test suite, the main script was still incorrectly routing the fix to the developer instead of the tester.
    * **The Solution:** I rewrote the debugging loop in `main_deployment.py` to correctly parse the JSON output from Athena and dynamically assign the next task to the agent specified in the `file_to_fix` key.

---

## How to Run Locally

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/MohammedPathariya/TheDigitalForge.git](https://github.com/MohammedPathariya/TheDigitalForge.git)
    cd TheDigitalForge
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Your Environment Variables:**
    * Create a file named `.env` in the project's root directory.
    * Add your OpenAI API key to this file:
        ```
        OPENAI_API_KEY="your_api_key_here"
        ```

5.  **Run the Application:**
    * The backend server and the front-end Streamlit app are now integrated. Simply run the Streamlit app:
        ```bash
        streamlit run streamlit_app.py
        ```
    * Open your browser to the local URL provided by Streamlit.

---

## Future Improvements

* **Multi-File Projects:** Extend the agents' capabilities to handle more complex requests that require generating multiple, interacting Python files.
* **Enhanced Context Memory:** Improve the agents' ability to remember the full history of a debugging session to prevent them from re-introducing old bugs.
* **Front-End Workspace Viewer:** Add a feature to the Streamlit UI that allows the user to view the contents of the in-memory workspace in real-time.
