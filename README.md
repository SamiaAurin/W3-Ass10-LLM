# Property Information Rewriting with Django and Ollama LLM

A Django CLI application that uses Ollama to enhance property listings by generating improved titles, descriptions, summaries, ratings, and reviews.

---

# Table of Contents
1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation](#installation)  
4. [Project Structure](#project-structure)  
5. [Database Models](#database-models)  
6. [Usage](#usage)  
   - [Command-Line Utilities](#command-line-utilities)  
7. [Testing](#testing)  
8. [Troubleshooting](#troubleshooting)

---
## Features
- **Automated Property Information Rewriting**: Utilizes the Ollama LLM to rewrite property titles and descriptions.  
- **Property Summaries Generation**: Automatically generates summaries from scraped property data.  
- **Property Rating and Review Generation**: AI-powered generation of property ratings and reviews based on available data.  
- **CLI Interface**: Provides an easy-to-use command-line interface for managing operations.  
- **Database Storage**: Stores all generated content (rewritten data, summaries, ratings, and reviews) in a PostgreSQL database for persistence.  

## Prerequisites
- **Python**: Version 3.9 or above  
- **Docker and Docker Compose**: Follow the official Docker installation guide to install Docker on your system: [Get Docker](https://docs.docker.com/get-docker/). For Docker Compose, refer to the official installation instructions: [Install Docker Compose](https://docs.docker.com/compose/install/) 
- **Ollama**: Installed and configured for local LLM interaction.   
 

## Installation

1. Clone the repositories:  

   ```bash
   git clone https://github.com/SamiaAurin/W3-Ass10-LLM.git
   cd W3-Ass10-LLM
   code .
   ```
   To ensure proper functionality of this project, you need to clone the previous project from my GitHub repository named `W3-Ass08-Scrapy`, which serves as a prerequisite. Detailed instructions for setting up and running the previous project are available in its `README.md` file.

   ```bash
   git clone https://github.com/SamiaAurin/W3-Ass08-Scrapy.git
   cd W3-Ass08-Scrapy
   cd travelscraper
   docker-compose build
   docker-compose up
   ```
   Ensure the previous project ( https://github.com/SamiaAurin/W3-Ass08-Scrapy.git ) is running correctly before proceeding with this project.

2. Set Up a Virtual Environment:

   **On Linux/macOS:**
   ```bash
   python3 -m venv venv  # or python -m venv venv 
   source venv/bin/activate
   ```
   **On Windows:**
   ```bash
   python3 -m venv venv   # or python -m venv venv 
   venv\Scripts\activate
   ```
3. Docker Desktop:

   Ensure Docker Desktop is running on your system, as it is required to manage the containers. Then, execute the following commands to build and run the application:

   ```bash
   docker-compose build
   docker-compose up
   ```
   To stop the application, press `Ctrl + C` or run:
   ```bash
   docker-compose down
   ```
   **Note:** The Docker build process may take some time to complete. This is because the `Dockerfile` and `docker-compose.yml` are configured to automatically install all dependencies listed in the `requirements.txt` file during the build phase. Please be patient while the setup is finalized.

4. Creating a Shared Docker Network

   To enable seamless communication between this project's database and the scraper's database, you need to create a shared Docker network. This can be done using the following command:

   ```bash
   docker network create ollama-network-new
   ```
   This command creates a custom Docker network named `ollama-network-new`. The network facilitates inter-service communication by allowing containers from different projects to connect securely. In the `docker-compose.yml` file, ensure the following networks are added to each service under the networks section:

   ```bash
      networks:
         - ollama-network-new  # Dedicated network for the Ollama project
         - travelscraper_default  # Network for the Scraper project
   ```
   **Description:**
      - **ollama-network-new:** This is a custom network created for the current project to ensure isolated and efficient communication.
      - **travelscraper_default:** This is the default network created by Docker Compose for the scraper project, allowing shared access between the two projects.
   Adding these networks to each service ensures that all containers (e.g., Django app, database, etc.) in the Ollama project can communicate with the containers in the scraper project over a shared network.

   Remember to restart the Docker containers after updating the `docker-compose.yml` file to apply the changes.

5. Ollama Model:

   ```bash
   docker-compose exec ollama /bin/bash
   ollama pull tinyllama  # or ollama pull phi
   ollama list # To check the list of models 
   ```
   **Note:** It is recommended to use a smaller-sized model, such as `TinyLlama`, as it ensures a more efficient and faster running process. Note that even with smaller models, initialization and processing may take a few minutes depending on your system configuration.
---

## Database Models

### Hotels Table
This table stores information about `hotels` scraped from the previous project.
Fields include:

- **city_id**: Identifier for the city where the hotel is located.
- **hotel_id**: Unique identifier for the hotel.
- **hotel_name**: Name of the hotel.
- **price**: Price of the hotel in decimal format.
- **hotel_img**: URL of the hotel's image.
- **rating**: The rating of the hotel.
- **room_type**: Type of room available in the hotel.
- **location**: Address or location details of the hotel.
- **latitude**: Geographical latitude of the hotel.
- **longitude**: Geographical longitude of the hotel.
- **description**: A detailed description of the hotel (optional field).


### Property Summaries
This table stores summaries generated by the LLM model.  
Fields include:
- **property_id**: Foreign key referencing the property.  
- **summary**: The AI-generated summary of the property.  

### Property Rating and Review Table
This table stores ratings and reviews for properties, generated by the LLM model.
Fields include:

- **property_id**:: Foreign key referencing the property.
- **rating**:: The rating assigned to the property, typically on a scale (e.g., 1–5).
- **review**:: The review text generated for the property.

---
# Project Structure

The project structure will look like this:

```bash
W3-ASS10-LLM/
│
├── ollama/                # Folder that auto-generates after pulling a model
│
├── ollama_project/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── property_info/
│   ├── management/
│   │   └── commands/
│   │       ├── rewrite_property_rating_review.py
│   │       ├── rewrite_property_summary.py
│   │       └── rewrite_property_titles.py
│   │
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── venv/                  # Virtual environment for dependencies
│
├── .coverage              # Coverage report file
├── .gitignore             # Git ignore file
├── commands.txt           # File containing commands for running the project
├── docker-compose.yml     # Configuration for Docker Compose
├── Dockerfile             # Instructions for building the Docker image
├── manage.py              # Command-line utility for Django
├── README.md              # Documentation for the project
└── requirements.txt       # List of Python dependencies
```
**Description of the Structure:**
- **W3-ASS10-LLM/:** Root directory of your project.
  - ollama/: Folder for auto-generated models after pulling.
  - ollama_project/: Main project directory containing essential files.
     - *settings.py:* Configuration settings for the Django project. Make sure your this file contains
        
         ```bash
         INSTALLED_APPS = [
         'property_info', # django app folder
         ]

         DATABASES = {
            'default': {
               'ENGINE': 'django.db.backends.postgresql',
               'NAME': 'ollama_data_new',  # database name
               'USER': 'username',         # Username for the PostgreSQL database
               'PASSWORD': 'password',     # Password for the PostgreSQL database
               'HOST': 'ollama-db-new',    # Ollama DB container name
               'PORT': '5432',             # Default PostgreSQL port
            },
            'travel': {
               'ENGINE': 'django.db.backends.postgresql',
               'NAME': 'hotels_data',
               'USER': 'username',
               'PASSWORD': 'password',
               'HOST': 'travelscraper-db-1',
               'PORT': '5432',
            }  # scraper project's db
         }   
       ```

  - property_info/: Main application directory.
  - management/commands/: Directory for custom management commands.
  - admin.py: Admin interface configurations.
  - models.py: Database models for the application.

---

# Usage

Download `Assignment10-LLM.pdf` file for better understanding of running commands.

## Command-Line Utilities
This project includes three Django CLI commands designed for automated processing:

1. `rewrite_property_titles.py`
   - Functionality: Automates the rewriting of property titles and descriptions using the Ollama LLM.
   - Purpose: Enhances clarity, improves SEO, and ensures consistency in property information.
   - Command To Run:

     ```bash
     docker exec -it django-new python manage.py rewrite_property_titles
     ```

2. `rewrite_property_summary.py`
   - Functionality: Generates concise property summaries from the scraped data.
   - Purpose: Provides quick, clear, and easy-to-digest overviews of each property.
   - Command To Run:
   
     ```bash
     docker exec -it django-new python manage.py rewrite_property_summary
     ```
3. `rewrite_property_rating_review.py`
    - Functionality: Automatically creates AI-powered ratings and reviews for properties based on the available data.
   - Purpose: Offers detailed insights and ratings for properties to aid user decision-making.
   - Command To Run:
   
     ```bash
     docker exec -it django-new python manage.py rewrite_property_rating_review
     ```
These CLI commands simplify the workflow by allowing seamless integration and execution directly from the command line.

---

# Testing

Download `Assignment10-LLM.pdf` file for better understanding of running commands.

```bash
docker exec -it django-new bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

# Troubleshooting

1. If you encounter any issues related to dependencies or changes made in the `requirements.txt`, `docker-compose.yml`, or `Dockerfile`, it is recommended to rebuild the Docker containers without using the cache. This ensures that all changes are reflected and any stale layers are removed.

   Run the following command to rebuild the containers:
   ```bash
   docker-compose build --no-cache
   ```
   This command will force Docker to rebuild the image from scratch, incorporating any updates or changes made to the configuration files.

2. If you make any changes to the property_info/models.py file, follow these steps to apply the migrations:

   **Create migrations:**

   ```bash
   docker exec -it django-new python manage.py makemigrations
   ```
   **Apply migrations:**

   ```bash
   docker exec -it django-new python manage.py migrate
   ```
   These commands will generate and apply the necessary database migrations to reflect the changes in your models. Make sure to run these commands whenever you modify the model definitions.