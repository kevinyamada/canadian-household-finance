import json
from pathlib import Path
import modal

app = modal.App('household-finance-gpu-audit')
image = modal.Image.debian_slim(python_version='3.12').pip_install('torch==2.6.0', 'numpy==2.2.6')
CONFIGS = [{'width': width, 'decay': decay, 'epochs': epochs}
           for width in [32, 64] for decay in [0.01, 0.1] for epochs in [250, 750]]
GPU_RATE = 0.001097


@app.function(image=image, gpu='H100!', cpu=(1, 2), memory=(4096, 8192),
              max_containers=8, scaledown_window=2, timeout=1180, startup_timeout=60, retries=0)
def experiment(job):
    import math
    import subprocess
    import time
    import numpy as np
    import torch
    from torch import nn

    started = time.monotonic()
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = True
    assert torch.cuda.is_available()
    payload, config = job['payload'], job['config']
    seconds = job['seconds']
    assert 0 < seconds <= 1150
    device = torch.device('cuda')
    seeds_per_batch = 8
    folds = len(payload['metadata'])
    base = {key: torch.tensor(payload[key], device=device, dtype=torch.float32)
            for key in ['x', 'y', 'mask', 'query']}
    tensors = {key: value.repeat_interleave(seeds_per_batch, dim=0) for key, value in base.items()}
    networks = folds * seeds_per_batch

    class Ensemble(nn.Module):
        def __init__(self):
            super().__init__()
            sizes = [len(payload['features']), config['width'], config['width'], 1]
            self.weights = nn.ParameterList()
            self.biases = nn.ParameterList()
            for first, second in zip(sizes[:-1], sizes[1:]):
                weight = torch.empty(networks, first, second, device=device)
                nn.init.uniform_(weight, -1 / math.sqrt(first), 1 / math.sqrt(first))
                self.weights.append(nn.Parameter(weight))
                self.biases.append(nn.Parameter(torch.zeros(networks, 1, second, device=device)))

        def forward(self, value):
            for index, (weight, bias) in enumerate(zip(self.weights, self.biases)):
                value = torch.bmm(value, weight) + bias
                if index < len(self.weights) - 1:
                    value = torch.tanh(value)
            return value

    predictions, trace = [], []
    batch = 0
    while time.monotonic() - started < seconds:
        torch.manual_seed(469 + batch)
        torch.cuda.manual_seed_all(469 + batch)
        model = Ensemble()
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=config['decay'])
        complete = True
        for epoch in range(config['epochs']):
            optimizer.zero_grad(set_to_none=True)
            residual = model(tensors['x']) - tensors['y']
            loss_by_network = (residual.square() * tensors['mask']).sum((1, 2)) / tensors['mask'].sum((1, 2))
            loss = loss_by_network.sum()
            loss.backward()
            optimizer.step()
            if epoch % 25 == 0 and time.monotonic() - started >= seconds:
                complete = False
                break
        torch.cuda.synchronize()
        if not complete:
            break
        with torch.no_grad():
            values = model(tensors['query']).reshape(folds, seeds_per_batch).cpu().numpy()
        assert np.isfinite(values).all()
        predictions.append(values.tolist())
        batch += 1
        stats = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                                '--format=csv,noheader,nounits'], capture_output=True, text=True).stdout.strip()
        trace.append({'batch': batch, 'elapsed_seconds': time.monotonic() - started,
                      'mean_training_loss': float(loss_by_network.mean().detach().cpu()),
                      'gpu_utilization_and_memory': stats})
        print(json.dumps({'config': config, 'complete_seeds': batch * seeds_per_batch,
                          'elapsed_seconds': round(time.monotonic() - started, 1)}), flush=True)
    assert predictions, 'No complete seed batch within time limit'
    torch.cuda.synchronize()
    elapsed = time.monotonic() - started
    return {'config': config, 'predictions_standardized_change': predictions,
            'trace': trace, 'elapsed_seconds': elapsed, 'gpu': torch.cuda.get_device_name(),
            'torch_version': str(torch.__version__), 'cuda_version': torch.version.cuda,
            'seeds_per_batch': seeds_per_batch, 'complete_batches': batch,
            'estimated_gpu_cost_usd': elapsed * GPU_RATE,
            'source_sha256': payload['source_sha256']}


@app.local_entrypoint()
def main(smoke: bool = False):
    import numpy as np
    root = Path(__file__).resolve().parent
    payload = json.loads((root / 'input.json').read_text(encoding='utf-8'))
    output = root / 'results'
    output.mkdir(exist_ok=True)
    configs = [dict(CONFIGS[0], epochs=25)] if smoke else CONFIGS
    seconds = 30 if smoke else 1150
    jobs = [{'payload': payload, 'config': config, 'seconds': seconds} for config in configs]
    for index, result in enumerate(experiment.map(jobs, order_outputs=True)):
        name = 'smoke' if smoke else f'config_{index}'
        predictions = np.array(result.pop('predictions_standardized_change'), dtype=np.float32)
        np.savez_compressed(output / (name + '.npz'), predictions=predictions)
        (output / (name + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'saved': name, 'batches': result['complete_batches'],
                          'estimated_gpu_cost_usd': result['estimated_gpu_cost_usd']}), flush=True)
