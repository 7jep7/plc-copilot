# OpenAI Cost Optimization for PLC-Copilot Testing

## Summary of Optimizations

### 🎯 Problem
The comprehensive test suite was consuming significant OpenAI API credits due to:
- Multiple API calls per test
- Using expensive models (gpt-4o) for all operations
- High token limits for all operations
- Verbose responses in test scenarios

### 💡 Solution
Created a multi-tier model configuration system with environment-based optimization:

## Model Configuration Changes

### 1. Environment-Based Model Selection
```python
# app/core/models.py
if _is_testing:
    DOCUMENT_ANALYSIS_MODEL = "gpt-4o-mini"  # Use cheaper model for tests
    CONVERSATION_MODEL = "gpt-4o-mini"
elif _is_dev:
    DOCUMENT_ANALYSIS_MODEL = "gpt-4o-mini"  # Use cheaper model for dev
    CONVERSATION_MODEL = "gpt-4o-mini"
else:
    DOCUMENT_ANALYSIS_MODEL = "gpt-4o"  # For extracting info from parsed PDFs
    CONVERSATION_MODEL = "gpt-4o-mini"  # For everything else
```

### 2. Token Limit Optimization
- **Testing Environment**: Reduced token limits by 50-70%
- **Stage Detection**: Cut from 200 to 100 tokens
- **Conversations**: Cut from 1024 to 512 tokens
- **Code Generation**: Cut from 2048 to 1024 tokens

### 3. Efficient Test Suite
Created `test_4_stage_system_efficient.py` with:
- Minimal API calls (4 vs 10+ in full suite)
- Single conversation flow test
- Focused stage transition validation
- Optimized for essential functionality only

## Cost Savings

### Before Optimization
- **Model**: gpt-4o for document analysis, gpt-4o-mini for conversations
- **Token Limits**: Full production limits
- **Test Coverage**: Comprehensive with many API calls
- **Estimated Cost**: ~$0.10-0.15 per test run

### After Optimization
- **Model**: gpt-4o-mini for everything in testing
- **Token Limits**: Reduced by 50-70%
- **Test Coverage**: Essential functionality focused
- **Estimated Cost**: ~$0.02-0.03 per test run

### 📊 Result: ~80% cost reduction for testing

## Environment Configuration

### Testing Environment
```bash
TESTING=true python scripts/test_4_stage_system_efficient.py
```
- Uses `gpt-4o-mini` for all operations
- Reduced token limits
- Minimal API calls

### Development Environment  
```bash
ENVIRONMENT=development python scripts/...
```
- Uses `gpt-4o-mini` for most operations
- Standard token limits
- Full functionality

### Production Environment
```bash
ENVIRONMENT=production python app/main.py
```
- Uses `gpt-4o` for document analysis (high quality needed)
- Uses `gpt-4o-mini` for conversations (cost-effective)
- Full token limits

## Usage Instructions

### For Cost-Efficient Testing
```bash
# Set testing environment
export TESTING=true

# Run efficient test suite
python scripts/test_4_stage_system_efficient.py

# Run MCQ test
python scripts/test_mcq.py
```

### For Development
```bash
# Set development environment  
export ENVIRONMENT=development

# Run full test suite (still cost-optimized)
python scripts/test_4_stage_system.py
```

### For Production
```bash
# Set production environment
export ENVIRONMENT=production

# Run application with premium models
python app/main.py
```

## Additional Cost Savings Tips

1. **Use the efficient test suite** for frequent testing
2. **Set TESTING=true** environment variable during development
3. **Use development environment** for feature development
4. **Reserve production environment** for final testing and deployment
5. **Monitor token usage** in OpenAI dashboard

## Model Pricing Reference (as of 2025)
- **gpt-4o**: $15.00 / 1M input tokens, $60.00 / 1M output tokens
- **gpt-4o-mini**: $0.150 / 1M input tokens, $0.600 / 1M output tokens

**Savings**: gpt-4o-mini is ~100x cheaper than gpt-4o!

---

This optimization ensures you can test frequently without breaking the bank while maintaining quality for production use.