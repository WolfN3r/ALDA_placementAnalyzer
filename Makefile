.PHONY: help init up down restart logs logs-follow stats memory ps clean clean-all rebuild stop start shell version

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# n8n version
N8N_VERSION := 0.236.3

# Project name
PROJECT_NAME := ALDA Placement Analyzer

##@ Setup Commands


init: ## Initialize the project (first time setup)
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  Initializing $(PROJECT_NAME)$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)n8n version: $(N8N_VERSION) (no authentication required)$(NC)"
	@echo ""
	@echo "$(YELLOW)Step 1/3:$(NC) Checking Docker installation..."
	@docker --version || (echo "$(RED)Docker not found! Please install Docker first.$(NC)" && exit 1)
	@docker compose version || (echo "$(RED)Docker Compose not found! Please install Docker Compose.$(NC)" && exit 1)
	@echo "$(GREEN)✓ Docker is installed$(NC)"
	@echo ""
	@echo "$(YELLOW)Step 2/3:$(NC) Creating necessary directories..."
	@mkdir -p n8n/workflows logs scripts
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo ""
	@echo "$(YELLOW)Step 3/3:$(NC) Building Docker image with n8n $(N8N_VERSION) (this may take a few minutes)..."
	@$(MAKE) build
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Initialization Complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run '$(YELLOW)make up$(NC)' to start the placer"
	@echo "  2. Open http://localhost:5678 in your browser"
	@echo "  3. $(GREEN)No login required!$(NC) Just start creating workflows"
	@echo "  4. Run '$(YELLOW)make help$(NC)' to see all available commands"
	@echo ""

build: ## Build the Docker image
	@echo "$(BLUE)Building alda-placement-analyzer Docker image (n8n v$(N8N_VERSION))...$(NC)"
	@docker compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

##@ Container Control

up: ## Start the container
	@echo "$(BLUE)Starting $(PROJECT_NAME) container...$(NC)"
	@docker compose up -d
	@echo "$(GREEN)✓ Container started$(NC)"
	@echo ""
	@echo "$(PROJECT_NAME) (n8n $(N8N_VERSION)) is now running at: $(YELLOW)http://localhost:5678$(NC)"
	@echo "$(GREEN)No authentication required - just open and start working!$(NC)"
	@echo ""
	@echo "Run '$(YELLOW)make logs$(NC)' to see the logs"

down: ## Stop and remove the container
	@echo "$(YELLOW)Stopping $(PROJECT_NAME) container...$(NC)"
	@docker compose down
	@echo "$(GREEN)✓ Container stopped$(NC)"

stop: ## Stop the container without removing it
	@echo "$(YELLOW)Stopping $(PROJECT_NAME) container...$(NC)"
	@docker compose stop
	@echo "$(GREEN)✓ Container stopped$(NC)"

start: ## Start an existing stopped container
	@echo "$(BLUE)Starting $(PROJECT_NAME) container...$(NC)"
	@docker compose start
	@echo "$(GREEN)✓ Container started$(NC)"

restart: ## Restart the container
	@echo "$(YELLOW)Restarting $(PROJECT_NAME) container...$(NC)"
	@docker compose restart
	@echo "$(GREEN)✓ Container restarted$(NC)"

rebuild: ## Rebuild and restart the container
	@echo "$(BLUE)Rebuilding and restarting $(PROJECT_NAME)...$(NC)"
	@$(MAKE) down
	@$(MAKE) build
	@$(MAKE) up
	@echo "$(GREEN)✓ Rebuild complete$(NC)"

##@ Monitoring & Debugging

logs: ## Show recent logs (last 100 lines)
	@echo "$(BLUE)Showing recent logs (press Ctrl+C to exit):$(NC)"
	@docker compose logs --tail=100

logs-follow: ## Follow logs in real-time
	@echo "$(BLUE)Following logs in real-time (press Ctrl+C to exit):$(NC)"
	@docker compose logs -f

stats: ## Show live container resource usage
	@echo "$(BLUE)Container resource usage (press Ctrl+C to exit):$(NC)"
	@echo ""
	@docker stats alda-placement-analyzer

memory: ## Show current memory usage
	@echo "$(BLUE)Current memory usage:$(NC)"
	@echo ""
	@docker stats alda-placement-analyzer --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

ps: ## Show container status
	@echo "$(BLUE)Container status:$(NC)"
	@echo ""
	@docker compose ps

shell: ## Open a shell inside the container
	@echo "$(BLUE)Opening shell in $(PROJECT_NAME) container...$(NC)"
	@docker compose exec n8n /bin/bash

version: ## Show n8n version
	@echo "$(BLUE)Checking n8n version...$(NC)"
	@docker compose exec n8n n8n --version || echo "$(RED)Container not running. Start it with 'make up'$(NC)"

##@ Cleanup Commands

clean: ## Remove container and volumes (keeps images)
	@echo "$(YELLOW)Removing containers and volumes...$(NC)"
	@docker compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: ## Remove everything including images
	@echo "$(RED)WARNING: This will remove all containers, volumes, and images!$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@docker compose down -v --rmi all
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

clean-logs: ## Clear log files
	@echo "$(YELLOW)Clearing log files...$(NC)"
	@rm -rf logs/*
	@touch logs/.gitkeep
	@echo "$(GREEN)✓ Logs cleared$(NC)"

reset: ## Full reset (clean all + rebuild)
	@echo "$(YELLOW)Performing full reset...$(NC)"
	@$(MAKE) clean-all
	@$(MAKE) init
	@echo "$(GREEN)✓ Reset complete$(NC)"

##@ Information

help: ## Display this help message
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  $(PROJECT_NAME) - Makefile$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(GREEN)n8n version: $(N8N_VERSION) (no authentication)$(NC)"
	@echo ""
	@echo "Usage:"
	@echo "  make $(YELLOW)<target>$(NC)"
	@echo ""
	@echo "$(BLUE)Setup Commands$(NC)"
	@echo "  init              Initialize the project (first time setup)"
	@echo "  build             Build the Docker image"
	@echo ""
	@echo "$(BLUE)Container Control$(NC)"
	@echo "  up                Start the container"
	@echo "  down              Stop and remove the container"
	@echo "  stop              Stop the container without removing it"
	@echo "  start             Start an existing stopped container"
	@echo "  restart           Restart the container"
	@echo "  rebuild           Rebuild and restart the container"
	@echo ""
	@echo "$(BLUE)Monitoring & Debugging$(NC)"
	@echo "  logs              Show recent logs (last 100 lines)"
	@echo "  logs-follow       Follow logs in real-time"
	@echo "  stats             Show live container resource usage"
	@echo "  memory            Show current memory usage"
	@echo "  ps                Show container status"
	@echo "  shell             Open a shell inside the container"
	@echo "  version           Show n8n version"
	@echo ""
	@echo "$(BLUE)Cleanup Commands$(NC)"
	@echo "  clean             Remove container and volumes (keeps images)"
	@echo "  clean-all         Remove everything including images"
	@echo "  clean-logs        Clear log files"
	@echo "  reset             Full reset (clean all + rebuild)"
	@echo ""
	@echo "$(BLUE)Information$(NC)"
	@echo "  help              Display this help message"
	@echo "  info              Show system information"
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. $(YELLOW)make init$(NC)    - First time setup"
	@echo "  2. $(YELLOW)make up$(NC)      - Start the placer"
	@echo "  3. Open http://localhost:5678 $(GREEN)(no login needed!)$(NC)"
	@echo ""
	@echo "$(BLUE)Common Tasks:$(NC)"
	@echo "  • View logs:      $(YELLOW)make logs-follow$(NC)"
	@echo "  • Check memory:   $(YELLOW)make memory$(NC)"
	@echo "  • Check version:  $(YELLOW)make version$(NC)"
	@echo "  • Restart:        $(YELLOW)make restart$(NC)"
	@echo "  • Reset all:      $(YELLOW)make reset$(NC)"
	@echo ""

info: ## Show system information
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  System Information$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Configuration:$(NC)"
	@echo "  Project: $(PROJECT_NAME)"
	@echo "  n8n version: $(N8N_VERSION)"
	@echo "  Authentication: Disabled"
	@echo ""
	@echo "$(YELLOW)Docker Version:$(NC)"
	@docker --version
	@docker compose version
	@echo ""
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(YELLOW)Disk Usage:$(NC)"
	@docker system df
	@echo ""