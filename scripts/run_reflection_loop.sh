#!/bin/bash
echo "🔄 Reflektor: uruchamianie cyklu refleksji..."
PYTHONPATH=$(pwd) python -m aletheia.scheduler.main
