# AGENTS.md

## Project Overview

This repository contains the SRM RAG Chatbot.

The chatbot answers questions about SRM Institute using Retrieval-Augmented Generation (RAG).

Knowledge sources include:

- SRM website pages
- PDF documents
- OCR extracted images
- Vector embeddings stored in ChromaDB

Primary objectives:

- Accurate retrieval
- Reliable citations
- Fast response time
- Clean architecture
- Maintainable code

---

# Engineering Principles

Follow these principles before making any code changes.

## Think Before Coding

Understand the existing implementation before changing anything.

Read surrounding code.

Identify the correct layer responsible for the task.

Avoid making assumptions.

---

## Simplicity First

Prefer the smallest change that solves the problem.

Avoid unnecessary abstractions.

Avoid adding new dependencies unless required.

Do not introduce additional complexity.

---

## Surgical Changes

Modify only files directly related to the requested feature.

Never refactor unrelated modules.

Avoid unnecessary formatting-only commits.

---

## Verify Before Completion

Before considering a task complete:

- verify imports
- verify type hints
- verify formatting
- verify existing functionality
- ensure new code integrates correctly

---

# Repository Architecture

Application Flow

Frontend
↓
FastAPI Backend
↓
Services
↓
RAG Pipeline
↓
Retriever
↓
ChromaDB
↓
Gemini LLM

---

# Folder Responsibilities

## frontend/

Contains HTML, CSS and JavaScript.

Responsible only for UI.

Do not implement backend logic here.

---

## backend/

Contains FastAPI server.

Responsibilities:

- routing
- API endpoints
- request validation

Business logic does not belong here.

---

## app/services/

Contains business logic.

Examples:

- chat orchestration
- analytics
- uploads

Whenever possible place logic here.

---

## app/generator/

Responsible for

- prompt creation
- LLM interaction
- reranking
- response generation
- RAG pipeline

Prompt changes belong here.

---

## app/retrieval/

Responsible for

- retrieval
- hybrid search
- ranking

Do not place prompt logic here.

---

## app/vector_db/

Responsible only for vector database interaction.

Avoid embedding logic here.

---

## app/embedding/

Responsible for

- embedding generation
- embedding testing

---

## app/processing/

Responsible for

- cleaning
- chunking
- metadata

---

## app/ingestion/

Responsible for

- website scraping
- PDF parsing
- OCR
- crawling

---

## app/utils/

Shared utilities.

Logging belongs here.

---

# Data Rules

Treat these as production data.

Never modify unless explicitly requested.

app/data/chroma_db/

app/data/final/

app/data/embeddings/

analytics.json

---

# Coding Standards

Target Python 3.10+

Use:

- pathlib
- dataclasses when appropriate
- type hints
- logging

Avoid:

- wildcard imports
- duplicated code
- deeply nested functions

Functions should have one responsibility.

---

# FastAPI Guidelines

Routes should remain thin.

Move business logic into services.

Avoid large endpoint functions.

Validate all input.

Return consistent response models.

---

# Retrieval Rules

When improving retrieval:

Prefer changing

app/retrieval/

or

generator/rag_pipeline.py

Avoid prompt modifications unless necessary.

---

# Prompt Rules

Prompt templates belong only inside

app/generator/

Avoid prompt duplication.

---

# ChromaDB Rules

Never delete

app/data/chroma_db

Never recreate embeddings without explicit permission.

Never rebuild the database unless requested.

---

# Performance

Prefer improving

- retrieval
- ranking
- chunking

before increasing prompt size.

Avoid unnecessary API calls.

---

# Logging

Use the existing logger.

Avoid print().

Errors should be meaningful.

---

# Error Handling

Handle exceptions close to their source.

Never silently ignore exceptions.

Provide useful error messages.

---

# Git Rules

Never

- delete user files
- rename folders
- overwrite datasets

without explicit instruction.

---

# Testing

If modifying

retrieval

run retrieval tests.

If modifying

embedding

run embedding tests.

If modifying

FastAPI

verify endpoints.

Never remove existing tests.

---

# Communication

Before implementing major changes:

Explain the approach briefly.

After implementation:

Summarize

- what changed
- why
- affected files

---

# Things Never To Do

Never:

- delete ChromaDB
- overwrite rag_data.json
- regenerate embeddings
- move folders
- rewrite architecture
- introduce breaking API changes

unless explicitly instructed.

Always preserve existing project organization.