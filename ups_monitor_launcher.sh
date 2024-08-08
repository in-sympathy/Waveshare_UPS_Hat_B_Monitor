#!/bin/bash
echo "$(tput setaf 3) Initial run of this script should only happen on a Pi itself with a connected display. VNC can be used, but SSH can not. Be warned! $(tput sgr0)"

#CHECKING IF NECESSARY PACKAGES ARE INSTALLED:
echo "$(tput setaf 3) Checking for any previous builds... $(tput sgr0)"
package_name_1="notification-daemon"
if dpkg -l "$package_name_1" >/dev/null 2>&1; then
  echo "$(tput setaf 1) $package_name_1 is already installed $(tput sgr0)"
else
  echo "$(tput setaf 2) $package_name_1 is not installed - fixing $(tput sgr0)"
	sudo apt update && sudo apt install $package_name_1 -y
fi

package_name_2="dunst"
if dpkg -l "$package_name_2" >/dev/null 2>&1; then
  echo "$(tput setaf 1) $package_name_2 is already installed $(tput sgr0)"
else
  echo "$(tput setaf 2) $package_name_2 is not installed - fixing $(tput sgr0)"
	sudo apt update && sudo apt install $package_name_2 -y
fi

echo "Done. Switching to a script installation directory: "
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo "UPS_Monitor.py is located in ${script_dir}"
cd "${script_dir}"
# Get the script filename
script_name=$(basename "$0")


echo "Activating necessary interfaces:"
# Check I2C status (no sudo needed)
i2c_status=$(sudo raspi-config nonint get_i2c)

# Enable I2C if currently disabled (uses sudo)
if [[ $i2c_status -eq 1 ]]; then
  echo "I2C is currently disabled. Enabling..."
  sudo raspi-config nonint do_i2c 0
  configChanged=1
else
  echo "I2C is already enabled."
  configChanged=0
fi



#Crontab autostart - doesnt show desktop notification for some reason after reboot:
echo "Creating cron job: "
# Define the cron job entry
CRON_ENTRY="@reboot export DISPLAY=${DISPLAY} && export XAUTHORITY=${XAUTHORITY} && sleep 10 && ${script_dir}/ups_monitor_launcher.sh"

# Function to check and add cron job (using sudo)
add_cron_job() {
  # Create temporary file with existing cron entries (no sudo needed)
  temp_file="$PWD/crontab.tmp"
  crontab -l 2>/dev/null > "$temp_file" || touch "$temp_file"  # Suppress errors, create empty file if no crontab

  # Check if job is present (avoiding grep on potentially empty file)
  if ! grep -q "$CRON_ENTRY" "$temp_file"; then
    # Add cron job entry to the end of the temporary file
    echo "$CRON_ENTRY" >> "$temp_file"
  fi

  # Update crontab with temporary file content (uses sudo)
  crontab "$temp_file"
  if [ $? -eq 0 ]; then
    echo "Cron job added/updated (if necessary): '$CRON_ENTRY'"
  fi

  # Clean up temporary file (no sudo needed)
  rm -f "$temp_file"
}

# Check for cron job and config change (combined condition)
if [[ ! $(crontab -l 2>/dev/null) =~ $CRON_ENTRY ]] || [[ $configChanged -eq 1 ]]; then
  # Call function to add/update cron job (uses sudo internally)
  add_cron_job

  # Prompt for reboot
  read -r -p "Cron job or configuration changed. Reboot now? (y/N) " response
  case "$response" in
    [yY]*)
      sudo reboot
      ;;
  esac  
fi


# Include a placeholder for the configChanged variable (modify as needed)
configChanged=0  # Replace with logic to determine configuration change

# Optional: Inform about existing cron job (if script reaches this point)
if [[ $(crontab -l 2>/dev/null) =~ $CRON_ENTRY ]]; then
  echo "Cron job already present: '$CRON_ENTRY'"
fi



#Let's try with rc.local:

## File to modify
#file='/etc/rc.local'

## Check if the directory change line is present above 'exit 0'
#if ! grep -Fq "cd ${script_dir}" "$file"; then
#    # If not present, add the line before the 'exit 0'
#    sudo sed -i "/^exit 0/i cd ${script_dir}" "$file"
#    echo "Added 'cd ${script_dir}' to $file"
#else
#    echo "'cd ${script_dir}' already present in $file"
#fi
#
## Check if the script execution line is present
#if ! grep -Fq "./${script_name}" "$file"; then
#    # If not present, add the line before the 'exit 0'
#    sudo sed -i "/^exit 0/i ./${script_name}" "$file"
#    echo "Added './${script_name}' to $file"
#else
#    echo "'./${script_name}' already present in $file"
#fi


#Fixing weird "externally managed environment error in Python 3.11:
if [[ -f "/usr/lib/python3.11/EXTERNALLY-MANAGED" ]]; then
  sudo mv /usr/lib/python3.11/EXTERNALLY-MANAGED /usr/lib/python3.11/EXTERNALLY-MANAGED.old
fi

#If any venv is active:
if [[ "${VIRTUAL_ENV}" != "" ]]; then
  echo "Deactivating virtual environment..."
  deactivate
else
  echo "No virtual environment is currently active."
fi

if [[ -f "Waveshare_UPS_Hat_B_Monitor/bin/activate" ]]; then
  echo "Found venv. Trying to activate"
  source ${PWD##*/}/bin/activate
  echo "Vitrual environment activated."
	echo "Freezing pip requirements"
	pip freeze > requirements.txt
	echo "Upgrading pip requirements"
  pip install --upgrade -r requirements.txt
  echo "All of the requirements are up to date"
else
  echo "Creating virtual environment:"
  python -m venv ${PWD##*/}
  echo "Activating venv:"
  source ${PWD##*/}/bin/activate
	echo "Freezing pip requirements"
	pip freeze > requirements.txt
	echo "Upgrading pip requirements"
  pip install --upgrade -r requirements.txt
  echo "All of the requirements are up to date"
  echo "Ready. Launching UPS_Monitor:"
fi

python UPS_Monitor.py