# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy only the requirements first for better build caching
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining project files
COPY . .

# Optionally, you can explicitly set the PYTHONUNBUFFERED environment variable
# to ensure output appears immediately in logs:
ENV PYTHONUNBUFFERED=1

# Expose port if needed (not strictly necessary unless you are hosting a web server)
# EXPOSE 8000

# The default command to run the bot
CMD ["python", "twitter_bot.py"]
