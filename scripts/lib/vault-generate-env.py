#!/usr/bin/env python3
"""Generate a .env file from a vault-mapping.yaml by reading secrets from Vault."""
import sys
import subprocess

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <mapping_file> <vault_token> <vault_container> [output_file]",
              file=sys.stderr)
        sys.exit(1)

    mapping_file = sys.argv[1]
    vault_token = sys.argv[2]
    vault_container = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else None

    lines = []
    with open(mapping_file) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if ':' not in line:
                continue
            env_var, rest = line.split(':', 1)
            env_var = env_var.strip()
            rest = rest.strip()
            if ':' not in rest:
                continue
            last_colon = rest.rfind(':')
            vault_path = rest[:last_colon].strip()
            vault_field = rest[last_colon + 1:].strip()

            result = subprocess.run(
                ['docker', 'exec', '-e', f'VAULT_TOKEN={vault_token}',
                 vault_container, 'vault', 'kv', 'get', f'-field={vault_field}', vault_path],
                capture_output=True, text=True
            )
            value = result.stdout.strip() if result.returncode == 0 else ''
            lines.append(f'{env_var}={value}')

    output = '\n'.join(lines) + '\n'
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Wrote {len(lines)} variables to {output_file}", file=sys.stderr)
    else:
        sys.stdout.write(output)

if __name__ == '__main__':
    main()
