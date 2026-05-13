# Deployment Guide

This guide covers deploying youtube-transcript-exporter in production environments (cloud runners, CI/CD, scheduled jobs, etc.).

## Local Development Setup

### Prerequisites
- Python 3.8+
- Git
- ~10 GB free disk space (per 1000 videos)
- Stable internet connection

### Installation
```bash
git clone https://github.com/1jehuang/youtube_transcript_exporter.git
cd youtube_transcript_exporter
pip install -r requirements.txt
./export.sh --help
```

### Verify Installation
```bash
./export.sh --audit          # Check system health
python tests/test_all.py     # Run unit tests
```

## Docker Deployment

### Build Image
```bash
docker build -t ytexporter:latest .
```

### Run Container
```bash
docker run -v $(pwd)/out:/app/out \
           -v $(pwd)/markdown:/app/markdown \
           -v $(pwd)/db:/app/db \
           ytexporter:latest \
           ./export.sh --new-channel "https://youtube.com/@channelname"
```

### Docker Compose (Multiple Channels)
```yaml
version: '3.8'
services:
  ytexporter:
    build: .
    volumes:
      - ./out:/app/out
      - ./markdown:/app/markdown
      - ./db:/app/db
    environment:
      - TZ=UTC
    command: ./export.sh --batch url1 url2 url3
```

## CI/CD Deployment

### GitHub Actions
```yaml
name: Export Transcripts
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: ./export.sh --new-channel "${{ secrets.CHANNEL_URL }}"
      - run: ./export.sh --audit
      - uses: actions/upload-artifact@v3
        with:
          name: transcripts
          path: |
            markdown/
            db/
```

### GitLab CI
```yaml
export_transcripts:
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - ./export.sh --new-channel "$CHANNEL_URL"
    - ./export.sh --audit
  artifacts:
    paths:
      - markdown/
      - db/
  schedule:
    - cron: "0 2 * * *"
```

## Cloud Platform Deployment

### AWS Lambda + CloudWatch
```bash
# 1. Create Lambda function
aws lambda create-function \
  --function-name ytexporter \
  --runtime python3.11 \
  --handler index.handler \
  --zip-file fileb://lambda_package.zip

# 2. Schedule with CloudWatch Events
aws events put-rule --name ytexporter-daily --schedule-expression "cron(0 2 * * ? *)"
aws events put-targets --rule ytexporter-daily --targets "Id"="1","Arn"="arn:aws:lambda:..."
```

### Google Cloud Run
```bash
# 1. Create Dockerfile (provided)
# 2. Deploy
gcloud run deploy ytexporter \
  --source . \
  --platform managed \
  --memory 2Gi \
  --timeout 3600

# 3. Schedule with Cloud Scheduler
gcloud scheduler jobs create app-engine ytexporter-daily \
  --schedule="0 2 * * *" \
  --http-method=POST \
  --uri=https://ytexporter-xxxx.run.app/export
```

### Heroku
```bash
# 1. Create Procfile
echo "web: ./export.sh --audit" > Procfile

# 2. Deploy
git push heroku main

# 3. Scale dynos
heroku ps:scale worker=1

# 4. Schedule with Heroku Scheduler
heroku addons:create scheduler:standard
heroku addons:open scheduler
# Add: ./export.sh --batch CHANNEL_URL
```

## Self-Hosted Deployment

### Linux Server (Ubuntu/Debian)
```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install python3.11 python3-pip git

# 2. Clone repo
git clone https://github.com/1jehuang/youtube_transcript_exporter.git
cd youtube_transcript_exporter
pip install -r requirements.txt

# 3. Create systemd service
sudo tee /etc/systemd/system/ytexporter.service > /dev/null <<EOF
[Unit]
Description=YouTube Transcript Exporter
After=network.target

[Service]
Type=simple
User=ytexporter
WorkingDirectory=/home/ytexporter/youtube_transcript_exporter
ExecStart=/home/ytexporter/youtube_transcript_exporter/export.sh --audit
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start
sudo systemctl enable ytexporter
sudo systemctl start ytexporter
```

### macOS (Launchd)
```bash
# 1. Create plist file
cat > ~/Library/LaunchAgents/com.ytexporter.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ytexporter</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USER/youtube_transcript_exporter/export.sh</string>
        <string>--batch</string>
        <string>CHANNEL_URL1</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

# 2. Load
launchctl load ~/Library/LaunchAgents/com.ytexporter.plist
```

## Environment Configuration

### Environment Variables
```bash
# YouTube settings
export YT_TIMEOUT=600              # Request timeout (seconds)
export YT_MAX_RETRIES=10           # Retry attempts
export YT_BATCH_SIZE=500           # Videos per batch

# Notion (optional)
export NOTION_TOKEN="ntn_xxxx"
export NOTION_DATABASE_ID="xxxx"

# Paths
export OUTPUT_DIR="./out"
export MARKDOWN_DIR="./markdown"
export DB_PATH="./db/canonical.json"

# Logging
export LOG_LEVEL=INFO
export LOG_FILE="./logs/exporter.log"
```

### Config File
Create `.env`:
```
YT_TIMEOUT=600
YT_MAX_RETRIES=10
NOTION_TOKEN=ntn_xxxx
LOG_LEVEL=INFO
```

Then source it:
```bash
source .env
./export.sh --new-channel "URL"
```

## Monitoring & Health Checks

### Health Check Script
```bash
#!/bin/bash
# Check last run
LAST_RUN=$(stat -f%m db/canonical.json)
NOW=$(date +%s)
DIFF=$((NOW - LAST_RUN))

if [ $DIFF -gt 86400 ]; then
  echo "ERROR: Last run was $(($DIFF / 3600)) hours ago"
  exit 1
fi

# Check database integrity
python -c "import json; json.load(open('db/canonical.json'))" || exit 1

echo "HEALTHY"
exit 0
```

### Log Aggregation
```bash
# Send logs to CloudWatch
aws logs create-log-group --log-group-name ytexporter
aws logs put-retention-policy --log-group-name ytexporter --retention-in-days 30
```

## Backup & Disaster Recovery

### Automated Backup
```bash
#!/bin/bash
BACKUP_DIR="/backups/ytexporter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/transcripts_$DATE.tar.gz \
  markdown/ db/ out/
```

### Restore from Backup
```bash
tar -xzf transcripts_20260509_120000.tar.gz
```

## Scaling Considerations

| Scale | Resources | Approach |
|-------|-----------|----------|
| 1-10 channels | 1 CPU, 2 GB RAM | Local/Docker |
| 10-100 channels | 2 CPU, 4 GB RAM | Docker Compose / Cloud Run |
| 100+ channels | 4+ CPU, 8+ GB RAM | Kubernetes / managed databases |

### Kubernetes Deployment
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ytexporter
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ytexporter
            image: ytexporter:latest
            volumeMounts:
            - name: data
              mountPath: /app/data
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: ytexporter-pvc
          restartPolicy: OnFailure
```

## Troubleshooting Deployments

### Common Issues

**Container won't start**
```bash
docker logs ytexporter-container
# Check Python version, dependencies
```

**Out of disk space**
```bash
# Clean old downloads
rm -rf out/*
# Or increase volume size
```

**Rate limited by YouTube**
```bash
# Slow down requests
export YT_TIMEOUT=1200
export YT_MAX_RETRIES=20
```

## Support

For deployment questions, see:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [FAQ.md](FAQ.md)
- GitHub Issues
- Email: d.lovecreator@gmail.com
