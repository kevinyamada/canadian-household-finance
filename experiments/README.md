# Modal GPU experiment

Question: does a neural alternative improve the next unpublished quarter estimate enough to justify more complexity?

This is an exploratory extension of the original study. The 2019 to 2026 results were already known when it was designed. Later neural results must not be described as a fresh untouched test.

## Design

Eight configurations combine hidden widths 32 and 64, AdamW weight decay 0.01 and 0.1, and 250 or 750 epochs. Each network has two tanh hidden layers and the same eight input features as the original models. The learning rate is 0.003. Each expanding window fits its own normalization and parameters. Training labels end no later than the forecast origin. Standardization of the target also uses training data only.

Independent networks are fitted in batches of eight seed replicates across 79 origins, including the next unpublished quarter. Batch b uses Torch seed 469 + b. Network initializations differ across origins and replicas. There are no shared model parameters across windows. Mean squared error is normalized within each window and summed across independent networks.

The experiment uses eight H100 workers for up to 1,150 seconds each. Completed batches are retained, incomplete batches are discarded. Every configuration is compared using the same number of first completed seed replicates. Selection uses the 2007Q1 to 2018Q4 ensemble MAE only. Test errors and seed variation are descriptive diagnostics. The 0.10 percentage point worsening flag is an illustrative monitoring threshold specified before the GPU result, not a bank policy.

The fixed compute allowance was requested for this project. It is not evidence that a small quarterly dataset requires expensive GPUs. Repeated seeds measure algorithmic stability and do not increase the number of economic observations.

## Reproduce without GPU charges

The committed compressed result files contain complete seed predictions and runtime traces. From the project root:

```powershell
.\.venv\Scripts\python.exe experiments\summarize_gpu.py
```

This regenerates the analysis tables, figure and written GPU report on the CPU. It checks the canonical source data digest before processing the saved results. Close Power BI before rebuilding its report with src/build_powerbi.py.

## Start another paid run

Only run these commands if another GPU charge is intended. Repeating the full experiment adds approximately US$10 in GPU runtime plus other usage costs.

```powershell
.\.venv\Scripts\python.exe -m pip install -r experiments\requirements.txt
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe experiments\prepare_gpu.py
.\.venv\Scripts\python.exe -m modal run experiments\gpu_benchmark.py --smoke
.\.venv\Scripts\python.exe -m modal run experiments\gpu_benchmark.py
.\.venv\Scripts\python.exe experiments\summarize_gpu.py
```

The main run requests H100 exactly, up to eight containers, one requested CPU core with a two core cap, and 4 GiB memory with an 8 GiB cap. Each worker has a 1,180 second execution timeout, a 60 second startup timeout, zero retries and a two second scale down window. No persistent deployment or recurring job is created.

Runtime based GPU cost estimates exclude startup, image builds, CPU and memory. Modal billing remains authoritative. The initial smoke attempt trained successfully but failed to deserialize the Torch version object locally; that was fixed by returning it as plain text. Its roughly 30 seconds of GPU work are additional to the saved successful smoke test.

[Modal pricing](https://modal.com/pricing) · [GPU configuration](https://modal.com/docs/guide/gpu)

## Reporting review experiment

This is a separate task from the neural forecast experiment. It checks whether supported and deliberately misleading report excerpts agree with real StatCan group evidence.

To regenerate the benchmark inputs without GPU spending:

```powershell
.\.venv\Scripts\python.exe src\segments.py
.\.venv\Scripts\python.exe experiments\prepare_audit.py
```

To summarize the saved results on the CPU:

```powershell
.\.venv\Scripts\python.exe experiments\summarize_audit.py
```

The summarizer verifies a canonical SHA256 hash of the cases and uses the same completed repetitions from every configuration. It selects the configuration using development results, then measures evaluation performance. Full response files retain partial tails even when those tails are excluded from the matched comparison.

The following command launches paid Modal work. It is not part of run.py or CI. Do not run it just to reproduce the published tables.

```powershell
.\.venv\Scripts\python.exe -m modal run experiments\modal_audit.py
```

The full experiment uses eight H100 workers with 2,280 second work budgets. Each worker evaluates a model and prompt combination across repeated generation seeds. Model download occurs in a CPU function first. The dedicated model cache volume can be removed after results are safely saved to avoid retaining unnecessary storage. A new run will download the public weights again if the volume has been removed.

The protocol was committed before the full run. Model revisions, the canonical input digest, response text, timing and estimated GPU cost are recorded with the outputs. The experiment measures controlled reporting mistakes, not actual fraud, audit assurance or production staff time saved.
