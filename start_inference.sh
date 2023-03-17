#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 study_number"
  exit 1
fi

study_number=$1

if [[ $study_number != 1 && $study_number != 2 && $study_number != 3 ]]; then
  echo "Warning: Study number must be 1, 2, or 3."
  echo "If you need more studies, please read the README."
  exit 1
fi

# Check which Python command is available
PYTHON_CMD=""
if command -v python3 > /dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python > /dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python is not installed or not available in the system PATH. Please install Python and try again."
  exit 1
fi

# Check if required Python libraries are installed
REQUIRED_LIBS=("pydicom" "torch" "numpy" "matplotlib" "PIL")
MISSING_LIBS=()

for lib in "${REQUIRED_LIBS[@]}"; do
  if ! $PYTHON_CMD -c "import $lib" > /dev/null 2>&1; then
    MISSING_LIBS+=("$lib")
  fi
done

if [ ${#MISSING_LIBS[@]} -ne 0 ]; then
  echo "The following required Python libraries are missing:"
  for lib in "${MISSING_LIBS[@]}"; do
    echo "  - $lib"
  done
  echo "Please install them using pip and try again."
  exit 1
fi

# Check if storescu is available
if ! command -v storescu > /dev/null 2>&1; then
  echo "storescu is not installed or not available in the system PATH. Please install the DCMTK package and try again."
  echo "You can find installation instructions for various platforms in the following links:"
  echo "  - Ubuntu/Debian: https://packages.debian.org/sid/dcmtk"
  echo "  - Windows: https://www.dcmtk.org/en/dcmtk/dcmtk-tools/"
  echo "  - macOS: https://formulae.brew.sh/formula/dcmtk"
  exit 1
fi

# Check if Docker is available
if ! command -v docker > /dev/null 2>&1; then
  echo "Docker is not installed or not available in the system PATH. Please install Docker and try again."
  exit 1
fi

# Check if the required Docker containers are running
REQUIRED_IMAGES=("jodogne/orthanc-plugins" "ohif/viewer" "maic01234/dcmtk")
MISSING_CONTAINERS=()

for image in "${REQUIRED_IMAGES[@]}"; do
  if ! docker ps --format '{{.Image}}' | grep -q "$image"; then
    MISSING_CONTAINERS+=("$image")
  fi
done

if [ ${#MISSING_CONTAINERS[@]} -ne 0 ]; then
  echo "The following required Docker containers are not running:"
  for container in "${MISSING_CONTAINERS[@]}"; do
    echo "  - $container"
  done
  echo "Please remember to start the containers with docker compose up"
  exit 1
fi

# Check that folders exists if not create them
if [ ! -d "images" ]; then
    mkdir images
fi

if [ ! -d "report" ]; then
    mkdir report
fi

if [ ! -d "report/sent" ]; then
    mkdir report/sent
fi

if [ ! -d "report/temp" ]; then
    mkdir report/temp
fi

if [ ! -d "data/received" ]; then
    mkdir data/received
fi

# Send volume to server
storescu localhost 4242 -v -aec Orthanc +r +sd "data/to_send/Study$study_number"

echo "Go to the website http://localhost:3000 and check the image uploaded."
echo "**********************************************************************"
echo -e "\033[32mPress 'y' to continue the inference, press 'n' to abort the operation.\033[32m"
echo "**********************************************************************"
read -r -n 1 continue_inference
echo

if [ "$continue_inference" == "y" ] || [ "$continue_inference" == "Y" ]; then
  $PYTHON_CMD inference.py ./data/received/
else
  echo "Inference aborted."
  exit 0
fi

echo -e "\033[32mInference completed sucessfully"
echo -e "\033[32mReport sended to the Orthanc server sucessfully"
echo -e "\033[32mPlease check the report by updating localhost:3000 to see it on the OHIF Viewer"
echo -e "\033[32mAll done here!"