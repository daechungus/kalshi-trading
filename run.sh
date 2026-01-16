#!/bin/bash
# Quick run script for common commands

# Example: ./run.sh info HIGHNY-25JAN16
# Example: ./run.sh backtest HIGHNY-25JAN16
# Example: ./run.sh live HIGHNY-25JAN16

COMMAND=$1
TICKER=$2

if [ -z "$COMMAND" ] || [ -z "$TICKER" ]; then
    echo "Usage: ./run.sh <command> <ticker>"
    echo ""
    echo "Commands:"
    echo "  info       - Get market information"
    echo "  backtest   - Run backtest"
    echo "  live       - Run live trading (dry run)"
    echo ""
    echo "Example:"
    echo "  ./run.sh info HIGHNY-25JAN16"
    echo "  ./run.sh backtest HIGHNY-25JAN16"
    exit 1
fi

uv run python main.py $COMMAND --ticker $TICKER "${@:3}"
