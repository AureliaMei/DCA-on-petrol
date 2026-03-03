FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# 1. Set the working directory inside the container
WORKDIR /work

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install browsers for Playwright
RUN playwright install chromium

# 4. Open port 8888 for Jupyter Lab
EXPOSE 8888

# 5. Start Jupyter Lab when the container runs
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--no-browser"]

