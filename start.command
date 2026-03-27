#!/bin/bash
cd "$(dirname "$0")"
/Users/colinpowers/miniconda3/bin/uvicorn api:app --host 0.0.0.0 --port 8000
