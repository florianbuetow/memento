# =============================================================================
# Justfile Rules (follow these when editing justfile):
#
# 1. Use printf (not echo) to print colors — some terminals won't render
#    colors with echo.
#
# 2. Always add an empty `@echo ""` line before and after each target's
#    command block.
#
# 3. Always add new targets to the help section and update it when targets
#    are added, modified or removed.
#
# 4. Target ordering in help (and in this file) matters:
#    - Setup targets first (init, setup, install, etc.)
#    - Start/stop/run targets next
#    - Code generation / data tooling targets next
#    - Checks, linting, and tests next (ordered fastest to slowest)
#    Group related targets together and separate groups with an empty
#    `@echo ""` line in the help output.
#
# 5. Composite targets (e.g. ci) that call multiple sub-targets must fail
#    fast: exit 1 on the first error. Never skip over errors or warnings.
#    Use `set -e` or `&&` chaining to ensure immediate abort with the
#    appropriate error message.
#
# 6. Every target must end with a clear short status message:
#    - On success: green (\033[32m) message confirming completion.
#      E.g. printf "\033[32m✓ init completed successfully\033[0m\n"
#    - On failure: red (\033[31m) message indicating what failed, then exit 1.
#      E.g. printf "\033[31m✗ ci failed: tests exited with errors\033[0m\n"
# 7. Targets must be shown in groups separated by empty newlines in the help section.
#    - init/destroy/clean/help on top, ci and other tests on the bottom, between other groups
# =============================================================================

# Default recipe: show available commands
_default:
    @just help

# Show help information
help:
    @clear
    @echo ""
    @printf "\033[0;34m=== memento-skills ===\033[0m\n"
    @echo ""
    @printf "\033[0;33mSetup & Lifecycle:\033[0m\n"
    @printf "  %-40s %s\n" "init" "Verify required tools and prepare the repository"
    @printf "  %-40s %s\n" "install" "Copy .memento to ~/.memento"
    @printf "  %-40s %s\n" "help" "Show this help message"
    @echo ""
    @printf "\033[0;33mSkill Graph:\033[0m\n"
    @printf "  %-40s %s\n" "build" "Rebuild the skill graph from all SKILL.md files"
    @echo ""
    @printf "\033[0;33mCI & Testing:\033[0m\n"
    @printf "  %-40s %s\n" "test" "Build the skill graph and assert it is correct"
    @echo ""

# Verify required tools and prepare the repository
init:
    @echo ""
    @printf "\033[0;34m=== Initializing memento-skills ===\033[0m\n"
    @if ! command -v awk >/dev/null 2>&1; then \
        printf "\033[0;31m✗ Error: awk is not installed\033[0m\n"; \
        printf "  awk ships with macOS and Linux; install it via your package manager if missing\n"; \
        echo ""; \
        exit 1; \
    fi
    @printf "\033[0;32m✓ awk is installed\033[0m\n"
    @if ! command -v python3 >/dev/null 2>&1; then \
        printf "\033[0;31m✗ Error: python3 is not installed\033[0m\n"; \
        printf "  Install Python 3 from: https://python.org/downloads/\n"; \
        echo ""; \
        exit 1; \
    fi
    @printf "\033[0;32m✓ python3 is installed\033[0m\n"
    @find .memento -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} +
    @printf "\033[0;32m✓ scripts in .memento are executable\033[0m\n"
    @printf "\033[0;32m✓ init completed successfully\033[0m\n"
    @echo ""

# Copy .memento to ~/.memento
install:
    #!/usr/bin/env bash
    set -e
    echo ""
    printf "\033[0;34m=== Installing .memento to ~/.memento ===\033[0m\n"
    if [ -z "$HOME" ]; then
        printf "\033[0;31m✗ install failed: HOME is not set\033[0m\n"
        echo ""
        exit 1
    fi
    DEST="$HOME/.memento"
    if [ -e "$DEST" ]; then
        printf "\033[0;33m! %s already exists and will be replaced.\033[0m\n" "$DEST"
    fi
    printf "Copy .memento to %s? [y/N] " "$DEST"
    read -r REPLY
    if [ "$REPLY" != "y" ] && [ "$REPLY" != "Y" ]; then
        printf "\033[0;31m✗ install aborted: not confirmed\033[0m\n"
        echo ""
        exit 1
    fi
    rm -rf "$DEST"
    cp -R .memento "$DEST"
    printf "\033[0;32m✓ copied to %s\033[0m\n" "$DEST"
    find "$DEST" -name "*.sh" -exec chmod +x {} +
    printf "\033[0;32m✓ scripts in %s are executable\033[0m\n" "$DEST"
    printf "\033[0;32m✓ install completed successfully\033[0m\n"
    echo ""

# Rebuild the skill graph from all SKILL.md files
build:
    @echo ""
    @printf "\033[0;34m=== Building Skill Graph ===\033[0m\n"
    @.memento/scripts/build_skill_graph.sh
    @printf "\033[0;32m✓ build completed successfully\033[0m\n"
    @echo ""

# Build the skill graph and assert it is correct
test: build
    @echo ""
    @printf "\033[0;34m=== Running Tests ===\033[0m\n"
    @python3 tests/test_skill_graph.py
    @python3 tests/test_find_connection.py
    @printf "\033[0;32m✓ test completed successfully\033[0m\n"
    @echo ""
