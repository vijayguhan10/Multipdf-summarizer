# Asynchronous PDF Processing with AWS Textract

## Overview
This guide explains the asynchronous API integration with AWS Textract for processing multiple PDFs with multiple pages.

## Features
- Multi-page PDF support
- Asynchronous processing
- Job status tracking
- Batch processing capabilities

## AWS Configuration Requirements

### 1. IAM Role Setup
1. Create an IAM Role with the following permissions:
   - `AWSTextractFullAccess`
   - `AmazonSNSFullAccess`
   - `AmazonS3ReadOnlyAccess`

2. Add the following trust relationship:
```json
{
  "Version": "2012-10-13",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "textract.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 2. SNS Topic Setup
1. Create an SNS Topic for Textract notifications
2. Add the IAM Role as a subscriber

### 3. Environment Variables
Add to your .env file:
```
AWS_ROLE_ARN=<your-role-arn>
AWS_SNS_TOPIC_ARN=<your-sns-topic-arn>
```

## Usage Limits and Costs

### AWS Textract Limits
- **Concurrent Jobs**: 10 async jobs per account (can be increased via AWS Support)
- **Document Size**: Up to 500MB per document
- **Page Limit**: 5000 pages per document

### Costs (US East Region)
- **Asynchronous Text Detection**: $0.0015 per page
- **First 1000 pages/month**: Free (as part of AWS Free Tier)

### Best Practices
1. **Rate Limiting**: Implement rate limiting in your application
2. **Job Tracking**: Monitor job status and implement proper error handling
3. **Timeout Handling**: Set appropriate timeouts for large documents
4. **Cost Monitoring**: Set up AWS Budget Alerts

## API Endpoints

### 1. Upload Single PDF
```http
POST /upload
Response: 
{
  "job_id": "string",
  "status": "IN_PROGRESS"
}
```

### 2. Upload Multiple PDFs
```http
POST /upload-multiple
Response:
{
  "jobs": [
    {
      "job_id": "string",
      "status": "IN_PROGRESS",
      "file_name": "string"
    }
  ]
}
```

### 3. Check Job Status
```http
GET /job/{job_id}
Response:
{
  "status": "string",
  "text": "string",  // Only when complete
  "summary": "string"  // Only when complete
}
```

## Error Handling
- Implement exponential backoff for rate limits
- Monitor job timeouts (default 3600 seconds)
- Handle SNS notification failures

## Security Considerations
1. Never expose AWS credentials in client-side code
2. Implement proper authentication for API endpoints
3. Validate file types and sizes before processing
4. Use HTTPS for all API communications