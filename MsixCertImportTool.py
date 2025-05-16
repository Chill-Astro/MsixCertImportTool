import requests
import subprocess
import os
import sys
import ctypes
import platform 

# --- Constants ---
UPDATE_VERSION_URL = "https://gist.githubusercontent.com/Chill-Astro/7e0d5246d48b0684ac303df756586c38/raw/MCIT_V.txt"
CURRENT_VERSION = "1.1" # Installer Bug Fix

# --- UAC Check and Re-launch Functions ---
def is_admin():
    """Checks if the script is running with administrator privileges."""
    try:
        # This check works specifically on Windows
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        # Return False if the check fails (e.g., not on Windows)
        return False

def run_as_admin():
    """Re-launches the current script with administrator privileges."""
    if not is_admin():
        # Note: We don't print any messages here to ensure UAC is the very first interaction.
        try:
            # Get the path to the current script
            script = os.path.abspath(sys.argv[0])
            # Prepare arguments for the new process (pass existing args)
            # sys.argv[0] is the script name, sys.argv[1:] are other arguments
            # Using list comprehension with f-strings and quoting for robustness with spaces
            params = " ".join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv])
            # Use ShellExecuteW with the "runas" verb to request elevation
            # The '1' at the end means SW_SHOWNORMAL - show the window normally
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            # Return True to indicate that the re-launch request was sent
            return True
        except Exception as e:
            # Print error if re-launch fails BEFORE UAC appears
            print(f"Error: Failed to request elevated privileges. Please run the script as Administrator manually. Error: {e}")
            return False
    else:
        # Already running as admin
        return True

# --- Certificate Import Logic (using PowerShell) ---
def import_cert_logic(certificate_path, store_location, store_name):
    """
    Contains the core certificate import logic using PowerShell's Import-Certificate cmdlet on Windows.
    Assumes administrator privileges if store_location is 'LocalMachine'.

    Args:
        certificate_path (str): The full path to the .cer file.
        store_location (str): The location of the certificate store ("CurrentUser" or "LocalMachine").
        store_name (str): The name of the certificate store (e.g., "Root", "My", "CA").
    """
    # Double-check for admin rights if targeting LocalMachine, though the main flow should handle this
    if store_location.lower() == 'localmachine' and not is_admin():
        print("Internal Error: Import logic called for LocalMachine without administrator privileges.")
        return # Should not happen if main flow is correct

    try:
        # Construct the PowerShell command
        # We need to quote the paths to handle spaces
        powershell_command = f"Import-Certificate -FilePath \"{certificate_path}\" -CertStoreLocation Cert:\\{store_location}\\{store_name}"

        # print(f"Executing command: powershell -Command \"{powershell_command}\"") # Optional: for debugging

        # Execute the PowerShell command
        # Use shell=True might be needed depending on the VM's configuration, but let's try without first
        result = subprocess.run(['powershell', '-Command', powershell_command], check=True, capture_output=True, text=True)
        # If the above fails, try:
        # result = subprocess.run(['powershell', '-Command', powershell_command], check=True, capture_output=True, text=True, shell=True)


        print("\nImport Succeeded!\n") # Success message as requested
        # Optionally print command output/errors for debugging:
        # print("Stdout:", result.stdout)
        # print("Stderr:", result.stderr)


    except subprocess.CalledProcessError as e:
        print(f"\n--- CERTIFICATE IMPORT FAILED ---")
        print(f"Error importing certificate {certificate_path} using PowerShell:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return Code: {e.returncode}")
        # PowerShell errors are often on stderr
        print(f"Stderr: {e.stderr}")
        print(f"-------------------------------")
        # Do not exit immediately on failure, allow user to see message

    except FileNotFoundError:
        print(f"\n--- CERTIFICATE IMPORT FAILED ---")
        print("Error : powershell.exe not found. Make sure PowerShell is installed and in your System's PATH.")
        print(f"-------------------------------")
        # Do not exit immediately on failure, allow user to see message
    except Exception as e:
        print(f"\n--- CERTIFICATE IMPORT FAILED ---")
        print(f"An unexpected error occurred during import: {e}")
        print(f"-------------------------------")
        # Do not exit immediately on failure, allow user to see message

# --- Update Check Function ---
def check_for_updates():
    """Checks for updates by comparing current version with a version file online."""
    try:
        # We don't print "Checking for updates..." here to match the desired output flow
        response = requests.get(UPDATE_VERSION_URL, timeout=5) # Fetch version file, timeout after 5 seconds
        response.raise_for_status() # Raise HTTPError for bad responses (e.g., 404, 500)
        latest_version = response.text.strip() # Get version string from file and remove whitespace

        if latest_version > CURRENT_VERSION:
            print("--- UPDATE AVAILABLE! ---")
            print(f"🎉 A NEW version of MsixCertTool is Available! : {latest_version}")
            print(f"Currently using : {CURRENT_VERSION}")
            # IMPORTANT: Update this URL to your tool's actual release page
            print("Please visit github.com/Chill-Astro/MsixCertImportTool/releases to download the latest release!")
            print("-----------------------")
        elif latest_version == CURRENT_VERSION:
            # This matches the desired "Up to Date" output
            print("🎉 MsixCertTool is Up to Date!\n")
        else:
            # This case handles if the online version is lower, suggesting a dev build or issue
            print("⚠️ This is a DEV. Build of MsixCertTool!\n")

    except requests.exceptions.RequestException as e:
        print("--- UPDATE CHECK FAILED ---")
        print("⚠️ Could not check for updates. Please check your internet connection.")
        print(f"Error: {e}")
        print("-------------------------")
    except Exception as e:
        print("--- UPDATE CHECK FAILED ---")
        print("⚠️ An unexpected error occurred while checking for updates.")
        print(f"Error: {e}")
        print("-------------------------")

# --- Main Execution ---
if __name__ == "__main__":
    # *** UAC Check and Re-launch happens first, BEFORE any other output ***
    if not is_admin():
        # Attempt to re-launch the script with administrator privileges.
        # If successful, the new process will start and this one will likely exit.
        # No print statements before run_as_admin() call as per requirement
        if run_as_admin():
            sys.exit(0) # Exit the non-admin instance
        else:
            # If re-launch failed (e.g., user cancelled UAC)
            print("Failed to get administrator privileges. Exiting.")
            # Keep window open briefly to show error
            input("Press Enter to exit...")
            sys.exit(1) # Exit with an error code

    # *** If we reach here, the script is running with administrator privileges ***

    # Print initial description (This now happens AFTER potential UAC prompt)
    print("MsixCertImportTool by Chill-Astro : A CUI App designed to import .cer files in Windows within a few keystrokes! Made in Python!\n")

    # Perform update check immediately after description
    check_for_updates()

    # Define the target store for importing MSIX package signing certificates
    target_store_location = "LocalMachine"
    target_store_name = "Root" # Trusted Root Certification Authorities
    print(f"The Certificate will be imported to the Local Machine's Trusted Root Certification Authourity Store.\n")    

   # --- Loop for getting valid certificate path ---
    cert_file_path = None
    # First, check if a path was provided as a command-line argument in the elevated process
    if len(sys.argv) > 1:
        potential_path = sys.argv[1]
        # Added check for .cer extension
        if os.path.exists(potential_path) and os.path.isfile(potential_path) and potential_path.lower().endswith('.cer'):
             cert_file_path = potential_path # Use the command line argument if valid

    # If no valid path from command line arguments, start the input loop
    if cert_file_path is None:
        while True:
            # Prompt the user for the certificate path
            cert_file_path_input = input("Enter Full Path of the .cer Certificate File : ") # Clarified prompt
            cert_file_path_input = cert_file_path_input.strip().strip('"') # Remove leading/trailing spaces and quotes
            # Validate the certificate file path
            if not os.path.exists(cert_file_path_input):
                print(f"\n--- INPUT ERROR ---")
                print(f"Error: File not found at '{cert_file_path_input}'. Please check the path and try again.\n")                
            elif not os.path.isfile(cert_file_path_input):
                 print(f"\n--- INPUT ERROR ---")
                 print(f"Error: The path '{cert_file_path_input}' is not a valid file. Please enter a file path.\n")                 
            # Added check for .cer extension
            elif not cert_file_path_input.lower().endswith('.cer'):
                 print(f"\n--- INPUT ERROR ---")
                 print(f"Error: The file '{cert_file_path_input}' does not appear to be a .cer file. Please provide the path to your .cer file.\n")
                 
            else:
                # Valid path found, store it and break the loop
                cert_file_path = cert_file_path_input
                break # Exit the validation loop

    # --- Perform the certificate import ---
    # Call the import logic function now that we have admin rights and a valid path
    print(f"\nInitiating import for: {cert_file_path}") # Confirm the path being imported before calling import logic
    import_cert_logic(cert_file_path, target_store_location, target_store_name)

    # --- Exit Prompt ---
    # Keep the console window open until the user presses a key
    input("Enter 0 or q to exit: ")
    sys.exit(0)