# Migration from Ollama to OpenAI with LlamaIndex

This document outlines the migration from Ollama (local LLM) to OpenAI via LlamaIndex for the resume tailoring functionality.

## Summary of Changes

### 1. Dependencies Updated (`pyproject.toml`)
**Removed:**
- `ollama = "^0.1.0"`

**Added:**
- `llama-index = "^0.10.0"`
- `llama-index-llms-openai = "^0.1.0"`
- `openai = "^1.0.0"`

### 2. Resume Tailor Module (`resume_tailor.py`)
**Changes:**
- Replaced `import ollama` with LlamaIndex imports
- Updated `ResumeTailor.__init__()` to accept OpenAI API key and model
- Changed from Ollama's `ollama.chat()` to LlamaIndex's `llm.chat()`
- Updated availability check to verify OpenAI API key instead of Ollama service
- Default model changed from `llama3.1` to `gpt-4o-mini`

**API Changes:**
```python
# Before (Ollama)
response = ollama.chat(
    model=self.model,
    messages=[...],
    options={"temperature": 0.7, "num_predict": 3000}
)
tailored_resume = response['message']['content']

# After (OpenAI via LlamaIndex)
messages = [ChatMessage(role="system", content=...), ...]
response = self.llm.chat(messages, temperature=0.7, max_tokens=3000)
tailored_resume = response.message.content
```

### 3. Resume Parser Module (`resume_parser.py`)
**Changes:**
- Replaced `import ollama` with LlamaIndex imports
- Updated `LLMResumeParser.__init__()` to accept OpenAI API key and model
- Changed from Ollama's API to LlamaIndex's OpenAI integration
- Updated error messages to reference OpenAI instead of Ollama

### 4. Streamlit App (`app.py`)
**Changes:**
- Removed `import ollama`
- Updated availability check from `ollama.list()` to checking `OPENAI_API_KEY` env var
- Changed model selection from Ollama models to OpenAI models:
  - `gpt-4o`
  - `gpt-4o-mini` (default)
  - `gpt-4-turbo`
  - `gpt-3.5-turbo`
- Updated UI messages and instructions

### 5. Environment Configuration (`.env.example`)
**Before:**
```bash
OLLAMA_MODEL=llama3.1
```

**After:**
```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 6. Documentation (`README.md`)
**Updated:**
- Prerequisites section: Ollama → OpenAI API Key
- Installation instructions: Ollama setup → OpenAI API key configuration
- Feature descriptions: "local AI" → "OpenAI via LlamaIndex"

## Migration Steps for Users

### 1. Install New Dependencies
```bash
poetry install
```

### 2. Configure OpenAI API Key
```bash
# Copy example file
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=your-api-key-here
```

Or set environment variable:
```bash
export OPENAI_API_KEY=your-api-key-here
```

### 3. Remove Ollama (Optional)
If you no longer need Ollama:
```bash
# On macOS
brew uninstall ollama

# Or just stop the service
# Ollama is no longer required
```

### 4. Restart the Application
```bash
poetry shell
streamlit run app.py
```

## Benefits of Migration

### ✅ Advantages
1. **No Local Installation**: No need to install and run Ollama locally
2. **Better Performance**: OpenAI models are generally faster and more accurate
3. **Consistent Results**: Cloud-based models provide more consistent outputs
4. **Latest Models**: Access to GPT-4o and other cutting-edge models
5. **Easier Setup**: Just need an API key, no local model management

### ⚠️ Considerations
1. **API Costs**: OpenAI charges per token (but gpt-4o-mini is very affordable)
2. **Internet Required**: Needs internet connection (Ollama worked offline)
3. **Data Privacy**: Resume data sent to OpenAI (vs. local processing with Ollama)

## Cost Estimation

Using **gpt-4o-mini** (recommended):
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

Typical resume tailoring:
- Input: ~5,000 tokens (resume + job description)
- Output: ~3,000 tokens (tailored resume)
- **Cost per resume: ~$0.002 (less than a penny!)**

For 100 tailored resumes: ~$0.20

## Model Recommendations

### For Most Users: `gpt-4o-mini`
- **Best balance** of cost and quality
- Fast responses
- Very affordable
- Default in the app

### For Maximum Quality: `gpt-4o`
- Highest quality outputs
- Best for complex resumes
- ~10x more expensive than gpt-4o-mini

### For Budget: `gpt-3.5-turbo`
- Cheapest option
- Still good quality
- Faster than GPT-4 models

## Rollback Instructions

If you need to revert to Ollama:

1. Checkout the previous commit before migration
2. Run `poetry install` to restore Ollama dependency
3. Install and start Ollama
4. Pull a model: `ollama pull llama3.1`

## Support

For issues or questions:
1. Check that `OPENAI_API_KEY` is set correctly
2. Verify API key is valid at https://platform.openai.com/api-keys
3. Ensure you have API credits in your OpenAI account
4. Check the Streamlit app for error messages

## Technical Details

### LlamaIndex Integration
LlamaIndex provides a unified interface for working with LLMs. Key features used:
- `OpenAI` class for model initialization
- `ChatMessage` for message formatting
- Consistent API across different LLM providers

### Future Extensibility
The LlamaIndex integration makes it easy to:
- Switch between different LLM providers (Anthropic, Cohere, etc.)
- Add RAG (Retrieval Augmented Generation) capabilities
- Implement more advanced prompting strategies
- Use embeddings for semantic search

## Changelog

### Version 2.0.0 (2026-02-15)
- **BREAKING**: Migrated from Ollama to OpenAI via LlamaIndex
- Added LlamaIndex and OpenAI dependencies
- Updated all AI-powered features to use OpenAI
- Improved error handling and user feedback
- Updated documentation and setup instructions
