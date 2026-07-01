import subprocess
handles = ['jukan05', 'aleabitoreddit', 'zephyr_z9', 'austinsemis']
for h in handles:
    print(f"\n=== 抓 {h} ===", flush=True)
    try:
        r = subprocess.run(['python3', '/workspace/scripts/intel_incremental_scrape.py', '--kol', h],
                           capture_output=True, text=True, timeout=120)
        # 找 new_persisted 行
        for line in r.stdout.split('\n'):
            if any(k in line for k in ['new_persisted', 'fetched', 'error', 'actor 返']):
                print('  ', line)
    except Exception as e:
        print(f'  ERROR: {e}')
