.PHONY: run install clean help

# Default target
help:
	@echo "Interior Design AI Assistant"
	@echo ""
	@echo "Usage:"
	@echo "  make install  - Install dependencies"
	@echo "  make run      - Run the Streamlit app"
	@echo "  make clean    - Clean output and cache files"
	@echo ""

# Install dependencies
install:
	uv sync

# Run the Streamlit app
run:
	uv run streamlit run src/interior_designer/app.py

# Clean output and cache
clean:
	rm -rf output/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
