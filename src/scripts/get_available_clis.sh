#!/bin/bash


determineVersion() {
    local message="$1"
    
    # Use awk to capture a version number pattern
    # The pattern captures versions like: x.y.z, x.y, x.y.z.a, etc.
    local version=$(echo "$message" | awk 'match($0, /[0-9]+(\.[0-9]+)+/) {print substr($0, RSTART, RLENGTH); exit}')
    
    echo "$version"
}

# Define languages, tools, and their respective check commands
declare -A languages=(
    ["node"]="node -v"
    ["npm"]="npm -v"
    ["go"]="go version"
    ["php"]="php -v"
    ["python"]="python --version"
    ["java"]="java -version"
    ["rust"]="rustc --version"
    ["bash"]="bash --version"
    ["sqlite3"]="sqlite3 --version"
    ["ruby"]="ruby -v"
    ["perl"]="perl -v"
    ["docker"]="docker --version"
    ["docker-compose"]="docker-compose --version"
    ["terraform"]="terraform version"
    ["typescript"]="tsc --version"
    ["awscli"]="aws --version"
    ["jq"]="jq --version"
    ["git"]="git --version"
    ["kubectl"]="kubectl version --client"
    ["ansible"]="ansible --version"
    ["vagrant"]="vagrant --version"
    ["mysql"]="mysql --version"
    ["psql"]="psql --version"
    ["mongo"]="mongo --version"
    ["dotnet"]="dotnet --version"
    ["helm"]="helm version --client"
    ["az"]="az --version"
    ["gcloud"]="gcloud --version"
    ["vault"]="vault version"
)

# Start with an empty JSON object
json="{}"

for lang in "${!languages[@]}"; do
    # Attempt to get the message, capturing stdout (and discarding stderr to avoid potential errors in output)
    message=$(${languages[$lang]} 2>/dev/null | tr -d '\n')
    
    # If command succeeded, process the message to extract the version
    if [ $? -eq 0 ]; then
        version=$(determineVersion "$message")

        # If both the message and version are non-empty, include them in the output
        if [[ -n "$message" && -n "$version" ]]; then
            # Use jq to safely add the new structure to the existing JSON
            json=$(echo "$json" | jq --arg key "$lang" --arg message "$message" --arg version "$version" '. + {($key): {"message": $message, "version": $version}}')
        fi
    fi
done

echo "$json" | jq -c .