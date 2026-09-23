#!/bin/bash
# Swxtch Installation Script
# Complete setup from git clone to boot-verified privacy
# Usage: bash install.sh [--trial-only] [--no-boot-service]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TRIAL_ONLY=false
NO_BOOT_SERVICE=false
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --trial-only)
            TRIAL_ONLY=true
            shift
            ;;
        --no-boot-service)
            NO_BOOT_SERVICE=true
            shift
            ;;
        -h|--help)
            echo "Usage: bash install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --trial-only       Install package only, skip boot service setup"
            echo "  --no-boot-service  Same as --trial-only"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "By default, installs everything including boot service"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Start installation
print_header "🔒 Swxtch Installation"
echo ""
echo "This will install Swxtch and set up boot-verified Wi-Fi privacy."
echo ""

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

# Check OS
if [[ ! "$OSTYPE" == "linux"* ]]; then
    print_error "Swxtch requires Linux"
    exit 1
fi
print_success "Running on Linux"

# Check Python
if ! check_command python3; then
    print_error "Python 3 not found. Install with:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora/RHEL:   sudo dnf install python3 python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    print_error "Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

# Check pip
if ! check_command pip3; then
    print_error "pip3 not found"
    exit 1
fi
print_success "pip3 found"

# Step 2: Install Python package
print_header "Step 2: Installing Swxtch Package"

cd "$INSTALL_DIR"
print_info "Installing swxtch with cryptography support..."

if pip3 install -e ".[crypto]" > /tmp/swxtch_install.log 2>&1; then
    print_success "Package installed successfully"
else
    print_error "Package installation failed"
    echo ""
    echo "Installation log:"
    cat /tmp/swxtch_install.log
    exit 1
fi

# Step 3: Verify installation
print_header "Step 3: Verifying Installation"

if python3 -c "from swxtch import cli; print('✓ Import successful')" 2>/dev/null; then
    print_success "Swxtch package verified"
else
    print_error "Package verification failed"
    exit 1
fi

if command -v swxtch &> /dev/null; then
    print_success "swxtch command available"
else
    print_error "swxtch command not found in PATH"
    print_info "Try: python3 -m swxtch --help"
fi

# Step 4: Boot service setup (optional)
if [ "$TRIAL_ONLY" = false ] && [ "$NO_BOOT_SERVICE" = false ]; then
    print_header "Step 4: Setting Up Boot Service"

    # Check if running with root/sudo
    if [[ "$EUID" -eq 0 ]]; then
        print_info "Installing boot-time MAC/IP rotation service..."

        # Create log directory
        mkdir -p /var/log/swxtch
        chmod 700 /var/log/swxtch
        print_success "Log directory created: /var/log/swxtch"

        # Copy service file
        if [ -f "$INSTALL_DIR/systemd/swxtch-boot.service" ]; then
            cp "$INSTALL_DIR/systemd/swxtch-boot.service" /etc/systemd/system/
            chmod 644 /etc/systemd/system/swxtch-boot.service
            print_success "Systemd service installed"
        else
            print_error "Service file not found at $INSTALL_DIR/systemd/swxtch-boot.service"
            echo "Skipping boot service installation"
        fi

        # Create boot wrapper
        cat > /usr/local/bin/swxtch-boot << 'BOOT_SCRIPT'
#!/bin/bash
# Swxtch boot-time rotation wrapper
python3 -m swxtch.boot "$@"
BOOT_SCRIPT
        chmod +x /usr/local/bin/swxtch-boot
        print_success "Boot wrapper created: /usr/local/bin/swxtch-boot"

        # Reload systemd
        systemctl daemon-reload
        print_success "Systemd reloaded"

        # Enable service
        if systemctl enable swxtch-boot 2>/dev/null; then
            print_success "Boot service enabled (will run on next boot)"
        else
            print_error "Failed to enable boot service"
            print_info "Try: sudo systemctl enable swxtch-boot"
        fi
    else
        print_error "Boot service setup requires root privileges"
        print_info "Run with sudo: sudo bash install.sh"
        print_info "Or skip boot service: bash install.sh --trial-only"
    fi
else
    if [ "$TRIAL_ONLY" = true ] || [ "$NO_BOOT_SERVICE" = true ]; then
        print_header "Step 4: Boot Service Setup (Skipped)"
        print_info "Skipped boot service installation"
        echo ""
        echo "To install boot service later, run:"
        echo "  sudo bash install.sh"
    fi
fi

# Step 5: Run tests
print_header "Step 5: Running Tests"

if check_command pytest; then
    print_info "Running test suite..."
    if pytest tests/ -v --tb=short > /tmp/swxtch_tests.log 2>&1; then
        TEST_COUNT=$(grep -c "PASSED" /tmp/swxtch_tests.log || echo "0")
        print_success "All tests passed ($TEST_COUNT tests)"
    else
        print_error "Some tests failed"
        echo ""
        echo "Test output:"
        tail -20 /tmp/swxtch_tests.log
        echo ""
        print_info "This may not prevent installation, but indicates potential issues"
    fi
else
    print_info "pytest not found, skipping test suite"
    print_info "To run tests later: pip3 install pytest && pytest tests/ -v"
fi

# Step 6: Show trial status
print_header "Step 6: Starting Your Free Trial"

print_success "Installation complete!"
echo ""
print_info "Your 7-day free trial is now active"
echo ""
echo "Next steps:"
echo ""
echo "1. Check your trial status:"
echo "   swxtch --license"
echo ""
echo "2. Test MAC rotation (requires sudo):"
echo "   sudo swxtch --list"
echo "   sudo swxtch -i wlan0 --interval 1"
echo ""

if [ "$TRIAL_ONLY" = false ] && [ "$NO_BOOT_SERVICE" = false ] && [[ "$EUID" -eq 0 ]]; then
    echo "3. Boot service is installed and enabled:"
    echo "   sudo systemctl status swxtch-boot"
    echo "   sudo reboot  # Test on next boot"
    echo ""
fi

echo "4. Read the documentation:"
echo "   cat README.md"
echo "   cat PRICING.md"
echo "   cat INSTALL.md"
echo ""

print_header "🎉 Welcome to Swxtch!"
echo ""
echo "Questions? Visit:"
echo "  GitHub: https://github.com/[GITHUB_ORG]/Swxtch"
echo "  Email:  [SUPPORT_EMAIL]"
echo ""
