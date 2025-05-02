# AWS Setup Guide for Asynchronous PDF Processing

## Prerequisites
- AWS Account with administrative access
- AWS CLI installed and configured
- Python 3.7 or higher

## Step 1: Create S3 Bucket
1. Go to AWS S3 Console
2. Click "Create bucket"
3. Enter a unique bucket name
4. Choose your preferred region
5. Keep default settings for other options
6. Click "Create bucket"

## Step 2: Create IAM Role
1. Go to AWS IAM Console
2. Navigate to Roles → Create Role
3. Select "AWS service" as the trusted entity
4. Choose "Textract" as the use case
5. Add the following policies:
   - `AWSTextractFullAccess`
   - `AmazonSNSFullAccess`
   - `AmazonS3ReadOnlyAccess`
6. Name the role (e.g., "TextractAsyncProcessingRole")
7. Add the following trust relationship in JSON editor:
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

## Step 3: Create SNS Topic
1. Go to Amazon SNS Console
2. Click "Create topic"
3. Choose "Standard" type
4. Name your topic (e.g., "textract-notifications")
5. Create the topic
6. Copy the Topic ARN for later use

## Step 4: Configure SNS Topic
1. In the SNS topic details:
   - Click "Edit" under "Access policy"
   - Add the following policy:
```json
{
  "Version": "2012-10-13",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "textract.amazonaws.com"
      },
      "Action": "SNS:Publish",
      "Resource": "<your-sns-topic-arn>"
    }
  ]
}
```
2. Replace `<your-sns-topic-arn>` with your actual SNS topic ARN

## Step 5: Create SQS Queue (Optional, for async processing)
1. Go to Amazon SQS Console
2. Click "Create Queue"
3. Choose "Standard Queue"
4. Name your queue (e.g., "textract-completion-queue")
5. Under Access Policy, add:
```json
{
  "Version": "2012-10-13",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "<your-queue-arn>",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "<your-sns-topic-arn>"
        }
      }
    }
  ]
}
```
6. Subscribe the SQS queue to the SNS topic

## Step 6: Environment Setup
1. Create a `.env` file in your project root:
```
AWS_REGION=<your-region>
AWS_S3_BUCKET=<your-bucket-name>
AWS_ROLE_ARN=<your-role-arn>
AWS_SNS_TOPIC_ARN=<your-sns-topic-arn>

```

## Step 7: Install Required Python Packages
```bash
pip install boto3 python-dotenv
```

## Step 8: Verify Setup
1. Test S3 access:
```python
import boto3
s3 = boto3.client('s3')
s3.list_buckets()
```

2. Test Textract access:
```python
textract = boto3.client('textract')
# Should not raise any permissions errors
```

## Common Issues and Troubleshooting
1. **Access Denied Errors**:
   - Verify IAM role permissions
   - Check trust relationships
   - Ensure proper policy attachment

2. **SNS/SQS Connection Issues**:
   - Verify topic and queue ARNs
   - Check subscription confirmation
   - Review access policies

3. **Textract Limits**:
   - Monitor usage against service quotas
   - Request limit increases if needed
   - Implement proper error handling