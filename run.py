import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from data import download, prepare
from models import run_models
from report import run_report
from build_powerbi import build

parser=argparse.ArgumentParser()
parser.add_argument('--refresh',action='store_true')
args=parser.parse_args()
download(refresh=args.refresh)
panel=prepare()
audit=run_models(panel)
summary=run_report(panel,audit)
gpu_summary=Path(__file__).resolve().parent/'experiments/input_metadata.json'
if gpu_summary.exists():
    sys.path.insert(0,str(gpu_summary.parent))
    from summarize_gpu import summarize
    summarize()
build()
print(json.dumps({'selected_model':audit['selected_model'],**summary},indent=2))
