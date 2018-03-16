#!powershell
# This file is part of Ansible

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author: Erwan Quelin (mail:erwan.quelin@gmail.com - GitHub: @equelin - Twitter: @erwanquelin)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

# Modules parameters

$path = Get-AnsibleParam -obj $params -name "path" -type "string" -failifempty $true
$minimum_version = Get-AnsibleParam -obj $params -name "minimum_version" -type "string" -failifempty $false

$result = @{
    changed = $false
}

if ($diff_mode) {
    $result.diff = @{}
}

# CODE
# Test if parameter $version is valid
Try {
    $minimum_version = [version]$minimum_version
}
Catch {
    Fail-Json -obj $result -message "Value '$minimum_version' for parameter 'minimum_version' is not a valid version format"
}

# Import Pester module if available
$Module = 'Pester'

If (-not (Get-Module -Name $Module -ErrorAction SilentlyContinue)) {
    If (Get-Module -Name $Module -ListAvailable -ErrorAction SilentlyContinue) {
        Import-Module $Module
    } else {
        Fail-Json -obj $result -message "Cannot find module: $Module. Check if pester is installed, and if it is not, install using win_psmodule or win_chocolatey."
    }
}

# Add actual pester's module version in the ansible's result variable
$Pester_version = (Get-Module -Name $Module).Version.ToString()
$result.pester_version = $Pester_version

# Test if the Pester module is available with a version greater or equal than the one specified in the $version parameter
If ((-not (Get-Module -Name $Module -ErrorAction SilentlyContinue | Where-Object {$_.Version -ge $minimum_version})) -and ($minimum_version)) {
    Fail-Json -obj $result -message "$Module version is not greater or equal to $minimum_version"
}

# Testing if test file or directory exist
If (-not (Test-Path -LiteralPath $path)) {
    Fail-Json -obj $result -message "Cannot find file or directory: '$path' as it does not exist"
}

#Prepare Invoke-Pester parameters depending of the Pester's version.
#Invoke-Pester output deactivation behave differently depending on the Pester's version
If ($result.pester_version -ge "4.0.0") {
    $Parameters = @{
        "show" = "none"
        "PassThru" = $True
    }
} else {
    $Parameters = @{
        "quiet" = $True
        "PassThru" = $True
    }
}

# Run Pester tests
If (Test-Path -Path $path -PathType Leaf) {
    if ($check_mode) {
        $result.output = "Run pester test in the file: $path"
    } else {
        try {
            $result.output = Invoke-Pester $path @Parameters
        } catch {
            Fail-Json -obj $result -message $_.Exception
        }
    }
} else {
    # Run Pester tests against all the .ps1 file in the local folder
    $files = Get-ChildItem -Path $path | Where-Object {$_.extension -eq ".ps1"}

    if ($check_mode) {
        $result.output = "Run pester test(s) who are in the folder: $path"
    } else {
        try {
            $result.output = Invoke-Pester $files.FullName @Parameters
        } catch {
            Fail-Json -obj $result -message $_.Exception
        }
    }
}

$result.changed = $true

Exit-Json -obj $result