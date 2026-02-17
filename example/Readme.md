# ArchiLLM Examples

Welcome to the `example` directory of **ArchiLLM**. This folder contains sample inputs, architectural descriptions, and generated models to help you understand how ArchiLLM leverages Large Language Models (LLMs) to assist in early-stage microservice architecture design.

These examples are aligned with the research presented in our paper: *"On the feasibility of identifying microservice early-stage architectures using LLMs"*.

## 📂 Folder Contents

This directory contains reference materials used to demonstrate and validate the tool, which typically include:

- **Natural Language Requirements (`.txt` / `.md`)**: Sample textual descriptions of various software systems. You can use these as minimal initial input prompts for the ArchiLLM tool.
- **Generated Architectures & Artifacts**: The resulting microservice decompositions, including service boundaries and recommendations for data-centric design patterns (e.g., *CQRS, Saga, API Composition, and Event Sourcing*).
- **Archi Dataset Extracts**: Sample data from the newly developed *Archi Dataset* (comprising academic and well-known open-source microservice projects) used to validate the tool's architectural decision-making capabilities.

## 🚀 How to Test the Examples

To test these examples using the ArchiLLM interactive assistant, follow these steps:

1. **Start the ArchiLLM Interface** Make sure you have completed the installation and `.env` configuration as outlined in the [main README](../README.md). From the root of the repository, launch the Streamlit app:
   ```bash
   streamlit run src/main.py
