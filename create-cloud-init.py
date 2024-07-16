import re
import argparse
import os
import subprocess
import getpass
import readline
import uuid

def get_user_input(prompt, required=True, auto_generate=False, default=None):
    while True:
        value = input(prompt)
        if required and not value and not auto_generate:
            print("This field is required.")
        elif auto_generate and not value:
            return str(uuid.uuid4()).lower()
        elif default and not value:
            return default
        else:
            return value

def get_sensitive_user_input(prompt):
    while True:
        value = getpass.getpass(prompt)
        if not value:
            print("This field is required.")
        else:
            return value

def remove_block(content, block_name):
    pattern = re.compile(rf'# start {block_name} block #.*?# end {block_name} block #', re.DOTALL)
    return re.sub(pattern, '', content)

def remove_empty_lines(content):
    return "\n".join([line for line in content.split("\n") if line.strip() != ""])

def remove_comments(content):
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('#cloud-config'):
            cleaned_lines.append(line)
        elif not line.strip().startswith('#'):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def generate_init_user_credentials(email, password):
    script_path = os.path.abspath('./generate-hash.sh')
    result = subprocess.run([script_path, email, password], capture_output=True, text=True)
    output_lines = result.stdout.splitlines()
    for line in output_lines:
        if line.startswith(email):
            return line
    return None

def format_entrypoint(entrypoint):
    entrypoint = entrypoint.strip('"')  # Remove any existing quotes
    if not entrypoint.startswith("https://"):
        entrypoint = f"https://{entrypoint}"
    return f'"{entrypoint}"'

def main(args):
    with open(args.input, 'r') as file:
        cloud_config = file.read()
    
    # Gather user inputs
    controller_hostname = get_user_input("Controller hostname: ")
    site_id = get_user_input("Site ID (leave blank to auto-generate): ", auto_generate=True)
    sync_psk = get_user_input("Sync PSK (leave blank to auto-generate): ", auto_generate=True)

    use_ssh_key = input("Do you want to include an SSH key? (yes/no): ").strip().lower() == 'yes'
    if use_ssh_key:
        public_ssh_key = get_user_input("Public SSH key (e.g.: ssh-ed25519 AAAA bowtie): ")
    else:
        public_ssh_key = ''

    use_sso = input("Do you want to use SSO for user authentication? (yes/no): ").strip().lower() == 'yes'
    if use_sso:
        idp_type = get_user_input("IDP type (lave blank to use oidc): ", required=False, default="oidc")
        idp_id = get_user_input("IDP ID (e.g.: gitlab): ")
        idp_name = get_user_input("IDP Name (e.g.: Gitlab): ")
        idp_issuer_url = get_user_input("IDP Issuer URL (e.g.: https://gitlab.com): ")
        idp_client_id = get_user_input("IDP Client ID (found in the Oauth application console): ")
        idp_client_secret = get_user_input("IDP Client Secret (found in the Oauth application console): ")
    else:
        idp_type = idp_id = idp_name = idp_issuer_url = idp_client_id = idp_client_secret = ''

    use_init_users = input("Do you want to generate an initial admin user? (yes/no): ").strip().lower() == 'yes'
    if use_init_users:
        init_user_email = get_user_input("Initial user email: ")
        init_user_password = get_sensitive_user_input("Initial user password: ")
        init_user_credentials = generate_init_user_credentials(init_user_email, init_user_password)
    else:
        init_user_credentials = ''

    use_should_join = input("Do you want to join this controller to an existing cluster? (yes/no): ").strip().lower() == 'yes'
    if use_should_join:
        first_controller_hostname = get_user_input("Existing controller hostname: ")
        first_controller_hostname = format_entrypoint(first_controller_hostname)
    else:
        first_controller_hostname = ''

    # Prepare replacements dictionary
    replacements = {
        'CONTROLLER_HOSTNAME': controller_hostname,
        'IDP_TYPE': idp_type,
        'IDP_ID': idp_id,
        'IDP_NAME': idp_name,
        'IDP_ISSUER_URL': idp_issuer_url,
        'IDP_CLIENT_ID': idp_client_id,
        'IDP_CLIENT_SECRET': idp_client_secret,
        'SITE_ID': site_id,
        'SYNC_PSK': sync_psk,
        'INIT_USER_CREDENTIALS': init_user_credentials,
        'FIRST_CONTROLLER_HOSTNAME': first_controller_hostname,
        'PUBLIC_SSH_KEY': public_ssh_key
    }
    
    # Handle optional blocks
    if not use_sso:
        cloud_config = remove_block(cloud_config, 'sso')
    if not use_init_users:
        cloud_config = remove_block(cloud_config, 'init-users')
    if not use_should_join:
        cloud_config = remove_block(cloud_config, 'should-join')
    if not use_ssh_key:
        cloud_config = remove_block(cloud_config, 'ssh key')

    # Replace placeholders
    cloud_config = replace_placeholders(cloud_config, replacements)
    
    # Remove extra new lines and comments
    cloud_config = remove_empty_lines(cloud_config)
    cloud_config = remove_comments(cloud_config)

    # Write the final cloud-config yaml to a file
    output_file = os.path.join(os.path.dirname(args.input), 'generated-cloud-init.yaml')
    with open(output_file, 'w') as file:
        file.write(cloud_config)
    
    # Output the final cloud-config yaml to stdout
    print(cloud_config)
    print(f"\nProcessed cloud-config YAML has been written to {output_file}")

# Function to replace placeholders with user input
def replace_placeholders(content, replacements):
    for key, value in replacements.items():
        content = content.replace('{{ ' + key + ' }}', value)
    return content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process cloud-init YAML with user input')
    parser.add_argument('--input', type=str, required=True, help='Path to the input YAML file')
    
    args = parser.parse_args()
    main(args)
