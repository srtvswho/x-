"""resolve + 拉 1 年日价"""
import json, os, sys
sys.path.insert(0, "/workspace")
# 通过 mcp 工具 resolve
from concurrent.futures import ThreadPoolExecutor

tickers = ["SIVE", "SIVEF", "AAOI", "IQE", "AXTI", "SOI", "MSS", "XFAB", "LPK", "FOCI", "AEHR", "TOWA", "FLNC", "NBIS", "JBL", "RDDT", "COHR", "FORM", "ONTO", "VIAV", "FN", "CRDO", "CDNS", "KEYS", "TER", "VICR", "ATKR", "POWL", "CLF", "GFS", "ASX", "AMKR", "LASR", "NGK", "HPS.A", "HOOD", "ARM", "DELL", "AAPL", "GOOGL", "AMZN", "INTC", "QCOM", "MRVL", "AVGO", "TSM", "AMAT", "LRCX", "KLAC", "SNPS", "TSLA", "MU", "WDC", "STX", "LITE", "NVDA", "AMD", "MSTR", "COIN", "PLTR", "SMCI", "MARA", "RIOT", "POET", "INVZ", "VRT", "MDB", "CRWV", "TSEM", "SKC", "HB", "CLS", "AHR", "CAMT", "PL", "FN", "HUT", "WULF", "CIFR", "WYFI", "IREN", "SLNH", "RPI", "SPCX", "SIVE", "TSEM", "688017.SH", "000660.KS", "005930.KS", "688017"]
tickers = sorted(set(tickers))
print(f"total: {len(tickers)}")
# 输出 JSON list 给后续 mcp 工具调用
json.dump(tickers, open("/workspace/logs/p5_industry_judgments/new_tickers_resolve.json", "w"))
