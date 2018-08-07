#!powershell
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Daniele Lazzari  <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
$result = @{
    'changed' = $False;
    'output'  = @()
}
Function Invoke-Query {
    Param(
        [string]$Query,
        [int]$QueryTimeout,
        [string]$Database,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [Security.SecureString]$ServerInstancePassword,
        [bool]$CheckMode
    )
    $output = @()
    try {
        if (!($CheckMode)) {
            if (!($ServerInstanceUser) -or !($ServerInstancePassword)) {
                $res = Invoke-SqlCmd -ServerInstance $ServerInstance -Database $Database -Query $Query -QueryTimeout $QueryTimeout
            }
            else {
                $SQLCredentials = New-Object -TypeName System.Management.Automation.PSCredential ($ServerInstanceUser, $ServerInstancePassword)
                $res = Invoke-SqlCmd -ServerInstance $ServerInstance -Query $Query -Database $Database -Credential $SQLCredentials -QueryTimeout $QueryTimeout
            }
        }
    }
    catch {
        $result.query = $Query
        $result.database = $Database
        Fail-Json -obj $result -message "Error: $($_.exception.message)"
    }
    if ($res) {
        Switch ($res.GetType()|Select-Object -ExpandProperty Name) {
            "Object[]" {$Columns = $res[0].Table.Columns.Caption; $output = $res |Select-Object -Property $Columns}
            "DataRow" {$Columns = $res.Table.Columns.Caption; $output = @($res |Select-Object -Property $Columns)}
        }
    }
    $result.output = $output
    $result.changed = $true
    Exit-Json $result
}

$params = Parse-Args $args -supports_check_mode $true

$query = Get-AnsibleParam -obj $params -name "query" -type "str" -failifempty $true
$queryTimeout = Get-AnsibleParam -obj $params -name "query_timeout" -type "int" -default 60
$database = Get-AnsibleParam -obj $params -name "database" -type "string" -default 'master'
$serverInstance = Get-AnsibleParam -obj $params -name "server_instance" -type "str" -default $env:COMPUTERNAME
$serverInstanceUser = Get-AnsibleParam -obj $params -name "server_instance_user" -type "str" -default $NULL
$serverInstancePassword = Get-AnsibleParam -obj $params -name "server_instance_password" -type "str" -default $NULL
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

Invoke-Query -Query $query `
    -QueryTimeout $queryTimeout `
    -Database $database `
    -ServerInstance $serverInstance `
    -ServerInstanceUser $serverInstanceUser `
    -ServerInstancePassword ($serverInstancePassword | ConvertTo-SecureString -AsPlainText -Force) `
    -CheckMode $check_mode
