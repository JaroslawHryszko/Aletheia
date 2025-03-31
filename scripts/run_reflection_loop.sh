#!/bin/bash
echo "🔄 Reflektor: running reflection cycle..."
PYTHONPATH=$(pwd) python -m aletheia.scheduler.main
