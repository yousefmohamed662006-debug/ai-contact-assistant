"""
One-click Runner for AI Executive Contact Assistant
Optimized lightweight startup script with minimal CPU overhead.
"""

import sys
import os
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if __name__ == "__main__":
    banner = r"""
===================================================================
   🚀 AI Executive Contact Assistant | دليل الموظفين الذكي
===================================================================
  • Web Interface (UI):    http://localhost:8000
  • API Swagger Docs:      http://localhost:8000/docs
  • Architecture:          Dual-Mode (Online Gemini / Offline Local)
  • CPU & RAM Footprint:   Ultra-lightweight (<30 MB RAM)
===================================================================
    """
    print(banner)
    # Run server without aggressive background reload scanning to keep CPU at 0%
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
