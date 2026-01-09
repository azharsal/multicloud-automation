import configparser
import os
import subprocess
import json
import re
from datetime import datetime


def execute_command(command, do_print):
    """
    Executes commands for azure and gcloud clis.
    """
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        if (do_print):
            print(f"Command executed successfully: {result.stdout}")
        return {"success": True, "info": result.stdout}  
    except subprocess.CalledProcessError as e:
        if (do_print):
            print("Error executing command = " + e.stderr)
        return {"success": False, "info": e.stderr} 

def create_documentation_file(vm_info):
    """
    Creates the documentation file for a specified vm creation
    """
    timestamp = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    filename = f"VMcreation_{timestamp}.txt"
    
    with open(filename, 'w') as file:
        file.write(f"Date Stamp: {timestamp}\n")
        file.write(f"System Admin Name: {os.getlogin()}\n")
        for key, value in vm_info.items():
            file.write(f"{key.title()}: {value}\n")

    print(f"Documentation file created: {filename}\n")

def open_port_azure(resource_group, vm_name, port):
    command = [
        "az", "vm", "open-port",
        "-g", resource_group,
        "-n", vm_name,
        "--port", str(port)
    ]
    result = execute_command(command, False)
    

def open_port_gcp(project, vm_name, zone, port):
    # For GCP, opening a port involves creating a firewall rule
    firewall_rule_name = f"allow-port-{port}-vm-{vm_name}"
    command = [
        "gcloud", "compute", "firewall-rules", "create", firewall_rule_name,
        "--allow", f"tcp:{port}",
        "--target-tags", vm_name,  # Assuming VM has a tag matching its name
        "--description", f"Allow port {port} access to {vm_name}"
    ]
    result = execute_command(command, False)


def create_vms_from_config(config, cloud_provider):
    """
    Creates VMs based on the configurations for the specified cloud provider.
    """
    base_command = {
        "azure": ["az", "vm", "create"],
        "gcp": ["gcloud", "compute", "instances", "create"]
    }.get(cloud_provider, [])

    if not base_command:
        print(f"Unsupported cloud provider: {cloud_provider}")
        return
    
    commands_dict = {}
    for section in config.sections():
        image_exists = False
        vm_doc = {"name": "", "project": "", "team": "", "purpose":"", "os":"", }
        for key, value in config[section].items():
            key = key.lower()
            value = value.lower()
            commands_dict[key] = value

        vm_size = commands_dict.get('vm_size')
        # cpu = commands_dict.get('cpu')
        # memory = commands_dict.get('memory')
        machine_type = commands_dict.get('machine_type')
        disk_size = commands_dict.get('disk_size')

        if cloud_provider == "azure":

            #Checks if the neccesary atttributes are present in teh conf file
            if (["name", "resource-group", "image", "location", "admin-username"] <= list(commands_dict.keys())):

                #Checks if the name matches azure standards
                pattern = r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,78}[A-Za-z0-9_]$'
                if re.match(pattern, commands_dict["name"]):

                    #Checks if the resource group exists, if not then it offfers instructions to create one
                    cmd = ["az", "group", "exists", "--name", commands_dict["resource-group"]]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if (result.stdout.strip() == 'true'):

                        #Checks if the image is offered by Azure
                        cmd = ["az", "vm", "image", "list", "--location", commands_dict["location"], "--output", "json"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        images = json.loads(result.stdout)

                        for image in images:
                            if image['urnAlias'].lower() == commands_dict["image"]:
                                image_exists = True
                        if (image_exists):

                            azure_command = [
                                "az", "vm", "create",
                                "--resource-group", commands_dict["resource-group"],
                                "--name", commands_dict["name"],
                                "--image", commands_dict["image"],
                                "--location", commands_dict["location"],
                                "--admin-username", commands_dict["admin-username"],
                                # "--generate-ssh-keys"
                            ]

                            #Modifies teh commadn for windows or linux machien creation
                            if commands_dict["os"].lower() == "linux":
                                azure_command.extend(["--generate-ssh-keys"])
                            elif commands_dict["os"].lower() == "windows":
                                azure_command.extend(["--admin-password", commands_dict["admin-password"]])


                            #Additional attributes for vm
                            if vm_size:
                                azure_command.extend(["--size", vm_size])
                            if disk_size:
                                azure_command.extend(["--os-disk-size-gb", disk_size])

                            azure_command.extend(["--output", "table"])
                            print(f"Executing command: {' '.join(azure_command)}")
                            additional_info = execute_command(azure_command, True)


                            if additional_info["success"]:
                                vm_info = {
                                    'name': commands_dict["name"],
                                    'project': commands_dict.get("project", "DefaultProject"),  
                                    'purpose': vm_doc["purpose"],
                                    'team': vm_doc["team"],
                                    'os': vm_doc["os"],
                                    'Relevant info': additional_info.get("info", "Not specified"),  
                                    'status': 'Successfully created' 
                                }

                                create_documentation_file(vm_info)
                        else:
                            print("Image does not exist")
                    else:
                        print("Resource group does not exist. Please create it by using the following commnd: az group create --name <ResourceGroupName> --location <Location>")
                else:
                    print("The name: '" + commands_dict["name"] + "' does not meet Azure naming standards. The name must begin with a word character, end with a word character or '_', "
                       "and may contain word characters, '.', '-', or '_'.")
            else:
                print("Missing required arguments for Azure VM creation.")
                
        elif cloud_provider == "gcp":

            #Check if the necessary attributes are present in the conf file
            if (["name", "image", "imageproject", "zone"] <= list(commands_dict.keys())):

                #Checks if the name matches GCP standards
                if commands_dict["name"].islower() and commands_dict["name"].isalnum():
                    gcp_command = ["gcloud", "compute", "instances", "create", commands_dict["name"],
                                "--zone", commands_dict["zone"],
                                "--image", commands_dict["image"],
                                "--image-project", commands_dict["imageproject"]]
                    
                    #Additional attribute for vm
                    if machine_type:
                        gcp_command.extend(["--machine-type", machine_type])
                    if disk_size:
                        gcp_command.extend(["--boot-disk-size", disk_size])

                    # gcp_command.extend(["--format", "json"])

                    print(f"Executing command: {' '.join(gcp_command)}")
                    additional_info = execute_command(gcp_command, True)
                    if additional_info["success"]:
                        vm_info = {
                            'name': commands_dict["name"],
                            'project': commands_dict["project"],  
                            'purpose': vm_doc["purpose"],
                            'team': vm_doc["team"],
                            'os': vm_doc["os"],
                            'Relevant info': additional_info.get("info", "Not specified"),  
                            'status': 'Successfully created' 
                        }


                        create_documentation_file(vm_info)
                else:
                    print("Invalid vm name " + commands_dict["name"] + ". It can only contain lower case letters and numbers.")
            else:
                print("Missing required arguments for GCP VM creation.")
            
        #If port is speicified in teh conf file, then it is opened
        if "port" in commands_dict:
            port = commands_dict["port"]
            if cloud_provider == "azure":
                open_port_azure(commands_dict["resource-group"], commands_dict["name"], port)
            elif cloud_provider == "gcp":
                open_port_gcp(commands_dict["project"], commands_dict["name"], commands_dict["zone"], port)

def move_conf_files():
    """
    Copies the conf files to a new file with time stamps
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for filename in ['azure.conf', 'gcp.conf']:
        if os.path.exists(filename):
            new_name = filename.replace('.conf', f'_{timestamp}.conf')
            with open(filename, 'r') as original_file:
                contents = original_file.read()
            with open(new_name, 'w') as new_file:
                new_file.write(contents)
            print(f"Copied contents of {filename} to {new_name}")

        
def read_conf_file(file_path):
    """
    Reads and parses a .conf file, returning the configurations as a dictionary.
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def main():
    azure_conf_path = './azure.conf'
    gcp_conf_path = './gcp.conf'
    
    if os.path.exists(azure_conf_path):
        azure_config = read_conf_file(azure_conf_path)
    else:
        print(f"{azure_conf_path} does not exist.")

    if os.path.exists(gcp_conf_path):
        gcp_config = read_conf_file(gcp_conf_path)
    else:
        print(f"{gcp_conf_path} does not exist.")
    
    create_vms_from_config(azure_config, "azure")
    create_vms_from_config(gcp_config, "gcp")

    move_conf_files()


if __name__ == "__main__":
    main()


