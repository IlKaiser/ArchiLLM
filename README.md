# ArchiLLM: an LLM-based solution for the generation of microservices architectures

This repository contains code for the paper *"On the feasibility of identifying microservice early-stage architectures using LLMs"*.

## Overview

ArchiLLM leverages the capabilities of Large Language Models to assist in architectural modeling tasks, potentially focusing on enterprise architecture, software architecture, or system design. This project explores the intersection of AI and architectural modeling to streamline and enhance the design process.

## Features

- **AI-Powered Architecture Generation**: Utilize LLMs to generate architectural models from natural language descriptions
- **Model Analysis**: Analyze and validate architectural designs using AI capabilities
- **Interactive Design Assistant**: Chat-based interface for architectural design guidance
- **Export Capabilities**: Generate various architectural artifacts and documentation

## Prerequisites

- Python 3.8+
- Streamlit
- Required dependencies (see `requirements.txt`)
- API access to LLM services (if applicable)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/IlKaiser/ArchiLLM.git
cd ArchiLLM
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (if needed):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Basic Usage

Launch the Streamlit web application:

```bash
streamlit run src/main.py
```

This will start the ArchiLLM web interface, typically accessible at `http://localhost:8501`. The Streamlit app provides an interactive interface for:

- Inputting architectural requirements and descriptions
- Generating architectural models using LLMs
- Visualizing and editing the generated architectures
- Exporting results in various formats



## Configuration

Configuration options can be set through environment variables or a configuration file:

- `OPENAI_API_KEY`: API key for LLM services


## Research Context

This project is part of ongoing research at DIAG-Sapienza-BPM-Smart-Spaces focusing on:

- The application of LLMs in architectural modeling
- Automated generation of architectural artifacts
- AI-assisted design validation and optimization
- Integration with existing modeling frameworks

## Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Academic Use

If you use this project in your research, please cite:

```bibtex
@misc{calamo2025archillm,
  title={ArchiLLM: Architecture Modeling with Large Language Models},
  author={Calamo, Marco and others},
  year={2025},
  institution={DIAG-Sapienza-BPM-Smart-Spaces},
  url={https://github.com/IlKaiser/ArchiLLM}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Author**: Marco Calamo
- **Institution**: DIAG-Sapienza-BPM-Smart-Spaces, Sapienza University of Rome
- **Location**: Rome, Italy
- **ORCID**: [0009-0006-2602-9604](https://orcid.org/0009-0006-2602-9604)
- **GitHub**: [@IlKaiser](https://github.com/IlKaiser)


## Acknowledgments

- DIAG-Sapienza-BPM-Smart-Spaces research group
- Sapienza University of Rome
- Contributors and collaborators
