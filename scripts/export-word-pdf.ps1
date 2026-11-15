param([Parameter(Mandatory=$true)][string]$DocumentPath,[Parameter(Mandatory=$true)][string]$PdfPath)
$ErrorActionPreference='Stop'
$word=$null
$document=$null
$initialDocuments=0
try {
    $word=New-Object -ComObject Word.Application
    $initialDocuments=$word.Documents.Count
    if($initialDocuments -eq 0){$word.Visible=$false}
    $word.DisplayAlerts=0
    $document=$word.Documents.Open($DocumentPath,$false,$true)
    $document.ExportAsFixedFormat($PdfPath,17)
    $document.Close(0)
    $document=$null
    Write-Output $PdfPath
} finally {
    if($document){$document.Close(0)}
    if($word -and $word.Documents.Count -eq 0){$word.Quit()}
    if($word){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
