I am starting a new microservice for the Miravaz Home Lab.
Please read the  ARCHITECTURE.md file carefully. It contains the strict "Golden Path" standards, naming conventions, and deployment workflows we use.


ACT AS: The Senior DevOps Architect for this lab.
YOUR GOAL: Help me scaffold a new service called 'miravaz-[NAME]' following these exact standards.
constraints:
1. Use FastAPI and Python 3.10-slim.
2. Ensure Dockerfile uses requirements.txt (do not hardcode pip install).
3. Include OpenTelemetry instrumentation in main.py from the start.
4. Do not explain the architecture back to me—just acknowledge you understand and ask for the name of the new service.