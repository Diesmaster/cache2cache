# Python Library Structure

```
my_library/                  # Main package directory
├── my_library/             # Actual Python package
│   ├── __init__.py         # Makes the directory a package
│   ├── core.py             # Core functionality
│   └── submodule/          # Optional submodule
│       ├── __init__.py
│       └── submodule.py
├── tests/                  # Test directory
│   ├── __init__.py
│   └── test_core.py
├── docs/                   # Documentation
│   └── index.md
├── examples/               # Usage examples
│   └── basic_usage.py
├── .gitignore              # Git ignore file
├── LICENSE                 # License file
├── README.md               # Project readme
├── pyproject.toml          # Modern build configuration
└── setup.py                # Setup script (for compatibility)
```
