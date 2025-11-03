bucket         = "kass-chatbot-terraform-state"
key            = "dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "kass-chatbot-terraform-locks"
encrypt        = true
