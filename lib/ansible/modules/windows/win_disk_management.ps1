#!powershell
#
# Copyright 2017, Marc Tschapek <marc.tschapek@bitgroup.de>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

function Search-Disk{

param(
    $DiskSize,
    $PartitionStyle,
    $OperationalStatus
)

$DiskSize = $DiskSize *1GB

Get-Disk | Where-Object {($_.PartitionStyle -eq $PartitionStyle) -and ($_.OperationalStatus -eq $OperationalStatus) -and ($_.Size -eq $DiskSize)}

}

function Set-OperationalStatus{

param(
            [switch]$Online,
            [switch]$Offline,
            $Disk
            )

if($Online){
        Set-Disk -Number ($Disk.Number) -IsOffline $false
}
elseif($Offline){
        Set-Disk -Number ($Disk.Number) -IsOffline $true
}

}

function Set-DiskWriteable{

param(
            $Disk
            )

Set-Disk -Number ($Disk.Number) -IsReadonly $false

}

function Search-Volume{

param(
            $Partition
            )

Get-Volume | Where-Object{$Partition.AccessPaths -like $_.ObjectId}      

}

function Set-Initialized{

param(
            $Disk,
            $PartitionStyle
            )

$Disk| Initialize-Disk -PartitionStyle $PartitionStyle -Confirm:$false -PassThru
}

function Convert-PartitionStyle{

param(
            $Disk,
            $PartitionStyle
            )

Invoke-Expression "'Select Disk $($Disk.Number)','Convert $($PartitionStyle)' | diskpart"
}

function Manage-ShellHWService{

param(
            $action
            )

switch($action){
Stop {Stop-Service -Name ShellHWDetection -PassThru -ErrorAction Stop}
Start {Start-Service -Name ShellHWDetection -PassThru -ErrorAction Stop}
Check {(Get-Service ShellHWDetection -ErrorAction Stop).Status -eq "Running"}
default {throw "Neither '-Stop', '-Start' nor 'Check' switch was passed to the function when invoked. Without the switches the service can not be maintained."}
}
}

function Create-Partition{

param(
            $Disk,
            $SetDriveLetter
            )

$Disk | New-Partition -UseMaximumSize -DriveLetter $SetDriveLetter

}

function Create-Volume{

param(
            $Volume,
            $FileSystem,
            $FileSystemLabel,
            $FileSystemAllocUnitSize,
            $FileSystemLargeFRS,
            $FileSystemShortNames,
            $FileSystemIntegrityStreams
)

$Alloc = $FileSystemAllocUnitSize *1KB

[hashtable]$ParaVol = @{
                                            FileSystem = $FileSystem
                                            NewFileSystemLabel = $FileSystemLabel
                                            AllocationUnitSize = $Alloc
}

if($FileSystem -eq "ntfs"){

        if(!($FileSystemLargeFRS)){
                $Volume | Format-Volume @ParaVol -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }
        else{
                $Volume | Format-Volume @ParaVol -UseLargeFRS -ShortFileNameSupport $FileSystemShortNames -Force -Confirm:$false
        }

}
elseif($FileSystem -eq "refs"){
$Volume | Format-Volume @ParaVol -SetIntegrityStreams $FileSystemIntegrityStreams -Force -Confirm:$false
}

}

$params = Parse-Args $args;

# Create a new result object
$result = [pscustomobject]@{changed=$false;log=[pscustomobject]@{};general_log=[pscustomobject]@{};parameters=[pscustomobject]@{};switches=[pscustomobject]@{}}

## Extract each attributes into a variable
# Find attributes
$Size = Get-Attr -obj $params -name "disk_size" -resultobj $result -failifempty $true
$FindPartitionStyle = Get-Attr -obj $params -name "partition_style_select" -default "raw" -ValidateSet "raw","mbr","gpt" -resultobj $result -failifempty $false
$OperationalStatus = Get-Attr -obj $params -name "operational_status" -default "offline" -ValidateSet "offline","online" -resultobj $result -failifempty $false

# Set attributes partition
$SetPartitionStyle = Get-Attr -obj $params -name "partition_style_set" -default "gpt" -ValidateSet "gpt","mbr" -resultobj $result -failifempty $false
$DriveLetter = Get-Attr -obj $params -name "drive_letter" -default "e" -resultobj $result -failifempty $false
# Set attributes partition
$FileSystem = Get-Attr -obj $params -name "file_system" -default "ntfs" -ValidateSet "ntfs","refs" -resultobj $result -failifempty $false
$Label = Get-Attr -obj $params -name "label" -default "ansible_disk" -resultobj $result -failifempty $false
$AllocUnitSize = Get-Attr -obj $params -name "allocation_unit_size" -default "4" -ValidateSet "4","8","16","32","64" -resultobj $result -failifempty $false
$LargeFRS = Get-Attr -obj $params -name "large_frs" -default $false -type "bool" -resultobj $result -failifempty $false
$ShortNames = Get-Attr -obj $params -name "short_names" -default $false -type "bool" -resultobj $result -failifempty $false
$IntegrityStreams = Get-Attr -obj $params -name "integrity_streams" -default $false -type "bool" -resultobj $result -failifempty $false

# Convert variable for disk size
[int32]$DSize = [convert]::ToInt32($Size, 10)

# Define script environment variables
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

# Rescan disks
try{
Invoke-Expression '"rescan" | diskpart' | Out-Null
   }
catch{
Set-Attr $result.general_log "rescan_disks" "failed"
}

Set-Attr $result.general_log "rescan_disks" "successful"

[hashtable]$ParamsDisk = @{
                          DiskSize = $DSize
                          PartitionStyle = $FindPartitionStyle
                          OperationalStatus = $OperationalStatus
                          }

# Search disk
try{
$disk = Search-Disk @ParamsDisk
}
catch{
Set-Attr $result.general_log "search_disk" "failed"
Fail-Json $result $_
}

if($disk){
            $diskcount = $disk | Measure-Object | Select-Object  -ExpandProperty Count
                                                      if($diskcount -ge 2){
                                                                                        $disk = $disk[0]
                                                                                        [string]$DiskNumber = $disk.Number
                                                                                        [string]$Location = $disk.Location
                                                                                        [string]$SerialN = $disk.SerialNumber
                                                                                        [string]$UniqueID = $disk.UniqueId
                                                                                        Set-Attr $result.log "disk" "Disks found: $diskcount, choosed: Disk number: $DiskNumber, Location: $Location, Serial Number: $SerialN, Unique ID: $UniqueID"
                                                                                        }
                                                      else{
                                                              [string]$DiskNumber = $disk.Number
                                                              [string]$Location = $disk.Location
                                                              [string]$SerialN = $disk.SerialNumber
                                                              [string]$UniqueID = $disk.UniqueId
                                                              Set-Attr $result.log "disk" "Disks found: $diskcount, Disk number: $DiskNumber, Location: $Location, Serial Number: $SerialN, Unique ID: $UniqueID"
                                                              }
}
else{
        Set-Attr $result.log "disk" "Disks found: 0, Disk number: n.a., Location: n.a., Serial Number: n.a., Unique ID: n.a."
        Set-Attr $result.general_log "search_disk" "failed"
        Fail-Json $result "No disk found (size or property is wrong or disk is not attached)."
}

Set-Attr $result.general_log "search_disk" "successful"

# Check and set Operational Status and writeable state
$SetOnline = $false
[string]$DPartStyle = $disk.PartitionStyle
if($DPartStyle -eq "RAW"){
    Set-Attr $result.log "operational_status" "Disk set not online because partition style is $DPartStyle"
    Set-Attr $result.log "disk_writeable" "Disk need not set to writeable because partition style is $DPartStyle"
}
else{
        if($disk.OperationalStatus -eq "Online"){
                Set-Attr $result.log "operational_status" "Disk is online already"
        }
        else{
                try{
                    Set-OperationalStatus -Online -Disk $disk
                }
                catch{
                            Set-Attr $result.general_log "set_operational_status" "failed"
                            Set-Attr $result.log "operational_status" "Disk failed to set online"
                            Fail-Json $result $_
                            }
                Set-Attr $result.log "operational_status" "Disk set online"
                Set-Attr $result "changed" $true;
                $SetOnline = $true   
                
                try{
                    Set-DiskWriteable -Disk $disk
                }
                catch{
                            Set-Attr $result.general_log "set_writeable_status" "failed"
                            Set-Attr $result.log "disk_writeable" "Disk failed to set from read-only to writeable"
                            Fail-Json $result $_
                            }
                Set-Attr $result.log "disk_writeable" "Disk set set from read-only to writeable"
                Set-Attr $result "changed" $true;                               
        }      
}

Set-Attr $result.general_log "set_operational_status" "successful"
Set-Attr $result.general_log "set_writeable_tatus" "successful"

# Check volumes and partitions
[string]$PartNumber = $disk.NumberOfPartitions
$OPStatusFailed = $false
if($PartNumber -ge 1){

                try{
                     $Fpartition = Get-Partition -DiskNumber ($disk.Number)
                }
                catch{
                        Set-Attr $result.general_log "check_volumes_partitions" "failed"
                        Fail-Json $result "General error while getting partitions of found disk."
                }

                [string]$PartType = $Fpartition.Type

                try{
                    $volume = Search-Volume -Partition $Fpartition
                }
                catch{
                        Set-Attr $result.general_log "check_volumes_partitions" "failed"
                        if($SetOnline){
                                        try{
                                            Set-OperationalStatus -Offline -Disk $disk
                                        }
                                        catch{
                                                $OPStatusFailed = $true
                                        }
                                        if(!$OPStatusFailed){
                                                        Set-Attr $result.general_log "set_operational_status" "successful"
                                                        Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                                        Set-Attr $result "changed" $true;
                                        }
                                        else{
                                                Set-Attr $result.general_log "set_operational_status" "failed"
                                                Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                                        }
                        }
                        else{
                              Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
                        }
                        Fail-Json $result $_
                            }
                

                if(!$volume){
                                        Set-Attr $result.log "existing_volumes" "Volumes found: 0"
                                                Set-Attr $result.log "existing_partitions" "Partition Style: $DPartStyle, Partitions found: $PartNumber, Partition types: $PartType"
                                                Set-Attr $result.general_log "check_volumes_partitions" "failed"
                                                if($SetOnline){
                                                            try{
                                                                Set-OperationalStatus -Offline -Disk $disk
                                                            }
                                                            catch{
                                                                    $OPStatusFailed = $true
                                                            }
                                                            if(!$OPStatusFailed){
                                                                            Set-Attr $result.general_log "set_operational_status" "successful"
                                                                            Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                                                            Set-Attr $result "changed" $true;
                                                            }
                                                            else{
                                                                    Set-Attr $result.general_log "set_operational_status" "failed"
                                                                    Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                                                            }
                                                }
                                                else{
                                                        Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
                                                }
                                                Fail-Json $result "Existing terminating partitions recognized on found disk."
                }
                else{
                    [string]$VolNumber = ($volume | Measure-Object).Count 
                    [string]$VolType = $volume.FileSystem
                    Set-Attr $result.log "existing_volumes" "Volumes found: $VolNumber, Volume types: $VolType, Partition Style: $DPartStyle, Partitions found: $PartNumber, Partition types: $PartType"
                    Set-Attr $result.general_log "check_volumes_partitions" "failed"
                    if($SetOnline){
                               try{
                                    Set-OperationalStatus -Offline -Disk $disk
                                }
                                catch{
                                        $OPStatusFailed = $true
                                }
                                if(!$OPStatusFailed){
                                                Set-Attr $result.general_log "set_operational_status" "successful"
                                                Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                                Set-Attr $result "changed" $true;
                                }
                                else{
                                        Set-Attr $result.general_log "set_operational_status" "failed"
                                        Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                                }
                    }
                    else{
                            Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
                    }
                    Fail-Json $result "Existing volumes recognized on found disk."
                }
 
}
else{
    Set-Attr $result.log "existing_volumes" "Volumes found: 0"
    Set-Attr $result.log "existing_partitions" "Partition Style: $FindPartitionStyle, Partitions found: $PartNumber" 
}

Set-Attr $result.general_log "check_volumes_partitions" "successful"


# Check set parameters
[char]$DriveLetter = [convert]::ToChar($DriveLetter)
if((Get-Partition).DriveLetter -notcontains $DriveLetter){
                                                                Set-Attr $result.parameters "drive_letter_set" "$DriveLetter"
                                                                Set-Attr $result.parameters "drive_letter_used" "no"
}
else{
    Set-Attr $result.parameters "drive_letter_set" "$DriveLetter"
    Set-Attr $result.parameters "drive_letter_used" "yes"
    Set-Attr $result.general_log "check_parameters" "failed"
    Fail-Json $result "Partition parameter 'SetDriveLetter' with value $DriveLetter is already set on another partition on this server which is not allowed."
}

if($DriveLetter -ne "C" -and $DriveLetter -ne "D"){
                                                                                    Set-Attr $result.parameters "forbidden_drive_letter_set" "no"
}
else{
    Set-Attr $result.parameters "forbidden_drive_letter_set" "yes"
    Set-Attr $result.general_log "check_parameters" "failed"
    Fail-Json $result "Partition parameter 'SetDriveLetter' with value $DriveLetter contains protected letters C or D."
}

if($FileSystem -eq "ntfs"){
                                                Set-Attr $result.parameters "file_system" "$FileSystem"
                                                if($DSize -le 256000){
                                                                                    Set-Attr $result.parameters "disk_size" "$($DSize)gb"
                                                                                    Set-Attr $result.parameters "allocation_unit_size" "$AllocUnitSize KB"
                                                }
                                                else{
                                                    Set-Attr $result.parameters "disk_size" "$($DSize)gb"
                                                    Set-Attr $result.general_log "check_parameters" "failed"
                                                    if($SetOnline){
                                                                try{
                                                                    Set-OperationalStatus -Offline -Disk $disk
                                                                }
                                                                catch{
                                                                        $OPStatusFailed = $true
                                                                }
                                                                if(!$OPStatusFailed){
                                                                                Set-Attr $result.general_log "set_operational_status" "successful"
                                                                                Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                                                                Set-Attr $result "changed" $true;
                                                                }
                                                                else{
                                                                        Set-Attr $result.general_log "set_operational_status" "failed"
                                                                        Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                                                                }
                                                    }
                                                    else{
                                                            Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
                                                    }
                                                    Fail-Json $result "Disk parameter 'FindSize' with value $DSize GB is not a valid size for NTFS. Disk will be findable but could be not formatted with this file system."
                                                }
}
elseif($FileSystem -eq "refs"){
                                                    Set-Attr $result.parameters "file_system" "$FileSystem"
                                                    if($AllocUnitSize -ne 64){
                                                                                                $AllocUnitSize = 64
                                                                                                Set-Attr $result.parameters "allocation_unit_size" "$($AllocUnitSize)kb_adjusted_refs"
                                                    }
                                                    else{
                                                        Set-Attr $result.parameters "allocation_unit_size" "$($AllocUnitSize)_kb"
                                                    }
}

Set-Attr $result.general_log "check_parameters" "successful"

# Check set switches
if($LargeFRS){
                        Set-Attr $result.switches "large_frs" "enabled"
                        if($FileSystem -ne "refs"){
                                                                    Set-Attr $result.switches "large_frs" "enabled_activated_no_refs"
                                                                    }
                        else{
                                Set-Attr $result.switches "large_frs" "enabled_deactivated_refs"
                                }
}
else{
    Set-Attr $result.switches "large_frs" "disabled"
}

if($ShortNames){
                        Set-Attr $result.switches "short_names" "enabled"
                        if($FileSystem -ne "refs"){
                                                                    Set-Attr $result.switches "short_names" "enabled_activated_no_refs)"
                                                                    }
                        else{
                                Set-Attr $result.switches "short_names" "enabled_deactivated_refs"
                                }
}
else{
    Set-Attr $result.switches "short_names" "disabled"
}

if($IntegrityStreams){
                        Set-Attr $result.switches "integrity_streams" "enabled"
                        if($FileSystem -eq "refs"){
                                                                     Set-Attr $result.switches "integrity_streams" "enabled_activated_no_ntfs"
                                                                    }
                        else{
                                Set-Attr $result.switches "integrity_streams" "enabled_deactivated_ntfs"
                                }
}
else{
    Set-Attr $result.switches "integrity_streams" "disabled"
}

Set-Attr $result.general_log "check_switches" "successful"

# Initialize / convert disk
if($DPartStyle -eq "RAW"){
                            try{
                                $Initialize = Set-Initialized -Disk $disk -PartitionStyle $SetPartitionStyle
                            }
                            catch{
                                    Set-Attr $result.general_log "initialize_convert_disk" "failed"
                                    Set-Attr $result.log "initialize_disk" "Disk initialization failed - Partition style $DPartStyle (partition_style_select) could not be initalized to $SetPartitionStyle (partition_style_set)"
                                    Fail-Json $result $_
                            }
                            Set-Attr $result.log "initialize_disk" "Disk initialization successful - Partition style $DPartStyle (partition_style_select) was initalized to $SetPartitionStyle (partition_style_set)"
                            Set-Attr $result "changed" $true;
}
else{
    # Convert disk
    if($DPartStyle -ne $SetPartitionStyle){
    try{
        $Convert = Convert-PartitionStyle -Disk $disk -PartitionStyle $SetPartitionStyle
    }
    catch{
        Set-Attr $result.general_log "initialize_convert_disk" "failed"
        Set-Attr $result.log "convert_disk" "Partition style $DPartStyle (partition_style_select) could not be converted to $SetPartitionStyle (partition_style_set)"
            if($SetOnline){
                       try{
                            Set-OperationalStatus -Offline -Disk $disk
                        }
                        catch{
                                $OPStatusFailed = $true
                        }
                        if(!$OPStatusFailed){
                                        Set-Attr $result.general_log "set_operational_status" "successful"
                                        Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                        Set-Attr $result "changed" $true;
                        }
                        else{
                                Set-Attr $result.general_log "set_operational_status" "failed"
                                Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                        }
            }
            else{
                    Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
            }
        Fail-Json $result $_
    }
    Set-Attr $result.log "convert_disk" "Partition style $DPartStyle (partition_style_select) was converted to $SetPartitionStyle (partition_style_set)"
    Set-Attr $result "changed" $true;
    }
    else{
    # No convertion
    Set-Attr $result.log "convert_disk" "$SetPartitionStyle (partition_style_set) is equal to selected partition style of disk, no convertion needed"
    }
}

Set-Attr $result.general_log "initialize_convert_disk" "successful"

# Maintain ShellHWService (not module terminating)
$StopSuccess = $false
$StopFailed = $false
$StartFailed = $false
try{
    $Check = Manage-ShellHWService -Action "Check"
}
catch{
        Set-Attr $result.general_log "maintain_shellhw_service" "failed"
        Set-Attr $result.log "shellhw_service_state" "Check failed"
}

if($Check){
                try{
                    Manage-ShellHWService -Action "Stop"
                    }
                catch{
                        $StopFailed = $true
                          }
                if(!$StopFailed){
                            Set-Attr $result.general_log "maintain_shellhw_service" "successful"
                            Set-Attr $result.log "shellhw_service_state" "Set from Running to Stopped"
                            $StopSuccess = $true
                            Set-Attr $result "changed" $true;
                }
                else{
                        Set-Attr $result.general_log "maintain_shellhw_service" "failed"
                        Set-Attr $result.log "shellhw_service_state" "Could not be set from Running to Stopped"
                }
}
else{
Set-Attr $result.log "shellhw_service_state" "Already Stopped"
Set-Attr $result.general_log "maintain_shellhw_service" "successful"
}

# Part disk
try{
    $CPartition = Create-Partition -Disk $disk -SetDriveLetter $DriveLetter
}
catch{
        Set-Attr $result.general_log "create_partition" "failed"
        Set-Attr $result.log "partitioning" "Partition was failed to create on disk with partition style $SetPartitionStyle"
            if($SetOnline){
                    try{
                        Set-OperationalStatus -Offline -Disk $disk
                    }
                    catch{
                            $OPStatusFailed = $true
                    }
                    if(!$OPStatusFailed){
                                    Set-Attr $result.general_log "set_operational_status" "successful"
                                    Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                    Set-Attr $result "changed" $true;
                    }
                    else{
                            Set-Attr $result.general_log "set_operational_status" "failed"
                            Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                    }
            }
            else{
                    Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
            }
            if($StopSuccess){
                                    try{
                                        Manage-ShellHWService -Action "Start"
                                        }
                                    catch{
                                            $StartFailed = $true
                                                }
                                    if(!$StartFailed){
                                                Set-Attr $result.log "shellhw_service_state" "Set from Stopped to Running again"
                                                Set-Attr $result "changed" $true;
                                    }
                                    else{
                                            Set-Attr $result.general_log "maintain_shellhw_service" "failed"
                                            Set-Attr $result.log "shellhw_service_state" "Could not be set from Stopped to Running again"
                                    }
            }
            else{
                    Set-Attr $result.log "shellhw_service_state" "Service was stopped already and need not to be started again"  
            }
        Fail-Json $result $_
}

Set-Attr $result.log "partitioning" "Initial partition $($CPartition.Type) was created successfully on partition style $SetPartitionStyle"
Set-Attr $result.general_log "create_partition" "successful"
Set-Attr $result "changed" $true;

# Create volume
[hashtable]$ParamsVol = @{
                                                    Volume = $CPartition
                                                    FileSystem = $FileSystem
                                                    FileSystemLabel = $Label
                                                    FileSystemAllocUnitSize = $AllocUnitSize
                                                    FileSystemLargeFRS = $LargeFRS
                                                    FileSystemShortNames = $ShortNames
                                                    FileSystemIntegrityStreams = $IntegrityStreams
                                                    }

try{
    $CVolume = Create-Volume @ParamsVol
}
catch{
        Set-Attr $result.general_log "create_volume" "failed"
        Set-Attr $result.log "formatting" "Volume was failed to create on disk with partition $($CPartition.Type)"
            if($SetOnline){
                    try{
                        Set-OperationalStatus -Offline -Disk $disk
                    }
                    catch{
                            $OPStatusFailed = $true
                    }
                    if(!$OPStatusFailed){
                                    Set-Attr $result.general_log "set_operational_status" "successful"
                                    Set-Attr $result.log "operational_status" "Disk set online and now offline again"
                                    Set-Attr $result "changed" $true;
                    }
                    else{
                            Set-Attr $result.general_log "set_operational_status" "failed"
                            Set-Attr $result.log "operational_status" "Disk failed to set offline again"
                    }
            }
            else{
                    Set-Attr $result.log "operational_status" "Disk was online already and need not to be set offline"  
            }
            if($StopSuccess){
                                    try{
                                        Manage-ShellHWService -Action "Start"
                                        }
                                    catch{
                                            $StartFailed = $true
                                                }
                                    if(!$StartFailed){
                                                Set-Attr $result.log "shellhw_service_state" "Set from Stopped to Running again"
                                                Set-Attr $result "changed" $true;
                                    }
                                    else{
                                            Set-Attr $result.general_log "maintain_shellhw_service" "failed"
                                            Set-Attr $result.log "shellhw_service_state" "Could not be set from Stopped to Running again"
                                    }
            }
            else{
                    Set-Attr $result.log "shellhw_service_state" "Service was stopped already and need not to be started again"  
            }
        Fail-Json $result $_
}

Set-Attr $result.log "formatting" "Volume $($CVolume.FileSystem) was created successfully on partition $($CPartition.Type)"
Set-Attr $result.general_log "create_volume" "successful"
Set-Attr $result "changed" $true;

# Finally check if ShellHWService needs to be started again
if($StopSuccess){
                        try{
                            Manage-ShellHWService -Action "Start"
                            }
                        catch{
                                $StartFailed = $true
                                    }
                        if(!$StartFailed){
                                    Set-Attr $result.log "shellhw_service_state" "Set from Stopped to Running again"
                                    Set-Attr $result "changed" $true;
                        }
                        else{
                                Set-Attr $result.general_log "maintain_shellhw_service" "failed"
                                Set-Attr $result.log "shellhw_service_state" "Could not be set from Stopped to Running again"
                        }
}
else{
        Set-Attr $result.log "shellhw_service_state" "Service was stopped already and need not to be started again"  
}

Exit-Json $result;
