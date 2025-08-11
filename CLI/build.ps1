$env:GOOS = "windows"
$env:GOARCH = "amd64"
go build -o medic-cli.exe


$env:GOOS = "darwin"
$env:GOARCH = "arm64"
go build -o medic-cli-mac-arm64