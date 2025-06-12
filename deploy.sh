#!/bin/bash

# Basketball Dashboard Deployment Script
# This script automates the deployment to AWS ECS Fargate

set -e  # Exit on any error

# Configuration
STACK_NAME=${STACK_NAME:-"basketball-dashboard"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_error "Please install them and try again."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites are satisfied"
}

# Function to create infrastructure if it doesn't exist
deploy_infrastructure() {
    print_status "Checking if CloudFormation stack exists..."
    
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" &> /dev/null; then
        print_status "Stack $STACK_NAME already exists. Skipping infrastructure deployment."
        print_warning "To update infrastructure, run: aws cloudformation update-stack --stack-name $STACK_NAME --template-body file://aws/cloudformation-template.yaml --parameters file://aws/parameters.json --capabilities CAPABILITY_NAMED_IAM"
    else
        print_error "CloudFormation stack $STACK_NAME does not exist."
        print_status "Please deploy the infrastructure first using:"
        print_status "aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://aws/cloudformation-template.yaml --parameters file://aws/parameters.json --capabilities CAPABILITY_NAMED_IAM"
        exit 1
    fi
}

# Function to get ECR repository URI
get_ecr_repository() {
    local ecr_repo=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ECRRepository'].OutputValue" \
        --output text)
    
    if [ -z "$ecr_repo" ]; then
        print_error "Could not find ECR repository in CloudFormation outputs"
        exit 1
    fi
    
    echo "$ecr_repo"
}

# Function to build and push Docker image
build_and_push_image() {
    local ecr_repo=$1
    local image_tag=${2:-"latest"}
    
    print_status "Building Docker image..."
    
    # Build the image
    docker build -t "$STACK_NAME:$image_tag" .
    
    # Tag for ECR
    docker tag "$STACK_NAME:$image_tag" "$ecr_repo:$image_tag"
    
    print_status "Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    print_status "Pushing image to ECR..."
    docker push "$ecr_repo:$image_tag"
    
    print_success "Image pushed successfully: $ecr_repo:$image_tag"
}

# Function to update ECS service
update_ecs_service() {
    print_status "Updating ECS service..."
    
    local cluster_name=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ECSCluster'].OutputValue" \
        --output text)
    
    local service_name=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ECSService'].OutputValue" \
        --output text)
    
    if [ -z "$cluster_name" ] || [ -z "$service_name" ]; then
        print_error "Could not find ECS cluster or service in CloudFormation outputs"
        exit 1
    fi
    
    # Force new deployment
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        > /dev/null
    
    print_status "Waiting for deployment to complete..."
    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$AWS_REGION"
    
    print_success "ECS service updated successfully"
}

# Function to get application URL
get_application_url() {
    local app_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerURL'].OutputValue" \
        --output text)
    
    if [ -n "$app_url" ]; then
        print_success "Application is available at: $app_url"
        print_status "Health check endpoint: $app_url/health"
    fi
}

# Function to validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    local app_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerURL'].OutputValue" \
        --output text)
    
    if [ -n "$app_url" ]; then
        # Wait for load balancer to be ready
        sleep 30
        
        # Check health endpoint
        local health_url="$app_url/health"
        print_status "Checking health endpoint: $health_url"
        
        local max_attempts=10
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -f -s "$health_url" > /dev/null; then
                print_success "Application is healthy and responding"
                return 0
            fi
            
            print_status "Attempt $attempt/$max_attempts: Waiting for application to be ready..."
            sleep 30
            ((attempt++))
        done
        
        print_warning "Application may not be fully ready yet. Please check manually."
    fi
}

# Main deployment function
main() {
    print_status "Starting deployment of Basketball Dashboard to AWS ECS Fargate"
    print_status "Stack Name: $STACK_NAME"
    print_status "AWS Region: $AWS_REGION"
    print_status "AWS Account: $AWS_ACCOUNT_ID"
    
    # Check prerequisites
    check_prerequisites
    
    # Check infrastructure
    deploy_infrastructure
    
    # Get ECR repository
    local ecr_repo=$(get_ecr_repository)
    print_status "ECR Repository: $ecr_repo"
    
    # Build and push image
    local image_tag="$(date +%Y%m%d-%H%M%S)"
    build_and_push_image "$ecr_repo" "$image_tag"
    
    # Update latest tag
    docker tag "$ecr_repo:$image_tag" "$ecr_repo:latest"
    docker push "$ecr_repo:latest"
    
    # Update ECS service
    update_ecs_service
    
    # Get application URL
    get_application_url
    
    # Validate deployment
    validate_deployment
    
    print_success "Deployment completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --stack-name NAME    CloudFormation stack name (default: basketball-dashboard)"
            echo "  --region REGION      AWS region (default: us-east-1)"
            echo "  --help              Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  STACK_NAME          CloudFormation stack name"
            echo "  AWS_REGION          AWS region"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main 