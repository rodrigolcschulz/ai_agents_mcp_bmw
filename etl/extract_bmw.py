import kagglehub

# Download latest version
path = kagglehub.dataset_download("sidraaazam/bmw-global-sales-analysis")

print("Path to dataset files:", path)