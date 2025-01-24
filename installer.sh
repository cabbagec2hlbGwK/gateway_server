#!/bin/bash

# Usage message
usage() {
    echo "Usage: $0 --name <service_name> --script <script_path> --args <script_args> --env <env_vars> --venv <venv_path> --python <python_exec>"
    echo "Example: $0 --name myservice --script /path/to/your_script.py --args '--arg1 value1' --env 'APPROVALSQSURL=https://sqs.us-east-2.amazonaws.com/767397688321/approval_list.fifo IDENTITY_ENDPOINT=https://xjv84b4gg1.execute-api.us-east-2.amazonaws.com/dev/userIdentify OWNERIDENTY=https://sqs.us-east-2.amazonaws.com/767397688321/OwnerIdentification.fifo S3BUCKET=temp-dc-store AWS_DEFAULT_REGION=us-east-2 SENDSQSURL=https://sqs.us-east-2.amazonaws.com/767397688321/OUTEMAIL.fifo SQSURL=https://sqs.us-n21/emailProcessingList.fifo' --venv /path/to/venv --python python"
    exit 1
}

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --name) service_name="$2"; shift ;;
        --script) script_path="$2"; shift ;;
        --args) script_args="$2"; shift ;;
        --env) env_vars="$2"; shift ;;
        --venv) venv_path="$2"; shift ;;
        --python) python_exec="$2"; shift ;;
        *) usage ;;
    esac
    shift
done

# Check if required arguments are provided
if [ -z "$service_name" ] || [ -z "$script_path" ] || [ -z "$venv_path" ] || [ -z "$python_exec" ]; then
    usage
fi

# Create systemd service file
service_file="/etc/systemd/system/$service_name.service"

sudo cat <<EOF > $service_file
[Unit]
Description=$service_name Python Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$(dirname "$script_path")
ExecStart=$venv_path/bin/$python_exec $script_path $script_args
Restart=always
EOF

# Add environment variables if provided
if [ ! -z "$env_vars" ]; then
    IFS=' ' read -r -a env_array <<< "$env_vars"
    for env_var in "${env_array[@]}"; do
        # Check for the presence of AWS_DEFAULT_REGION and ensure no extra quotes
        if [[ "$env_var" == AWS_DEFAULT_REGION* ]]; then
            env_var="${env_var//\"/}"  # Remove quotes if present
        fi
        echo "Environment=\"$env_var\"" | sudo tee -a $service_file > /dev/null
    done
fi

sudo cat <<EOF >> $service_file
[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to apply the new service
sudo systemctl daemon-reload

# Start the service
sudo systemctl start $service_name

# Enable the service to start on boot
sudo systemctl enable $service_name

echo "$service_name service installed and started successfully."

