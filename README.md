# Aptos Wallet Explorer

An interactive blockchain analytics tool that provides insights into Aptos wallet activity.

## Features

- Wallet profile generation and analysis
- Transaction timeline visualization
- Function call network graph
- LLM-powered health assessment and insights
- Entity and activity extraction

## Installation

1. Install requirements:

```bash
pip install -r requirements.txt
```

2. If using OpenAI or another LLM provider, set up your API key:

```bash
export OPENAI_API_KEY=your_api_key_here
# or for local LLM
export LLM_BASE_URL=http://localhost:1234/v1/
```

## Usage

### Web Interface

1. Start the Flask web server:

```bash
python app.py
```

2. Navigate to `http://localhost:8080` in your web browser
3. Enter an Aptos wallet address and analyze

### Command Line

You can also use the command-line tool to analyze a wallet:

```bash
python main.py 0xYourWalletAddressHere
```

## Visualizations

To generate standalone visualizations:

```bash
python viz.py 0xYourWalletAddressHere
```

## Dependencies

- Flask
- Plotly
- NetworkX
- Pandas
- OpenAI (or compatible LLM)
- Dash Bootstrap Components
- Matplotlib
