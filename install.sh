#!/bin/bash

# - Developer Identity
DEV="@LAXXYPLAYZZ"
FOOTER="@DRX_POWER"

# Colors
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m' # No Color

clear

# Banner Function
show_banner() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  _____  _______  __  _____   ______          ________ _____  ${NC}"
    echo -e "${YELLOW} |  __ \|  __ \ \ / / |  __ \ / __ \ \        / /  ____|  __ \ ${NC}"
    echo -e "${YELLOW} | |  | | |__) \ V /  | |__) | |  | \ \  /\  / /| |__  | |__) |${NC}"
    echo -e "${YELLOW} | |  | |  _  / > <   |  ___/| |  | |\ \/  \/ / |  __| |  _  / ${NC}"
    echo -e "${YELLOW} | |  | | | \ \/ . \  | |    | |__| | \  /\  /  | |____| | \ \ ${NC}"
    echo -e "${YELLOW} |_____/|_|  \_\_/\_\ |_|     \____/   \/  \/   |______|_|  \_|${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "       ${GREEN}🚀 DRX POWER SYSTEM AUTO-INSTALLER v3.0 🚀${NC}"
    echo -e "       ${CYAN}Owner: $FOOTER | Dev: $DEV${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Progress Bar Function
progress_bar() {
    local duration=$1
    local task=$2
    echo -ne "${YELLOW}[#] $task: [          ] (0%)\r"
    sleep 0.5
    echo -ne "${YELLOW}[#] $task: [■■        ] (20%)\r"
    sleep 0.5
    echo -ne "${YELLOW}[#] $task: [■■■■      ] (40%)\r"
    sleep 0.5
    echo -ne "${YELLOW}[#] $task: [■■■■■■    ] (60%)\r"
    sleep 0.5
    echo -ne "${YELLOW}[#] $task: [■■■■■■■■  ] (80%)\r"
    sleep 0.5
    echo -ne "${GREEN}[#] $task: [■■■■■■■■■■] (100%)\n"
}

show_banner

# Step 1: System Update
echo -e "${CYAN}[>] Initializing System Update...${NC}"
pkg update -y > /dev/null 2>&1 && pkg upgrade -y > /dev/null 2>&1
progress_bar 1 "System Update"

# Step 2: Python Installation
echo -e "${CYAN}[>] Installing Python Environment...${NC}"
pkg install python python-pip -y > /dev/null 2>&1
progress_bar 1 "Python & Pip Setup"

# Step 3: Library Installation
echo -e "${CYAN}[>] Deploying Telegram Libraries...${NC}"
pip install pyTelegramBotAPI threading > /dev/null 2>&1
progress_bar 1 "Bot Library Integration"

# Step 4: Permissions
echo -e "${CYAN}[>] Configuring File Permissions...${NC}"
[ -f "drx" ] && chmod +x drx
[ -f "txt.py" ] && chmod +x txt.py
progress_bar 1 "Security & Permissions"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ CORE INSTALLATION COMPLETED SUCCESSFULLY!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Auto Start Logic
if [ -f "drx.py" ]; then
    echo -e "${YELLOW}[!] Launching Bot Terminal...${NC}"
    sleep 1
    python3 drx.py
else
    echo -e "${RED}[X] CRITICAL ERROR: drx.py not found in directory!${NC}"
fi
