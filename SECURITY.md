# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in youtube-transcript-exporter, please **do not** open a public GitHub issue. Instead:

1. Email: d.lovecreator@gmail.com with subject line `[SECURITY] YouTube Transcript Exporter`
2. Include:
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Suggested fix (if you have one)

We will acknowledge receipt within 48 hours and work with you on a fix.

## Known Security Considerations

### Data Handling
- **Transcripts are public** -- all data is sourced from public YouTube captions
- **No credentials stored** -- system uses only public YouTube APIs
- **Local-first** -- all processing happens on your machine; no cloud uploads
- **No telemetry** -- system does not phone home or collect usage data

### Dependencies
- Python standard library + minimal third-party packages (yt-dlp, requests)
- All dependencies pinned to specific versions (see `requirements.txt`)
- Regular audits recommended when updating dependencies

### File System Security
- **Permissions** -- markdown and database files inherit user's umask
- **No world-readable by default** -- but verify with `ls -la` if sensitive
- **Recommendation** -- store on encrypted volumes for sensitive content

### Environment Variables
- `NOTION_TOKEN` -- if used, keep this secret (never commit to git)
- `NOTION_DATABASE_ID` -- treat as private if sharing repos

### API Security
- **YouTube API** -- system uses public captions only; no authentication required
- **Rate limits** -- system respects YouTube rate limits with backoff
- **Notion API** -- optional; requires explicit token if used

## Vulnerability Disclosure Timeline

Once we receive your report, we commit to:
1. **Immediate acknowledgment** (within 48 hours)
2. **Root cause analysis** (within 1 week)
3. **Patch release** (within 2 weeks, or explanation of delay)
4. **Public disclosure** (after patch is available)

## Security Best Practices for Users

1. **Keep yt-dlp updated** -- YouTube changes their structure frequently
2. **Review markdown before sharing** -- transcripts may contain sensitive info
3. **Audit canonical.json periodically** -- ensure no unwanted videos are tracked
4. **Use `--audit` flag regularly** -- catches orphaned or corrupted files

## Third-Party Security

- **yt-dlp** -- maintained by the community; widely trusted
- **requests** -- standard Python HTTP library; security-focused
- **Python >= 3.8** -- use current versions; old Python has known vulnerabilities

For questions, contact: d.lovecreator@gmail.com
