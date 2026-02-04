# Agent Quick Start Guide

> **For**: AI Coding Agents starting implementation
> 
> **Time to read**: 5 minutes
>
> **Purpose**: Get started immediately with clear first steps

---

## 🚀 Start Here

### Step 1: Read These Documents (30 minutes)

**Required reading in this order**:

1. **PYTHON_PORT_SUMMARY.md** (10 min)
   - Understand the "why" and "what"
   - Review feasibility and tech stack
   
2. **IMPLEMENTATION_PLAN.md** (15 min)
   - Understand the execution plan
   - Review phase structure
   
3. **PYTHON_PORT_QUICK_REFERENCE.md** (5 min)
   - Bookmark for quick lookup
   - Review code templates

**Optional (for deep dive)**:
- PYTHON_PORT_GUIDE.md (1-2 hours) - Complete implementation details
- PYTHON_PORT_ROADMAP.md (30 min) - Detailed project roadmap

---

## 🎯 Your First Day

### Morning: Setup (2-3 hours)

#### Task 1: Initialize Repository (30 min)

```bash
# Create repository
mkdir conduit-py
cd conduit-py
git init

# Create basic files
touch README.md LICENSE .gitignore

# Initial commit
git add .
git commit -m "Initial commit"
```

#### Task 2: Create Project Structure (30 min)

```bash
# Create directory structure
mkdir -p src/conduit/{core,schema,providers,interceptors,tools,agent,rag,memory,flow,streaming,structured,errors,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p examples docs

# Create __init__.py files
touch src/conduit/__init__.py
touch src/conduit/{core,schema,providers,interceptors,tools,agent,rag,memory,flow,streaming,structured,errors,utils}/__init__.py

# Create py.typed marker
touch src/conduit/py.typed
```

#### Task 3: Setup Poetry (1 hour)

Create `pyproject.toml`:

```toml
[tool.poetry]
name = "conduit-py"
version = "0.1.0"
description = "Simple, functional LLM orchestration for Python"
authors = ["Your Name <you@example.com>"]
license = "MIT"
readme = "README.md"
packages = [{include = "conduit", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.0"
httpx = "^0.27"
numpy = "^1.26"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
pytest-httpx = "^0.30"
mypy = "^1.8"
ruff = "^0.1"
black = "^24.0"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "B", "UP", "ANN"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Install dependencies:

```bash
poetry install
```

Verify setup:

```bash
poetry run pytest --version
poetry run mypy --version
poetry run black --version
```

### Afternoon: First Code (3-4 hours)

#### Task 4: Implement Error Classes (1 hour)

**File**: `src/conduit/errors/base.py`

Copy the error class implementation from IMPLEMENTATION_PLAN.md Task 1.1

**File**: `tests/unit/test_errors.py`

Copy the test implementation from IMPLEMENTATION_PLAN.md Task 1.1

**Validate**:
```bash
poetry run pytest tests/unit/test_errors.py -v
poetry run mypy src/conduit/errors
```

#### Task 5: Implement Message Schema (2 hours)

**File**: `src/conduit/schema/messages.py`

Copy the implementation from IMPLEMENTATION_PLAN.md Task 1.2

**File**: `tests/unit/test_messages.py`

Create tests:

```python
"""Tests for message schemas."""

import pytest
from pydantic import ValidationError
from conduit.schema.messages import Message, TextBlock, ImageBlock, ImageSource


def test_simple_message():
    """Test simple text message."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_message_with_blocks():
    """Test message with content blocks."""
    msg = Message(
        role="user",
        content=[
            TextBlock(text="What's in this image?"),
            ImageBlock(
                source=ImageSource(
                    type="url",
                    url="https://example.com/image.jpg"
                )
            )
        ]
    )
    assert len(msg.content) == 2


def test_invalid_role():
    """Test invalid role raises error."""
    with pytest.raises(ValidationError):
        Message(role="invalid", content="test")


def test_message_serialization():
    """Test message can be serialized."""
    msg = Message(role="user", content="Hello")
    data = msg.model_dump()
    assert data["role"] == "user"
    assert data["content"] == "Hello"
```

**Validate**:
```bash
poetry run pytest tests/unit/test_messages.py -v
poetry run mypy src/conduit/schema
```

---

## 📋 Daily Workflow

### Every Morning

1. **Review progress**:
   - Check what you completed yesterday
   - Review today's tasks
   - Check for blockers

2. **Pull latest code** (if team):
   ```bash
   git pull origin develop
   ```

3. **Run tests**:
   ```bash
   poetry run pytest
   ```

### During Development

1. **Write test first**:
   ```python
   # tests/unit/test_feature.py
   def test_new_feature():
       """Test new feature."""
       result = new_feature()
       assert result == expected
   ```

2. **Implement feature**:
   ```python
   # src/conduit/module.py
   def new_feature():
       """Implement feature."""
       return result
   ```

3. **Run tests frequently**:
   ```bash
   poetry run pytest tests/unit/test_feature.py -v
   ```

4. **Check types**:
   ```bash
   poetry run mypy src/conduit/module.py
   ```

5. **Format code**:
   ```bash
   poetry run black src/conduit/module.py
   poetry run ruff check src/conduit/module.py
   ```

### Before Committing

```bash
# Run all checks
poetry run pytest
poetry run mypy src/conduit
poetry run ruff check src/conduit
poetry run black src/conduit --check

# If all pass, commit
git add .
git commit -m "feat: implement feature X"
git push
```

---

## 🎓 Learning Resources

### Essential Reading

1. **Pydantic v2**: https://docs.pydantic.dev/
   - Models and validation
   - Field types and constraints
   - JSON schema generation

2. **httpx**: https://www.python-httpx.org/
   - Async client
   - Streaming responses
   - Error handling

3. **Python asyncio**: https://docs.python.org/3/library/asyncio.html
   - Async/await syntax
   - AsyncIterator
   - Context managers

### Code Templates

All templates are in PYTHON_PORT_QUICK_REFERENCE.md:
- Basic chat example
- Streaming example
- Tool calling example
- Interceptor example
- RAG pipeline example

---

## 🔍 Quick Reference

### Common Commands

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/test_errors.py -v

# Run with coverage
poetry run pytest --cov=conduit --cov-report=term-missing

# Type check
poetry run mypy src/conduit

# Lint
poetry run ruff check src/conduit

# Format
poetry run black src/conduit

# Install new dependency
poetry add package-name

# Install dev dependency
poetry add --group dev package-name
```

### Project Structure

```
conduit-py/
├── src/conduit/          # Source code
│   ├── core/            # Protocols, base classes
│   ├── schema/          # Pydantic models
│   ├── providers/       # LLM provider implementations
│   ├── interceptors/    # Middleware
│   ├── tools/           # Tool calling
│   ├── agent/           # Agent loops
│   └── rag/             # RAG pipeline
├── tests/               # Tests
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
└── examples/           # Example code
```

### File Naming

- Source: `snake_case.py`
- Tests: `test_snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

---

## ✅ Phase 1 Checklist

Complete these in order:

### Week 1: Foundation

- [ ] **Day 1**: Setup project structure
- [ ] **Day 1**: Implement error classes
- [ ] **Day 2**: Implement message schemas
- [ ] **Day 2**: Implement response schemas
- [ ] **Day 3**: Implement options schema
- [ ] **Day 3**: Implement core protocols
- [ ] **Day 4**: Write comprehensive tests
- [ ] **Day 5**: Fix any issues, improve coverage

**Success Criteria**:
- ✅ All tests passing
- ✅ >90% coverage
- ✅ 0 type errors
- ✅ 0 linting errors

### Week 2: OpenAI Provider

- [ ] **Day 1**: Implement OpenAI base class
- [ ] **Day 2**: Implement chat method
- [ ] **Day 3**: Implement streaming
- [ ] **Day 4**: Implement tool calling
- [ ] **Day 5**: Write integration tests

**Success Criteria**:
- ✅ OpenAI provider fully functional
- ✅ All features working
- ✅ >85% coverage
- ✅ Integration tests passing

---

## 🚨 Common Mistakes to Avoid

### ❌ Don't Do This

```python
# Missing type hints
def process(data):
    return data.upper()

# Blocking I/O in async
async def fetch():
    return requests.get(url)  # Wrong!

# Bare except
try:
    result = await model.chat(messages)
except:
    print("Error")

# Plain dict instead of Pydantic
def create_message(role, content):
    return {"role": role, "content": content}
```

### ✅ Do This Instead

```python
# Complete type hints
def process(data: str) -> str:
    return data.upper()

# Async I/O
async def fetch() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Specific exceptions
try:
    result = await model.chat(messages)
except httpx.HTTPError as e:
    raise ProviderError(f"API error: {e}") from e

# Pydantic models
def create_message(role: str, content: str) -> Message:
    return Message(role=role, content=content)
```

---

## 💡 Pro Tips

### Tip 1: Use TDD

Write tests first, then implement:

```python
# 1. Write failing test
def test_feature():
    assert feature() == "result"

# 2. Implement to pass test
def feature() -> str:
    return "result"

# 3. Refactor if needed
```

### Tip 2: Run Tests Frequently

Don't accumulate errors:

```bash
# After every change
poetry run pytest tests/unit/test_current.py -v

# Before committing
poetry run pytest
```

### Tip 3: Use Type Hints Everywhere

Let mypy catch errors:

```python
# Good
def process(data: str, count: int = 5) -> list[str]:
    return [data] * count

# Bad
def process(data, count=5):
    return [data] * count
```

### Tip 4: Document as You Go

Don't leave it for later:

```python
def complex_function(param: str) -> dict:
    """Short description.
    
    Longer description with details.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
        
    Examples:
        >>> complex_function("test")
        {"result": "test"}
    """
    ...
```

### Tip 5: Use Code Templates

Don't reinvent the wheel - copy templates from PYTHON_PORT_GUIDE.md

---

## 🎯 Success Metrics

### After Day 1

- ✅ Project structure created
- ✅ Poetry configured
- ✅ Dependencies installed
- ✅ Can run pytest, mypy, black

### After Week 1

- ✅ Error classes complete
- ✅ All schemas implemented
- ✅ Core protocols defined
- ✅ >90% test coverage
- ✅ All type checks passing

### After Week 2

- ✅ OpenAI provider working
- ✅ Can chat with GPT-4
- ✅ Streaming functional
- ✅ Tool calling works
- ✅ Integration tests passing

---

## 📞 Getting Help

### Documentation

1. **IMPLEMENTATION_PLAN.md** - Detailed task breakdown
2. **PYTHON_PORT_GUIDE.md** - Complete implementation guide
3. **PYTHON_PORT_QUICK_REFERENCE.md** - Quick patterns
4. **PYTHON_PORT_ROADMAP.md** - Project phases

### External Resources

- [Pydantic Docs](https://docs.pydantic.dev/)
- [httpx Docs](https://www.python-httpx.org/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Code Examples

Look in PYTHON_PORT_GUIDE.md:
- Module 3: Provider implementation
- Module 4: Interceptor implementation
- Module 5: Tool implementation

---

## 🎉 You're Ready!

You now have:
- ✅ Clear understanding of the project
- ✅ Development environment setup
- ✅ First tasks identified
- ✅ Reference documentation
- ✅ Code templates
- ✅ Testing strategy

**Next step**: Start with Task 1.1 in IMPLEMENTATION_PLAN.md

**Remember**:
1. Write tests first
2. Use type hints everywhere
3. Follow the templates
4. Run checks frequently
5. Document as you go

**Good luck! 🚀**

---

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Next Review**: After Phase 1 completion
