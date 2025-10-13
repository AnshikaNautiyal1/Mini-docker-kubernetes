"""
EduDistOS Master Controller
==========================

This is a distributed operating system master controller that manages containers
across multiple nodes. It provides a command-line interface for:

- Listing running containers with detailed information
- Starting new containers on remote nodes
- Stopping running containers
- Viewing detailed container information including resource usage, network settings, etc.

The system uses TCP socket communication to send commands to worker nodes
and displays container information in a user-friendly format.

Author: EduDistOS Team
Version: 1.0
Date: 2025

Usage:
    python master.py
    
Commands:
    list [container_id]  - List all containers or show details for specific container
    run <image>         - Start a new container with specified image
    stop <container_id> - Stop a running container
    help                - Show available commands
    exit/quit           - Exit the program
"""

# Import required modules
import socket      # For TCP socket communication with worker nodes
import json        # For JSON data handling (future use for structured data exchange)
from datetime import datetime  # For timestamp handling (future use for logging)

# Sample container data structure - represents the state of containers in the system
# This data would typically come from worker nodes via the send_command function
# Sample container data structure - represents the state of containers in the system
# This data would typically come from worker nodes via the send_command function
SAMPLE_CONTAINERS = [
    {
        # Basic container identification
        "container_id": "c1f2e3d4a5b6",        # Unique identifier for the container
        "container_name": "web-server-prod",   # Human-readable name
        "image_name": "nginx",                 # Docker image name
        "image_tag": "latest",                 # Image version/tag
        
        # Container runtime state information
        "state": {
            "status": "running",               # Current status: running, stopped, paused, etc.
            "started_at": "2025-10-12T17:30:05Z",  # When container was started
            "finished_at": None,               # When container finished (None if still running)
            "exit_code": None,                 # Exit code when container stops
            "error": ""                        # Any error messages
        },
        "created_at": "2025-10-12T17:30:00Z", # When container was created
        
        # Process and resource usage details
        "process_details": {
            "pid": 12345,                     # Process ID of the main container process
            "command": ["nginx", "-g", "daemon off;"],  # Command being executed
            "cpu_usage": "5.2%",              # Current CPU usage percentage
            "memory_usage": "128.5MB"         # Current memory usage
        },
        
        # Metadata for organization and management
        "metadata": {
            "labels": {                       # Key-value pairs for categorization
                "app": "frontend",
                "tier": "web",
                "environment": "production"
            },
            "annotations": {                  # Additional descriptive information
                "description": "Handles production ingress traffic",
                "owner": "devops-team"
            }
        },
        
        # Resource allocation configuration
        "resource_config": {
            "requests": {                     # Minimum resources guaranteed
                "cpu": "250m",                # CPU in millicores (250m = 0.25 CPU cores)
                "memory": "128Mi"             # Memory in mebibytes
            },
            "limits": {                       # Maximum resources allowed
                "cpu": "500m",                # Maximum CPU allocation
                "memory": "256Mi"             # Maximum memory allocation
            }
        },
        
        # Network configuration and connectivity
        "network_settings": {
            "ip_address": "172.17.0.2",       # Container's IP address
            "ports": [                        # Port mappings
                {
                    "host_port": 8080,        # Port on the host machine
                    "container_port": 80,     # Port inside the container
                    "protocol": "TCP"         # Network protocol
                }
            ],
            "dns_servers": ["8.8.8.8"]       # DNS servers for name resolution
        },
        
        # Volume mounts for persistent storage
        "volumes": [
            {
                "type": "bind",               # Type of volume mount
                "source": "/var/data/website",  # Host directory path
                "destination": "/usr/share/nginx/html",  # Container directory path
                "read_only": True             # Whether the mount is read-only
            }
        ],
        
        # Health monitoring configuration
        "health_check": {
            "liveness_probe": {              # Check if container is alive
                "type": "httpGet",           # Type of health check
                "path": "/healthz",          # HTTP endpoint to check
                "port": 80,                  # Port to check
                "initial_delay_seconds": 15, # Wait time before first check
                "period_seconds": 20         # Interval between checks
            },
            "readiness_probe": {             # Check if container is ready to serve traffic
                "type": "tcpSocket",         # Type of readiness check
                "port": 80,                  # Port to check
                "initial_delay_seconds": 5,  # Wait time before first check
                "period_seconds": 10         # Interval between checks
            }
        },
        
        # Security and access control settings
        "security_context": {
            "run_as_user": 1001,             # User ID to run the container as
            "privileged": False,             # Whether container runs in privileged mode
            "capabilities": {                # Linux capabilities
                "add": ["NET_BIND_SERVICE"], # Additional capabilities granted
                "drop": ["ALL"]              # Capabilities to drop
            }
        },
        
        # Container restart behavior
        "restart_policy": {
            "name": "on-failure",            # Restart policy: always, on-failure, never
            "max_retries": 5                 # Maximum restart attempts
        },
        
        # Logging configuration
        "logging_config": {
            "driver": "json-file",           # Logging driver type
            "options": {
                "max-size": "10m",           # Maximum size per log file
                "max-file": "3"              # Maximum number of log files to keep
            }
        }
    }
]

def send_command(node_ip, command):
    """
    Send a command to a remote worker node via TCP socket communication.
    
    This function establishes a TCP connection to the specified node, sends a command,
    receives the response, and returns it. It includes proper error handling for
    common network issues.
    
    Args:
        node_ip (str): IP address of the target worker node
        command (str): Command string to send to the node
        
    Returns:
        str: Response from the node, or error message if connection fails
        
    Example:
        response = send_command("192.168.1.100", "list")
        print(response)  # Outputs container list or error message
    """
    try:
        # Create a TCP socket for communication
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set a timeout to prevent hanging on unresponsive nodes
        s.settimeout(5)  # 5 second timeout
        
        # Connect to the worker node on port 5050
        s.connect((node_ip, 5050))
        
        # Send the command as bytes (encode string to UTF-8)
        s.send(command.encode())
        
        # Receive response with increased buffer size for larger data
        data = s.recv(4096).decode()  # Increased buffer size for container data
        
        # Close the socket connection
        s.close()
        
        # Return the response data
        return data
        
    except socket.timeout:
        # Handle case where node doesn't respond within timeout period
        return "Error: Connection timeout"
    except ConnectionRefusedError:
        # Handle case where no service is listening on the target port
        return "Error: Connection refused - is the node running?"
    except Exception as e:
        # Handle any other unexpected errors
        return f"Error: {str(e)}"

def display_containers(containers):
    """
    Display container information in a formatted table view.
    
    This function takes a list of container dictionaries and displays them in a
    user-friendly table format showing key information like ID, name, image,
    status, resource usage, and port mappings.
    
    Args:
        containers (list): List of container dictionaries to display
        
    Example:
        display_containers(SAMPLE_CONTAINERS)
        # Outputs a formatted table with container information
    """
    # Check if there are any containers to display
    if not containers:
        print("No containers found.")
        return
    
    # Print table header with column names and alignment
    print(f"\n{'Container ID':<15} {'Name':<20} {'Image':<25} {'Status':<10} {'CPU':<8} {'Memory':<10} {'Ports'}")
    print("-" * 100)  # Print separator line
    
    # Iterate through each container and display its information
    for container in containers:
        # Extract and truncate container ID to fit column width
        container_id = container['container_id'][:12]
        
        # Extract and truncate container name to fit column width
        name = container['container_name'][:19]
        
        # Combine image name and tag, truncate to fit column width
        image = f"{container['image_name']}:{container['image_tag']}"[:24]
        
        # Extract and truncate status to fit column width
        status = container['state']['status'][:9]
        
        # Extract and truncate CPU usage to fit column width
        cpu = container['process_details']['cpu_usage'][:7]
        
        # Extract and truncate memory usage to fit column width
        memory = container['process_details']['memory_usage'][:9]
        
        # Format port mappings for display
        ports = []
        for port in container['network_settings']['ports']:
            # Create port mapping string in format "host:container"
            ports.append(f"{port['host_port']}:{port['container_port']}")
        port_str = ", ".join(ports)[:15]  # Join multiple ports and truncate
        
        # Print formatted row with all container information
        print(f"{container_id:<15} {name:<20} {image:<25} {status:<10} {cpu:<8} {memory:<10} {port_str}")

def display_container_details(container_id, containers):
    """
    Display detailed information for a specific container.
    
    This function searches for a container by its ID (supports partial matching)
    and displays comprehensive information including process details, network
    settings, resource usage, and metadata.
    
    Args:
        container_id (str): Container ID to search for (can be partial)
        containers (list): List of container dictionaries to search through
        
    Example:
        display_container_details("c1f2e3d4", SAMPLE_CONTAINERS)
        # Outputs detailed information for the matching container
    """
    # Initialize container variable to track if we find a match
    container = None
    
    # Search through all containers to find a match
    for c in containers:
        # Check if the container ID starts with the provided ID (partial matching)
        if c['container_id'].startswith(container_id):
            container = c
            break  # Stop searching once we find a match
    
    # Check if we found a matching container
    if not container:
        print(f"Container {container_id} not found.")
        return
    
    # Display container header with name
    print(f"\n=== Container Details: {container['container_name']} ===")
    
    # Display basic container information
    print(f"ID: {container['container_id']}")
    print(f"Image: {container['image_name']}:{container['image_tag']}")
    print(f"Status: {container['state']['status']}")
    print(f"Created: {container['created_at']}")
    print(f"Started: {container['state']['started_at']}")
    
    # Display process and resource information
    print(f"\nProcess Details:")
    print(f"  PID: {container['process_details']['pid']}")
    print(f"  Command: {' '.join(container['process_details']['command'])}")
    print(f"  CPU Usage: {container['process_details']['cpu_usage']}")
    print(f"  Memory Usage: {container['process_details']['memory_usage']}")
    
    # Display network configuration
    print(f"\nNetwork Settings:")
    print(f"  IP Address: {container['network_settings']['ip_address']}")
    # Format port mappings for display
    port_mappings = [f"{p['host_port']}:{p['container_port']}" for p in container['network_settings']['ports']]
    print(f"  Ports: {', '.join(port_mappings)}")
    
    # Display container labels for organization
    print(f"\nLabels:")
    for key, value in container['metadata']['labels'].items():
        print(f"  {key}: {value}")

def handle_list_command(args):
    """
    Handle the 'list' command with optional container ID for detailed view.
    
    This function processes the list command which can be used in two ways:
    1. 'list' - Shows a table of all containers
    2. 'list <container_id>' - Shows detailed information for a specific container
    
    Args:
        args (list): Command arguments where args[0] is 'list' and args[1] is optional container ID
        
    Example:
        handle_list_command(['list'])  # Shows all containers
        handle_list_command(['list', 'c1f2e3d4'])  # Shows details for specific container
    """
    if len(args) > 1:
        # Show detailed information for a specific container
        display_container_details(args[1], SAMPLE_CONTAINERS)
    else:
        # Show table view of all containers
        display_containers(SAMPLE_CONTAINERS)

def handle_run_command(args):
    """
    Handle the 'run' command to start a new container.
    
    This function processes the run command which starts a new container with
    the specified image. Currently simulated, but would send commands to worker nodes
    in a real implementation.
    
    Args:
        args (list): Command arguments where args[0] is 'run' and args[1] is the image name
        
    Example:
        handle_run_command(['run', 'nginx'])  # Starts nginx container
        handle_run_command(['run', 'redis:alpine'])  # Starts redis container with alpine tag
    """
    # Check if image name was provided
    if len(args) < 2:
        print("Usage: run <image_name> [options]")
        return
    
    # Extract the image name from arguments
    image_name = args[1]
    
    # Display what we're doing
    print(f"Starting container with image: {image_name}")
    print("Simulated: Container started successfully")
    
    # In a real implementation, this would:
    # 1. Send the run command to an available worker node
    # 2. Wait for confirmation that the container started
    # 3. Update the local container list with the new container

def handle_stop_command(args):
    """
    Handle the 'stop' command to stop a running container.
    
    This function processes the stop command which stops a running container
    by its ID. Currently simulated, but would send commands to worker nodes
    in a real implementation.
    
    Args:
        args (list): Command arguments where args[0] is 'stop' and args[1] is the container ID
        
    Example:
        handle_stop_command(['stop', 'c1f2e3d4a5b6'])  # Stops specific container
        handle_stop_command(['stop', 'web-server-prod'])  # Stops container by name
    """
    # Check if container ID was provided
    if len(args) < 2:
        print("Usage: stop <container_id>")
        return
    
    # Extract the container ID from arguments
    container_id = args[1]
    
    # Display what we're doing
    print(f"Stopping container: {container_id}")
    print("Simulated: Container stopped successfully")
    
    # In a real implementation, this would:
    # 1. Find which worker node is running the container
    # 2. Send the stop command to that node
    # 3. Wait for confirmation that the container stopped
    # 4. Update the local container list to reflect the stopped state

# Main program entry point - only runs when script is executed directly
if __name__ == "__main__":
    # Display welcome message and available commands
    print("EduDistOS Master Controller")
    print("Available commands: list, run, stop, help, exit")
    print("Type 'help' for more information\n")
    
    # Main command loop - continues until user exits
    while True:
        try:
            # Get user input and clean it up
            cmd = input("EduDistOS> ").strip()
            
            # Skip empty commands
            if not cmd:
                continue
                
            # Split command into arguments for processing
            args = cmd.split()
            command = args[0].lower()  # Convert to lowercase for case-insensitive matching
            
            # Handle exit commands
            if command == "exit" or command == "quit":
                print("Goodbye!")
                break
                
            # Handle help command - display usage information
            elif command == "help":
                print("\nAvailable commands:")
                print("  list [container_id]  - List all containers or show details for specific container")
                print("  run <image>         - Start a new container")
                print("  stop <container_id> - Stop a running container")
                print("  help                - Show this help message")
                print("  exit/quit           - Exit the program")
                
            # Handle list command - show containers or container details
            elif command == "list":
                handle_list_command(args)
                
            # Handle run command - start a new container
            elif command == "run":
                handle_run_command(args)
                
            # Handle stop command - stop a running container
            elif command == "stop":
                handle_stop_command(args)
                
            # Handle unknown commands
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        # Handle Ctrl+C (KeyboardInterrupt) gracefully
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
            
        # Handle any unexpected errors
        except Exception as e:
            print(f"Error: {str(e)}")
