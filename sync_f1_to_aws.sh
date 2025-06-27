#!/bin/bash

# --- Configuration ---
# Path to your local F1 Dashboard project directory (relative to where you run this script).
# Change this to '.' if you intend to run the script *from inside* the f1_dashboard directory.
# This tells rsync to sync the current directory.
LOCAL_PROJECT_DIR="./" # <--- REVISED: Use './' to sync the current directory

# Remote user and host alias (as defined in your ~/.ssh/config)
REMOTE_HOST="aws"
REMOTE_USER="ec2-user" # Or 'ubuntu', depending on your EC2 instance's user

# Remote path where you want to sync the files (e.g., your user's home directory)
REMOTE_PATH="/home/${REMOTE_USER}/f1_dashboard/" # This should be the target directory on the remote

# --- Rsync Exclude List ---
EXCLUDES=(
    '.git/'
    '.gitignore'
    '.env*'
    'node_modules/'
    'build/'
    'cache/'
    '*.log'
    '*.tar.gz'
    '*.zip'
    '*.sublime-project'
    '*.sublime-workspace'
    '.vscode/'
    '.idea/'
    '.DS_Store'
    'npm-debug.log'
    'yarn-debug.log'
    'yarn-error.log'
    'coverage/'
    'temp/'
    'tmp/'
    'vendor/bundle/'
    '*.swp'
    '~*'
    'sync_f1_to_aws.sh' # <--- NEW: Exclude the sync script itself if it's in the project dir
)

# --- rsync command ---
echo "Starting rsync to AWS instance..."
echo "Local: ${LOCAL_PROJECT_DIR}"
echo "Remote: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

# Build the --exclude arguments
EXCLUDE_ARGS=""
for EXCL in "${EXCLUDES[@]}"; do
    EXCLUDE_ARGS+="--exclude='$EXCL' "
done

# Perform the rsync
# -a: archive mode (recursive, preserves symlinks, permissions, ownership, timestamps)
# -v: verbose
# -z: compress file data during the transfer
# --delete: deletes extra files on the destination that are not in the source
# Note the trailing slash on "${LOCAL_PROJECT_DIR}" is crucial with './'
rsync -avz --delete ${EXCLUDE_ARGS} \
      "${LOCAL_PROJECT_DIR}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

RSYNC_EXIT_CODE=$?

if [ ${RSYNC_EXIT_CODE} -eq 0 ]; then
    echo "Rsync completed successfully."
elif [ ${RSYNC_EXIT_CODE} -eq 24 ]; then
    echo "Rsync completed with some non-fatal errors (e.g., vanished files). Check output."
else
    echo "Rsync failed with exit code: ${RSYNC_EXIT_CODE}"
    echo "Please check the rsync output for details."
fi

# --- Optional: Restart Docker Compose services on AWS after sync ---
read -p "Do you want to restart Docker Compose services on AWS? (y/N): " -n 1 -r REPLY
echo # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Restarting Docker Compose services on AWS..."
    # Ensure this command is run from the project root on the remote side
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && docker compose down && docker compose up --build -d"
    echo "Docker Compose restart command sent."
else
    echo "Skipping Docker Compose restart."
fi
