#!/usr/bin/env bash
# Aider wrapper to suppress interactive prompts using expect
# Auto-answers common prompts with "n" (no) or "y" (yes)

set -e

# Check if expect is available
if ! command -v expect &> /dev/null; then
    echo "⚠️  expect not found. Install with: brew install expect"
    # Fall back to direct aider execution
    exec /usr/local/bin/aider "$@"
fi

# Create expect script
cat > /tmp/aider_expect.tcl <<'EOF'
#!/usr/bin/expect -f
set timeout 3600
set arguments [lrange $argv 0 end]

# Start aider with all arguments
set process [open "|aider {*}$arguments" r+]
fconfigure $process -buffering line

# Main loop: read output and respond to prompts
while {[gets $process line] >= 0} {
    puts $line
    flush stdout

    # Check for common aider/litellm prompts and auto-respond
    if {[string match "*documentation*" $line] ||
        [string match "*Open URL*" $line] ||
        [string match "*more info*" $line] ||
        [string match "*proceed*" $line] ||
        [string match "*(y/n)*" $line] ||
        [string match "*(Y/n)*" $line] ||
        [string match "*[Yy]es*[Nn]o*" $line]} {
        puts -nonewline $process "n\n"
        flush $process
    }

    if {[string match "*Continue*" $line] ||
        [string match "*continue*" $line] ||
        [string match "*(Y/n)*" $line]} {
        puts -nonewline $process "y\n"
        flush $process
    }
}

catch {close $process}
EOF

# Execute aider through expect
expect /tmp/aider_expect.tcl "$@"
exit_code=$?

# Clean up
rm -f /tmp/aider_expect.tcl

exit $exit_code
