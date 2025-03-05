# Use an official lightweight Python image
FROM python:3.10-slim  

# Set the working directory inside the container
WORKDIR /app  

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt  
RUN pip install --no-cache-dir -r requirements.txt  

# Copy the rest of the app files
COPY . .  

# Expose the port Flask runs on
EXPOSE 10000  

# Define the command to start the app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
