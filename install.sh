#!/bin/bash
# Enable error handling
set -e

if [ ! -d "scripts" ]; then
    echo "Please run the script from the root directory of the project."
    exit 1
fi

echo "Checking if Python 3 is installed..."
if ! python3 --version &>/dev/null; then
    echo "Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MIN_VERSION="3.10.0"

if [[ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
    echo "Detected Python version is less than 3.10.0. Please upgrade your Python version."
    exit 1
else
    echo "Python version is compatible."
fi

echo "Checking if \"envsubtrans\" folder exists..."
if [ -d "envsubtrans" ]; then
    echo "\"envsubtrans\" folder already exists."
    read -p "Do you want to perform a clean install? This will delete the existing environment. (Y/N): " user_choice
    if [ "$user_choice" = "Y" ] || [ "$user_choice" = "y" ]; then
        echo "Performing a clean install..."
        rm -rf envsubtrans
        [ -f .env ] && rm .env
    elif [ "$user_choice" != "N" ] && [ "$user_choice" != "n" ]; then
        echo "Invalid choice. Exiting installation."
        exit 1
    fi
fi

python3 -m venv envsubtrans
source envsubtrans/bin/activate

scripts/generate-cmd.sh gui-subtrans
scripts/generate-cmd.sh llm-subtrans

echo "Select which provider you want to install:"
echo "0 = None"
echo "1 = OpenAI"
echo "2 = Google Gemini"
echo "3 = Anthropic Claude"
read -p "Enter your choice (0/1/2/3): " provider_choice

case $provider_choice in
    0)
        echo "No additional provider selected. Moving forward without any installations."
        ;;
    1)
        read -p "Enter your OpenAI API Key: " openai_api_key
        if [ -f ".env" ]; then
            sed -i '' "/^OPENAI_/d" .env
            sed -i '' "/^PROVIDER=OpenAI/d" .env
        fi
        echo "PROVIDER=OpenAI" >> .env
        echo "OPENAI_API_KEY=$openai_api_key" >> .env
        echo "Installing OpenAI module..."
        pip install openai
        scripts/generate-cmd.sh gpt-subrans
        ;;
    2)
        read -p "Enter your Google Gemini API Key: " gemini_api_key
        if [ -f ".env" ]; then
            sed -i '' "/^GEMINI_/d" .env
            sed -i '' "/^PROVIDER=Google Gemini/d" .env
        fi
        echo "PROVIDER=Google Gemini" >> .env
        echo "GEMINI_API_KEY=$gemini_api_key" >> .env
        echo "Installing Google GenerativeAI module..."
        pip install google-generativeai
        scripts/generate-cmd.sh gemini-subtrans
        ;;
    3)
        read -p "Enter your Anthropic API Key: " anthropic_api_key
        if [ -f ".env" ]; then
            sed -i '' "/^CLAUDE_/d" .env
            sed -i '' "/^PROVIDER=Claude/d" .env
        fi
        echo "PROVIDER=Claude" >> .env
        echo "CLAUDE_API_KEY=$anthropic_api_key" >> .env
        echo "Installing Anthropic module..."
        pip install anthropic
        scripts/generate-cmd.sh claude-subtrans
        ;;
    *)
        echo "Invalid choice. Exiting installation."
        exit 1
        ;;
esac

echo "Installing required modules..."
pip install --upgrade -r requirements.txt

echo "Setup completed successfully. To uninstall just delete the directory"

exit 0
