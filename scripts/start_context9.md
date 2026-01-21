```shell
# 基本使用（使用默认值）
python scripts/start.py --config_file config.yaml

# 指定所有参数
python scripts/start.py \
  --config_file config.yaml \
  --github_sync_interval 300 \
  --port 8011 \
  --panel_port 8012

# 使用 webhook 模式
python scripts/start.py \
  --config_file config.yaml \
  --enable_github_webhook \
  --port 8011 \
  --panel_port 8012
```