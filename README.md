## Project Overview

This repository provides a fully functional Docker Compose setup for running **n8n** with custom Python nodes. With this environment, users can visually build workflows in n8n that call external Python scripts for processing data, logging, and displaying pop-up windows. It's ideal for quick experiments, ML pipeline testing, or any scenario requiring Python code execution within n8n.

### Key Features

* **Dockerized n8n** on port 5678
* **Pyenv** support for easy Python version switching (default: 3.12.3)
* External Python script execution via PythonFunction nodes or Execute Command nodes
* Fire-and-forget mode for display scripts (Tkinter pop-ups)
* Per-workflow logging and persistent volumes
* Cross-platform instructions for Windows, macOS, and Linux

## System Requirements

* **Docker** >= 20.10.0 and **Docker Compose** plugin
* **Git** for cloning the repo
* **Make** (optional, recommended on macOS/Linux or via WSL/Git Bash on Windows)
* **X server** for pop-up windows (Xming on Windows, XQuartz on macOS, or X11 on Linux)

## Getting the Code

```
git clone https://github.com/WolfN3r/ALDA_n8n_python_env.git
cd ALDA_n8n_python_env
```

---

## Installation & Setup

Choose your platform below and follow the steps.

### Common Steps before Platform-Specific

1. Verify Docker is installed:

```
docker --version
docker compose version
````
2. If missing, install Docker Desktop (Windows/macOS) or Docker Engine & Compose (Linux).
3. (Optional) Install Make:
   - **macOS/Linux**: `sudo apt install make` or `brew install make`
   - **Windows**: Use WSL or Git Bash with `make` support

---

## 1. Linux
1. Ensure `make` is installed:
```
sudo apt update && sudo apt install -y make
````

2. (Optional for pop-ups) Install X11 utilities:

```
sudo apt install -y x11-utils
````
3. Prepare environment for X11:
```
make env    # creates .env with DISPLAY=:0
make x11-init  # also runs xhost +local:root
````

4. Start services:

```
make up
````
5. Access n8n at `http://localhost:5678`.

---

## 2. macOS
1. Install Homebrew if needed: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Install Make: `brew install make`
3. Install XQuartz for X11 pop-ups.
4. Set up XQuartz security:
   - Open XQuartz > Preferences > Security > check "Allow connections from network clients"
   - In a terminal: `xhost +localhost`
5. Prepare and start:
```
make init
make up
````

6. Open `http://localhost:5678` in your browser.

---

## 3. Windows (WSL + Xming)

1. Install WSL and Ubuntu from Microsoft Store.
2. Install Xming on Windows and launch with `Xming :0 -ac -multiwindow -clipboard`.
3. In PowerShell, launch WSL:

```
wsl
````
4. Install Make & x11-utils inside WSL:
```
sudo apt update && sudo apt install -y make x11-utils
````

5. Navigate to your project:

```
cd /mnt/c/Users/<you>/ALDA\_n8n\_python\_env
````
6. Run setup:
```
make init
make up
````

7. Point your browser on Windows to `http://localhost:5678`.

---

## Usage

* Create workflows in n8n
* Use **PythonFunction** nodes to run custom scripts in `scripts/`
* Use **Execute Command** nodes for simple Python calls
* View logs with `make logs`

## Sharing & Version Control

* All code, scripts, and configs are versioned with Git
* To update dependencies, edit `requirements.txt` and run:

```
make build
```

## 🤖 Need Help?

If you run into issues during setup or usage, you can get guided support from the official GPT assistant trained specifically for this project:

👉 [ALDA n8n Python Assistant (ChatGPT)](https://chatgpt.com/g/g-681899e9488c8191a9b5c4da0cf268e1-alda-n8n-python-assistant)

It will help you based on your operating system and common issues (Docker, X11, Python scripts, etc).

---

## Troubleshooting
- **Make not found**: install via your OS package manager
- **No DISPLAY** errors: ensure X server is running and `.env` has `DISPLAY` set
- **Permission issues**: check Docker Desktop's resource sharing settings

---

_Remember to only uncomment X11 lines in `docker-compose.yml` if you need pop-up windows._

```