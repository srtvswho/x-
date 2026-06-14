"""支持 `python -m signalboard scraper ...` 调用 scraper CLI。"""
import sys

from .scraper import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
