Django Property Information Rewriter
A Django CLI application that uses Ollama to enhance property listings by generating improved titles, descriptions, summaries, ratings, and reviews.
Features

Automated property information rewriting using Ollama LLM
Generation of property summaries from scraped data
Property rating and review generation
CLI interface for easy operation
Database storage for all generated content

Database Schema
Properties Table

Original property information
Rewritten title and description

Property Summaries

property_id (Foreign Key)
summary

Property Reviews

property_id (Foreign Key)
rating
review

Usage

Select an Ollama model
Input property data
Generate enhanced content:

Rewritten titles and descriptions
Comprehensive property summaries
Ratings and reviews



Requirements

Django
Ollama
Python 3.x

Installation
[Installation instructions to be added]
License
[License information to be added]