# Legal-Document-Summarizer
LegalEase is an AI-powered web app that simplifies complex legal documents into concise summaries using NLP. It highlights risks, supports 50+ language translations, and provides text-to-speech output, making legal content easy to understand for individuals, startups, and professionals.

LegalEase — AI Contract Summarizer

LegalEase is a Flask-based web application that uses AI to simplify complex legal documents. It generates concise summaries, detects potential risks, translates content into multiple languages, and provides audio output for accessibility.

Features
AI Summarization: Uses BART model for concise summaries
Multi-language Translation: Supports 100+ languages
Text-to-Speech: Converts summaries into audio
Risk Detection: Identifies penalties, disputes, and confidentiality clauses
File Support: Works with .txt and .csv files

Tech Stack
Flask, HuggingFace Transformers, Pandas, Googletrans, gTTS

 Setup
pip install flask transformers torch pandas googletrans==4.0.0-rc1 gtts
python app.py

Usage
Upload file → Select language → Get summary, translation, audio & risk analysis

Use Cases
Legal document review
Contract analysis
Learning & accessibility


License
MIT License


Data Source
Legal text and case-related data were scraped from Indian Kanoon to support summarization and risk analysis.
